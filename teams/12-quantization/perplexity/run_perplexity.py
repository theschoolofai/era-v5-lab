"""Run WikiText-2 perplexity on every GGUF in a folder and append one row per file to runs_ppl.csv.

Usage (GGUFs from scripts/quantize_eval.py or quantize/quantize_olmoe.sh, llama.cpp binaries on PATH):
    pip install gguf==0.19.0
    python teams/12-quantization/perplexity/run_perplexity.py --models-dir <folder with *.gguf>

The format is taken from the file name after the last "-" (olmoe-Q4_K_M.gguf -> Q4_K_M).
Bits per weight = file size x 8 / parameter count, with the parameter count read from the GGUF.
The test text is the one llama.cpp's scripts/get-wikitext-2.sh downloads; it is fetched once into --models-dir.
"""
import argparse, csv, datetime, io, platform, re, shutil, subprocess, sys, time, urllib.request, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
WIKITEXT_URL = "https://huggingface.co/datasets/ggml-org/ci/resolve/main/wikitext-2-raw-v1.zip"
WIKITEXT_FILE = "wikitext-2-raw/wiki.test.raw"
CSV_FIELDS = ["date", "model", "format", "bits_per_weight", "size_gb", "metric", "score", "score_err",
              "time_s", "machine", "tool"]

def machine_name() -> str:
    if shutil.which("nvidia-smi"):
        out = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], capture_output=True, text=True)
        gpus = [g.strip() for g in out.stdout.splitlines() if g.strip()]
        if gpus:
            return f"{len(gpus)}x {gpus[0]}"
    if platform.system() == "Darwin":
        return subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True).stdout.strip()
    return platform.processor() or platform.machine()

def llama_version(binary: str) -> str:
    out = subprocess.run([binary, "--version"], capture_output=True, text=True)
    # "version: 0.7.0-dev (build 1, commit 620d222)" or, in older builds, "version: 10050 (b15ca938a)"
    m = re.search(r"version: (\S+) \((?:build \d+, commit )?(\w+)\)", out.stdout + out.stderr)
    if not m:
        return "llama.cpp"
    ver = f"b{m.group(1)}" if m.group(1).isdigit() else m.group(1)
    return f"llama.cpp {ver} ({m.group(2)})"

def wikitext(cache: Path) -> Path:
    path = cache / WIKITEXT_FILE
    if not path.exists():
        print(f"downloading {WIKITEXT_URL}", flush=True)
        with urllib.request.urlopen(WIKITEXT_URL) as r:
            zipfile.ZipFile(io.BytesIO(r.read())).extract(WIKITEXT_FILE, cache)
    return path

def n_params(gguf_path: Path) -> int:
    try:
        from gguf import GGUFReader
    except ImportError:
        sys.exit("the gguf package is missing: pip install gguf==0.19.0")
    return sum(int(t.n_elements) for t in GGUFReader(gguf_path).tensors)

def perplexity(binary: str, model: Path, text: Path, ngl: int, ctx: int, chunks: int | None):
    cmd = [binary, "-m", str(model), "-f", str(text), "-ngl", str(ngl), "-c", str(ctx)]
    if chunks:
        cmd += ["--chunks", str(chunks)]
    print("+", " ".join(cmd), flush=True)
    out = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).stdout
    m = re.search(r"Final estimate: PPL = ([\d.]+) \+/- ([\d.]+)", out)
    if not m:
        sys.exit(f"no perplexity result for {model.name}; last output:\n{out[-2000:]}")
    return float(m.group(1)), float(m.group(2))

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--models-dir", type=Path, required=True, help="folder with the .gguf files")
    ap.add_argument("--model", default="allenai/OLMoE-1B-7B-0924", help="label for the model column")
    ap.add_argument("--llama-bin", type=Path, help="folder with llama-perplexity (default: PATH)")
    ap.add_argument("--out", type=Path, default=HERE / "runs_ppl.csv")
    ap.add_argument("--machine", help="label for the machine column; detected if omitted")
    ap.add_argument("--ngl", type=int, default=99, help="layers on the GPU (ignored on CPU-only builds)")
    ap.add_argument("--ctx", type=int, default=512, help="context per chunk; 512 is the llama-perplexity default")
    ap.add_argument("--chunks", type=int, help="use only the first N chunks (quick test); default: the whole test set")
    a = ap.parse_args()

    binary = str(a.llama_bin / "llama-perplexity") if a.llama_bin else shutil.which("llama-perplexity")
    if not binary or not Path(binary).exists():
        sys.exit("llama-perplexity not found: put llama.cpp's bin folder on PATH or pass --llama-bin")
    models = sorted(a.models_dir.glob("*.gguf"), key=lambda p: p.stat().st_size, reverse=True)
    if not models:
        sys.exit(f"no .gguf files in {a.models_dir}")
    text = wikitext(a.models_dir)
    # Context length and chunk count change the result, so non-default values go into the metric name.
    metric = ("ppl_wikitext2_test" + (f"_ctx{a.ctx}" if a.ctx != 512 else "")
              + (f"_{a.chunks}chunks" if a.chunks else ""))
    machine, tool = a.machine or machine_name(), llama_version(binary)

    for path in models:
        fmt = path.stem.rsplit("-", 1)[-1]
        start = time.time()
        score, err = perplexity(binary, path, text, a.ngl, a.ctx, a.chunks)
        size = path.stat().st_size
        row = {"date": datetime.date.today().isoformat(), "model": a.model, "format": fmt,
               "bits_per_weight": f"{size * 8 / n_params(path):.2f}", "size_gb": f"{size / 1e9:.2f}",
               "metric": metric, "score": f"{score:.4f}", "score_err": f"{err:.5f}",
               "time_s": round(time.time() - start), "machine": machine, "tool": tool}
        new = not a.out.exists()
        with a.out.open("a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            if new:
                w.writeheader()
            w.writerow(row)
        print(f"{fmt}: PPL {score:.4f} +/- {err:.5f}, {row['bits_per_weight']} bpw, {row['time_s']}s", flush=True)

if __name__ == "__main__":
    main()
