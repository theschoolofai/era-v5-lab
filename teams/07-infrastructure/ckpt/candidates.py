"""Which committed checkpoints a restart may try, newest first (ADR 0001 §3).

In simple words: this is the one rule for "is there anything to resume from?". `Checkpointer.candidates()` uses it
to restore, and `queue/job_queue.py start-mode` uses it to choose fresh or resume before the trainer starts, so the
launcher and the restore can never disagree. It has no torch import, so the job wrapper stays light.

The function only decides. Reading `latest.json` and `commits.jsonl` is the caller's job, because the callers need
different failure behavior: a restore may treat a missing file as empty, and start-mode must fail closed.
"""


def pick_candidates(commits: list, latest, from_step: int = None) -> list:
    """Commits to try, newest first.

    commits    the parsed lines of commits.jsonl, oldest first
    latest     the parsed latest.json, or None when the file does not exist
    from_step  a rollback: only the newest commit at that step, whatever latest.json says
    """
    if from_step is not None:
        return [c for c in reversed(commits) if c["step"] == from_step][:1]
    if latest is None:
        return []
    rest = [c for c in reversed(commits) if c["path"] != latest.get("path")]
    # a claim with no commit yet has path None: only the commit history is left to try
    return ([latest] if latest.get("path") else []) + rest
