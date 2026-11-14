"""CPU acceptance fixture; deliberately not the missing MoE production trainer."""
import argparse
import json
import os
from pathlib import Path
import random
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import torch
import ckpt


class Sampler:
    def __init__(self, size, seed):
        self.size = size
        self.generator = torch.Generator().manual_seed(seed)
        self.epoch = 0
        self.cursor = 0
        self.order = torch.randperm(size, generator=self.generator).tolist()

    def batch(self, size):
        ids = []
        for _ in range(size):
            if self.cursor == self.size:
                self.epoch += 1
                self.cursor = 0
                self.order = torch.randperm(self.size, generator=self.generator).tolist()
            ids.append(self.order[self.cursor])
            self.cursor += 1
        return ids

    def state_dict(self):
        return {'size': self.size, 'epoch': self.epoch, 'cursor': self.cursor,
                'order': self.order, 'generator': self.generator.get_state()}

    def load_state_dict(self, state):
        if state['size'] != self.size or sorted(state['order']) != list(range(self.size)) or not 0 <= state['cursor'] <= self.size:
            raise ValueError('Invalid sampler state')
        self.epoch, self.cursor, self.order = state['epoch'], state['cursor'], state['order']
        self.generator.set_state(state['generator'])


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--config', type=Path, required=True)
    p.add_argument('--run-dir', type=Path, required=True)
    p.add_argument('--resume', required=True)
    p.add_argument('--stop-at', type=int)
    p.add_argument('--pause-at', type=int)
    a = p.parse_args()
    c = json.loads(a.config.read_text())
    identity = json.loads((a.run_dir / 'identity.json').read_text())
    if identity['config'] != c:
        raise ValueError('Config changed after admission')
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    random.seed(c['seed'])
    np.random.seed(c['seed'])
    torch.manual_seed(c['seed'])
    model = torch.nn.Sequential(torch.nn.Linear(16, 16), torch.nn.GELU(), torch.nn.Dropout(.3), torch.nn.Linear(16, 4))
    optimizer = torch.optim.AdamW(model.parameters(), lr=.001)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=7, gamma=.95)
    sampler = Sampler(c['dataset_size'], c['seed'] + 1)
    step = 0
    if a.resume != 'none':
        meta = ckpt.load(a.resume, model, optimizer, scheduler, expected_config=identity)
        sampler.load_state_dict(meta['sampler_state'])
        step = meta['step']
        if meta['sampler_cursor'] != step * c['batch_size']:
            raise ValueError('Sampler consumed count mismatch')
    print(json.dumps({'restored_step': step, 'torch': str(torch.__version__), 'device': 'cpu'}), flush=True)
    # Remove speculative records beyond checkpoint; preserve one committed record per step.
    trace = a.run_dir / 'trace.jsonl'
    rows = []
    if trace.exists():
        for line in trace.read_text().splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                break
            if row['step'] <= step:
                rows.append(row)
    if [r['step'] for r in rows] != list(range(1, step + 1)):
        raise ValueError('Missing or duplicated committed trace records')
    ckpt.write_synced(trace, ''.join(json.dumps(r, sort_keys=True) + '\n' for r in rows))
    end = a.stop_at or c['steps']
    with open(trace, 'a', buffering=1) as out:
        while step < end:
            ids = sampler.batch(c['batch_size'])
            base = torch.tensor(ids, dtype=torch.float32).unsqueeze(1)
            # Exercise all global RNGs, dropout, actual ID order, AdamW and scheduler.
            x = torch.sin(base / 10 + torch.arange(16)) + torch.randn(len(ids), 16) * .05
            x = x * (1 + random.random()) + float(np.random.random())
            target = torch.cos(base / 10 + torch.arange(4))
            optimizer.zero_grad(set_to_none=True)
            loss = torch.nn.functional.mse_loss(model(x), target)
            bits = loss.detach().numpy().tobytes().hex()
            loss.backward()
            optimizer.step()
            scheduler.step()
            step += 1
            out.write(json.dumps({'step': step, 'loss': loss.item(), 'loss_float32_hex': bits,
                                  'data_ids': ids, 'lr': scheduler.get_last_lr()}, sort_keys=True) + '\n')
            out.flush()
            os.fsync(out.fileno())
            if step % c['checkpoint_every'] == 0:
                ckpt.save(a.run_dir / 'checkpoints', model, optimizer, scheduler, step=step,
                          sampler_cursor=step*c['batch_size'], sampler_state=sampler.state_dict(), config=identity)
            if step == a.pause_at and a.resume == 'none':
                ckpt.write_synced(a.run_dir / 'paused', str(os.getpid()))
                while True:
                    time.sleep(.1)
    torch.save({'model': model.state_dict(), 'optimizer': optimizer.state_dict(),
                'scheduler': scheduler.state_dict(), 'sampler': sampler.state_dict(), 'rng': ckpt.rng_state()},
               a.run_dir / 'final.pt')


if __name__ == '__main__':
    main()
