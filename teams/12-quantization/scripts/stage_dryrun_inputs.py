#!/usr/bin/env python3
"""Stage the inputs of the dry run 2 quantize job (jobs/2026-11-27-dryrun2-quantize-eval.md) once, WITH network, and check
them offline (G12, Lab 5, 28 Nov 2026). TSAI's note: the job is blocked on llama.cpp b11669 and on the code_contests and
hendrycks_math sets; this is the recipe.

    python teams/12-quantization/scripts/stage_dryrun_inputs.py all --inputs ./inputs --work ./work [--cuda]
    python teams/12-quantization/scripts/stage_dryrun_inputs.py check --inputs ./inputs --work ./work \\
        --tokenizer ./inputs/tokenizer.json --model ./inputs/dryrun2-1234/model.safetensors

  sources  every pinned file Team 10's effort_manifest.json reads (25 code_contests files, 4.8 GB; 6 hendrycks_math
           files, 2.7 MB), at the manifest's revision, into <inputs>/code_contests/ and <inputs>/hendrycks_math/ (the
           layout effort_suite.py --source-dir reads). Each file's sha256 is checked against the manifest; a file that
           does not match is deleted and the step fails. Files already there and correct are skipped.
  llama    llama.cpp b11669 (commit 620d2225cc43...) at <work>/llama.cpp-b11669 and its binaries in
           <work>/llama.cpp-b11669/build/bin. It is built with -DLLAMA_BUILD_NUMBER=11669 -DLLAMA_BUILD_COMMIT=620d222:
           a shallow clone otherwise reports build 1, quantize_eval.py then cannot find its checkout by build number and
           calls `git ls-remote` (network), and llama-server's UI step fails.
  venv     <work>/.venv-convert: Python 3.12 with b11669's requirements-convert_hf_to_gguf.txt (torch, transformers
           4.57.6, gguf), gguf-py and pyarrow<19; --with-llama-cpp-python adds llama-cpp-python==0.3.36.
  check    no network: sha256 of every source file, the llama.cpp commit and binaries (`llama-server --version` must say
           build 11669), the venv's packages, and, if given, the tokenizer's sha256 and the model files. Exit 1 on any FAIL.
"""
from __future__ import annotations

import argparse, hashlib, json, os, re, shutil, subprocess, sys, time, urllib.error, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
LLAMA_URL, LLAMA_TAG = "https://github.com/ggml-org/llama.cpp", "b11669"
LLAMA_COMMIT = "620d2225cc436ab0b001e3200e590e3b286ef9ab"
LLAMA_BUILD = 11669
TARGETS = ["llama-quantize", "llama-server", "llama-tokenize", "llama-perplexity"]
TOKENIZER_SHA = "e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b"      # frozen p1536
LLAMA_CPP_PYTHON, TRANSFORMERS = "0.3.36", "4.57.6"
DEFAULT_MANIFEST = HERE.parents[1] / "10-post-training" / "eval" / "effort_manifest.json"
UA = {"User-Agent": "era-v5-g12-staging/0.1 (theschoolofai/era-v5-lab, teams/12-quantization)"}


def log(*a):
    print(*a, flush=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 22), b""):
            h.update(block)
    return h.hexdigest()


# ------------------------------------------------------------------ sources
def manifest_sources(manifest: dict) -> dict[str, dict]:
    """{source key: {"dataset", "revision", "files": {relative path: sha256}}} for every resolved slot."""
    out = {k: {"dataset": v["dataset"], "revision": v["revision"], "files": {}} for k, v in manifest["sources"].items()}
    for slot in manifest["slots"]:
        if slot.get("status") == "resolved":
            out[slot["source"]]["files"][slot["file"]] = slot["file_sha256"]
    return {k: v for k, v in out.items() if v["files"]}


def hf_urls(dataset: str, revision: str, rel: str) -> list[str]:
    """The manifest names a file relative to the dataset's source dir; code_contests keeps its files under data/."""
    base = f"https://huggingface.co/datasets/{dataset}/resolve/{revision}"
    return [f"{base}/{rel}", f"{base}/data/{rel}"]


def download(urls: list[str], dest: Path, sha: str, retries: int = 5) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    last = None
    for url in urls:
        for attempt in range(retries):
            try:
                h = hashlib.sha256()
                with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r, open(part, "wb") as f:
                    for block in iter(lambda: r.read(1 << 22), b""):
                        h.update(block); f.write(block)
                if h.hexdigest() != sha:
                    part.unlink(missing_ok=True)
                    sys.exit(f"{dest.name}: sha256 {h.hexdigest()} != pinned {sha} ({url})")
                part.rename(dest)
                return
            except urllib.error.HTTPError as e:
                last = e
                if e.code == 404:
                    break                                     # next candidate path
                time.sleep(5 * (attempt + 1))
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                last = e
                time.sleep(5 * (attempt + 1))
    part.unlink(missing_ok=True)
    sys.exit(f"{dest.name}: could not download ({last})")


