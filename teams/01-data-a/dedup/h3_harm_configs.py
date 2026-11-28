"""The configs of the H3 harm check (run_h3_harm.sh). For each held-out language (sa, hi, en) it writes overlap.json,
h3.json and dedup_{noh3,report,remove}.json in <out>/<lang>-held/. Run from the repository root:

    python3 -I teams/01-data-a/dedup/h3_harm_configs.py out/h3harm

h3.json is E5c's config (jobs/2026-11-18-h3-e5c/h3.json) for the ruled scope (sa-en, sa-hi, hi-en; Odia has no gold
set), with these inputs: LaBSE at E5c's pinned revision 836121a, device auto, report_floor 0 (every verified pair is
listed, for the margin) and max_verify 60,000 as in E5c's full rerun, so that every candidate is verified. The dedup
configs are teams/01-data-a/dedup/dedup.json (pack order, licence map, gold_dirs) with this run's results, inputs and
out; "remove" runs H3 with h3.remove true, "report" with false, "noh3" without H3.
"""
import json
import sys
from pathlib import Path

OUT = sys.argv[1]
LANG = {"ind-sa-fw2": "sa", "ind-hi-fw2": "hi", "ind-hi-hplt": "hi", "ind-hi-indiccorp": "hi",
        "ind-hi-sangraha-s": "hi", "ind-hi-sangraha-v": "hi", "en-fineweb-edu": "en", "en-dclm": "en",
        "en-nemotroncc": "en"}
base = {k: v for k, v in json.loads(Path("teams/01-data-a/dedup/dedup.json").read_text(encoding="utf-8")).items()
        if not k.startswith("_")}


def write(path, cfg):
    Path(path).write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    print("wrote", path)


for held in ("sa", "hi", "en"):                                   # the layouts
    r = f"{OUT}/{held}-held"
    write(f"{r}/overlap.json", {"inputs": f"{r}/inputs", "splits": ["train", "heldout"], "out": f"{r}/overlap",
                                "floor": 0.5, "k": 5, "block": 256, "top": 20, "max_output_mb": 50,
                                "expected_packs": sorted(LANG)})
    write(f"{r}/h3.json", {"inputs": f"{r}/inputs", "out": f"{r}/h3", "cache": "out/h3harm_cache",
                           "model_path": "../models/LaBSE-hub-836121a", "device": "auto", "precision": "auto",
                           "packs": {"ind-sa-fw2": "sa", "ind-hi-*": "hi", "en-fineweb-edu": "en", "en-dclm": "en",
                                     "en-nemotroncc": "en"},
                           "pairs": [["sa", "en"], ["sa", "hi"], ["hi", "en"]],
                           "sentence_threshold": {"sa-en": 0.55, "sa-hi": 0.55},
                           "coverage_threshold": 0.6, "report_floor": 0.0, "max_verify": 60000,
                           "max_minutes": 60, "max_output_mb": 50})
    for mode in ("noh3", "report", "remove"):                     # the three dedup.py runs
        cfg = {**base, "results": f"{r}/overlap", "inputs": f"{r}/inputs", "out": f"{r}/dedup_{mode}"}
        if mode != "noh3":
            cfg["h3"] = {"matches": f"{r}/h3/h3_matches.csv", "remove": mode == "remove"}
        write(f"{r}/dedup_{mode}.json", cfg)
