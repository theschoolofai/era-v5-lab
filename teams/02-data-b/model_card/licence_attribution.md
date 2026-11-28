# Model card text: Licence and attribution, Data B part

Date: 28 Nov 2026

Section "Licence and attribution" of `teams/11-release/model_card/model_card_outline.md`: the licence of the model,
and credit for each data source. Owner teams: Post-training, Data A, Data B. This file is the Data B part: credit for
the Indian-language and code-adjacent sources. It fills part of the `[text: waiting for Data A and Data B]`
placeholder. Release edits it into the model card and TSAI approves it.

## Text

The Indian-language and code-adjacent text comes from these public datasets, under these licences:

- FineWeb-2 (`HuggingFaceFW/fineweb-2`), ODC-By 1.0: web text in Indian languages.
- Sangraha (`ai4bharat/sangraha`) of AI4Bharat, CC BY 4.0: Indian-language text.
- IndicCorp V2 (`ai4bharat/IndicCorpV2`) of AI4Bharat, CC BY 4.0: Hindi text.
- HPLT 3.0, Hindi: CC0 1.0 for the packaging. The web text in it keeps the terms of its own websites.
- CommitPackFT (`bigcode/commitpackft`), MIT: commit messages. Each commit keeps the licence of its repository.
- Kaggle notebooks (`HuggingFaceTB/issues-kaggle-notebooks`), Apache 2.0.
- Stack Exchange posts from the StarCoder2 extra data (`bigcode/starcoder2data-extras`), CC BY-SA 4.0.

The lab's licence table lists each source with its link.

## Where each statement comes from (for the review, not for the model card)

| Statement | Source |
|---|---|
| Each dataset, its licence and its link | `teams/10-post-training/licences/licence_table.md` on main, Stage 0 rows `ind-*` and `cadj-*` |
| Which datasets are Data B's | `teams/02-data-b/model_card/training_data.md` (#525, #782), the same list of sources |
| IndicCorp V2 is Hindi only | the licence table has one IndicCorp row, `ind-hi-indiccorp` |
| HPLT 3.0 is Hindi only | the licence table has one HPLT row, `ind-hi-hplt` (`hin_Deva`) |

No number is in the text. Which datasets the release uses stays TSAI's decision (the licence table's last column).
