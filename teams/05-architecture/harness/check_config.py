"""Report every setting that has no value or no source.

An open size may be null. That is a value, and it is not an error.
A missing value, a null on a closed setting, or a blank source is an error.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml


def load_settings(path: Path) -> list[dict]:
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict) or not isinstance(data.get("settings"), list):
        raise SystemExit(f"{path}: expected a settings list")
    return data["settings"]


def merge(base: list[dict], override_path: Path | None) -> list[dict]:
    by_key = {item["key"]: dict(item) for item in base}
    if override_path is None:
        return list(by_key.values())
    data = yaml.safe_load(override_path.read_text())
    overrides = data.get("overrides") if isinstance(data, dict) else None
    if not isinstance(overrides, list):
        raise SystemExit(f"{override_path}: expected an overrides list")
    for item in overrides:
        key = item.get("key")
        if key not in by_key:
            by_key[key] = {"key": key, "open": False}
        by_key[key]["value"] = item.get("value")
        by_key[key]["source"] = item.get("source", "")
        by_key[key]["open"] = False
    return list(by_key.values())


def errors_for(settings: list[dict]) -> list[str]:
    found = []
    seen = set()
    for item in settings:
        key = item.get("key")
        if not key or key in seen:
            found.append(f"bad key: {key!r}")
            continue
        seen.add(key)
        if "value" not in item:
            found.append(f"{key}: no value")
        elif item["value"] is None and not item.get("open"):
            found.append(f"{key}: no value")
        source = item.get("source")
        if not isinstance(source, str) or not source.strip():
            found.append(f"{key}: no source")
    found.extend(relation_errors(settings))
    return found


def relation_errors(settings: list[dict]) -> list[str]:
    values = {item.get("key"): item.get("value") for item in settings}
    found = []
    d_model = values.get("model.d_model")
    n_head = values.get("model.n_head")
    if isinstance(d_model, int) and isinstance(n_head, int) and n_head > 0 and d_model % n_head:
        found.append(f"model.d_model {d_model} is not divisible by model.n_head {n_head}")
    n_expert = values.get("moe.n_expert")
    top_k = values.get("moe.top_k")
    if isinstance(n_expert, int) and isinstance(top_k, int) and not (1 <= top_k <= n_expert):
        found.append(f"moe.top_k {top_k} is outside 1..{n_expert}")
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    parser.add_argument("--tiny", type=Path, default=None)
    args = parser.parse_args()
    settings = merge(load_settings(args.config), args.tiny)
    found = errors_for(settings)
    if found:
        for line in found:
            print(line)
        print(f"{len(found)} errors")
        return 1
    print("0 errors")
    return 0


if __name__ == "__main__":
    sys.exit(main())
