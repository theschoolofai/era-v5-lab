"""vllm_probe.py on one Modal NVIDIA L4, vLLM 0.33.0 (Team 12's pin, as in ../kv_cache/), same volume as modal_sgl.py.

    modal run modal_vllm.py::main [--only v2_s002_bf16] [--out-dir out]

Each config writes <out-dir>/<name>.json and <name>.log, as modal_sgl.py does.
"""
import json, os, subprocess
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
app = modal.App('era-v5-g12-vllm-ernie-check')
image = (modal.Image.from_registry('nvidia/cuda:13.0.3-devel-ubuntu24.04', add_python='3.12')
         .pip_install('vllm==0.33.0')
         .env({'CUDA_HOME': '/usr/local/cuda'})
         .add_local_file(HERE / 'vllm_probe.py', '/probe/vllm_probe.py'))
vol = modal.Volume.from_name('era-v5-g12-sglang')
M, P = 'export_t2_s002_fp32', 'ref_s002'
CONFIGS = {
    'v1_s002_fp32': ['--dtype', 'float32', '--eager'],   # exactness, if vLLM runs fp32 (it did not start in 0.33.0)
    'v2_s002_bf16': ['--dtype', 'bfloat16'],
    'v3_s002_fp16': ['--dtype', 'float16'],
}


@app.function(image=image, gpu='L4', volumes={'/vol': vol}, timeout=3600)
def probe(name: str, args: list[str]) -> dict:
    Path('/vol/out').mkdir(exist_ok=True)
    cmd = ['python', '/probe/vllm_probe.py', '--model', f'/vol/{M}', '--prompts', f'/vol/{P}/prompts.json',
           '--out', f'/vol/out/{name}.json', *args]
    env = dict(os.environ, NVIDIA_TF32_OVERRIDE='0') if 'float32' in args else dict(os.environ)
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
    vol.commit()
    f = Path(f'/vol/out/{name}.json')
    return dict(name=name, returncode=p.returncode, log=(p.stdout + '\n' + p.stderr)[-20000:],
                result=json.loads(f.read_text()) if p.returncode == 0 and f.exists() else None)


@app.local_entrypoint()
def main(only: str = '', out_dir: str = 'out'):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    names = [n for n in CONFIGS if not only or n in only.split(',')]
    for r in probe.starmap([(n, CONFIGS[n]) for n in names]):
        (out / f"{r['name']}.log").write_text(r['log'])
        if r['result'] is not None:
            (out / f"{r['name']}.json").write_text(json.dumps(r['result']))
        print(r['name'], 'returncode', r['returncode'], 'result' if r['result'] else 'NO RESULT')
