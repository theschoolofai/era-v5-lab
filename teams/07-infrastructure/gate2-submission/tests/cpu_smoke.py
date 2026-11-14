"""CPU tensor/checkpoint utility validation, not a model training replacement."""
from pathlib import Path
import os
import random
import sys
import tempfile
import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ckpt import save_checkpoint, load_checkpoint

print(f'torch={torch.__version__} cuda_available={torch.cuda.is_available()} gpu_count={torch.cuda.device_count()}', flush=True)
assert torch.equal(torch.tensor([1, 2]) + torch.tensor([3, 4]), torch.tensor([4, 6]))
random.seed(7)
np.random.seed(7)
torch.manual_seed(7)
model = torch.nn.Linear(3, 1)
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

def step():
    x = torch.rand(4, 3) + random.random() + float(np.random.rand())
    optimizer.zero_grad()
    loss = model(x).square().mean()
    loss.backward()
    optimizer.step()
    return loss.item()

step()
with tempfile.TemporaryDirectory() as directory:
    previous = os.getcwd()
    try:
        os.chdir(directory)
        save_checkpoint({'model': model, 'optimizer': optimizer, 'step': 1}, 'state.pt')
        assert not Path('state.pt.tmp').exists()
        expected_losses = [step() for _ in range(5)]
        expected_state = {k: v.clone() for k, v in model.state_dict().items()}
        restored = load_checkpoint('state.pt', model, optimizer)
        assert restored['step'] == 1
        actual_losses = [step() for _ in range(5)]
        assert expected_losses == actual_losses, (expected_losses, actual_losses)
        assert all(torch.equal(expected_state[k], v) for k, v in model.state_dict().items())
    finally:
        os.chdir(previous)
print('[PASS] CPU tensor math; atomic checkpoint replacement; model, optimizer and Python/NumPy/Torch RNG restore; five identical resumed CPU losses', flush=True)
