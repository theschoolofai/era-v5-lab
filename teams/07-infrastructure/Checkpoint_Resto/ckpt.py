import os
import torch
import random
import numpy as np

def save_checkpoint(state_dict, filepath):
    """
    Saves a checkpoint atomically using a temporary file followed by an atomic rename
    to prevent corruption if a node crashes mid-write.
    """
    dir_name = os.path.dirname(filepath)
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
        
    checkpoint = torch.load(filepath, map_location='cpu')
    
    if model and checkpoint['model_state']:
        model.load_state_dict(checkpoint['model_state'])
    if optimizer and checkpoint['optimizer_state']:
        optimizer.load_state_dict(checkpoint['optimizer_state'])
        
    # Restore RNG states
    rngs = checkpoint['rng_states']
    random.setstate(rngs['python'])
    np.random.set_state(rngs['numpy'])
    torch.set_rng_state(rngs['rng_states']['torch'])
    if torch.cuda.is_available() and rngs['rng_states']['cuda']:
        torch.cuda.set_rng_state_all(rngs['rng_states']['cuda'])
        
    print(f"[CHECKPOINT] Successfully loaded checkpoint from {filepath} (Step {checkpoint['step']})")
    return checkpoint