#!/usr/bin/env python3
"""Build G1 gold CSVs from merged diagnosis submissions and open GitHub PRs.

No pack text, evidence, hex dumps, or notes are emitted to output files.
Python 3.9+. Stdlib-only unless --pack-dir is used (then pyarrow required).
"""

from __future__ import annotations

import argparse
import base64
from collections import defaultdict
import csv
from dataclasses import dataclass
import io
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import json

# The csv module defaults to 128 KiB per field, which rejects some PR labels.
# Allow up to 16 MiB; larger/corrupt sheets are skipped with an audit warning.
csv.field_size_limit(16 * 1024 * 1024)

SUBMISSION_PATTERN = re.compile(
    r"^diagnosis/submissions/(?P<pack>[^/]+)/(?P<handle>[^/]+)/labels\.csv$",
    flags=re.IGNORECASE,
)
REQUIRED_COLUMNS = ("doc_id", "read", "verdict", "diseases", "evidence", "hex", "note")
GOLD_COLUMNS = ("doc_id", "reader_1", "reader_2")
COVERAGE_COLUMNS = (
    "pack_id", "label_files", "reviewers", "skipped_label_files", "unique_docs_labeled", "docs_with_full_read",
    "docs_with_2_full_reads", "docs_with_2_clean_votes", "disputed_gold_candidates",
    "gold_docs", "target", "shortfall", "status",
)
DEFAULT_PREFIXES = ("en-", "code-", "math-", "sci-", "cadj-")


@dataclass(frozen=True)
class Submission:
    pack_id: str
    handle: str
    source: str
    csv_text: str
    priority: Tuple[str, int]  # timestamp + PR number, newest wins over local


@dataclass(frozen=True)
class Vote:
    read: str
    verdict: str
    diseases: str
    conflicted_duplicate: bool = False  # same reviewer gave incompatible rows for this doc

    @property
    def fully_read(self) -> bool:
        return self.read == "full" and not self.conflicted_duplicate

    @property
    def disease_codes(self) -> Set[str]:
        # D3 (natural mixed language) is a label only; preserve the source verdict.
        return {code.strip().upper() for code in self.diseases.split(";") if code.strip()}

    @property
    def clean(self) -> bool:
        # D3-only CLEAN counts as a gold vote, but D3-only FIX does not.
        return (not self.conflicted_duplicate and self.read == "full"
                and self.verdict == "clean"
                and not (self.disease_codes - {"D3"}))

    @property
    def negative(self) -> bool:
        # Keep every FIX/DROP as a veto, including D3-only FIX, until reviewed.
        # D3-only CLEAN is label-only and is not dissent; other diseases are.
        return (self.conflicted_duplicate or self.verdict in {"fix", "drop"}
                or bool(self.disease_codes - {"D3"}))


class MalformedLabelsError(ValueError):
    """An individual labels file is not decodable as usable CSV."""


def decode_labels_bytes(raw: bytes, source: str, warnings: List[str]) -> str:
    """Decode a submission CSV without modifying IDs or machine-readable labels.

    Prefer UTF-8 and honor UTF-16 BOMs. Some submitted CSVs use Windows-1252
    or Latin-1 in free-form evidence/note fields, so those are explicit,
    reported fallbacks. Never use errors=replace: corrupted text must not
    silently become invented characters.
    """
    if not raw:
        raise MalformedLabelsError(f"{source}: empty labels CSV")

    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        encoding = "utf-16"
        try:
            decoded = raw.decode(encoding)
        except UnicodeError as exc:
            raise MalformedLabelsError(f"{source}: invalid UTF-16 CSV") from exc
        warnings.append(f"{source}: decoded UTF-16 CSV (prefer UTF-8 for future submissions)")
    else:
        try:
            decoded = raw.decode("utf-8-sig")
        except UnicodeDecodeError as utf8_exc:
            if b"\x00" in raw:
                raise MalformedLabelsError(
                    f"{source}: NUL bytes in non-UTF-8 file; possible UTF-16 without BOM or binary data"
                ) from utf8_exc
            try:
                decoded = raw.decode("cp1252")
                fallback = "Windows-1252"
            except UnicodeDecodeError:
                decoded = raw.decode("latin-1")
                fallback = "ISO-8859-1"
            warnings.append(
                f"{source}: not UTF-8 (first invalid byte at offset {utf8_exc.start}); "
                f"decoded as {fallback}. Ask author to re-export as UTF-8."
            )

    if "\x00" in decoded:
        raise MalformedLabelsError(f"{source}: NUL characters in decoded CSV; refusing binary data")

    # A fallback encoding is acceptable only if the CSV header survives intact.
    try:
        header = next(csv.reader(io.StringIO(decoded, newline="")), [])
    except csv.Error as exc:
        raise MalformedLabelsError(f"{source}: cannot parse CSV header") from exc
    fields = {column.strip().lower() for column in header}
    if not set(REQUIRED_COLUMNS).issubset(fields):
        missing = sorted(set(REQUIRED_COLUMNS) - fields)
        raise MalformedLabelsError(f"{source}: invalid CSV header; missing {missing}")
    return decoded


