#!/usr/bin/env python3
"""Measure size, memory and speed of GGUF files on a Mac and append one row per file to a rows CSV (Lab 5 task 1 and 7).

  python measure_mac.py --bench ./work/llama.cpp-b11669/build/bin/llama-bench --build b11669 \
      --contributor therahulbhati --out rows/therahulbhati_m1_8gb.csv ./work/*.gguf

Two llama-bench runs per file:
  speed:  -p 512 -n 128 -r 5 (prompt and generation tokens/s at an empty context)
  long:   -p 0 -n 16 -d 8192 -r 1 -v (generation tokens/s with 8,192 tokens already in the cache, and the memory)
Memory is what llama.cpp allocates in the long run, read from its own log (-v): the weights (the GGUF, mapped), the KV
cache for the context it reserved, and the compute buffers; total = their sum. macOS's process counters (peak memory
footprint, resident set) leave out the Metal buffers on unified memory, so they are not used. The GPU working-set limit
that llama.cpp reads from Metal (recommendedMaxWorkingSetSize) is recorded too: fits_gpu says whether the total is under it.
No network call. Every row carries the GGUF's sha256, so rows from different Macs can be checked to be the same file.
"""
import argparse, csv, datetime, hashlib, json, platform, re, subprocess, sys
from pathlib import Path

FIELDS = ['date', 'contributor', 'machine', 'chip', 'ram_gb', 'os', 'runtime', 'model', 'format', 'gguf_sha256',
          'size_bytes', 'n_params', 'bpw', 'pp512_tok_s', 'tg128_tok_s', 'depth', 'tg16_at_depth_tok_s',
          'weights_mb', 'kv_mb', 'kv_cells', 'kv_mb_per_1k', 'compute_mb', 'total_mb', 'gpu_working_set_mb', 'fits_gpu',
          'command', 'notes']
FORMATS = ['BF16', 'F16', 'Q8_0', 'Q6_K', 'Q5_K_M', 'Q5_K_S', 'Q4_K_M', 'Q4_K_S', 'Q4_0', 'Q3_K_M', 'Q3_K_S', 'Q2_K']


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def fmt_from_name(name: str) -> str:
    """The format from the file name, the way quantize_eval.py names its files (<model>-<format>.gguf)."""
    up = name.upper().replace('.GGUF', '')
    for f in FORMATS:  # longest names first within a family, so Q5_K_M is not read as Q5_K
        if up.endswith('-' + f) or up.endswith('.' + f) or up.endswith('_' + f):
            return 'bf16' if f == 'BF16' else f
    return ''


def model_from_name(name: str, fmt: str) -> str:
    stem = name[:-5] if name.lower().endswith('.gguf') else name
    return stem[:len(stem) - len(fmt) - 1] if fmt and stem.upper().endswith(fmt.upper()) else stem


def parse_log(log: str) -> dict:
    """Memory from llama.cpp's own log (llama-bench -v), in MiB. The KV cache and the compute buffers are taken from the
    first context only (llama-bench makes one per test; the long run has one test)."""
    out = {}
    m = re.search(r'recommendedMaxWorkingSetSize\s*=\s*([\d.]+) MB', log)
    if m:
        out['working_set'] = float(m.group(1))
    m = re.search(r'file size\s*=\s*([\d.]+) (MiB|GiB)', log)
    if m:
        out['weights'] = float(m.group(1)) * (1024 if m.group(2) == 'GiB' else 1)
    m = re.search(r'llama_kv_cache: size =\s*([\d.]+) MiB \(\s*(\d+) cells', log)
    if m:
        out['kv'], out['kv_cells'] = float(m.group(1)), int(m.group(2))
    comp, seen = 0.0, set()
    for dev, size in re.findall(r'sched_reserve:\s+(\S+) compute buffer size =\s*([\d.]+) MiB', log):
        if dev not in seen:
            seen.add(dev); comp += float(size)
    for size in re.findall(r'output buffer size =\s*([\d.]+) MiB', log)[:1]:
        comp += float(size)
    if seen:
        out['compute'] = comp
    return out


def run_bench(cmd: list[str]) -> tuple[list[dict], dict]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit(f'llama-bench failed ({p.returncode}): {" ".join(cmd)}\n{p.stderr[-2000:]}')
    try:
        rows = json.loads(p.stdout)
    except json.JSONDecodeError:
        sys.exit(f'llama-bench printed no JSON: {" ".join(cmd)}\n{p.stdout[-1000:]}\n{p.stderr[-1000:]}')
    if not rows:
        sys.exit(f'llama-bench ran no test: {" ".join(cmd)}')
    return rows, parse_log(p.stderr)


def pick(rows: list[dict], n_prompt: int, n_gen: int, depth: int = 0) -> float:
    for r in rows:
        if r['n_prompt'] == n_prompt and r['n_gen'] == n_gen and r.get('n_depth', 0) == depth:
            return round(r['avg_ts'], 1)
    sys.exit(f'no llama-bench result for p{n_prompt} n{n_gen} d{depth}')


