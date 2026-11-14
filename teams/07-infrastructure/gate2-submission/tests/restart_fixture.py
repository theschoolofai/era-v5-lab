"""Failure-policy fixture for runner regression tests; not a trainer."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import torch
import ckpt
p=argparse.ArgumentParser()
p.add_argument('--config')
p.add_argument('--run-dir',type=Path)
p.add_argument('--resume')
p.add_argument('--mode',choices=['temporary','no-checkpoint','fatal'],required=True)
a=p.parse_args()
if a.mode=='temporary' and a.resume=='none':
    model=torch.nn.Linear(1,1)
    optimizer=torch.optim.SGD(model.parameters(),lr=.1)
    ckpt.save(a.run_dir/'checkpoints',model,optimizer,None,step=0,sampler_cursor=0,
              config=json.loads((a.run_dir/'identity.json').read_text()))
sys.exit(2 if a.mode=='fatal' else 75)
