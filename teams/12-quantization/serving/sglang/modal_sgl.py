"""sgl_probe.py on one Modal NVIDIA L4, SGLang 0.5.23 from PyPI (stock, or with patch_topk.py applied in the image).

    modal volume create era-v5-g12-sglang
    modal volume put era-v5-g12-sglang <export dir> /export_t2_s002_fp32
    modal volume put era-v5-g12-sglang <ref dir>/prompts.json /ref_s002/prompts.json
    modal run modal_sgl.py::main                                               # stock: c1, c2, c3
    modal run modal_sgl.py::main --patched --only c2_s002_bf16,c3_s002_fp16    # with patch_topk.py
    modal run modal_sgl.py::check                                              # versions in the image

Each config writes <out-dir>/<name>.json (the probe output, about 860 KB) and <name>.log (the last 20,000 characters
of its output). The outputs stay local; summarize.py turns them into results/spike_summary.json.
"""
import json, os, subprocess
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
app = modal.App('era-v5-g12-sglang-check')
base = (modal.Image.from_registry('nvidia/cuda:13.0.3-devel-ubuntu24.04', add_python='3.12')
        .pip_install('sglang==0.5.23')
        .env({'CUDA_HOME': '/usr/local/cuda'}))
image = base.add_local_file(HERE / 'sgl_probe.py', '/probe/sgl_probe.py')
image_patched = (base.add_local_file(HERE / 'patch_topk.py', '/probe/patch_topk.py', copy=True)
                 .run_commands('python /probe/patch_topk.py')
                 .add_local_file(HERE / 'sgl_probe.py', '/probe/sgl_probe.py'))
vol = modal.Volume.from_name('era-v5-g12-sglang', create_if_missing=True)

M, P = 'export_t2_s002_fp32', 'ref_s002'
CONFIGS = {   # name: probe args
    'c1_s002_fp32': ['--dtype', 'float32', '--attention-backend', 'torch_native', '--disable-cuda-graph'],
    'c2_s002_bf16': ['--dtype', 'bfloat16'],
    # fp16 (10 mantissa bits against bf16's 7): rounding noise should shrink several-fold; a mapping error would not
    'c3_s002_fp16': ['--dtype', 'float16'],
}


def _probe(name: str, args: list[str]) -> dict:
    Path('/vol/out').mkdir(exist_ok=True)
    cmd = ['python', '/probe/sgl_probe.py', '--model', f'/vol/{M}', '--prompts', f'/vol/{P}/prompts.json',
           '--out', f'/vol/out/{name}.json', *args]
    env = dict(os.environ, NVIDIA_TF32_OVERRIDE='0') if 'float32' in args else dict(os.environ)  # no TF32 in cuBLAS
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
    vol.commit()
    f = Path(f'/vol/out/{name}.json')
    return dict(name=name, returncode=p.returncode, log=(p.stdout + '\n' + p.stderr)[-20000:],
                result=json.loads(f.read_text()) if p.returncode == 0 and f.exists() else None)


@app.function(image=image, gpu='L4', volumes={'/vol': vol}, timeout=3600)
def probe(name: str, args: list[str]) -> dict:
    return _probe(name, args)


@app.function(image=image_patched, gpu='L4', volumes={'/vol': vol}, timeout=3600)
def probe_patched(name: str, args: list[str]) -> dict:
    return _probe(name, args)


@app.local_entrypoint()
def main(only: str = '', patched: bool = False, out_dir: str = 'out'):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    names = [n for n in CONFIGS if not only or n in only.split(',')]
    fn = probe_patched if patched else probe
    for r in fn.starmap([(n + ('_patched' if patched else ''), CONFIGS[n]) for n in names]):
        (out / f"{r['name']}.log").write_text(r['log'])
        if r['result'] is not None:
            (out / f"{r['name']}.json").write_text(json.dumps(r['result']))
        print(r['name'], 'returncode', r['returncode'], 'result' if r['result'] else 'NO RESULT')


@app.function(image=image, gpu='L4', timeout=900)
def env_check() -> str:
    import torch, sglang, transformers
    smi = subprocess.run(['nvidia-smi', '--query-gpu=name,driver_version,compute_cap', '--format=csv,noheader'],
                         capture_output=True, text=True).stdout.strip()
    return f'sglang {sglang.__version__}, torch {torch.__version__} (cuda {torch.version.cuda}), ' \
           f'transformers {transformers.__version__}, gpu {smi}, cuda ok {torch.cuda.is_available()}'


@app.local_entrypoint()
def check():
    print(env_check.remote())
