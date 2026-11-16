"""SFT data v1 pack manifest (G10, work-order task 1): one record per set in scope, and the #391 area budget.

    python sft/sft_v1_manifest.py --out sft/results/sft_data_v1_manifest.json [--mask-dir sft/results/sft_v1_mask_checks]

Reads only files in this folder: the admission summaries (`results/sft_v1_admission/`), the full C3 conversion records
(`results/sft_v1_records/<set>.full.record.json`), the OCR-2 pack manifest, the loss-mask reports (counts only) and the
prefix records of sets whose full build is a pending job. It writes counts, hashes and revisions: no row text or id.

Scope (BLOCKED B1 fallback, no admission ruling for the TSAI-reserves sets): the sets whose licence decision is
`allowed` and the TSAI-admitted OCR-2 pack. A set is `in_pack` only when its decontamination covers the whole set;
otherwise it is listed with its status and does not count toward the area budget.

Area budget: the #391 shares are shares of the mix, not absolute sizes. With Code the only area that has a large
admitted set, the budget is anchored on it: total = Code tokens / Code share, and every other area needs share x total.
This says how far each area falls short if v1 kept Code at its admitted size; a smaller total (dropping Code rows)
scales every need down by the same factor.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
SCHEMA = "g10-sft-data-v1-manifest/1"
MAX_LEN = 32768

# #391 shares (sft_mix_proposal.md section 2 and the 3 Nov revision); fallback from section 3, Area 6
SHARES = {"code": 0.35, "agentic": 0.25, "tool_use": 0.15, "indic": 0.15, "general": 0.07, "safety": 0.03}
SHARES_NO_SAFETY = {**SHARES, "general": 0.10, "safety": 0.0}

# sets in scope: allowed licence decision (or TSAI-admitted), with their #391 area
IN_SCOPE = {
    "sft-code-opencodereasoning-2": "code",
    "sft-dolly-15k": "general",
    "sft-indic-indic-align-dolly-t": "indic",
    "sft-math-nemotron-proofs": "general",
    "sft-math-nemotron-math-v2": "general",
}
JOBS = {
    "sft-math-nemotron-proofs": "jobs/2026-11-16-sft-v1-proofs-decontam.md",
    "sft-math-nemotron-math-v2": "jobs/2026-11-14-sft-v1-math-v2-full.md",
    "sft-code-opencodereasoning-2": "jobs/2026-11-16-ocr2-pack-v1.md",
}
# what fills each area that has no admitted set (the ruling that would add it)
FILLED_BY = {
    "code": "B1: opencodereasoning, codeforces-cots, commitpackft (TSAI reserves)",
    "agentic": "B1: swe-rebench-openhands, nemotron-terminal, nemotron-cascade-swe (TSAI reserves)",
    "tool_use": "B1: agentic-v1, agentic-v2 tool-calling (TSAI reserves); B2: xlam-60k (held)",
    "indic": "B1: aya-dataset, aya-collection 10 subsets, indic-align-oasst-t (TSAI reserves); B3: templated_hindi_news",
    "general": "B1: openthoughts3, openmathreasoning, openr1-math, nemotron-science, bespoke-stratos, glm51-phd, oasst2, "
               "proofs-v3-sft (TSAI reserves); B2: nemotron-if-v1/v2, science-v2 (held); B6: Proofs decontam",
    "safety": "B7: TSAI names a safety set with chat rows, or the 0% safety / 10% general fallback",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def from_admission(set_id: str, results: Path, mask_dir: Path | None) -> dict:
    adm_path = results / "sft_v1_admission" / f"{set_id}.admission.json"
    rec_path = results / "sft_v1_records" / f"{set_id}.full.record.json"
    adm, rec = load(adm_path), load(rec_path)
    assert adm["record"]["content_sha256"] == rec["content_sha256"], f"{set_id}: admission bound to another conversion"
    complete = bool(adm["decontam"]["complete"])
    out = {
        "area": IN_SCOPE[set_id], "source": rec["source"], "revision": rec["hub_revision"], "input": rec["input"],
        "selection": rec["selection"], "generator": rec["generator_model"], "licence": rec["licence"],
        "licence_decision": rec["decision"], "tokenizer_sha256": rec["tokenizer_sha256"],
        "conversion": {"rows_in": rec["rows_in"], "rows": rec["rows_out"], "tokens": rec["checks"]["tokens"],
                       "trained_tokens": rec["checks"]["trained_tokens"], "skipped": rec["skipped"],
                       "row_checks_ok": rec["checks"]["checks_ok"], "deterministic_rerun": rec["deterministic_rerun"],
                       "content_sha256": rec["content_sha256"], "parts": len(rec["parts"]),
                       "record": {"name": rec_path.name, "sha256": sha256_file(rec_path)}},
        "decontam": adm["decontam"],
        "over_length": {"max_sequence_tokens": MAX_LEN, "rows_dropped": adm["excluded_each"]["over_max_len"],
                        "kept_max_len": adm["kept_max_len"]},
        "admission": {"rows_kept": adm["rows_kept"], "tokens_kept": adm["tokens_kept"], "rows_excluded": adm["rows_excluded"],
                      "excluded_each": adm["excluded_each"], "kept_ids_sha256": adm["kept_ids_sha256"],
                      "excluded_sha256": adm["excluded_sha256"], "status": adm["status"],
                      "summary": {"name": adm_path.name, "sha256": sha256_file(adm_path)}},
        "in_pack": complete and adm["status"] == "admissible",
        "status": "admissible" if complete and adm["status"] == "admissible" else adm["status"],
    }
    out["loss_mask"] = mask_entry(set_id, mask_dir)
    if set_id in JOBS:
        out["job_request"] = JOBS[set_id]
    return out


def mask_entry(set_id: str, mask_dir: Path | None) -> dict:
    if mask_dir is None:
        return {"checked": False}
    hits = sorted(mask_dir.glob(f"{set_id}*.json"))
    if not hits:
        return {"checked": False}
    r = load(hits[0])
    mask_bad = {k: v for k, v in r["violations"].items() if k != "over_limit"}
    return {"checked": True, "report": hits[0].name, "rows_checked": r["rows"], "tokens_checked": r["tokens"],
            "mask_violations": mask_bad, "rows_over_limit_before_admission": r["violations"].get("over_limit", 0),
            "trained_tokens_by_role": r["trained_tokens_by_role"], "mask_ok": not mask_bad and r["rows"] > 0,
            "scope": r.get("scope", "every converted row of the set")}


def from_ocr2(results: Path, mask_dir: Path | None) -> dict:
    path = results / "ocr2_pack_v1_manifest.json"
    m = load(path)
    f = m["funnel"]
    return {
        "area": "code", "source": m["sources"]["ocr2"]["repo"], "revision": m["sources"]["ocr2"]["revision"],
        "joined_sources": {k: v["revision"] for k, v in m["sources"].items() if k.endswith("/train") and not v.get("protected")},
        "generator": "DeepSeek-R1 (MIT) for the trained reasoning and solutions; QwQ-32B (Apache-2.0) critiques are a "
                     "filter signal only, never a target (licence_table.md, ocr2_policy.json teacher)",
        "licence": "cc-by-4.0 (Hub tag); joined questions from TACO, APPS and code_contests train at pinned revisions",
        "licence_decision": "allowed (TSAI admitted, 11 Nov 2026)", "tokenizer_sha256": m["build"]["tokenizer_sha256"],
        "decontam": {"complete": m["checks"]["decontam.full_set_v2"] and m["checks"]["decontam.second_pass_zero_hits"],
                     "covers": "whole set, all 70 shards", "rows_flagged": f["screened.rows_flagged"],
                     "rows_canary": f["screened.rows_canary"], "by_benchmark": m["decontam_flagged_by_benchmark"],
                     "fingerprint_set_sha256": m["build"]["fingerprint_set_sha256"]},
        "over_length": {"max_sequence_tokens": m["build"]["max_sequence_tokens"], "rows_dropped": 0,
                        "kept_max_len": m["max_length_tokens"]},
        "heldout": {"rows": m["heldout_eval_v1"]["rows"], "families": m["heldout_eval_v1"]["families"],
                    "id_list_sha256": m["heldout_eval_v1"]["id_list_sha256"], "salt": m["heldout_eval_v1"]["rule"]["salt"],
                    "fraction": m["heldout_eval_v1"]["rule"]["fraction"]},
        "unclear_source_left_out": {"keys": m["unclear_source"]["keys"], "rows": m["unclear_source"]["rows_excluded"]},
        "admission": {"rows_kept": f["pack.train_rows"], "tokens_kept": f["train.tokens"],
                      "trained_tokens": f["train.shifted_assistant_targets"], "status": "admitted, pack built"},
        "pack": {"run_id": m["build"]["run_id"], "shards": len(m["shards"]), "manifest": {"name": path.name, "sha256": sha256_file(path)},
                 "acceptance_checks": f"{sum(m['checks'].values())} of {len(m['checks'])}"},
        "loss_mask": {"checked": True, "mask_ok": True, "rows_checked": 32855, "tokens_checked": 212547311,
                      "mask_violations": {}, "report": "ocr2_pack_v1.md, Checks (14 Nov build)",
                      "scope": "check_pack_rows.py on every train and held-out row of shards 0-3; shards 4-69 only by "
                               "pack_admission.py's in-pipeline recompute (ids and mask equal a fresh tokenisation), "
                               "because their bytes were deleted in the containers"},
        "in_pack": True, "status": "admitted; pack final as built", "job_request": JOBS["sft-code-opencodereasoning-2"],
    }


def from_prefix(set_id: str, results: Path) -> dict:
    path = results / "sft_v1_records" / f"{set_id}.record.json"
    rec = load(path)
    c = rec["checks"]
    return {"area": IN_SCOPE[set_id], "source": rec["source"], "revision": rec["hub_revision"], "generator": rec["generator_model"],
            "licence": rec["licence"], "licence_decision": rec["decision"], "tokenizer_sha256": rec["tokenizer_sha256"],
            "prefix_record": {"name": path.name, "sha256": sha256_file(path), "scope": rec["scope"], "rows": c["rows"],
                              "tokens": c["tokens"], "rows_over_max_len": c["rows_over_max_len"], "row_checks_ok": c["checks_ok"]},
            "decontam": {"complete": False, "covers": "not run at this revision"},
            "in_pack": False, "status": "full conversion pending (job request)", "job_request": JOBS[set_id]}


def budget(sets: dict, shares: dict) -> dict:
    have = {a: 0 for a in shares}
    for s in sets.values():
        if s["in_pack"]:
            have[s["area"]] += s["admission"]["tokens_kept"]
    anchor = have["code"] / shares["code"] if have["code"] else 0
    rows = {}
    for a, share in shares.items():
        need = round(share * anchor)
        rows[a] = {"share": share, "tokens_admitted": have[a], "tokens_needed_at_code_anchor": need,
                   "fill": round(have[a] / need, 6) if need else None,
                   "shortfall_tokens": max(need - have[a], 0), "filled_by": FILLED_BY[a]}
    total = sum(have.values())
    return {"anchor": "Code at its admitted size", "total_at_anchor": round(anchor), "tokens_admitted_total": total,
            "admitted_share_by_area": {a: round(have[a] / total, 6) if total else 0 for a in shares}, "areas": rows}


def build(results: Path, mask_dir: Path | None) -> dict:
    sets = {"sft-code-opencodereasoning-2": from_ocr2(results, mask_dir)}
    for s in ("sft-dolly-15k", "sft-indic-indic-align-dolly-t", "sft-math-nemotron-proofs"):
        sets[s] = from_admission(s, results, mask_dir)
    sets["sft-math-nemotron-math-v2"] = from_prefix("sft-math-nemotron-math-v2", results)
    return {
        "schema": SCHEMA,
        "scope": "BLOCKED B1 fallback: sets with an allowed licence decision plus the TSAI-admitted OCR-2 pack; no "
                 "TSAI-reserves set is in scope until admitted",
        "tokenizer": {"sha256": "15468e66457b43af79f695cbe585c0d03e3cfe7a4a5d04d189dd3c6b9f02ddc3", "name": "C3",
                      "note": "every count here is C3. TSAI's Gate 3 notice (15 Nov 2026) moved new work to p1536 "
                              "(sha256 e6b93a93...; same special ids, eos 130822, same vocabulary size). Transfer "
                              "measured on Dolly, dolly-t, OCR-2 shards 0-3 and 10 Proofs parts: "
                              "results/sft_v1_p1536_transfer.json"},
        "max_sequence_tokens": MAX_LEN,
        "loss_mask_rule": "assistant bodies and their closing <|im_end|> are trained; system, user, tool results, role "
                          "headers, <|im_start|> and the final <|endoftext|> (130822) are not",
        "sets": sets,
        "in_pack": sorted(k for k, v in sets.items() if v["in_pack"]),
        "budget_391": budget(sets, SHARES),
        "budget_no_safety_fallback": budget(sets, SHARES_NO_SAFETY),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", type=Path, default=RESULTS)
    ap.add_argument("--mask-dir", type=Path, default=RESULTS / "sft_v1_mask_checks")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    m = build(a.results, a.mask_dir if a.mask_dir.is_dir() else None)
    a.out.write_text(json.dumps(m, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    b = m["budget_391"]
    print(f"in pack: {', '.join(m['in_pack'])}; admitted tokens {b['tokens_admitted_total']:,}")
    for area, r in b["areas"].items():
        fill = "n/a" if r["fill"] is None else f"{r['fill']:.2%}"
        print(f"  {area:<9} share {r['share']:.0%} admitted {r['tokens_admitted']:>14,} need {r['tokens_needed_at_code_anchor']:>14,} fill {fill}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
