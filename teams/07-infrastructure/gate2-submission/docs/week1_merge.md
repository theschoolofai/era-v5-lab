# Week 1 integration provenance

Updated in the existing checkout, without git reset, commit, push or creating a new repository.

- Existing source: the historical standalone `Team7-infrastructure` working tree (local absolute path not included in shared submission).
- Origin: `https://github.com/murthyap63-a11y/Team7-infrastructure`.
- Base HEAD: `7beee4005f0b5fed3df4b993f2ded7f6f37ab6a6`.
- Checkout already contained uncommitted launcher, GPU checks, Docker and documentation fixes from Week 1. All were retained. A full pre-edit backup is retained in this chat's work directory.
- Additional Week 1 source: a separate historical Week 1 bootstrap source archive (not bundled here). Exact source SHA256 inventory: `docs/week1/source_sha256.json`.

| Week 1 input | Integration decision |
|---|---|
| Bootstrap `ckpt.py` | Reused its single-writer guard, fsync/rename publication, COMPLETE marker, manifest/state SHA256, safe serialization, RNG, scheduler/config validation. Extended to checkpoint format v2 with real sampler state, strict reader checks, rejection reports and resume selection. |
| Existing checkout `ckpt.py` | Kept `save_checkpoint` and `load_checkpoint` for existing callers; legacy CPU smoke still passes. Legacy files are not eligible for automatic COMPLETE restart. |
| Bootstrap `checkpoint_demo.py` and tests | Extended the fresh-process proof in `tests/gate2_worker.py`, `gate2_validate.py` and `test_gate2.py`: full steps 101..200, raw loss bytes, actual shuffled ordered IDs, final model/optimizer/scheduler/RNG/sampler, kill/restart/corruption/cancellation. Obsolete duplicate demo API was not installed. |
| Bootstrap checkpoint and queue design v0 | Preserved verbatim under `docs/week1/`; queue v1 and parallel layout identify remaining TSAI approvals and distributed work. |
| Bootstrap launcher/GPU health/collective/XID files | Existing checkout's newer single-task/eight-worker launcher, UUID mapping, ECC handling, cleanup, CPU/Gloo and queue scripts take precedence over earlier bootstrap variants. No rollback to the old topology. |
| Bootstrap `slurm-docker/` | Reused the user's already installed nested `slurm-docker-cluster` deployment for real CPU queue evidence; did not create a second cluster or replace its configuration. |
| Existing `docs/RUNBOOK.md` | Preserved its contents as `docs/week1_runbook.md`, and supplied requested `docs/runbook.md` as the current Gate 2 runbook. This also avoids case-only file collisions on macOS. |

No real model checkout/config/data or remote GPU environment was found. The added CPU fixture is explicitly labeled as infrastructure acceptance code, not a replacement model project. An external TSAI schema was not supplied; `docs/job_package_v1.md` defines the implemented repository contract for TSAI review.

**Note for shared-repo readers:** Historical source SHA-256 values in `docs/week1/source_sha256.json` refer to bootstrap inputs, some of which were intentionally not copied into this combined folder. They must not be used as checksums for this submission. Use `../evidence/SHA256SUMS.json` for that purpose.