class GithubAPI:
    """Small read-only GitHub REST client; requires an auth token for PR harvesting."""

    def __init__(self, token: str):
        self.token = token

    def get(self, endpoint: str):
        url = "https://api.github.com/" + endpoint.lstrip("/")
        request = Request(url, headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + self.token,
            "User-Agent": "era-v5-data-a-gold-builder",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        try:
            with urlopen(request, timeout=40) as response:
                return json.load(response)
        except HTTPError as exc:
            message = f"GitHub API HTTP {exc.code} for {endpoint}"
            if exc.code in (403, 429):
                message += " (check API rate limit or token permissions)"
            raise RuntimeError(message) from exc
        except URLError as exc:
            raise RuntimeError(f"GitHub API connection failed for {endpoint}: {exc.reason}") from exc

    def paged(self, endpoint: str) -> Iterable[dict]:
        page = 1
        while True:
            separator = "&" if "?" in endpoint else "?"
            items = self.get(f"{endpoint}{separator}per_page=100&page={page}")
            if not isinstance(items, list):
                raise RuntimeError(f"Expected GitHub API list for {endpoint}")
            yield from items
            if len(items) < 100:
                break
            page += 1


def resolve_token() -> Optional[str]:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        return token.strip()
    try:
        proc = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, check=False, timeout=10
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def github_pr_submissions(
    api: GithubAPI, repo: str, warnings: Optional[List[str]] = None
) -> List[Submission]:
    """Use blob SHAs from PR file listings to read full current CSVs, not diff patches."""
    warnings = warnings if warnings is not None else []
    submissions = []
    blob_cache: Dict[str, Optional[str]] = {}
    for pr in api.paged(f"repos/{repo}/pulls?state=open"):
        if pr.get("base", {}).get("ref") != "main":
            continue
        pr_number = int(pr["number"])
        updated = pr.get("updated_at", "")
        for file_info in api.paged(f"repos/{repo}/pulls/{pr_number}/files"):
            path = file_info.get("filename", "")
            match = SUBMISSION_PATTERN.fullmatch(path)
            if not match or file_info.get("status") == "removed":
                continue
            blob_sha = file_info.get("sha")
            if not blob_sha:
                raise RuntimeError(f"PR #{pr_number}: missing blob SHA for {path}")
            if blob_sha not in blob_cache:
                try:
                    blob = api.get(f"repos/{repo}/git/blobs/{blob_sha}")
                except RuntimeError:
                    # Some unmerged fork objects may not be readable through
                    # the base repo API; retry against the head fork.
                    head_repo = (pr.get("head", {}).get("repo") or {}).get("full_name")
                    if not head_repo or head_repo == repo:
                        raise
                    blob = api.get(f"repos/{head_repo}/git/blobs/{blob_sha}")
                source = f"PR #{pr_number}: {path}"
                try:
                    if blob.get("encoding") != "base64":
                        raise MalformedLabelsError(f"{source}: unsupported GitHub blob encoding")
                    raw = base64.b64decode("".join(blob["content"].split()), validate=True)
                    blob_cache[blob_sha] = decode_labels_bytes(raw, source, warnings)
                except (MalformedLabelsError, ValueError, KeyError) as exc:
                    # One broken CSV should not prevent processing all other PRs.
                    warnings.append(f"Skipping {source}: {exc}")
                    blob_cache[blob_sha] = None
            if blob_cache[blob_sha] is None:
                continue
            submissions.append(Submission(
                pack_id=match.group("pack"), handle=match.group("handle"),
                source=f"PR #{pr_number}: {path}", csv_text=blob_cache[blob_sha],
                priority=(updated, pr_number),
            ))
    return submissions


def local_submissions(repo_root: Path, warnings: Optional[List[str]] = None) -> List[Submission]:
    root = repo_root / "diagnosis" / "submissions"
    if not root.is_dir():
        raise FileNotFoundError(f"Missing directory: {root}")
    warnings = warnings if warnings is not None else []
    result = []
    for path in sorted(root.glob("*/*/labels.csv")):
        match = SUBMISSION_PATTERN.fullmatch(path.relative_to(repo_root).as_posix())
        if match:
            source = f"main/local: {path.relative_to(repo_root).as_posix()}"
            try:
                csv_text = decode_labels_bytes(path.read_bytes(), source, warnings)
            except MalformedLabelsError as exc:
                warnings.append(f"Skipping {source}: {exc}")
                continue
            result.append(Submission(
                pack_id=match.group("pack"), handle=match.group("handle"),
                source=source, csv_text=csv_text,
                priority=("", 0),
            ))
    return result


def choose_current_submissions(submissions: Sequence[Submission], warnings: List[str]) -> List[Submission]:
    """At most one current CSV per pack/reviewer; current open PR supersedes main."""
    grouped = defaultdict(list)
    for s in submissions:
        grouped[(s.pack_id.casefold(), s.handle.casefold())].append(s)
    selected = []
    for key, files in sorted(grouped.items()):
        ordered = sorted(files, key=lambda s: (s.priority, s.source))
        winning = ordered[-1]
        # A reviewer does not become multiple readers because of duplicate PRs.
        if len(ordered) > 1 and len({s.csv_text for s in ordered}) > 1:
            warnings.append(
                f"{winning.pack_id}/{winning.handle}: {len(files)} versions of labels.csv; "
                f"using newest {winning.source} (check overlapping PRs)"
            )
        selected.append(winning)
    return selected


def parse_labels(submission: Submission, warnings: List[str]) -> Dict[str, Vote]:
    """Keep duplicate conflicts as disqualifying evidence; never print private note text."""
    stream = io.StringIO(submission.csv_text, newline="")
    try:
        reader = csv.DictReader(stream)
        fields = [c.strip().lower() if c is not None else "" for c in (reader.fieldnames or [])]
        if not set(REQUIRED_COLUMNS).issubset(fields):
            missing = sorted(set(REQUIRED_COLUMNS) - set(fields))
            raise ValueError(f"{submission.source}: missing required columns: {missing}")
        # Handle minor whitespace/case variants in header names.
        normalized = []
        for row in reader:
            normalized.append({(k.strip().lower() if k else ""): v for k, v in row.items()})
    except csv.Error as exc:
        raise ValueError(f"{submission.source}: malformed CSV ({exc})") from exc
    votes = {}
    conflicted = set()
    for row_num, row in enumerate(normalized, start=2):
        if "" in row:  # extra, unquoted commas: DictReader stores overflow under None
            warnings.append(f"{submission.source}, row {row_num}: extra CSV fields; skipping row")
            continue
        doc_id = (row.get("doc_id") or "").strip()
        read = (row.get("read") or "").strip().lower()
        verdict = (row.get("verdict") or "").strip().lower()
        diseases = (row.get("diseases") or "").strip()
        if not doc_id or read not in {"full", "partial"} or verdict not in {"clean", "fix", "drop"}:
            warnings.append(f"{submission.source}, row {row_num}: invalid ID/read/verdict; skipping row")
            continue
        vote = Vote(read, verdict, diseases)
        if verdict == "clean" and vote.disease_codes - {"D3"}:
            warnings.append(f"{submission.source}, row {row_num}: clean with non-D3 disease codes; not a clean vote")
        if read == "partial" and verdict == "clean":
            warnings.append(f"{submission.source}, row {row_num}: partial+clean; not a clean vote")
        if doc_id in conflicted:
            continue
        if doc_id in votes and votes[doc_id] != vote:
            warnings.append(f"{submission.source}, row {row_num}: conflicting duplicate doc_id; marking document disputed")
            # Do not erase a fix/drop just because this reviewer also wrote clean.
            # The marker excludes this reviewer's clean vote AND prevents the
            # document becoming gold from two other reviewers' clean votes.
            previous = votes[doc_id]
            votes[doc_id] = Vote(previous.read, previous.verdict,
                                 previous.diseases, conflicted_duplicate=True)
            conflicted.add(doc_id)
            continue
        votes[doc_id] = vote
    return votes


def load_pack_ids(pack_list: Optional[Path]) -> Optional[Set[str]]:
    if pack_list is None:
        return None
    if not pack_list.exists():
        raise FileNotFoundError(pack_list)
    if pack_list.suffix.lower() == ".csv":
        with pack_list.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if "pack_id" not in (reader.fieldnames or []):
                raise ValueError("--pack-list CSV must have pack_id column")
            ids = {r["pack_id"].strip() for r in reader if r.get("pack_id", "").strip()}
    else:
        ids = {line.strip() for line in pack_list.read_text(encoding="utf-8").splitlines()
               if line.strip() and not line.lstrip().startswith("#")}
    if not ids:
        raise ValueError("--pack-list is empty")
    return ids


def verify_pack_ids(pack_dir: Path, pack: str) -> Set[str]:
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError("--pack-dir requires: pip install pyarrow") from exc
    path = pack_dir / (pack + ".parquet")
    if not path.is_file():
        raise FileNotFoundError(f"Pack file missing: {path}")
    table = pq.read_table(path, columns=["doc_id"])
    return {str(v) for v in table.column("doc_id").to_pylist() if v is not None}


def build_gold(
    submissions: Sequence[Submission], output_dir: Path,
    expected_packs: Optional[Set[str]] = None, target: int = 200,
    allow_disputed: bool = False, pack_dir: Optional[Path] = None,
    prefixes: Sequence[str] = DEFAULT_PREFIXES,
    all_packs: bool = False,
    warnings: Optional[List[str]] = None,
    remove_stale: bool = False,
) -> List[dict]:
    warnings = warnings if warnings is not None else []
    current = choose_current_submissions(submissions, warnings)
    by_pack: Dict[str, List[Submission]] = defaultdict(list)
    selected = set(expected_packs or [])
    for submission in current:
        if expected_packs is not None:
            if submission.pack_id not in expected_packs:
                continue
        elif not all_packs and not submission.pack_id.lower().startswith(tuple(prefixes)):
            continue
        by_pack[submission.pack_id].append(submission)
        selected.add(submission.pack_id)

    if not selected:
        warnings.append("No matching packs found. Check --pack-list or prefix filtering.")
    output_dir.mkdir(parents=True, exist_ok=True)
    if remove_stale:
        expected_filenames = {f"{pack}_gold.csv" for pack in selected}
        for old_file in output_dir.glob("*_gold.csv"):
            if old_file.name not in expected_filenames:
                old_file.unlink()
    summary = []
    for pack in sorted(selected):
        review_votes: Dict[str, Dict[str, Vote]] = defaultdict(dict)
        file_count = 0
        skipped_files = 0
        for submission in sorted(by_pack[pack], key=lambda x: x.handle.casefold()):
            try:
                parsed_votes = parse_labels(submission, warnings)
            except (ValueError, csv.Error) as exc:
                # One broken submission must not prevent other packs/reviewers
                # from producing gold evidence. Ignore this sheet in full.
                skipped_files += 1
                warnings.append(f"Skipping invalid labels CSV from {submission.source}: {exc}")
                continue
            file_count += 1
            for doc_id, vote in parsed_votes.items():
                review_votes[doc_id][submission.handle] = vote
        known_doc_ids = verify_pack_ids(pack_dir, pack) if pack_dir else None
        gold_rows = []
        full_count = two_full = two_clean = disputed = 0
        for doc_id in sorted(review_votes):
            votes = review_votes[doc_id]
            full = [handle for handle, vote in votes.items() if vote.fully_read]
            clean = sorted([handle for handle, vote in votes.items() if vote.clean], key=str.casefold)
            has_dispute = any(vote.negative for vote in votes.values())
            has_duplicate_conflict = any(vote.conflicted_duplicate for vote in votes.values())
            if full:
                full_count += 1
            if len(full) >= 2:
                two_full += 1
            if len(clean) >= 2:
                two_clean += 1
                if has_dispute:
                    disputed += 1
                # Duplicate conflicting rows are untrustworthy even when the
                # optional --allow-disputed override permits other dissent.
                if has_duplicate_conflict or (has_dispute and not allow_disputed):
                    continue
                if known_doc_ids is not None and doc_id not in known_doc_ids:
                    warnings.append(f"{pack}: gold candidate doc_id {doc_id} not found in source Parquet; skipping")
                    continue
                gold_rows.append((doc_id, clean[0], clean[1]))
        output_path = output_dir / f"{pack}_gold.csv"
        with output_path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(GOLD_COLUMNS)
            writer.writerows(gold_rows)
        gold_total = len(gold_rows)
        summary.append({
            "pack_id": pack, "label_files": file_count,
            "reviewers": file_count, "skipped_label_files": skipped_files,
            "unique_docs_labeled": len(review_votes),
            "docs_with_full_read": full_count, "docs_with_2_full_reads": two_full,
            "docs_with_2_clean_votes": two_clean,
            "disputed_gold_candidates": disputed, "gold_docs": gold_total,
            "target": target, "shortfall": max(0, target - gold_total),
            "status": "TARGET_MET" if gold_total >= target else "BELOW_TARGET",
        })
    with (output_dir / "gold_coverage.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=COVERAGE_COLUMNS)
        writer.writeheader()
        writer.writerows(summary)
    return summary


def make_parser():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[3],
                        help="Local era-v5-lab checkout (default: inferred from script position)")
    parser.add_argument("--repo", default="theschoolofai/era-v5-lab", help="GitHub owner/repo")
    parser.add_argument("--include-open-prs", action="store_true", help="Read unmerged diagnosis PRs (GH_TOKEN/GITHUB_TOKEN or gh auth login required)")
    parser.add_argument("--pack-list", type=Path, help="File with Data A pack IDs: one per line or CSV with pack_id column")
    parser.add_argument("--all-packs", action="store_true", help="Include all submitted packs, including Indic (overrides prefix filter)")
    parser.add_argument("--pack-prefixes", default=",".join(DEFAULT_PREFIXES),
                        help="Auto-include these prefixes when --pack-list is omitted")
    parser.add_argument("--pack-dir", type=Path, help="Optional source Parquet directory; validate candidate doc IDs (requires pyarrow)")
    parser.add_argument("--out", type=Path, help="Gold output directory (default: teams/01-data-a/gold in repo)")
    parser.add_argument("--target", type=int, default=200, help="Reporting goal per pack; not a cap (default: 200)")
    parser.add_argument("--allow-disputed", action="store_true", help="Allow 2 clean votes even when another reviewer says fix/drop")
    parser.add_argument("--fail-under-target", action="store_true", help="Return code 2 if any pack falls below --target")
    parser.add_argument("--fail-on-warnings", action="store_true", help="Return code 3 on decoding fallbacks, skipped files, or other anomalies")
    parser.add_argument("--remove-stale", action="store_true", help="Delete old *_gold.csv files not in this run's pack selection")
    return parser


def main(argv=None) -> int:
    args = make_parser().parse_args(argv)
    if args.target < 1:
        print("ERROR: --target must be positive", file=sys.stderr)
        return 1
    warnings: List[str] = []
    try:
        root = args.repo_root.resolve()
        subs = local_submissions(root, warnings)
        if args.include_open_prs:
            token = resolve_token()
            if not token:
                raise RuntimeError("To include open PRs, set GH_TOKEN / GITHUB_TOKEN or run 'gh auth login'.")
            remote = github_pr_submissions(GithubAPI(token), args.repo, warnings)
            print(f"Read {len(remote)} labels.csv files from open PRs; {len(subs)} from local checkout")
            subs.extend(remote)
        expected = load_pack_ids(args.pack_list)
        out = args.out or (root / "teams" / "01-data-a" / "gold")
        prefix_list = tuple(p.strip().lower() for p in args.pack_prefixes.split(",") if p.strip())
        summary = build_gold(
            subs, out, expected_packs=expected, target=args.target,
            allow_disputed=args.allow_disputed, pack_dir=args.pack_dir,
            prefixes=prefix_list, all_packs=args.all_packs, warnings=warnings,
            remove_stale=args.remove_stale,
        )
    except (FileNotFoundError, ValueError, RuntimeError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"\nWrote {len(summary)} pack gold file(s) and coverage to {out}")
    print(f"{'pack_id':28} {'files':>5} {'skipped':>7} {'2-clean':>8} {'gold':>6} {'shortfall':>9}")
    print("-" * 70)
    for row in summary:
        print(f"{row['pack_id'][:28]:28} {row['label_files']:5} {row['skipped_label_files']:7} "
              f"{row['docs_with_2_clean_votes']:8} {row['gold_docs']:6} {row['shortfall']:9}")
    if warnings:
        print(f"\n{len(warnings)} warning(s), including:", file=sys.stderr)
        for warning in warnings[:60]:
            print(f"  - {warning}", file=sys.stderr)
        if len(warnings) > 60:
            print(f"  ... {len(warnings) - 60} more warnings", file=sys.stderr)
    if args.fail_on_warnings and warnings:
        return 3
    if args.fail_under_target and any(row["shortfall"] > 0 for row in summary):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