def stage_sources(manifest_path: Path, inputs: Path, limit: int | None, only: str | None) -> None:
    sources = manifest_sources(json.loads(manifest_path.read_text(encoding="utf-8")))
    staged = {}
    for key, src in sources.items():
        if only and key != only:
            continue
        files = list(src["files"].items())[:limit]
        for i, (rel, sha) in enumerate(files, 1):
            dest = inputs / key / rel
            if dest.is_file() and sha256_file(dest) == sha:
                log(f"  {key} {i}/{len(files)} {rel}: already staged")
            else:
                t0 = time.time()
                download(hf_urls(src["dataset"], src["revision"], rel), dest, sha)
                log(f"  {key} {i}/{len(files)} {rel}: {dest.stat().st_size / 1e6:.0f} MB, sha256 ok, {time.time() - t0:.0f}s")
            staged.setdefault(key, {})[rel] = {"sha256": sha, "bytes": dest.stat().st_size}
    (inputs / "staged_sources.json").write_text(json.dumps(
        {"manifest": str(manifest_path), "sources": {k: {"dataset": sources[k]["dataset"], "revision": sources[k]["revision"],
                                                          "files": v} for k, v in staged.items()}}, indent=1))
    for key, files in staged.items():
        log(f"{key}: {len(files)} files, {sum(f['bytes'] for f in files.values()) / 1e9:.2f} GB, all match the manifest")


# ------------------------------------------------------------------ llama.cpp
def head_commit(src: Path) -> str | None:
    """The checkout's HEAD commit, read from .git (no git call); a detached HEAD holds the sha itself."""
    head = src / ".git" / "HEAD"
    if not head.is_file():
        return None
    text = head.read_text().strip()
    if not text.startswith("ref: "):
        return text
    ref = text[5:]
    ref_file = src / ".git" / ref
    if ref_file.is_file():
        return ref_file.read_text().strip()
    packed = src / ".git" / "packed-refs"
    if packed.is_file():
        for line in packed.read_text().splitlines():
            if line.endswith(" " + ref):
                return line.split()[0]
    return None


def run(cmd: list, **kw) -> None:
    log("$", " ".join(map(str, cmd)))
    if subprocess.run([str(c) for c in cmd], **kw).returncode:
        sys.exit(f"failed: {' '.join(map(str, cmd))}")


def llama_src(work: Path) -> Path:
    return work / f"llama.cpp-{LLAMA_TAG}"


def stage_llama(work: Path, cuda: bool, jobs: int, cmake_args: list[str]) -> None:
    src = llama_src(work)
    if not (src / "convert_hf_to_gguf.py").is_file():
        work.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", "--depth", "1", "--branch", LLAMA_TAG, LLAMA_URL, src])
    if head_commit(src) != LLAMA_COMMIT:
        sys.exit(f"{src}: HEAD is {head_commit(src)}, b11669 is {LLAMA_COMMIT}")
    build = src / "build"
    run(["cmake", "-S", src, "-B", build, "-DCMAKE_BUILD_TYPE=Release", "-DLLAMA_CURL=OFF",
         f"-DGGML_CUDA={'ON' if cuda else 'OFF'}", f"-DLLAMA_BUILD_NUMBER={LLAMA_BUILD}",
         f"-DLLAMA_BUILD_COMMIT={LLAMA_COMMIT[:7]}", *cmake_args])
    run(["cmake", "--build", build, "-j", str(jobs), "--target", *TARGETS])
    log(f"binaries: {build / 'bin'}  (pass --llama-bin {build / 'bin'} to quantize_eval.py, or put it on PATH)")


def server_build(binary: Path) -> tuple[int, str] | None:
    out = subprocess.run([str(binary), "--version"], capture_output=True, text=True)
    m = re.search(r"build (\d+), commit (\w+)", out.stdout + out.stderr) or re.search(r"version: (\d+) \((\w+)\)", out.stdout + out.stderr)
    return (int(m.group(1)), m.group(2)) if m else None


# ------------------------------------------------------------------ venv
def venv_python(work: Path) -> Path:
    return work / ".venv-convert" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def stage_venv(work: Path, with_llama_cpp_python: bool) -> None:
    src, venv, py = llama_src(work), work / ".venv-convert", venv_python(work)
    req = src / "requirements/requirements-convert_hf_to_gguf.txt"
    if not req.is_file():
        sys.exit(f"{req}: run the llama step first")
    if not py.exists():
        if shutil.which("uv"):
            run(["uv", "venv", "--python", "3.12", venv])
            run(["uv", "pip", "install", "--python", py, "-r", req, "--index-strategy", "unsafe-best-match"])
            run(["uv", "pip", "install", "--python", py, src / "gguf-py", "pyarrow<19"])
        else:
            base = shutil.which("python3.12") or sys.exit("need uv or python3.12 for the conversion venv")
            run([base, "-m", "venv", venv])
            run([py, "-m", "pip", "install", "-r", req, src / "gguf-py", "pyarrow<19"])
    if with_llama_cpp_python:
        pkg = f"llama-cpp-python=={LLAMA_CPP_PYTHON}"
        run(["uv", "pip", "install", "--python", py, pkg] if shutil.which("uv") else [py, "-m", "pip", "install", pkg])


