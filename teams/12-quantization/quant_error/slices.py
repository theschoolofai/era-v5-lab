"""Held-out text slices for the quantization-error harness.

Reads the G5 heldout_v1 jsonl (after checking its sha256), groups documents by slice, and writes one UTF-8 text file
per slice for llama.cpp (and a PyTorch forward pass) to score.
"""
import hashlib, json, re
from pathlib import Path
from typing import Callable

# id prefix -> (language or kind, script)
SLICES: dict[str, tuple[str, str]] = {
    'c4-val': ('English', 'Latin'),
    'fw2-hi-test': ('Hindi', 'Devanagari'),
    'fw2-bn-test': ('Bengali', 'Bengali'),
    'fw2-ta-test': ('Tamil', 'Tamil'),
    'fw2-te-test': ('Telugu', 'Telugu'),
    'fw2-kn-test': ('Kannada', 'Kannada'),
    'fw2-ml-test': ('Malayalam', 'Malayalam'),
    'fw2-mr-test': ('Marathi', 'Devanagari'),
    'fw2-gu-test': ('Gujarati', 'Gujarati'),
    'fw2-pa-test': ('Punjabi', 'Gurmukhi'),
    'fw2-or-test': ('Odia', 'Odia'),
    'fw2-as-test': ('Assamese', 'Bengali'),
    'owm-test': ('math', 'Latin'),
    'pes2o-val': ('science', 'Latin'),
    'vault-py-test': ('code', 'Python'),
    'vault-cpp-test': ('code', 'C++'),
    'vault-go-test': ('code', 'Go'),
    'vault-java-test': ('code', 'Java'),
    'vault-js-test': ('code', 'JavaScript'),
    'vault-rs-test': ('code', 'Rust'),
}

DOC_SEPARATOR = '\n\n'


def _expected_sha(sums: Path, name: str) -> str:
    for line in sums.read_text(encoding='utf-8').splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].lstrip('*') == name:
            return parts[0]
    raise ValueError(f'{sums} has no checksum for {name}')


def load_slices(jsonl: Path, sums: Path) -> dict[str, list[str]]:
    """Return {slice prefix: [document text, ...]} in file order; ValueError if the jsonl fails its sha256 check."""
    raw = Path(jsonl).read_bytes()
    actual, expected = hashlib.sha256(raw).hexdigest(), _expected_sha(Path(sums), Path(jsonl).name)
    if actual != expected:
        raise ValueError(f'{jsonl} sha256 {actual} does not match {expected} in {sums}')
    out: dict[str, list[str]] = {}
    for line in raw.decode('utf-8').splitlines():
        if line.strip():
            row = json.loads(line)
            out.setdefault(re.sub(r'-\d+$', '', row['id']), []).append(row['text'])
    return out


def write_slice_texts(slices: dict[str, list[str]], out_dir: Path,
                      normalizer: Callable[[str], str] | None = None) -> dict[str, Path]:
    """Write <out_dir>/<slice>.txt per slice (documents joined by a blank line); return {slice: path}."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, docs in slices.items():
        if normalizer is not None:
            docs = [normalizer(d) for d in docs]
        paths[name] = out_dir / f'{name}.txt'
        paths[name].write_bytes(DOC_SEPARATOR.join(docs).encode('utf-8'))
    return paths
