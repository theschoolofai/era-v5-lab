# Diagnosis tracker

`build_tracker.py` makes one row per student: their diagnosis pull request, how many rows are labelled,
the medicine sheet state, and problems to fix.

```
python -I build_tracker.py --roster ~/private/roster.csv --out ~/private/tracker
python -I build_tracker.py --roster ~/private/roster.csv --out ~/private/tracker --as-of 2026-10-27T23:59+05:30
```

- **Roster:** a private CSV with columns `student,team,pack`, copied from the pack table on the CAP plan
  sheet. Keep it out of git. Do not put emails in it.
- **Output:** `tracker.csv` and `tracker.md` in `--out`. They hold student names, so keep them out of git too.
- **Matching:** the `Name:` line of the pull request, then the `Pack:` line or folder when only one student
  has that pack. Unmatched pull requests are listed at the end of `tracker.md`.
- **`--as-of`:** reads each pull request at its last commit before that time, as the graders do at each due date.
- Needs the `gh` CLI, logged in. Commit files are cached in `<out>/cache`.

| Column | Meaning |
|---|---|
| status | `on track` (at least `--target` labelled rows, default 150), `behind`, `closed`, or `no PR` |
| labelled / rows | rows with verdict clean, fix or drop / all rows in `labels.csv` |
| medicine | `missing`, `template` (unchanged copy), or its size |
| issues | folder pack differs from the roster, header lines missing, folder is not the PR author, evidence or note may hold an email or phone number, more than one open PR |
| other_prs | the student's other pull requests |

The email/phone check reports a count only. It never prints the value.

## Results: run of 27 Oct 2026, 11:42 UTC

Roster: the CAP plan pack table of 26 Oct (92 students with a pack, 45 on the waitlist). 86 pull requests read.

| Status | Students with a pack | Waitlist |
|---|---|---|
| on track (150+ labelled rows) | 45 | 1 |
| behind | 5 | 0 |
| no PR | 42 | 44 |

- **Labelled rows:** 13,391 across 51 students: clean 5,928 (44%), fix 6,374 (48%), drop 1,089 (8%).
- **Full pack:** 16 students have 500 or more labelled rows.
- **Medicine sheet:** written 28, missing 16, unchanged template 7.
- **Issues:** 5 pull requests may have an email or phone number in `evidence` or `note`.
  DISEASES.md allows only the type and offset there. No other issue was found.
- **Not matched:** 3 pull requests. Two are the sample pull requests. One gives a name that is not in the roster.

By team (students with a pack):

| Team | On track | Behind | No PR |
|---|---|---|---|
| 1. Data A | 8 | 1 | 3 |
| 2. Data B | 2 | 1 | 3 |
| 2. Data B (diagnosis only) | 0 | 0 | 5 |
| 3. Tokenizer | 0 | 1 | 4 |
| 4. KE2 | 3 | 0 | 3 |
| 5. Architecture | 5 | 1 | 5 |
| 6. Performance and Kernels | 7 | 0 | 2 |
| 7. Infrastructure | 1 | 1 | 4 |
| 8. Monitoring and Records | 4 | 0 | 1 |
| 9. Evaluation | 3 | 0 | 5 |
| 10. Post-training and Agentic | 7 | 0 | 5 |
| 11. Release | 1 | 0 | 1 |
| 12. Quantization and Serving | 4 | 0 | 1 |

Counts only. Names stay in the private output.
