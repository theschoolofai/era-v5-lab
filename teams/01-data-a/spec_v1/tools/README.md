# Sample-job runner

The cleaner's build and validation scripts moved: [build/](../build/README.md) generates `clean.py` from the sheets, and [validate/](../validate/README.md) checks the sheets and the cleaner. This folder holds only the streaming sample-job runner, which stays here until the tokenizer-sample job PR is merged: the committed job request pins its path.

| Purpose | Script | Inputs / outputs |
|---|---|---|
| Run the tokenizer sample cleaning job | [run_tokenizer_sample.py](run_tokenizer_sample.py) | [Pinned sample config/manifest](../jobs/README.md); outputs under fresh `out/<job>/` |

Install [../requirements.txt](../requirements.txt) before running it; [the cleaner guide](../README_clean.md) covers the single-pack runner. Report files and their snapshot status are indexed in [../results/README.md](../results/README.md).
