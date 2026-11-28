"""Count what DA-B4-001's `{[ ]}` form does on the math packs, with the real clean() (counts only, no text).

  python teams/01-data-a/spec_v1_1/scripts/count_da_b4_001_latex.py <packs_root>

<packs_root> holds <pack>/<part folder>/part-*.parquet (the 38 sample packs; every part, held-out included).
For each of math-finemath and math-megamath: docs with a `{[ ]}` group (pattern `\\{\\[\\s*\\w+\\s*\\]\\}`, the first
alternative of B4_RX), what clean() does to them (fix / drop / keep, and which rule dropped them), how many groups
DA-B4-001 removed, and, for the fixed docs, what was removed: a spaced template variable (`{[ name ]}`), a footnote
marker (`^{[digit]}`), or another bracket group (LaTeX arguments and the like).
"""
import collections, importlib.util, json, re, sys
from pathlib import Path

import pyarrow.parquet as pq

CLEAN = Path(__file__).resolve().parents[1] / "clean.py"
spec = importlib.util.spec_from_file_location("clean_v1_1", CLEAN)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
GROUP = re.compile(r"\{\[\s*\w+\s*\]\}")
PIPE = list(c._PIPELINES["math"]) + [c._shared_f1_rule]


def kind(text, m):
    g = m.group(0)
    inner = g[2:-2].strip()
    if g != "{[" + inner + "]}":
        return "spaced_template"
    if text[max(0, m.start() - 1):m.start()] == "^" and inner.isdigit():
        return "footnote_marker"
    return "other_bracket_group"


def dropped_by(d):
    d = dict(d)
    for make in PIPE:
        if d["pack_id"] not in c.SCOPE[c._ID[make]]:
            continue
        action, text = make()(d)
        if action == "drop":
            return c._ID[make]
        d["text"] = text
    return None


def main(root):
    out = {}
    for pack in ("math-finemath", "math-megamath"):
        n = docs = groups = removed = 0
        actions, drops, fixed_kinds, fixed_docs_by = collections.Counter(), collections.Counter(), collections.Counter(), collections.Counter()
        for f in sorted(Path(root, pack).glob("*/*.parquet")):
            for r in pq.read_table(f, columns=["doc_id", "text", "url", "lang_label", "pack_id"]).to_pylist():
                n += 1
                ms = list(GROUP.finditer(r["text"]))
                if not ms:
                    continue
                docs += 1; groups += len(ms)
                action, text = c.clean(r)
                actions[action] += 1
                if action == "drop":
                    drops[dropped_by(r)] += 1
                    continue
                gone = len(ms) - len(GROUP.findall(text))
                if action == "fix" and gone > 0:
                    removed += gone
                    ks = {kind(r["text"], m) for m in ms}
                    for m in ms:
                        fixed_kinds[kind(r["text"], m)] += 1
                    fixed_docs_by["with_other_bracket_group" if "other_bracket_group" in ks else
                                  "footnote_markers_only" if ks == {"footnote_marker"} else "templates_or_footnotes"] += 1
        out[pack] = {"docs": n, "docs_with_group": docs, "groups": groups, "clean_actions": dict(actions),
                     "dropped_by_rule": dict(drops), "groups_removed_in_fixed_docs": removed,
                     "fixed_docs_with_groups_removed": sum(fixed_docs_by.values()), "fixed_docs_by_kind": dict(fixed_docs_by),
                     "groups_in_fixed_docs_by_kind": dict(fixed_kinds)}
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1])
