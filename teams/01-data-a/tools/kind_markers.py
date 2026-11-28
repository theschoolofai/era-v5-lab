"""D8: how many documents per pack carry markers of the "missing kinds" (counts only, no text printed).

  python -I teams/01-data-a/tools/kind_markers.py <packs_root>

Markers (substring or regex on the text column): reasoning traces (`<think>`), chat format (`<|im_start|>`), tool calls
(`<tool_call>`, `"tool_calls"`, `"function_call"`), execution output (`<jupyter_output>`, IPython `Out[n]:`, a Python
`Traceback (most recent call last)`). A marker is a sign, not a classifier: a hit can sit inside code or a quotation.
"""
import json, re, sys
from collections import defaultdict
from pathlib import Path
import pyarrow.parquet as pq

MARKERS = {
    "think_tag": re.compile(r"<think>"),
    "chatml": re.compile(r"<\|im_start\|>"),
    "tool_call_tag": re.compile(r"<tool_call>"),
    "tool_calls_json": re.compile(r'"tool_calls"'),
    "function_call_json": re.compile(r'"function_call"'),
    "jupyter_output": re.compile(r"<jupyter_output>"),
    "ipython_out": re.compile(r"\bOut\[\d+\]:"),
    "py_traceback": re.compile(r"Traceback \(most recent call last\)"),
}
counts = defaultdict(lambda: defaultdict(int)); docs = defaultdict(int)
for f in sorted(Path(sys.argv[1]).glob("*/*/*.parquet")):
    pack = f.parent.parent.name
    for t in pq.read_table(f, columns=["text"]).column(0).to_pylist():
        docs[pack] += 1
        hit_exec = False
        for k, rx in MARKERS.items():
            if rx.search(t):
                counts[pack][k] += 1
                hit_exec |= k in ("jupyter_output", "ipython_out", "py_traceback")
        counts[pack]["any_execution_output"] += hit_exec
tot = defaultdict(int)
for p in counts:
    for k, v in counts[p].items(): tot[k] += v
print(json.dumps({"docs": sum(docs.values()), "totals": dict(tot),
                  "packs": {p: {"docs": docs[p], **{k: v for k, v in sorted(counts[p].items()) if v}} for p in sorted(docs) if counts[p]}}, indent=1))
