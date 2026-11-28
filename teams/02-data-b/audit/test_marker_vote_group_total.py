"""Failing test for the marker_vote group-total bug (data-b, PR #842).

`lang_id.marker_vote` checks `marker_min_hits` against the *group* total, then returns one language from that
group with a smaller count of its own. With `marker_min_hits = 3` and `marker_groups = [["as", "sa_Beng"]]`, two
hits each pass a 3-hit minimum.

This file is the failing test only. No change to `lang_id.py` is included: the fix is the PR author's to make.
Run it with:

    python -m pytest teams/02-data-b/audit/test_marker_vote_group_total.py -q

Expected today: 2 xfailed (strict), 1 passed. Lab rule 3 (28 Nov): no red tests on main, so the two
known-bug cases are marked xfail(strict=True) against #842. They will report XPASS -- and so fail -- as soon as
the bug is fixed, which is the reminder to drop the markers.
"""

import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import pytest  # noqa: E402

import lang_id  # noqa: E402

CFG = json.load(open(HERE / "lang_label_config.json", encoding="utf-8"))


class MarkerVoteGroupTotalTest(unittest.TestCase):
    """The threshold must be met by the language that is returned, not by the group it belongs to."""

    def setUp(self):
        self.group = next((g for g in CFG.get("marker_groups", []) if len(g) >= 2), None)
        if self.group is None:
            self.skipTest("no multi-language marker group in the config")
        self.a, self.b = self.group[0], self.group[1]
        self.min_hits = CFG["marker_min_hits"]

    @pytest.mark.xfail(strict=True, reason="known bug #842: marker_vote tests marker_min_hits on the group total")
    def test_group_total_does_not_satisfy_the_per_language_minimum(self):
        """Two hits each in a 2-language group sums to 4, which is over a 3-hit minimum, but neither language
        has 3 hits of its own, so the vote must be 'unknown'."""
        hits = {self.a: 2, self.b: 2}
        self.assertGreaterEqual(sum(hits.values()), self.min_hits)      # the group total clears the bar
        self.assertLess(max(hits.values()), self.min_hits)              # no single language does
        self.assertEqual(
            lang_id.marker_vote(hits, CFG), "unknown",
            f"{hits} returned a language although no member met marker_min_hits={self.min_hits}",
        )

    @pytest.mark.xfail(strict=True, reason="known bug #842: marker_vote returns a language below marker_min_hits")
    def test_returned_language_meets_the_minimum(self):
        """Whatever marker_vote returns must be a language whose own hit count clears marker_min_hits."""
        for hits in ({self.a: 2, self.b: 2}, {self.a: 3, self.b: 1}, {self.a: 1, self.b: 2}):
            got = lang_id.marker_vote(hits, CFG)
            if got == "unknown":
                continue
            self.assertGreaterEqual(
                hits.get(got, 0), self.min_hits,
                f"marker_vote returned {got!r} on {hits[got]} hits, below marker_min_hits={self.min_hits}",
            )

    def test_a_language_that_clears_the_minimum_still_wins(self):
        """The fix must not make a genuine winner unknown: 4 hits for one language is a real result."""
        hits = {self.a: 4, self.b: 1}
        self.assertEqual(lang_id.marker_vote(hits, CFG), self.a)


if __name__ == "__main__":
    unittest.main()
