#!/usr/bin/env python3
"""Tests for the held-out slicer:  python test_slices.py"""
import hashlib, json, sys, tempfile, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import slices as s  # noqa: E402

DATA = HERE.parents[1] / '05-architecture' / 'heldout_v1' / 'data'
JSONL, SUMS = DATA / 'heldout_v1.jsonl', DATA / 'SHA256SUMS'


def make_corpus(directory: Path, rows, name='heldout_v1.jsonl'):
    """Write rows as the jsonl plus a SHA256SUMS that matches it."""
    jsonl = directory / name
    jsonl.write_text(''.join(json.dumps(r) + '\n' for r in rows), encoding='utf-8')
    sums = directory / 'SHA256SUMS'
    sums.write_text(f'{hashlib.sha256(jsonl.read_bytes()).hexdigest()}  {name}\n', encoding='utf-8')
    return jsonl, sums


ROWS = [{'id': 'c4-val-000000', 'text': 'alpha'}, {'id': 'c4-val-000001', 'text': 'beta'},
        {'id': 'fw2-hi-test-000000', 'text': 'namaste'}]


class SliceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_slice_prefixes(self):
        expected = {'c4-val', 'owm-test', 'pes2o-val'}
        expected |= {f'fw2-{l}-test' for l in 'hi bn ta te kn ml mr gu pa or as'.split()}
        expected |= {f'vault-{l}-test' for l in 'py cpp go java js rs'.split()}
        self.assertEqual(set(s.SLICES), expected)
        self.assertEqual(set(s.load_slices(JSONL, SUMS)), set(s.SLICES))

    def test_sha_checked(self):
        data = bytearray(JSONL.read_bytes())
        data[0] ^= 1
        bad = self.dir / JSONL.name
        bad.write_bytes(bytes(data))
        with self.assertRaises(ValueError):
            s.load_slices(bad, SUMS)

    def test_load_groups_documents_by_prefix(self):
        jsonl, sums = make_corpus(self.dir, ROWS)
        self.assertEqual(s.load_slices(jsonl, sums),
                         {'c4-val': ['alpha', 'beta'], 'fw2-hi-test': ['namaste']})

    def test_write_and_normalize(self):
        slices = {'c4-val': ['alpha', 'beta'], 'fw2-hi-test': ['namaste']}
        plain = s.write_slice_texts(slices, self.dir / 'plain')
        self.assertEqual(set(plain), set(slices))
        self.assertEqual(plain['c4-val'].read_text(encoding='utf-8'), 'alpha\n\nbeta')
        self.assertEqual(plain['fw2-hi-test'].read_text(encoding='utf-8'), 'namaste')
        upper = s.write_slice_texts(slices, self.dir / 'upper', normalizer=str.upper)
        self.assertEqual(upper['c4-val'].read_text(encoding='utf-8'), 'ALPHA\n\nBETA')
        self.assertEqual(upper['fw2-hi-test'].read_text(encoding='utf-8'), 'NAMASTE')


if __name__ == '__main__':
    unittest.main()
