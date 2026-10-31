"""Build eval_mini_v0_spec.json: a fixed, seeded item list that anyone can rerun with stock lm-eval and evalplus.

Every lm-eval task is 5-shot, so one `lm-eval run` command covers them all. Code uses the full HumanEval+ and MBPP+
(evalplus refuses partial datasets). For each task the spec records the dataset revision and a sha256 over the chosen
items, so a changed or reordered hub dataset is detected instead of silently giving different numbers.

Usage (from this folder):  python make_eval_mini_spec.py
"""
import hashlib
import json
import random

from huggingface_hub import dataset_info
from lm_eval.tasks import TaskManager, get_task_dict

from run_lm_eval import HERE

SEED = 20261028
TASKS = {  # task: number of items (priority: code and agentic, then Indic, then everything else)
    "leaderboard_mmlu_pro": 300,
    "gsm8k": 100,
    "belebele_hin_Deva": 100,
    "belebele_tel_Telu": 100,
    "belebele_tam_Taml": 100,
    "milu_Hindi": 100,
    "milu_Telugu": 100,
    "milu_Tamil": 100,
    "milu_Bengali": 100,
}
NUM_FEWSHOT = 5


def items_sha256(docs, ids):
    h = hashlib.sha256()
    for i in ids:
        h.update(json.dumps(docs[i], sort_keys=True, ensure_ascii=False, default=str).encode("utf-8"))
    return h.hexdigest()


def main():
    tm = TaskManager(include_path=str(HERE / "tasks"))
    task_objs = get_task_dict(list(TASKS), tm)
    rng = random.Random(SEED)
    spec_tasks = {}
    for name, k in TASKS.items():
        task = task_objs[name]
        docs = list(task.eval_docs)
        ids = sorted(rng.sample(range(len(docs)), k))
        path = task.config.dataset_path
        try:
            rev = dataset_info(path).sha
        except Exception as e:  # gated or offline: record why
            rev = f"unavailable: {type(e).__name__}"
        spec_tasks[name] = {"doc_ids": ids, "num_fewshot": NUM_FEWSHOT, "n_test_docs": len(docs),
                            "dataset": path, "dataset_name": task.config.dataset_name, "dataset_revision": rev,
                            "items_sha256": items_sha256(docs, ids), "task_version": task.VERSION if hasattr(task, "VERSION") else None}
        print(f"{name:22s} {k:4d} of {len(docs):6d}  {path}@{str(rev)[:10]}")

    samples_arg = json.dumps({t: v["doc_ids"] for t, v in spec_tasks.items()}, separators=(",", ":"))
    spec = {
        "name": "eval-mini", "version": "v0", "created": "2026-10-25", "seed": SEED,
        "sampler": "random.Random(seed).sample(range(n_test_docs), k), sorted; tasks drawn in the order listed",
        "scoring_note": "subset scores are for comparing checkpoints and formats; they are NOT comparable to published full-set scores",
        "noise_note": ("Measured 26 Oct on Qwen2.5-1.5B: switching only the attention kernel (math -> memory-efficient SDPA) moved "
                       "100-item tasks by up to 2 items and MMLU-Pro (300) by 4 items, because near-tie items flip. Treat "
                       "differences of about 2 points on a 100-item task as implementation noise, not a real change."),
        "tasks": spec_tasks,
        "code": {"humaneval_plus": "all 164 problems", "mbpp_plus": "all 378 problems", "harness": "evalplus 0.3.1",
                 "settings": "greedy, base (completion) prompt, bf16",
                 "known_evalplus_0.3.1_bugs": [
                     "Shared EOS list: running humaneval then mbpp in one process gives mbpp humaneval's stop strings and truncates answers. Use one process per dataset, or run_codegen.py.",
                     "HF backend stacks one stop criterion per problem; stale ones can end generation after 1 token. Use --backend vllm, or run_codegen.py.",
                     "Check your tokenizer round-trips text (transformers 5 rebuilt deepseek-coder's tokenizer wrongly); run_codegen.py checks this."]},
        "commands": {
            "lm_eval": ("lm-eval run --model hf --model_args pretrained=<model>,revision=<sha>,dtype=bfloat16,max_length=<context> "
                        "--tasks " + ",".join(spec_tasks) + f" --num_fewshot {NUM_FEWSHOT} --batch_size 1 "
                        "--include_path <this folder>/tasks --samples '<the samples_arg below>'"),
            "max_length_used": "4096 for Qwen2.5-1.5B and Llama-3.2-3B, 8192 for gemma-2-2b (each model's Open LLM Leaderboard run)",
            "small_gpu_note": ("On GPUs with 8 GB or less, stock lm-eval runs out of memory for 2-3B models (full-sequence logits, "
                               "math-kernel attention). Use: python run_lm_eval.py --model <key> --samples-file eval_mini_v0_spec.json "
                               "--tag eval_mini_v0 (keeps only the scored logits, bit-identical; memory-efficient attention)."),
            "items_builder": ("python make_eval_mini_items.py [--skip-gated] -> runs/eval_mini_v0_items.json: the same items as "
                              "question/choices/answer for pipelines without lm-eval (Team 12's quantize_eval.py --eval). Never commit it."),
            "samples_arg": samples_arg,
            "evalplus_generate": ("python run_codegen.py --model <key in published_scores.json>  "
                                  "(recommended: patches two evalplus 0.3.1 bugs, see below). With stock evalplus, run ONE dataset per process: "
                                  "evalplus.codegen <model> humaneval --backend vllm --greedy True --force_base_prompt True, then a new process for mbpp."),
            "evalplus_execute": "evalplus.evaluate --dataset humaneval --samples <file>.jsonl  (Linux only; see code_eval_colab.ipynb)",
        },
    }
    out = HERE / "eval_mini_v0_spec.json"
    out.write_text(json.dumps(spec, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print("wrote", out, f"({out.stat().st_size / 1024:.0f} KiB)")


if __name__ == "__main__":
    main()
