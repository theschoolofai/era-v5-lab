"""Mark which rows count toward supply (no double counting of overlaps), then total supply per part.

Usage: python supply.py dataset_list.csv supply_by_part.md
Rows not counted keep their reason in count_reason, so the team can change the choice in one place (COUNT below).
Supply uses tokens_p1536 where measured, else the card count (other tokenizer, flagged).
"""
import csv, sys

# dataset -> (counted?, reason). Rows not listed: counted.
COUNT = {
    "the-stack-v2-dedup": (False, "superset of starcoderdata; size not on Hub (Software Heritage)"),
    "stack-edu": (False, "filtered subset of the-stack-v2; overlaps starcoderdata"),
    "commitpack (full)": (False, "superset of commitpackft; jsonl, size not measured"),
    "starcoder2data-extras issues+kaggle": (False, "same sources as issues-kaggle-notebooks"),
    "issues-kaggle-notebooks (issues)": (False, "overlaps starcoderdata GitHub issues"),
    "the-stack-github-issues": (False, "overlaps starcoderdata GitHub issues; gated"),
    "finemath-4plus": (False, "subset of finemath-3plus, which is counted"),
    "MegaMath web-pro": (False, "LLM-refined from megamath-web; generator not checked"),
    "opc-fineweb-math-corpus": (False, "recalled from fineweb; overlaps finemath"),
    "open-web-math": (False, "overlaps megamath-web and infiwebmath"),
    "fineweb-edu": (False, "subset of fineweb, which is counted"),
    "dclm-baseline-1.0-parquet": (False, "same Common Crawl as fineweb; counted as overlap"),
    "dolma": (False, "Common Crawl overlap; URL lists only"),
    "Nemotron-CC v1 (real)": (False, "Common Crawl overlap with fineweb"),
    "Nemotron-CC-v2 real": (False, "Common Crawl overlap; gated"),
    "common-pile arxiv_papers": (False, "overlaps starcoder2data-extras arxiv"),
    "proof-pile-2 arxiv": (False, "overlaps starcoder2data-extras arxiv"),
}
# ponytail: sample-v0 document rates (clean #244, dedup v1), applied to tokens; swap for per-part token rates when measured
CLEAN_KEEP = (1 - 0.0197) * (1 - 1345 / 1414996)
PARTS = ["code", "synthetic code", "code-adjacent", "math", "English real", "English synthetic", "science"]


def tokens(s):
    if not s:
        return 0.0
    s = s.split()[0].upper()
    mult = {"T": 1e12, "B": 1e9, "M": 1e6}.get(s[-1], 1)
    return float(s.rstrip("TBM")) * (mult if s[-1] in "TBM" else 1)


def main(csv_path, out_path):
    rows = list(csv.DictReader(open(csv_path, encoding="utf-8")))
    cols = list(rows[0].keys())
    for c in ["counted", "count_reason"]:
        if c not in cols:
            cols.insert(cols.index("notes"), c)
    for r in rows:
        ok, why = COUNT.get(r["dataset"], (True, ""))
        r["counted"], r["count_reason"] = ("yes" if ok else "no"), why
    w = csv.DictWriter(open(csv_path, "w", newline="", encoding="utf-8"), fieldnames=cols)
    w.writeheader()
    w.writerows(rows)

    out = [f"Cleaned = raw x {CLEAN_KEEP:.4f} (sample-v0: cleaning dropped 1.97% of docs, dedup 1,345 of 1,414,996).", "",
           "| Part | Measured p1536 (B) | Card-only, other tokenizer (B) | Counted rows | Rows with no number | Raw max share of 20T, 4 passes | 3 passes | Cleaned, 4 passes | 3 passes |",
           "|---|---:|---:|---:|---|---:|---:|---:|---:|"]
    for part in PARTS:
        rs = [r for r in rows if r["part"] == part and r["counted"] == "yes"]
        meas = sum(float(r["tokens_p1536"]) for r in rs if r["tokens_p1536"]) / 1e9
        card = sum(tokens(r["tokens_card"]) for r in rs if not r["tokens_p1536"]) / 1e9
        none = [r["dataset"] for r in rs if not r["tokens_p1536"] and not r["tokens_card"]]
        tot = (meas + card) * 1e9
        out.append(f"| {part} | {meas:,.1f} | {card:,.1f} | {len(rs)} | {'; '.join(none) or '-'} | "
                   f"{tot * 4 / 20e12:.2%} | {tot * 3 / 20e12:.2%} | "
                   f"{tot * CLEAN_KEEP * 4 / 20e12:.2%} | {tot * CLEAN_KEEP * 3 / 20e12:.2%} |")
    open(out_path, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
