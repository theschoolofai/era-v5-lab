"""Packed rows with a document mask (Lab 5, lab5/packed_rows/README.md)."""

from pathlib import Path
import sys
import unittest

import torch

TEAM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TEAM / "harness"))
sys.path.insert(0, str(TEAM / "tests"))
from test_week2_model import fixture
from week2.config import validate
from week2.data import BatchStream, DocumentWindows
from week2.model import LanguageModel


def model_for(kind="global"):
    c, rows, lengths = fixture()
    if kind == "local":
        c["model"].update(attn_pattern=["L", "G"], attn_window=3, attn_sink=True)
    torch.manual_seed(1234)
    model = LanguageModel(c["model"], rows, lengths)
    model.eval()
    return model


def one_row(*docs, length=8, pad=0):
    """A packed row from token lists: ids, valid, doc_ids, pos_ids (batch of one)."""
    ids = torch.full((1, length), pad, dtype=torch.long)
    doc = torch.zeros_like(ids)
    pos = torch.zeros_like(ids)
    at = 0
    for n, tokens in enumerate(docs, start=1):
        ids[0, at : at + len(tokens)] = torch.tensor(tokens)
        doc[0, at : at + len(tokens)] = n
        pos[0, at : at + len(tokens)] = torch.arange(len(tokens))
        at += len(tokens)
    return ids, doc != 0, doc, pos


class ModelTests(unittest.TestCase):
    def test_no_segments_is_todays_path(self):
        # (a) Without segments nothing changes: same logits as the unchanged call.
        model = model_for()
        ids = torch.arange(16).reshape(2, 8) % 31
        valid = torch.ones_like(ids, dtype=torch.bool)
        with torch.no_grad():
            self.assertTrue(torch.equal(model(ids, valid), model(ids, valid, segments=None)))

    def test_one_document_per_row_matches_unpacked(self):
        # (b) One window filling the row, positions 0..7: same logits as today.
        for kind in ("global", "local"):
            model = model_for(kind)
            ids = torch.arange(16).reshape(2, 8) % 31
            valid = torch.ones_like(ids, dtype=torch.bool)
            doc = torch.ones_like(ids)
            pos = torch.arange(8).expand(2, 8)
            with torch.no_grad():
                plain = model(ids, valid)
                packed = model(ids, valid, segments=(doc, pos))
            torch.testing.assert_close(packed, plain, rtol=0, atol=1e-6, msg=kind)

    def test_two_documents_in_a_row_match_each_alone(self):
        # (c) Each token's logits are the same as when its document has a row of its own.
        for kind in ("global", "local"):
            model = model_for(kind)
            a, b = [3, 9, 4], [7, 1, 12, 5]
            ids, valid, doc, pos = one_row(a, b)
            ia, va, da, pa = one_row(a)
            ib, vb, db, pb = one_row(b)
            with torch.no_grad():
                both = model(ids, valid, segments=(doc, pos))
                alone_a = model(ia, va, segments=(da, pa))
                alone_b = model(ib, vb, segments=(db, pb))
            torch.testing.assert_close(both[0, :3], alone_a[0, :3], rtol=0, atol=1e-5, msg=kind)
            torch.testing.assert_close(both[0, 3:7], alone_b[0, :4], rtol=0, atol=1e-5, msg=kind)

    def test_mask_blocks_the_earlier_document(self):
        # Changing the first document must not change the second document's logits.
        model = model_for()
        ids1, valid, doc, pos = one_row([3, 9, 4], [7, 1, 12, 5])
        ids2, _, _, _ = one_row([20, 21, 22], [7, 1, 12, 5])
        with torch.no_grad():
            first = model(ids1, valid, segments=(doc, pos))
            second = model(ids2, valid, segments=(doc, pos))
        torch.testing.assert_close(first[0, 3:7], second[0, 3:7], rtol=0, atol=1e-5)
        self.assertFalse(torch.allclose(first[0, :3], second[0, :3]))

    def test_padding_gives_finite_output(self):
        model = model_for()
        ids, valid, doc, pos = one_row([3, 9])
        with torch.no_grad():
            out = model(ids, valid, segments=(doc, pos))
        self.assertTrue(torch.isfinite(out).all())

    def test_sdpa_matches_eager_on_packed_rows(self):
        # P17: SDPA with the explicit document mask gives eager's logits and gradients.
        ids, valid, doc, pos = one_row([3, 9, 4], [7, 1, 12, 5])
        out = {}
        for impl in ("eager", "sdpa"):
            c, rows, lengths = fixture()
            c["model"]["attn_impl"] = impl
            torch.manual_seed(1234)
            model = LanguageModel(c["model"], rows, lengths)
            logits = model(ids, valid, segments=(doc, pos))
            logits.float().pow(2).mean().backward()
            grads = {n: p.grad.clone() for n, p in model.named_parameters() if p.grad is not None}
            out[impl] = (logits.detach(), grads)
        torch.testing.assert_close(out["sdpa"][0], out["eager"][0], rtol=0, atol=1e-5)
        self.assertEqual(sorted(out["sdpa"][1]), sorted(out["eager"][1]))
        for name, g in out["eager"][1].items():
            torch.testing.assert_close(out["sdpa"][1][name], g, rtol=1e-4, atol=1e-6, msg=name)

    def test_gradient_coverage_is_the_same_on_both_paths(self):
        # TSAI's lab rule for speed claims: parameters whose gradient is None or all zero must be
        # the same with the fast path (SDPA) on and off.
        ids, valid, doc, pos = one_row([3, 9, 4], [7, 1, 12, 5])
        sys.path.insert(0, str(TEAM / "lab5" / "packed_rows"))
        from measure_attention import gradient_gaps
        gaps = {}
        for impl in ("eager", "sdpa"):
            c, rows, lengths = fixture()
            c["model"]["attn_impl"] = impl
            torch.manual_seed(1234)
            model = LanguageModel(c["model"], rows, lengths)
            model(ids, valid, segments=(doc, pos)).float().pow(2).mean().backward()
            gaps[impl] = gradient_gaps(model)
        self.assertEqual(gaps["sdpa"], gaps["eager"])


