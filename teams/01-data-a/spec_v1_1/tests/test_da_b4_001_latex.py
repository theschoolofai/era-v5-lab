"""DA-B4-001 (math, sheets/specv1_1.md medicine 53; clean.py _math_b4_001, B4_RX at line 3495) and LaTeX.

  python3 -m unittest spec_v1_1/tests/test_da_b4_001_latex.py      (from teams/01-data-a)

The medicine deletes template markup: `{[ name ]}`, `{{ name.attr | filter }}`, `{% ... %}`, `[TheoryMissing]`,
`document.write(...)`. Its sheet note says the `{{ }}` form needs "spaces inside, so LaTeX `{{x}}` is not hit", and
B4_RX does use \\s+ there. The `{[ ]}` form uses \\s* instead, so it also matches bracket groups that LaTeX uses as
arguments: `i^{[j]}` (falling factorial), `\\sum_{i=1}^{[at]}`, `\\frac{[R_f]}{...}` (a concentration), `\\frac{[MNP]}{[ABC]}`
(a ratio of areas). The real clean() on the 38 sample packs changes 21 math-finemath docs, 20 of them this way, and
68 math-megamath docs, 61 of which only lose Wikipedia footnote markers `^{[1]}` (leaving a stray `^`).

FAILING tests (LatexKept): the medicine should leave LaTeX bracket groups unchanged. They fail on clean.py
d275556e and are the finding; they pass once the sheet's `{[ ]}` form needs spaces inside, as its `{{ }}` form does.
PASSING tests (TemplateStillRemoved): the template markup the medicine was written for, from its card's own evidence
docs, is still removed; any fix must keep these green.
All text is made up, in the shape of the matched documents (no document text is copied).
"""
import importlib.util
import unittest
from pathlib import Path

CLEAN = Path(__file__).resolve().parents[1] / "clean.py"
_spec = importlib.util.spec_from_file_location("clean_v1_1_b4", CLEAN)
c = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(c)
b4 = c._math_b4_001()


def doc(text, pack="math-finemath"):
    return {"doc_id": "0" * 16, "text": text, "url": "", "lang_label": "en", "pack_id": pack}


LATEX = {
    "falling factorial": r"so the sum is $\sum_{i} i^{[j]}(n-i)^{[k]}$ for all $j, k$.",
    "upper limit": r"we get $\sum_{i=1}^{[at]} x_i = 1$ when $a > 0$.",
    "concentration": r"The constant is $K_D = \frac{[R_f]}{[R]_0 - [R_f]}$ at equilibrium.",
    "ratio of areas": r"Find the ratio of the areas \(\frac{[MNP]}{[ABC]}\) of the two triangles.",
    "integer part": r"Solve $\sqrt[9]{[x]} = 2$ where $[x]$ is the integer part of $x$.",
    "bracketed subscript": r"Let $a_{[1]} \le a_{[2]}$ be the order statistics.",
}


class LatexKept(unittest.TestCase):
    """The finding: these fail today. The medicine must not touch a LaTeX bracket group."""

    def test_rule_keeps_latex_bracket_groups_on_both_math_packs(self):
        for pack in ("math-finemath", "math-megamath"):
            for name, text in LATEX.items():
                with self.subTest(pack=pack, case=name):
                    self.assertEqual(b4(doc(text, pack)), ("keep", text))

    def test_full_cleaner_keeps_the_ratio_of_areas(self):
        text = LATEX["ratio of areas"]
        self.assertIn(r"\frac{[MNP]}{[ABC]}", c.clean(doc(text))[1])


class TemplateStillRemoved(unittest.TestCase):
    """The medicine's purpose (its card's evidence shapes): these pass today and must still pass after a fix."""

    def test_spaced_template_variables_are_removed(self):
        for junk in ("{[ snackBarMessage ]}", "{[ promptMessage ]}"):
            with self.subTest(junk=junk):
                action, out = b4(doc(f"Chapter 2\n\n{junk}\n\nThe derivative of x^2 is 2x."))
                self.assertEqual(action, "fix")
                self.assertNotIn(junk, out)
                self.assertIn("The derivative of x^2 is 2x.", out)

    def test_other_template_forms_are_removed(self):
        for junk in ("{{ 'ml-label-loading-course' | message }}", "[TheoryMissing]", "{% if user %}"):
            with self.subTest(junk=junk):
                action, out = b4(doc(f"Lesson 3\n\n{junk}\n\nA prime has two divisors."))
                self.assertEqual(action, "fix")
                self.assertNotIn(junk, out)

    def test_latex_double_braces_without_spaces_are_kept_already(self):
        text = r"Here $x^{{2}} = {{a}}$ is fine."
        self.assertEqual(b4(doc(text)), ("keep", text))


if __name__ == "__main__":
    unittest.main()