# ------------------------------------------------------------------ check
def check(args) -> int:
    results: list[tuple[str, bool, str]] = []

    def rec(name: str, ok: bool, detail: str = "") -> None:
        results.append((name, ok, detail))
        log(f"{'PASS' if ok else 'FAIL'}  {name}" + (f": {detail}" if detail else ""))

    sources = manifest_sources(json.loads(args.manifest.read_text(encoding="utf-8")))
    for key, src in sources.items():
        bad = [rel for rel, sha in src["files"].items()
               if not (args.inputs / key / rel).is_file() or sha256_file(args.inputs / key / rel) != sha]
        rec(f"{key}: {len(src['files'])} pinned files", not bad,
            f"{len(src['files']) - len(bad)} match" + (f", missing or different: {bad[:3]}" if bad else ""))
    srcdir = llama_src(args.work)
    rec("llama.cpp checkout", head_commit(srcdir) == LLAMA_COMMIT, f"{srcdir} HEAD {head_commit(srcdir)}")
    bindir = srcdir / "build" / "bin"
    for name in TARGETS[:2]:
        rec(f"binary {name}", (bindir / name).is_file(), str(bindir / name))
    got = server_build(bindir / "llama-server") if (bindir / "llama-server").is_file() else None
    rec("llama-server --version", bool(got) and got[0] == LLAMA_BUILD and LLAMA_COMMIT.startswith(got[1]),
        f"build {got[0]}, commit {got[1]}" if got else "not readable")
    py = venv_python(args.work)
    if py.exists():
        probe = ("import importlib.metadata as m, json, sys; v=lambda n: m.version(n);"
                 "print(json.dumps({'python': sys.version.split()[0], 'torch': v('torch'), 'transformers': v('transformers'),"
                 "'gguf': v('gguf'), 'pyarrow': v('pyarrow')}))")
        out = subprocess.run([str(py), "-c", probe], capture_output=True, text=True)
        try:
            pk = json.loads(out.stdout.strip().splitlines()[-1])
            rec("convert venv packages", pk["transformers"] == TRANSFORMERS and tuple(map(int, pk["python"].split(".")[:2])) >= (3, 12),
                json.dumps(pk))
        except Exception:
            rec("convert venv packages", False, (out.stderr or out.stdout)[-200:])
    else:
        rec("convert venv", False, f"{py} missing")
    if args.tokenizer:
        got_sha = sha256_file(args.tokenizer) if args.tokenizer.is_file() else "missing"
        rec("tokenizer sha256", got_sha == TOKENIZER_SHA, got_sha[:16])
    if args.model:
        ok = args.model.is_file() and (args.model.parent / "manifest.json").is_file()
        rec("model files", ok, f"{args.model} ({args.model.stat().st_size / 1e6:.0f} MB, sha256 {sha256_file(args.model)[:16]})"
            if args.model.is_file() else f"{args.model} missing" + ("" if (args.model.parent / 'manifest.json').is_file() else "; manifest.json missing"))
    failed = [n for n, ok, _ in results if not ok]
    log(f"\n{len(results) - len(failed)} of {len(results)} checks pass" + (f"; FAILED: {failed}" if failed else ""))
    return 1 if failed else 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", choices=["sources", "llama", "venv", "check", "all"])
    ap.add_argument("--inputs", type=Path, default=Path("inputs"))
    ap.add_argument("--work", type=Path, default=Path("work"))
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--only", choices=["code_contests", "hendrycks_math"], help="sources: one dataset")
    ap.add_argument("--limit", type=int, help="sources: first N files per dataset (a test, not a staging)")
    ap.add_argument("--cuda", action="store_true", help="llama: build with CUDA")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--cmake-arg", action="append", default=[], help="llama: extra argument for the cmake configure step")
    ap.add_argument("--with-llama-cpp-python", action="store_true", help="venv: add llama-cpp-python==0.3.36")
    ap.add_argument("--tokenizer", type=Path, help="check: the frozen p1536 tokenizer.json")
    ap.add_argument("--model", type=Path, help="check: model.safetensors (manifest.json beside it)")
    a = ap.parse_args()
    if a.step in ("sources", "all"):
        log("== sources"); stage_sources(a.manifest, a.inputs, a.limit, a.only)
    if a.step in ("llama", "all"):
        log("== llama.cpp"); stage_llama(a.work, a.cuda, a.jobs, a.cmake_arg)
    if a.step in ("venv", "all"):
        log("== venv"); stage_venv(a.work, a.with_llama_cpp_python)
    if a.step in ("check", "all"):
        log("== check"); sys.exit(check(a))


if __name__ == "__main__":
    main()
