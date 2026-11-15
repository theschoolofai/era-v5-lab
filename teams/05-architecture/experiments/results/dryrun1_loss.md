# Dry run 1: the loss record

**Owner:** Deepjyoti Saha (G5, week-3 task 4). **Status:** DRAFT, layout only; filled in from the dry run 1 logs
when TSAI returns them. **Gate 3 evidence:** "dry run 1 ends with a stable loss curve" (Fri 20 Nov, 23:59 IST).

How the numbers are made, the two spike rules and how to rerun everything: [`dryrun1_README.md`](dryrun1_README.md).

## 1. What ran

| Item | Value | Source |
|---|---|---|
| Config | `teams/05-architecture/configs/config_v1.yaml` (signed at Gate 2, #447) | main commit `aec75afc93070f56d891f438ccdd9a791b2c18bd` (G5 group, 14 Nov) |
| Optimizer | Muon for the block matrices, AdamW for the rest; `optim.lr` 0.001 | config v1 |
| `muon_lr` | **0.01**, the EXP-2 Muon arm's rate (`configs/arms/exp2_muon.yaml`) | TSAI in the G5 group, 15 Nov: "dry run 1 uses muon_lr 0.01" |
| Job request | _to fill: PR number and file_ | Shivanshu, Mon 16 Nov |
| Shards | _to fill: which Team 1 shards, with their manifest hashes_ | job request |
| Model size, steps, batch, sequence length | _to fill_ | job request / run manifest |
| Hardware, run by, start and end | _to fill_ | job log |
| Logs used | _to fill: file names and sha256_ | returned logs |

## 2. The loss curve

_To fill: the table printed by `dryrun1_spikes.py` (about 20 rows, every spike step marked), and a chart._

## 3. Every spike

_To fill: the spike table printed by `dryrun1_spikes.py`, both rules side by side, plus "what happened next" for
each row from the job log (continued; paged; held and rolled back to step K on a new branch)._

## 4. Stops and restarts

| Time | Step | Exit code | Cause | What happened | Source |
|---|---:|---:|---|---|---|
| _to fill_ | | | | | job log; Dharshan's shift log for Team 7 |

Exit 75: saved and requeued by itself. Exit 78: no save, the job is held until a person rolls back.

## 5. Is the curve stable?

_To fill: four to six sentences. Does the loss fall; how many spikes by each rule; did each recover, and how
fast; any hold or rollback and why; anything unexplained. This reports what the logs show; the Gate 3 judgement
is TSAI's._

## 6. Sources

- _to fill: the job request, the returned logs, Team 8's alarm output for dry run 1, Dharshan's shift log._