def sysctl(key: str) -> str:
    try:
        return subprocess.run(['sysctl', '-n', key], capture_output=True, text=True).stdout.strip()
    except OSError:
        return ''


def machine_info() -> dict:
    mem = sysctl('hw.memsize')
    return dict(machine=sysctl('hw.model') or platform.machine(), chip=sysctl('machdep.cpu.brand_string') or platform.processor(),
                ram_gb=round(int(mem) / 2**30) if mem.isdigit() else '', os=f'macOS {platform.mac_ver()[0]}'.strip())


def measure(gguf: Path, a: argparse.Namespace, info: dict) -> dict:
    fmt = a.format or fmt_from_name(gguf.name)
    base = [str(a.bench), '-m', str(gguf), '-ngl', str(a.ngl), '-o', 'json']
    speed_cmd = base + ['-p', '512', '-n', '128', '-r', str(a.reps)]
    long_cmd = base + ['-p', '0', '-n', '16', '-d', str(a.depth), '-r', '1', '-v']
    speed, m_speed = run_bench(speed_cmd)
    long, mem = run_bench(long_cmd)
    if not {'weights', 'kv', 'compute'} <= set(mem):
        sys.exit(f'{gguf.name}: llama-bench -v printed no buffer sizes (found {sorted(mem)}); is this a b11669 build?')
    size, n_params = speed[0]['model_size'], speed[0]['model_n_params']
    ws = mem.get('working_set') or m_speed.get('working_set')
    mb = lambda x: round(x * 2**20 / 1e6, 1)  # MiB from the log, written as MB (10^6 bytes) like size_bytes
    total = mem['weights'] + mem['kv'] + mem['compute']
    return dict(date=datetime.date.today().isoformat(), contributor=a.contributor, **info,
                runtime=f'llama.cpp {a.build} ({speed[0].get("build_commit", "")}), Metal, ngl {a.ngl}',
                model=a.model or model_from_name(gguf.name, fmt), format=fmt, gguf_sha256=sha256(gguf),
                size_bytes=gguf.stat().st_size, n_params=n_params, bpw=round(8 * size / n_params, 2),
                pp512_tok_s=pick(speed, 512, 0), tg128_tok_s=pick(speed, 0, 128), depth=a.depth,
                tg16_at_depth_tok_s=pick(long, 0, 16, a.depth), weights_mb=mb(mem['weights']), kv_mb=mb(mem['kv']),
                kv_cells=mem['kv_cells'], kv_mb_per_1k=round(mb(mem['kv']) * 1024 / mem['kv_cells'], 2),
                compute_mb=mb(mem['compute']), total_mb=mb(total), gpu_working_set_mb=round(ws, 1) if ws else '',
                fits_gpu='' if not ws else ('yes' if mb(total) <= ws else 'no'),  # ggml prints the limit in MB (1e6)
                command=' '.join(Path(c).name if c == str(a.bench) else c for c in speed_cmd) + ' ; ' +
                ' '.join(Path(c).name if c == str(a.bench) else c for c in long_cmd),
                notes=a.notes)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('gguf', nargs='+', type=Path)
    ap.add_argument('--bench', type=Path, required=True, help='llama-bench binary')
    ap.add_argument('--build', required=True, help='llama.cpp build tag the binary was made from, e.g. b11669')
    ap.add_argument('--contributor', required=True, help='GitHub login')
    ap.add_argument('--out', type=Path, required=True, help='rows CSV (appended; header written when new)')
    ap.add_argument('--model', default='', help='model name (default: from the file name)')
    ap.add_argument('--format', default='', help='format (default: from the file name)')
    ap.add_argument('--depth', type=int, default=8192, help='tokens in the cache for the long run (default 8192)')
    ap.add_argument('--reps', type=int, default=5)
    ap.add_argument('--ngl', type=int, default=99, help='layers on the GPU (default 99: all)')
    ap.add_argument('--notes', default='')
    a = ap.parse_args()
    info = machine_info()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    for g in a.gguf:
        row = measure(g, a, info)
        new = not a.out.exists()
        with open(a.out, 'a', newline='') as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            if new:
                w.writeheader()
            w.writerow(row)
        print(f'{g.name}: {row["format"]} {row["bpw"]} bpw | pp512 {row["pp512_tok_s"]} tg128 {row["tg128_tok_s"]} '
              f'tg16@{a.depth} {row["tg16_at_depth_tok_s"]} tok/s | memory at {a.depth}: weights {row["weights_mb"]} + '
              f'KV {row["kv_mb"]} + compute {row["compute_mb"]} = {row["total_mb"]} MB '
              f'(GPU limit {row["gpu_working_set_mb"]} MB)', flush=True)


if __name__ == '__main__':
    main()
