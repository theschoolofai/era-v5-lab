#!/usr/bin/env python3
"""Check that a dense model's W4A16 folder really has its decoder linears packed (the dense counterpart of gpu_path/model_check.py).

    python check_dense_w4a16.py <model_dir> --layers 28 [--base <bf16_dir>] [--out check.json]

llm-compressor can skip layers silently. This reads the safetensors headers (no weights are loaded) and fails unless every
decoder linear (q, k, v, o, gate, up, down in each layer) is stored packed (`weight_packed`), and reports where the output
layer is (a separate `lm_head`, or tied to the embedding, as in Qwen2.5-Coder-1.5B) and its dtype, with the size of the
folder against a bf16 base if given. model_check.py is for MoE models (it needs router tensors) and cannot be used here.
"""
from __future__ import annotations

import argparse, json, re, struct, sys
from pathlib import Path

LINEAR = re.compile(r"\.layers\.(\d+)\.(self_attn\.(q|k|v|o)_proj|mlp\.(gate|up|down)_proj)\.")


def read_header(path: Path) -> dict:
    with open(path, "rb") as f:
        n = struct.unpack("<Q", f.read(8))[0]
        return json.loads(f.read(n))


def tensors(model_dir: Path) -> dict[str, str]:
    files = sorted(model_dir.glob("*.safetensors"))
    if not files:
        raise SystemExit(f"{model_dir}: no .safetensors files")
    out = {}
    for f in files:
        out.update({k: v["dtype"] for k, v in read_header(f).items() if k != "__metadata__"})
    return out


def check(ts: dict[str, str], layers: int) -> dict:
    linears = {m.group(0) + "weight" for k in ts for m in [LINEAR.search(k)] if m}
    packed = {k.replace("weight_packed", "weight") for k in ts if k.endswith(".weight_packed") and LINEAR.search(k)}
    plain = {k for k in ts if k.endswith(".weight") and LINEAR.search(k)}
    lm = {k: v for k, v in ts.items() if k.startswith("lm_head.")}
    return {"expected_linears": 7 * layers, "linears_seen": len(packed | plain), "packed": len(packed), "unpacked": sorted(plain)[:5],
            "unpacked_count": len(plain), "lm_head": ("absent (tied to the embedding)" if not lm else sorted(set(lm.values()))),
            "dtypes_of_packed_tensors": sorted({v for k, v in ts.items() if k.endswith(".weight_packed")})}


def problems(info: dict) -> list[str]:
    out = []
    if info["packed"] != info["expected_linears"]:
        out.append(f"{info['packed']} decoder linears are packed, {info['expected_linears']} expected")
    if info["unpacked_count"]:
        out.append(f"{info['unpacked_count']} decoder linears are stored unpacked, for example {info['unpacked']}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("model_dir", type=Path); ap.add_argument("--layers", type=int, required=True)
    ap.add_argument("--base", type=Path, default=None); ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    info = check(tensors(a.model_dir), a.layers)
    size = sum(f.stat().st_size for f in a.model_dir.glob("*.safetensors"))
    info["size_bytes"] = size
    if a.base:
        base = sum(f.stat().st_size for f in a.base.glob("*.safetensors"))
        info["base_size_bytes"], info["size_vs_base"] = base, round(size / base, 3)
    bad = problems(info)
    if a.out:
        a.out.write_text(json.dumps({**info, "problems": bad}, indent=1))
    if bad:
        sys.exit("; ".join(bad))
    print(f"{info['packed']} of {info['expected_linears']} decoder linears packed; lm_head {info['lm_head']}; size {size / 1e9:.2f} GB"
          + (f" ({info['size_vs_base']:.2f} of the base)" if a.base else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
