# Model card text: Data cleaning, Data B part

Date: 28 Nov 2026

Section "Data cleaning" of `teams/11-release/model_card/model_card_outline.md`: how we cleaned the data and removed
duplicates. Owner teams: Data A, Data B. This file is the Data B part: the Indian-language and code-adjacent text. It
fills the `[text: waiting for Data B]` placeholder at the end of the section. Release edits it into the model card and
TSAI approves it.

## Text

Data B wrote cleaning rules for the Indian-language text, and the shared pipeline of Data A runs them. Each rule fixes
one problem that native readers found. Examples are hidden characters, letters from another script inside a word, and
a word cut before its vowel sign. A rule acts only on the sources where readers found its problem.

Before a rule joined the pipeline, Data B ran it on the gold set of its language. A rule that changed or dropped more
than 1% of the gold documents failed.

The Malayalam and Odia text and part of the Tamil text have no gold set. So no Data B rule was tested on them.
[text: waiting for TSAI, how these sources are cleaned before training]

Indian scripts break easily, so Data B compared the cleaned training files with the raw text. Cleaning lost no joiner
character (ZWJ or ZWNJ) from the text that it kept. It also kept every visarga in that text. An earlier cleaning step
had turned this sign into a colon.

Native readers then read samples of the cleaned files in their own languages. Almost all the damage that they found
was already in the raw text. Cleaning caused two problems. One rule removed verse numbers from Sanskrit texts, and it
is now fixed in the cleaning code. Another rule removed a list from the middle of one Bengali page, and it is not
fixed.

Data B also checked the language labels of the Hindi, Marathi, Sanskrit and Bengali sources. A document was flagged
only when a language identification model and a list of marker words both named another language. The flagged
documents were Sanskrit in Bengali script, and Jain Prakrit in a Hindi source. The check cannot find a language that
the model has no class for.

In the code-adjacent text, cleaning replaces the e-mail addresses in commit messages with a placeholder.
[text: waiting for TSAI, whether the notebooks and the posts are cleaned before training]

## Where each statement comes from (for the review, not for the model card)

| Statement | Source |
|---|---|
| Data B's rules, run by Data A's pipeline, each on named sources | `teams/01-data-a/spec_v1_1/clean.py` on main: the `DB-*` rules, each with its list of packs |
| The kinds of problem | `diagnosis/DISEASES.md`: A1 (invisible characters), A6 (wrong or mixed script), G1 (cut at the vowel sign) |
| Harm test, 1% of the gold set | `diagnosis/DISEASES.md` section 4, step 4; gold sets: section 5 and `teams/02-data-b/gold/` |
| No gold set: Malayalam, Odia, part of Tamil | `audit/gate3_indic.md` section 2 (`ind-ml-fw2`, `ind-or-fw2`, `ind-ta-fw2`, `ind-ta-sangraha-s`: no cleaner rules). These four packs are in `teams/01-data-a/jobs/2026-11-19-first-training/staged_packs_33.json` |
| No joiner lost, no visarga edited in kept text | `audit/gate3_indic.md` section 1 (#523, #576, #653) |
| Damage mostly in the raw text, two problems from cleaning | `audit/gate3_indic.md` section 3 and its source check |
| Sanskrit verse numbers, fixed | issue #734, fixed on main by #767; the corpus-v1 job pins that `clean.py` |
| Bengali list, not fixed | `DB-C5-007`, `audit/gate3_indic.md` section 3 (#766) |
| Language labels | `audit/lang_label_check.md` (#622, #673, #842); flags in `audit/lang_label_mislabelled_ids.csv` |
| E-mail addresses in commit messages | `clean.py` (#767): the shared F1 masks e-mail addresses only, on `cadj-commits` |
| Notebooks and posts | `clean.py` (#767): deferred, no gold set; the same open point as in `training_data.md` |

Numbers in the text: 1% is TSAI's own rule in `diagnosis/DISEASES.md`, and "two problems" counts the two findings
from cleaning in `audit/gate3_indic.md` section 3. The two open points are marked `[text: waiting for TSAI]`.
`check_style.py`: 0 errors.
