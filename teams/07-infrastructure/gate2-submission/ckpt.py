"""Team 7 single-process COMPLETE checkpoint store, merged from Week 1. Sharded training needs a later adapter."""
import re
import hashlib
import json
import os
import random
import shutil
import tempfile
from pathlib import Path
import torch
import numpy as np

FORMAT_VERSION = 2


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def config_hash(config):
    return hashlib.sha256(json.dumps(config, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def sync_dir(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_synced(path, text):
    with open(path, "w") as stream:
        stream.write(text)
        stream.flush()
        os.fsync(stream.fileno())


def rng_state():
    state = {"python": random.getstate(), "torch_cpu": torch.get_rng_state(),
             "torch_cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else []}
    try:
        import numpy as np
        name, keys, pos, has_gauss, cached = np.random.get_state()
        state["numpy"] = (name, keys.tolist(), pos, has_gauss, cached)
    except ImportError:
        state["numpy"] = None
    return state


def restore_rng(state):
    random.setstate(state["python"])
    torch.set_rng_state(state["torch_cpu"])
    if state["torch_cuda"]:
        if not torch.cuda.is_available() or len(state["torch_cuda"]) != torch.cuda.device_count():
            raise ValueError("CUDA RNG device count mismatch")
        torch.cuda.set_rng_state_all(state["torch_cuda"])
    if state["numpy"] is not None:
        import numpy as np
        name, keys, pos, has_gauss, cached = state["numpy"]
        np.random.set_state((name, np.array(keys, dtype=np.uint32), pos, has_gauss, cached))


def save(root, model, optimizer, scheduler, *, step, sampler_cursor, config, sampler_state=None):
    if torch.distributed.is_initialized() and torch.distributed.get_world_size() > 1:
        raise RuntimeError("This Week 1 reference does not save distributed/sharded state")
    if type(step) is not int or not 0 <= step < 100000000 or type(sampler_cursor) is not int or sampler_cursor < 0:
        raise ValueError("step must be an integer 0..99999999 and sampler_cursor a nonnegative integer")
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    final = root / f"step-{step:08d}"
    lock = root / f".step-{step:08d}.lock"
    lock.mkdir()  # Atomic single-writer guard. A stale lock requires operator inspection.
    tmp = None
    try:
        if final.exists():
            raise FileExistsError(final)
        tmp = Path(tempfile.mkdtemp(prefix=".incomplete-", dir=root))
        state = {"format_version": FORMAT_VERSION, "model": model.state_dict(),
                 "optimizer": optimizer.state_dict(),
                 "scheduler": scheduler.state_dict() if scheduler else None,
                 "step": step, "sampler_cursor": sampler_cursor, "sampler_state": sampler_state, "config": config,
                 "rng": rng_state(), "model_training": model.training}
        with open(tmp / "state.pt", "wb") as stream:
            torch.save(state, stream)
            stream.flush()
            os.fsync(stream.fileno())
        manifest = {"format_version": FORMAT_VERSION, "step": step,
                    "config_sha256": config_hash(config), "file": "state.pt",
                    "size": (tmp / "state.pt").stat().st_size, "sha256": digest(tmp / "state.pt")}
        write_synced(tmp / "manifest.json", json.dumps(manifest, sort_keys=True))
        write_synced(tmp / "COMPLETE", digest(tmp / "manifest.json") + "\n")
        sync_dir(tmp)
        os.rename(tmp, final)
        tmp = None
        sync_dir(root)
        return final
    finally:
        if tmp is not None:
            shutil.rmtree(tmp)
        lock.rmdir()


def verify(path):
    path = Path(path)
    if not re.fullmatch(r"step-[0-9]{8}", path.name) or path.is_symlink():
        raise ValueError("Not a published checkpoint directory")
    if any((path / name).is_symlink() for name in ("COMPLETE", "manifest.json", "state.pt")):
        raise ValueError("Checkpoint symlinks are unsupported")
    marker = (path / "COMPLETE").read_text().strip()
    if marker != digest(path / "manifest.json"):
        raise ValueError("Manifest checksum mismatch")
    manifest = json.loads((path / "manifest.json").read_text())
    if manifest["format_version"] != FORMAT_VERSION or manifest["file"] != "state.pt":
        raise ValueError("Unsupported checkpoint manifest")
    if path.name != f"step-{manifest['step']:08d}":
        raise ValueError("Checkpoint step/path mismatch")
    if (path / "state.pt").stat().st_size != manifest["size"] or digest(path / "state.pt") != manifest["sha256"]:
        raise ValueError("State checksum mismatch")
    return manifest


def read_state(path):
    manifest = verify(path)
    state = torch.load(Path(path) / "state.pt", map_location="cpu", weights_only=True)
    required = {"format_version", "model", "optimizer", "scheduler", "step",
                "sampler_cursor", "sampler_state", "config", "rng", "model_training"}
    if not isinstance(state, dict) or not required <= state.keys():
        raise ValueError("Incomplete training state")
    if state["format_version"] != FORMAT_VERSION or state["step"] != manifest["step"]:
        raise ValueError("State/manifest mismatch")
    if config_hash(state["config"]) != manifest["config_sha256"]:
        raise ValueError("State configuration mismatch")
    if type(state["sampler_cursor"]) is not int or state["sampler_cursor"] < 0:
        raise ValueError("Invalid sampler cursor")
    if type(state['step']) is not int or type(state['model_training']) is not bool:
        raise ValueError('Invalid step or training mode')
    if not isinstance(state['model'], dict) or not state['model'] or not isinstance(state['optimizer'], dict):
        raise ValueError('Invalid model/optimizer state')
    if not {'state', 'param_groups'} <= state['optimizer'].keys():
        raise ValueError('Incomplete optimizer state')
    if state['scheduler'] is not None and not isinstance(state['scheduler'], dict):
        raise ValueError('Invalid scheduler state')
    if state['sampler_state'] is not None and not isinstance(state['sampler_state'], dict):
        raise ValueError('Invalid sampler state')
    rng = state['rng']
    if not isinstance(rng, dict) or not {'python', 'torch_cpu', 'torch_cuda', 'numpy'} <= rng.keys():
        raise ValueError('Incomplete RNG state')
    random.Random().setstate(rng['python'])
    torch.Generator().set_state(rng['torch_cpu'])
    if not isinstance(rng['torch_cuda'], list):
        raise ValueError('Invalid CUDA RNG state')
    if rng['numpy'] is not None:
        name, keys, pos, has_gauss, cached = rng['numpy']
        np.random.RandomState().set_state((name, np.array(keys, dtype=np.uint32), pos, has_gauss, cached))
    return state


def latest_complete(root, *, expected_config=None, rejected=None):
    # Verify payload as well as hashes; a matching hash alone cannot prove torch
    # serialization or the required state fields are usable.
    for path in sorted(Path(root).glob("step-[0-9]*"), reverse=True):
        try:
            state = read_state(path)
        except Exception as exc:
            if rejected is not None:
                rejected.append({"path": str(path), "reason": str(exc)})
            continue
        if expected_config is not None and config_hash(state["config"]) != config_hash(expected_config):
            raise ValueError("Run configuration mismatch: use a new run directory")
        return path
    raise FileNotFoundError("No verified COMPLETE checkpoint")


def load(path, model, optimizer, scheduler, *, expected_config):
    manifest = verify(path)
    if manifest["config_sha256"] != config_hash(expected_config):
        raise ValueError("Run configuration mismatch")
    # Only use lab-created checkpoints. Hashes detect corruption, not an untrusted writer.
    state = read_state(path)
    if (scheduler is None) != (state["scheduler"] is None):
        raise ValueError("Scheduler presence mismatch")
    model.load_state_dict(state["model"], strict=True)
    optimizer.load_state_dict(state["optimizer"])
    if scheduler:
        scheduler.load_state_dict(state["scheduler"])
    model.train(state["model_training"])
    restore_rng(state["rng"])
    return {"step": state["step"], "sampler_cursor": state["sampler_cursor"],
            "sampler_state": state["sampler_state"]}


# Legacy file API retained for existing callers; no COMPLETE publication contract.
def save_checkpoint(state_dict, filepath):
    """
    Saves a checkpoint atomically using a temporary file followed by an atomic rename
    to prevent corruption if a node crashes mid-write.
    """
    filepath = os.fspath(filepath)
    dir_name = os.path.dirname(filepath) or '.'
    os.makedirs(dir_name, exist_ok=True)
    
    tmp_filepath = filepath + ".tmp"
    
    # Save training state dict, model weights, optimizer, and RNG states
    checkpoint = {
        'model_state': state_dict.get('model').state_dict() if 'model' in state_dict else None,
        'optimizer_state': state_dict.get('optimizer').state_dict() if 'optimizer' in state_dict else None,
        'step': state_dict.get('step', 0),
        'loss': state_dict.get('loss', 0.0),
        'rng_states': {
            'python': random.getstate(),
            'numpy': np.random.get_state(),
            'torch': torch.get_rng_state(),
            'cuda': torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None
        }
    }
    
    # Atomic write to temp file
    torch.save(checkpoint, tmp_filepath)
    
    # Atomic replacement
    os.replace(tmp_filepath, filepath)
    print(f"[CHECKPOINT] Atomically saved checkpoint to {filepath}")

def load_checkpoint(filepath, model=None, optimizer=None):
    """
    Loads a checkpoint and restores model, optimizer, and RNG states for bit-equal resumption.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Checkpoint file not found at {filepath}")
        
    # Includes Python/NumPy RNG objects: load only checkpoints you trust.
    checkpoint = torch.load(filepath, map_location='cpu', weights_only=False)
    
    if model and checkpoint['model_state']:
        model.load_state_dict(checkpoint['model_state'])
    if optimizer and checkpoint['optimizer_state']:
        optimizer.load_state_dict(checkpoint['optimizer_state'])
        
    # Restore RNG states
    rngs = checkpoint['rng_states']
    random.setstate(rngs['python'])
    np.random.set_state(rngs['numpy'])
    torch.set_rng_state(rngs['torch'])
    if torch.cuda.is_available() and rngs['cuda'] is not None:
        torch.cuda.set_rng_state_all(rngs['cuda'])
        
    print(f"[CHECKPOINT] Successfully loaded checkpoint from {filepath} (Step {checkpoint['step']})")
    return checkpoint
