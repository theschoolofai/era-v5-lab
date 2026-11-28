# ERA V5 Lab: decision log

**Date:** 28 Nov 2026
**Owner of this log:** Release

This log records how the lab reached its model. It lists each decision with its date, its evidence and its owner team. It lists each experiment with its command and result, and each job with its inputs and hashes. A reader should be able to rebuild the path to the model from this log and the files that it cites.

## How to use this log

- Add a row by pull request. Each row cites a merged pull request or a file on main.
- Write negative results too. A rejected idea with its numbers is a result.
- Write `[waiting for <team>]` for a command, a hash or a number that the owner team has not sent yet.
- Numbers come from the cited file. A number in public text still needs TSAI approval (`public_internal.md`).
- Release keeps the log. Each owner team checks its own rows.

## Decisions

| Date | Decision | Proposed by | Evidence | Owner team |
|---|---|---|---|---|
| 14 Nov 2026 | Freeze the tokenizer candidate C3, with eos at id 130822. TSAI approves each later fix. | Tokenizer | [#407](https://github.com/theschoolofai/era-v5-lab/pull/407); `updates/gate2.md` ([#443](https://github.com/theschoolofai/era-v5-lab/pull/443)) | Tokenizer |
| 14 Nov 2026 | Accept the KE2 validation of C3, and align the KE2 special-token map to the eos id. | KE2 | [#372](https://github.com/theschoolofai/era-v5-lab/pull/372); `updates/gate2.md` | KE2 |
| 14 Nov 2026 | First model configuration: the Muon optimizer, the v0 attention, and 16 routed experts plus 1 shared expert, top-2. | Architecture | [#447](https://github.com/theschoolofai/era-v5-lab/pull/447); `updates/gate2.md` | Architecture |
| 14 Nov 2026 | One data spec, v1.1. The cleaner ran on sample v0, and the dedup design runs on the cleaned sample. | Data A | [#244](https://github.com/theschoolofai/era-v5-lab/pull/244), [#255](https://github.com/theschoolofai/era-v5-lab/pull/255); `updates/gate2.md` | Data A |
| 14 Nov 2026 | Supervised fine-tuning mix v1. The tuning method waits for tests against full fine-tuning. | Post-training | [#391](https://github.com/theschoolofai/era-v5-lab/pull/391); `updates/gate2.md` | Post-training |
| 14 Nov 2026 | No bit width yet, for lack of evidence. The decision moves to Gate 3. | Quantization | `updates/gate2.md` | Quantization |
| 21 Nov 2026 | The first dry run: go. The run finished, and a restore from the checkpoint matched bit for bit. | Architecture, Infrastructure | [#475](https://github.com/theschoolofai/era-v5-lab/pull/475), [#620](https://github.com/theschoolofai/era-v5-lab/pull/620), [#573](https://github.com/theschoolofai/era-v5-lab/pull/573), [#633](https://github.com/theschoolofai/era-v5-lab/pull/633); `updates/gate3.md` ([#701](https://github.com/theschoolofai/era-v5-lab/pull/701)) | Infrastructure |
| 21 Nov 2026 | The tokenizer for training is the frozen p1536, not C3. | Tokenizer | [#504](https://github.com/theschoolofai/era-v5-lab/pull/504); `updates/gate3.md` | Tokenizer |
| 21 Nov 2026 | Indic text in its own script is 8% of every batch. Romanised Indic text is at most 1% of tokens per language. | Data A, Data B | [#400](https://github.com/theschoolofai/era-v5-lab/pull/400), [#522](https://github.com/theschoolofai/era-v5-lab/pull/522); `updates/gate3.md` | Data B |
| 21 Nov 2026 | The learning rate of 1e-3 is final. | Architecture | [#447](https://github.com/theschoolofai/era-v5-lab/pull/447); `updates/gate3.md` | Architecture |
| 21 Nov 2026 | Keep the v0 attention and the expert layout. A test with more experts did worse. | Architecture | [#659](https://github.com/theschoolofai/era-v5-lab/pull/659), [#668](https://github.com/theschoolofai/era-v5-lab/pull/668); `updates/gate3.md` | Architecture |
| 21 Nov 2026 | The model uses the KE2 output head, in place of the dense untied head. | KE2, Architecture | `teams/04-ke2/gate3.md` ([#694](https://github.com/theschoolofai/era-v5-lab/pull/694), corrected in [#702](https://github.com/theschoolofai/era-v5-lab/pull/702)) | KE2 |
| 21 Nov 2026 | TSAI accepted the public dashboard panels and their text. | Monitoring, Release | [#495](https://github.com/theschoolofai/era-v5-lab/pull/495), [#598](https://github.com/theschoolofai/era-v5-lab/pull/598), [#629](https://github.com/theschoolofai/era-v5-lab/pull/629); `updates/gate3.md` | Monitoring |
| 22 Nov 2026 | The learning rate for the Muon optimizer is 0.006, the current estimate. | Architecture | [#725](https://github.com/theschoolofai/era-v5-lab/pull/725); `teams/05-architecture/configs/config_v1.yaml` | Architecture |
| 23 Nov 2026 | The router uses the Muon optimizer by default. | Architecture | [#736](https://github.com/theschoolofai/era-v5-lab/pull/736), from the comparison in [#712](https://github.com/theschoolofai/era-v5-lab/pull/712); `config_v1.yaml` | Architecture |
| 23 Nov 2026 | Loss-free load balancing is in the training plan, with gamma 0.001. | Architecture | [#748](https://github.com/theschoolofai/era-v5-lab/pull/748); `config_v1.yaml` | Architecture |
| 24 Nov 2026 | The KE2 output head is in the training code. | Architecture | [#717](https://github.com/theschoolofai/era-v5-lab/pull/717) | Architecture |
| 24 Nov 2026 | TSAI approved the draft of the launch announcement. | Release | [#753](https://github.com/theschoolofai/era-v5-lab/pull/753) | Release |
| 24 Nov 2026 | The second dry run trains on the first 41 shards, not on corpus v1. The finished run trained on one English web shard instead. | TSAI | [#787](https://github.com/theschoolofai/era-v5-lab/pull/787), [#641](https://github.com/theschoolofai/era-v5-lab/pull/641) | Architecture |
| 27 Nov 2026 | The model card may cite outside papers for the benchmarks and methods that it uses. | Release | [#852](https://github.com/theschoolofai/era-v5-lab/pull/852) | Release |
| 27 Nov 2026 | Cross-language duplicate removal is on for Hindi and English only. The other pairs stay report-only. | Data A | [#860](https://github.com/theschoolofai/era-v5-lab/pull/860) (open) | Data A |
| 27 Nov 2026 | TSAI accepted the second dry run as the Gate 4 evidence. | Architecture, Infrastructure | `updates/gate4.md` ([#705](https://github.com/theschoolofai/era-v5-lab/pull/705)); run record [#869](https://github.com/theschoolofai/era-v5-lab/pull/869) | Infrastructure |
| Open | Still open: the go or no-go on the main run, and the exact model size. Also open: the tuning method after training, the bit width ([#853](https://github.com/theschoolofai/era-v5-lab/pull/853)) and the starting context length ([#825](https://github.com/theschoolofai/era-v5-lab/pull/825)). | Architecture, Post-training, Quantization | `updates/gate4.md` ([#705](https://github.com/theschoolofai/era-v5-lab/pull/705)) | TSAI |

## Experiments

| Date | Experiment | Command or job | Result | Evidence |
|---|---|---|---|---|
| 18 Nov 2026 | First dry run, with the dense untied head | [waiting for Infrastructure] | The run finished, and the restore matched bit for bit. | [#475](https://github.com/theschoolofai/era-v5-lab/pull/475), [#620](https://github.com/theschoolofai/era-v5-lab/pull/620), [#573](https://github.com/theschoolofai/era-v5-lab/pull/573), [#633](https://github.com/theschoolofai/era-v5-lab/pull/633) |
| 19 Nov 2026 | More routed experts than 16 | [waiting for Architecture] | Worse than 16 routed experts. Negative result. | [#659](https://github.com/theschoolofai/era-v5-lab/pull/659), [#668](https://github.com/theschoolofai/era-v5-lab/pull/668) |
| 22 Nov 2026 | Learning rate of Muon against AdamW, one seed | [waiting for Architecture] | Muon at 0.006 had the lower held-out bits per byte. One seed only. | [#725](https://github.com/theschoolofai/era-v5-lab/pull/725); `config_v1.yaml` |
| 22 Nov 2026 | Router on Muon against router on AdamW, one seed per arm | job in [#712](https://github.com/theschoolofai/era-v5-lab/pull/712) | No measurable quality difference: the gap was far below the spread between seeds. | [#712](https://github.com/theschoolofai/era-v5-lab/pull/712); `config_v1.yaml` |
| 27 Nov 2026 | Second dry run (dryrun2-1234), with the KE2 output head | `teams/05-architecture/jobs/2026-11-22-dryrun2.md`; `configs/arms/dryrun2.yaml` | All planned steps finished, and the loss stayed valid. It trained on one English web shard, not the planned 41 shards. One seed. The run record confirms the KE2 output head. | [#787](https://github.com/theschoolofai/era-v5-lab/pull/787), [#869](https://github.com/theschoolofai/era-v5-lab/pull/869); result comment on [#705](https://github.com/theschoolofai/era-v5-lab/pull/705) |
| 25 Nov 2026 | Faster attention as a separate arm beside the second dry run | job in [#805](https://github.com/theschoolofai/era-v5-lab/pull/805) | Queued. No result yet. | [#804](https://github.com/theschoolofai/era-v5-lab/pull/804), [#805](https://github.com/theschoolofai/era-v5-lab/pull/805) |
| 27 Nov 2026 | Smaller file formats on public models, with wide benchmarks | [waiting for Quantization] | The format closest to full size kept the scores. The smallest lost points, most on Indian-language reading tasks. | [#714](https://github.com/theschoolofai/era-v5-lab/pull/714), [#737](https://github.com/theschoolofai/era-v5-lab/pull/737), [#786](https://github.com/theschoolofai/era-v5-lab/pull/786), [#808](https://github.com/theschoolofai/era-v5-lab/pull/808), [#853](https://github.com/theschoolofai/era-v5-lab/pull/853) |

## Jobs

| Job | Inputs | Hashes | Evidence |
|---|---|---|---|
| dryrun2-1234 | `configs/arms/dryrun2.yaml`; one English web shard; tokenizer p1536 | Final model sha256 in TSAI's result comment on [#705](https://github.com/theschoolofai/era-v5-lab/pull/705); file hashes in `manifest.json` | [#869](https://github.com/theschoolofai/era-v5-lab/pull/869) |
| First dry run | [waiting for Infrastructure] | [waiting for Infrastructure] | [#620](https://github.com/theschoolofai/era-v5-lab/pull/620) |
| First 41 shards (sample v0) | sample v0; tokenizer p1536 | [waiting for Data A] | [#641](https://github.com/theschoolofai/era-v5-lab/pull/641) |
| Tokenizer p1536 | [waiting for Tokenizer] | [waiting for Tokenizer] | [#504](https://github.com/theschoolofai/era-v5-lab/pull/504) |
