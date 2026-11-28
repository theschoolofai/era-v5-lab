"""One-off: add the new (not in the 38) candidate rows to dataset_list.csv, with overlaps, generators and card token counts."""
import csv
from huggingface_hub import HfApi

api = HfApi()
rows = list(csv.DictReader(open("dataset_list.csv", encoding="utf-8")))
cols = list(rows[0].keys())
for c in ["overlaps_with", "generator"]:
    if c not in cols:
        cols.insert(cols.index("notes"), c)
for r in rows:
    r.setdefault("overlaps_with", "")
    r.setdefault("generator", "")

used = {"go", "javascript", "typescript", "java", "cpp", "rust", "python"}
cadj = {"git-commits-cleaned", "github-issues-filtered-structured", "jupyter-scripts-dedup-filtered", "jupyter-structured-clean-dedup"}
other = [f.path for f in api.list_repo_tree("bigcode/starcoderdata", repo_type="dataset")
         if not f.path.startswith(".") and "." not in f.path and f.path not in used | cadj]
CADJ = "Also in Data B's task 1; their total is a cross-check"
SC2 = "no Hub licence tag; check card per subset"

# part, dataset, hub_id, hub_paths, access, tokens_card, card_tokenizer, licence, overlaps_with, generator, fallback, notes
NEW = [
    ("code", "starcoderdata other languages", "bigcode/starcoderdata", ";".join(other), "gated-auto", "", "", "other (per-file permissive Stack licences)", "the-stack-v2-dedup", "", "the-stack-v2-dedup", f"{len(other)} language folders"),
    ("code", "the-stack-v2-dedup", "bigcode/the-stack-v2-dedup", "", "gated-auto", "", "", "other (per-file)", "starcoderdata; stack-edu", "", "starcoderdata", "Hub holds file ids only; content from Software Heritage S3, so no Hub size"),
    ("code", "stack-edu", "HuggingFaceTB/stack-edu", "", "open", "125B", "SmolLM2 tokenizer", "per-file (license_type column)", "the-stack-v2 (filtered subset)", "", "the-stack-v2-dedup", "Hub holds blob ids only; content from Software Heritage S3"),
    ("code", "starcoder2data-extras compiler IR", "bigcode/starcoder2data-extras", "ir_cpp;ir_python;ir_rust;ir_low_resource", "open", "", "", SC2, "", "", "", ""),
    ("code", "opc-fineweb-code-corpus", "OpenCoder-LLM/opc-fineweb-code-corpus", "data", "open", "", "", "mit", "fineweb (code-related pages recalled from it)", "", "", "Web pages about code; may belong in code-adjacent"),
    ("code", "opc-annealing-corpus algorithmic", "OpenCoder-LLM/opc-annealing-corpus", "algorithmic_corpus", "open", "", "", "odc-by", "", "", "", ""),
    ("synthetic code", "opc-annealing-corpus synthetic", "OpenCoder-LLM/opc-annealing-corpus", "synthetic_code_snippet;synthetic_qa", "open", "", "", "odc-by", "", "not named on card", "Nemotron-Pretraining-Code-v1 synthetic", "Generator must be checked before it counts (closed-model output is Out)"),
    ("synthetic code", "Nemotron-Pretraining-Code-v1 synthetic", "nvidia/Nemotron-Pretraining-Code-v1", "Synthetic-Code", "gated-manual", "", "", "other (gated card)", "", "card gated", "opc-annealing-corpus synthetic", "Card and licence need login"),
    ("code-adjacent", "commitpack (full)", "bigcode/commitpack", "data", "open", "", "", "mit", "commitpackft (superset)", "", "commitpackft", CADJ),
    ("code-adjacent", "starcoderdata git commits", "bigcode/starcoderdata", "git-commits-cleaned", "gated-auto", "", "", "other", "commitpack", "", "commitpack", CADJ),
    ("code-adjacent", "starcoderdata GitHub issues", "bigcode/starcoderdata", "github-issues-filtered-structured", "gated-auto", "", "", "other", "the-stack-github-issues; issues-kaggle-notebooks issues", "", "issues-kaggle-notebooks (issues)", CADJ),
    ("code-adjacent", "starcoderdata Jupyter", "bigcode/starcoderdata", "jupyter-scripts-dedup-filtered;jupyter-structured-clean-dedup", "gated-auto", "", "", "other", "issues-kaggle-notebooks kaggle", "", "issues-kaggle-notebooks (kaggle)", CADJ),
    ("code-adjacent", "starcoder2data-extras documentation", "bigcode/starcoder2data-extras", "documentation", "open", "", "", SC2, "", "", "", CADJ),
    ("code-adjacent", "starcoder2data-extras issues+kaggle", "bigcode/starcoder2data-extras", "issues;kaggle", "open", "", "", SC2, "issues-kaggle-notebooks", "", "issues-kaggle-notebooks", CADJ),
    ("code-adjacent", "issues-kaggle-notebooks (issues)", "HuggingFaceTB/issues-kaggle-notebooks", "issues", "open", "11B", "not stated", "apache-2.0 (check card)", "starcoderdata GitHub issues", "", "starcoderdata GitHub issues", CADJ),
    ("code-adjacent", "the-stack-github-issues", "bigcode/the-stack-github-issues", "data", "gated-auto", "", "", "card gated", "starcoderdata GitHub issues", "", "issues-kaggle-notebooks (issues)", CADJ),
    ("math", "finemath-3plus", "HuggingFaceTB/finemath", "finemath-3plus", "open", "34B", "not stated", "odc-by", "finemath-4plus (superset: about 24B more than 4plus)", "", "", ""),
    ("math", "infiwebmath-3plus", "HuggingFaceTB/finemath", "infiwebmath-3plus", "open", "20.5B", "not stated", "odc-by", "open-web-math", "", "", ""),
    ("math", "MegaMath web-pro", "IFM/MegaMath", "megamath-web-pro", "open", "", "", "odc-by", "megamath-web (refined from it)", "LLM-refined; check model", "", "Llama output is Out; check the refining model first"),
    ("math", "opc-fineweb-math-corpus", "OpenCoder-LLM/opc-fineweb-math-corpus", "data", "open", "", "", "odc-by", "fineweb (math pages recalled from it)", "", "", ""),
    ("math", "open-web-math", "open-web-math/open-web-math", "data", "open", "14.7B", "not stated", "check card", "proof-pile-2 open-web-math; starcoder2data-extras owm; megamath-web", "", "proof-pile-2 algebraic-stack", ""),
    ("math", "proof-pile-2 algebraic-stack", "EleutherAI/proof-pile-2", "algebraic-stack", "open", "11B", "not stated (repo ships tokenizer.model)", "check card", "", "", "", ""),
    ("math", "Nemotron-CC-Math-v1", "nvidia/Nemotron-CC-Math-v1", "3;4plus", "gated-auto", "", "", "other (gated card)", "megamath-web; finemath", "", "finemath-3plus", "4plus_MIND (synthetic) left out of this row"),
    ("English real", "fineweb", "HuggingFaceFW/fineweb", "data", "open", "18.5T", "GPT-2", "odc-by", "fineweb-edu (superset); dclm", "", "dclm-baseline", "Only the part not in fineweb-edu is new supply"),
    ("English real", "dolma", "allenai/dolma", "", "open", "3T", "Llama (card table)", "odc-by", "Common Crawl sets (fineweb, dclm)", "", "fineweb", "Hub holds URL lists only; no Hub size"),
    ("English real", "Nemotron-CC-v2 real", "nvidia/Nemotron-CC-v2", "High-Quality;Medium-High-Quality;Medium-Quality", "gated-manual", "", "", "other (gated card)", "Nemotron-CC v1", "", "Nemotron-CC v1 (real)", ""),
    ("English real", "starcoder2data-extras wikipedia", "bigcode/starcoder2data-extras", "wikipedia", "open", "", "", SC2, "", "", "", ""),
    ("English synthetic", "cosmopedia", "HuggingFaceTB/cosmopedia", "data", "open", "25B", "not stated", "apache-2.0", "", "Mixtral-8x7B-Instruct-v0.1 (Apache-2.0)", "smollm-corpus cosmopedia-v2", ""),
    ("English synthetic", "smollm-corpus cosmopedia-v2", "HuggingFaceTB/smollm-corpus", "cosmopedia-v2", "open", "", "", "odc-by", "cosmopedia (same method, new prompts)", "Mixtral-8x7B-Instruct-v0.1 (Apache-2.0)", "cosmopedia", ""),
    ("English synthetic", "Nemotron-CC-v2 synthetic", "nvidia/Nemotron-CC-v2", "Diverse-QA;High-Quality-Synthetic;Translated-Diverse-QA", "gated-manual", "", "", "other (gated card)", "Nemotron-CC v1 (synthetic)", "card gated", "cosmopedia", ""),
    ("science", "peS2o", "allenai/peS2o", "data", "open", "42B", "whitespace words, not BPE", "odc-by", "", "", "common-pile arxiv_papers", ""),
    ("science", "common-pile arxiv_papers", "common-pile/arxiv_papers", ".", "open", "", "", "per document (open licences)", "proof-pile-2 arxiv; starcoder2data-extras arxiv", "", "proof-pile-2 arxiv", ""),
    ("science", "common-pile pubmed", "common-pile/pubmed", "data", "open", "", "", "per document (CC BY, CC BY-SA, CC0)", "peS2o", "", "peS2o", ""),
    ("science", "proof-pile-2 arxiv", "EleutherAI/proof-pile-2", "arxiv", "open", "29B", "not stated (repo ships tokenizer.model)", "check card", "common-pile arxiv_papers; starcoder2data-extras arxiv", "", "common-pile arxiv_papers", ""),
    ("science", "starcoder2data-extras arxiv", "bigcode/starcoder2data-extras", "arxiv", "open", "", "", SC2, "proof-pile-2 arxiv", "", "", ""),
]
for p, d, h, hp, acc, tc, ct, lic, ov, gen, fb, n in NEW:
    if any(r["dataset"] == d for r in rows):
        continue
    r = {c: "" for c in cols}
    r.update(part=p, dataset=d, hub_id=h, hub_paths=hp, in_38="new", access=acc, tokens_card=tc, card_tokenizer=ct,
             licence=lic, licence_source="Hub card/tag, 28 Nov 2026", overlaps_with=ov, generator=gen, fallback=fb, notes=n)
    rows.append(r)

CARD = {"en-fineweb-edu": ("1.3T", "GPT-2", "fineweb (subset of it)"), "en-dclm": ("4T", "not stated", "fineweb"),
        "math-finemath": ("9.6B", "not stated", "finemath-3plus (subset of it)"), "cadj-notebooks": ("1.7B", "not stated", ""),
        "math-megamath": ("", "", "open-web-math; finemath")}
for r in rows:
    if r["pack_id"] in CARD:
        tc, ct, ov = CARD[r["pack_id"]]
        r["tokens_card"] = r["tokens_card"] or tc
        r["card_tokenizer"] = r["card_tokenizer"] or ct
        r["overlaps_with"] = r["overlaps_with"] or ov

w = csv.DictWriter(open("dataset_list.csv", "w", newline="", encoding="utf-8"), fieldnames=cols)
w.writeheader()
w.writerows(rows)
print(len(rows), "rows")
