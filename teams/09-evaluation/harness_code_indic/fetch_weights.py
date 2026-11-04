"""Download one pinned model revision with parallel, resumable range requests, and verify every file.

On this connection a single Hugging Face download stream runs at about 0.23 MiB/s and Xet at about 0.07 MiB/s. Four parallel ranged
requests reach about 0.94 MiB/s (measured 25 Oct 2026). Chunks are kept on disk, so a dropped connection or a restart
only repeats the unfinished chunks.

Usage (from this folder):
    python -u fetch_weights.py --model qwen2.5-1.5b

Gated models (gemma-2-2b, llama-3.2-3b) need your own login first: `hf auth login`. The token is read at
run time by huggingface_hub and sent only to huggingface.co (requests drops it on the redirect to the CDN). It is never written anywhere.
"""
import argparse
import hashlib
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from huggingface_hub import get_token

HERE = Path(__file__).resolve().parent
DEST = Path(os.environ.get("G9_MODELS", Path.home() / ".cache" / "g9_models"))
CHUNK = 32 * 2**20
WANT = (".json", ".safetensors", ".txt", ".model", ".tiktoken")


def local_dir(hf_id, revision):
    return DEST / f"{hf_id.replace('/', '__')}__{revision[:12]}"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(8 * 2**20), b""):
            h.update(block)
    return h.hexdigest()


def get_chunk(session, url, headers, start, end, part, tries=12):
    """Fetch bytes [start, end] into part; resume a partial chunk; back off on errors."""
    want, last = end - start + 1, None
    for attempt in range(tries):
        have = part.stat().st_size if part.exists() else 0
        if have == want:
            return want
        try:
            with session.get(url, headers={**headers, "Range": f"bytes={start + have}-{end}"}, stream=True, timeout=(20, 60)) as r:
                if r.status_code != 206:  # a 200 means the range was ignored; appending it would corrupt the chunk
                    raise IOError(f"HTTP {r.status_code}")
                with open(part, "ab") as f:
                    for block in r.iter_content(256 * 1024):
                        f.write(block)
        except Exception as e:
            time.sleep(min(60, 2 ** attempt))
            last = e
    raise IOError(f"chunk {part.name} failed after {tries} tries: {last!r}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="key in published_scores.json 'models'")
    ap.add_argument("--connections", type=int, default=4)
    a = ap.parse_args()

    m = json.loads((HERE / "published_scores.json").read_text(encoding="utf-8"))["models"][a.model]
    hf_id, rev = m["hf_id"], m["revision"]
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    session = requests.Session()

    tree = session.get(f"https://huggingface.co/api/models/{hf_id}/tree/{rev}", headers=headers, timeout=30).json()
    files = [f for f in tree if f["type"] == "file" and f["path"].endswith(WANT)]
    if not any(f["path"].endswith(".safetensors") for f in files):  # older repos ship only pytorch_model*.bin
        files += [f for f in tree if f["type"] == "file" and f["path"].startswith("pytorch_model") and f["path"].endswith(".bin")]
    out = local_dir(hf_id, rev)
    parts = out / ".parts"
    parts.mkdir(parents=True, exist_ok=True)
    total = sum(f["size"] for f in files)
    print(f"{hf_id}@{rev[:12]}: {len(files)} files, {total / 2**30:.2f} GiB -> {out}", flush=True)

    done_bytes, t0 = 0, time.time()
    for f in sorted(files, key=lambda x: x["size"]):
        target = out / f["path"]
        expect_sha = (f.get("lfs") or {}).get("oid")
        if target.exists() and target.stat().st_size == f["size"] and (not expect_sha or sha256(target) == expect_sha):
            done_bytes += f["size"]
            continue
        url = f"https://huggingface.co/{hf_id}/resolve/{rev}/{f['path']}"
        spans = [(s, min(s + CHUNK, f["size"]) - 1) for s in range(0, f["size"], CHUNK)] or [(0, -1)]
        chunk_files = [parts / f"{f['path'].replace('/', '__')}.{i:05d}" for i in range(len(spans))]
        if f["size"] == 0:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"")
            continue
        with ThreadPoolExecutor(a.connections) as pool:
            futures = {pool.submit(get_chunk, session, url, headers, s, e, p): p for (s, e), p in zip(spans, chunk_files)}
            last_print = time.time()
            for fut in as_completed(futures):
                done_bytes += fut.result()
                if time.time() - last_print > 60:
                    rate = done_bytes / max(time.time() - t0, 1) / 2**20
                    print(f"  {done_bytes / 2**30:.2f}/{total / 2**30:.2f} GiB  {rate:.2f} MiB/s", flush=True)
                    last_print = time.time()
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(target.suffix + ".tmp")
        with open(tmp, "wb") as w:
            for p in chunk_files:
                w.write(p.read_bytes())
        if tmp.stat().st_size != f["size"] or (expect_sha and sha256(tmp) != expect_sha):
            tmp.unlink()
            raise IOError(f"{f['path']}: size or sha256 mismatch; chunks kept, rerun to retry")
        tmp.replace(target)
        for p in chunk_files:
            p.unlink()
        print(f"  ok {f['path']} ({f['size'] / 2**20:.0f} MiB, sha256 {'verified' if expect_sha else 'n/a (small file)'})", flush=True)

    (out / "SOURCE.json").write_text(json.dumps({"hf_id": hf_id, "revision": rev}, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"done: {out} in {(time.time() - t0) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