class FakeWindows:
    """Just what BatchStream and packed_batch read from DocumentWindows."""

    packed_batch = DocumentWindows.packed_batch

    def __init__(self, sizes, seq_len=8):
        self.seq_len, self.pad_id = seq_len, 0
        self.windows = []
        for w, n in enumerate(sizes):
            target = [(10 * w + i) % 31 for i in range(n)]
            self.windows.append(([1] + target[:-1], target, [2] * n))


class LoaderTests(unittest.TestCase):
    def test_rows_hold_whole_windows_with_ids_and_positions(self):
        data = FakeWindows([3, 4, 5, 2, 6, 7, 7, 7, 7, 7])
        stream = BatchStream(data, batch_size=2, seed=0, pack=True)
        stream.order = list(range(10))
        stream.PACK_POOL = 5
        x, y, lengths, doc, pos = stream.next(torch.device("cpu"))
        # Pool starts as windows 0-4 (sizes 3, 4, 5, 2, 6). Row 0: the largest that fits is 6
        # (window 4), then 2 (window 3): full. Row 1: the pool now also holds windows 5 and 6
        # (size 7); it takes 7, and nothing else fits in the last slot, which stays padding.
        self.assertEqual(doc[0].tolist(), [1, 1, 1, 1, 1, 1, 2, 2])
        self.assertEqual(pos[0].tolist(), [0, 1, 2, 3, 4, 5, 0, 1])
        self.assertEqual(doc[1].tolist(), [1, 1, 1, 1, 1, 1, 1, 0])
        self.assertEqual(y[0, :6].tolist(), data.windows[4][1])
        self.assertEqual(y[0, 6:].tolist(), data.windows[3][1])
        self.assertEqual(y[1, 7].item(), -100)
        self.assertEqual(stream.pool, [0, 1, 2, 6, 7])
        # (e) Bytes: every target byte of the placed windows is counted once.
        self.assertEqual(int(lengths.sum()), 2 * (6 + 2 + 7))

    def test_padding_is_marked(self):
        # Window 0 (3) is placed; window 1 (6) does not fit in the 5 left, so they are padding.
        data = FakeWindows([3, 6])
        stream = BatchStream(data, batch_size=1, seed=0, pack=True)
        stream.order, stream.PACK_POOL = [0, 1], 1
        _, y, _, doc, pos = stream.next(torch.device("cpu"))
        self.assertEqual(doc[0].tolist(), [1, 1, 1, 0, 0, 0, 0, 0])
        self.assertEqual(y[0, 3:].tolist(), [-100] * 5)

    def test_resume_continues_at_the_same_window(self):
        # (g) Save after one batch, restore into a fresh stream: the next batch is identical.
        data = FakeWindows([3, 4, 5, 2, 6, 1, 7, 3])
        stream = BatchStream(data, batch_size=2, seed=5, pack=True)
        stream.next(torch.device("cpu"))
        state = stream.state_dict()
        expected = stream.next(torch.device("cpu"))
        again = BatchStream(data, batch_size=2, seed=99, pack=True)
        again.load_state_dict(state)
        for a, b in zip(again.next(torch.device("cpu")), expected):
            self.assertTrue(torch.equal(a, b))

    def test_fill_rises_over_one_window_per_row(self):
        # (f) The same windows need fewer positions packed than one per row.
        sizes = [3, 4, 5, 2, 6, 1, 7, 3, 2, 2]
        data = FakeWindows(sizes)
        stream = BatchStream(data, batch_size=1, seed=0, pack=True)
        stream.order = list(range(len(sizes)))
        # Count windows placed per row (the stream reshuffles when a pass ends, so offset wraps).
        rows = placed = 0
        while placed < len(sizes):
            doc = stream.next(torch.device("cpu"))[3]
            placed += int(doc.max())
            rows += 1
        # 35 tokens need at least 5 rows of 8; best fit reaches that.
        self.assertEqual(rows, 5)
        self.assertLess(rows * 8, len(sizes) * 8)

    def test_ids_are_32_bit(self):
        # P15: the format table fixes doc_ids and pos_ids as 32-bit integers.
        data = FakeWindows([3, 4, 5])
        stream = BatchStream(data, batch_size=1, seed=0, pack=True)
        x, y, lengths, doc, pos = stream.next(torch.device("cpu"))
        self.assertEqual((doc.dtype, pos.dtype), (torch.int32, torch.int32))
        self.assertEqual(x.dtype, torch.long)

    def test_each_pass_places_every_window_once(self):
        # P18: the pool drains at the end of a pass before the next pass starts, so every pass
        # places each window exactly once (topping up across the boundary repeated some windows
        # and skipped others within a pass).
        sizes = [3, 4, 5, 2, 6, 1, 7, 3, 2, 2, 8, 1, 5, 6, 4, 2, 3, 7, 1, 5]
        data = FakeWindows(sizes)
        stream = BatchStream(data, batch_size=1, seed=3, pack=True)
        stream.PACK_POOL = 6
        log = []  # every window placed, in placing order

        class Logged(list):
            def pop(self, i):
                v = list.pop(self, i)
                log.append(v)
                return v
        stream.pool = Logged()
        for _ in range(40):
            stream.next(torch.device("cpu"))
        n = len(sizes)
        full = len(log) // n
        self.assertGreaterEqual(full, 2)
        for k in range(full):
            self.assertEqual(sorted(log[k * n : (k + 1) * n]), list(range(n)), msg=f"pass {k}")

    def test_resume_across_the_end_of_a_pass(self):
        # A checkpoint taken while the pool drains resumes to the same rows.
        data = FakeWindows([3, 4, 5, 2, 6, 1, 7, 3])
        stream = BatchStream(data, batch_size=1, seed=5, pack=True)
        stream.PACK_POOL = 4
        while stream.offset < len(stream.order):
            stream.next(torch.device("cpu"))
        state = stream.state_dict()
        expected = [stream.next(torch.device("cpu")) for _ in range(3)]
        again = BatchStream(data, batch_size=1, seed=99, pack=True)
        again.PACK_POOL = 4
        again.load_state_dict(state)
        for batch in expected:
            for a, b in zip(again.next(torch.device("cpu")), batch):
                self.assertTrue(torch.equal(a, b))

    def test_pool_of_one_is_strict_order(self):
        # P11: run.pack_pool sets the pool; a pool of 1 places windows strictly in order.
        sys.path.insert(0, str(TEAM / "lab5" / "packed_rows"))
        import numpy as np
        from measure_fill import in_order_rows, packed_rows
        sizes = [3, 4, 5, 2, 6, 1, 7, 3, 2, 2, 8, 1, 5]
        self.assertEqual(packed_rows(np.array(sizes), 8, pool=1), in_order_rows(np.array(sizes), 8))
        data = FakeWindows(sizes)
        stream = BatchStream(data, batch_size=1, seed=0, pack=True, pool=1)
        stream.order = list(range(len(sizes)))
        per_row = []  # windows placed in each row
        while sum(per_row) < len(sizes):
            per_row.append(int(stream.next(torch.device("cpu"))[3][0].max()))
        self.assertEqual(len(per_row), in_order_rows(np.array(sizes), 8))

    def test_unpacked_stream_is_unchanged(self):
        data = FakeWindows([3, 4, 5])
        data.batch = DocumentWindows.batch.__get__(data)
        stream = BatchStream(data, batch_size=2, seed=0)
        self.assertEqual(len(stream.next(torch.device("cpu"))), 3)
        # An unpacked checkpoint has exactly today's keys.
        self.assertEqual(sorted(stream.state_dict()), ["offset", "order", "rng"])

    def test_measure_fill_uses_the_loader_rule(self):
        # measure_fill.packed_rows gives the same row count as BatchStream on the same order.
        sys.path.insert(0, str(TEAM / "lab5" / "packed_rows"))
        import numpy as np
        from measure_fill import packed_rows
        sizes = [3, 4, 5, 2, 6, 1, 7, 3, 2, 2, 8, 1, 5]
        data = FakeWindows(sizes)
        stream = BatchStream(data, batch_size=1, seed=0, pack=True)
        stream.order = list(range(len(sizes)))
        rows = placed = 0
        while placed < len(sizes):
            placed += int(stream.next(torch.device("cpu"))[3].max())
            rows += 1
        self.assertEqual(rows, packed_rows(np.array(sizes), 8))


class ConfigTests(unittest.TestCase):
    def test_pack_is_validated(self):
        c, _, _ = fixture()
        c["run"]["pack"] = True
        self.assertFalse(any("pack" in e for e in validate(c)))
        c["run"]["pack"] = "yes"
        self.assertTrue(any("run.pack" in e for e in validate(c)))
        c["run"]["pack"] = True
        c["model"]["attn_impl"] = "sdpa"  # P17: SDPA takes the document mask too
        self.assertFalse(any("pack" in e for e in validate(c)))
        c["run"]["pack_pool"] = 0  # P11
        self.assertTrue(any("run.pack_pool" in e for e in validate(c)))
        c["run"]["pack_pool"] = 32
        self.assertFalse(any("pack" in e for e in validate(c)))


if __name__ == "__main__":
    unittest.main()
