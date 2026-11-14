"""Tests for scripts/time_rules.py. Every doc and rule here is made up; packs are written to a temporary folder.

  python3 -m unittest discover -s spec_v1_1/tests      (from teams/01-data-a)
"""
import contextlib
import io
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

SPEC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SPEC / "scripts"))
import time_rules as t  # noqa: E402

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
except ImportError:  # the pack tests need pyarrow
    pa = None

TE = "తెలుగు వాక్యం"  # made-up Telugu words


def write_pack(folder, name, rows, with_pack_id=True):
    cols = {"doc_id": [r[0] for r in rows], "text": [r[1] for r in rows]}
    if with_pack_id:
        cols["pack_id"] = [name] * len(rows)
    path = Path(folder) / f"{name}.parquet"
    pq.write_table(pa.table(cols), path)
    return path


def keep(doc):
    return ("keep", doc["text"])


def upper(doc):
    return ("fix", doc["text"].upper())


def same_fix(doc):
    return ("fix", doc["text"])


def drop_short(doc):
    return ("drop", doc["text"]) if len(doc["text"]) < 5 else ("keep", doc["text"])


def boom(doc):
    raise ValueError("made-up failure")


def slow(doc):
    time.sleep(0.5)
    return ("keep", doc["text"])


DOC = {"doc_id": "0" * 16, "text": "abc def", "pack_id": "made-up"}


class Call(unittest.TestCase):
    def test_verdicts(self):
        self.assertEqual(t.call(keep, DOC, 5)[:2], ("keep", "abc def"))
        self.assertEqual(t.call(upper, DOC, 5)[:2], ("fix", "ABC DEF"))
        self.assertEqual(t.call(boom, DOC, 5)[:2], ("error", "abc def"))
        self.assertEqual(t.call(lambda d: True, DOC, 5)[:2], ("drop", "abc def"))

    def test_a_fix_that_changes_nothing_is_keep(self):
        self.assertEqual(t.call(same_fix, DOC, 5)[0], "keep")

    def test_the_rule_gets_a_copy(self):
        def mutate(doc):
            doc["text"] = "changed"
            return ("keep", "abc def")
        doc = dict(DOC)
        t.call(mutate, doc, 5)
        self.assertEqual(doc, DOC)

    @unittest.skipUnless(t.HAS_ALARM, "no per-doc time limit on this platform")
    def test_timeout(self):
        import signal
        old = signal.signal(signal.SIGALRM, t._alarm)
        try:
            verdict, new, seconds = t.call(slow, DOC, 0.05)
        finally:
            signal.signal(signal.SIGALRM, old)
        self.assertEqual((verdict, new), ("timeout", "abc def"))
        self.assertLess(seconds, 0.4)


class Timing(unittest.TestCase):
    DOCS = [{"doc_id": f"{i:016x}", "text": text, "pack_id": "made-up"} for i, text in enumerate(("ab", "abcdef", "xyz uvw"))]

    def test_counts_and_slowest_doc(self):
        r = t.time_rule(upper, self.DOCS, 5)
        self.assertEqual((r["fix"], r["keep"], r["drop"], r["error"], r["timeout"]), (3, 0, 0, 0, 0))
        self.assertIn(r["slowest_doc"], {d["doc_id"] for d in self.DOCS})
        self.assertGreaterEqual(r["seconds"], 0)

    def test_in_order_a_drop_stops_and_a_fix_carries(self):
        seen = []

        def record(doc):
            seen.append(doc["text"])
            return ("keep", doc["text"])
        wall, dropped, errors = t.time_in_order({"a": upper, "b": drop_short, "c": record}, self.DOCS, 5)
        self.assertEqual((dropped, errors), (1, 0))
        self.assertEqual(seen, ["ABCDEF", "XYZ UVW"])  # "ab" was dropped before c; c saw the fixed text

    def test_in_order_counts_errors(self):
        self.assertEqual(t.time_in_order({"a": boom}, self.DOCS, 5)[1:], (0, 3))


@unittest.skipIf(pa is None, "pyarrow is not installed")
class Packs(unittest.TestCase):
    def test_read_pack_names_the_pack_from_the_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_pack(tmp, "made-up-pack", [("a" * 16, "x")], with_pack_id=False)
            self.assertEqual(t.read_pack(path), [{"doc_id": "a" * 16, "text": "x", "pack_id": "made-up-pack"}])

    def test_no_harm_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_pack(tmp, "made-up-pack", [("a" * 16, "x")])
            self.assertEqual(t.harm_check(path, t.sha256(path)), "no harm report to compare")

    def test_end_to_end_on_the_indic_sheet(self):
        sheet = SPEC / "sheets" / "medicine_indic.md"
        with tempfile.TemporaryDirectory() as tmp:
            path = write_pack(tmp, "ind-te-sangraha-v", [("1" * 16, TE + " . . " + TE), ("2" * 16, TE + ". " + TE)])
            out = Path(tmp) / "timing.json"
            with contextlib.redirect_stdout(io.StringIO()) as printed:
                code = t.main(["--sheet", str(sheet), "--pack", str(path), "--json", str(out)])
            self.assertEqual(code, 0)
            report = json.loads(out.read_text())
            rule = report["packs"]["ind-te-sangraha-v"]["rules"]["DB-C6-001"]
            self.assertEqual((rule["fix"], rule["keep"], rule["error"], rule["timeout"]), (1, 1, 0, 0))
            self.assertEqual(report["packs"]["ind-te-sangraha-v"]["in_order_dropped"], 0)
            self.assertIn("ALL IN ORDER", printed.getvalue())
            self.assertNotIn(TE, printed.getvalue() + out.read_text())  # never the text


if __name__ == "__main__":
    unittest.main()
