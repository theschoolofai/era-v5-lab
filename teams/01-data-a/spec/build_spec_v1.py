"""Build the G1 Data A parent medicine from EVERY submitted medicine.md.

Inputs: teams/01-data-a/medicines/submissions/<pack>/<handle>/medicine.md
Output: teams/01-data-a/spec/spec_v1.md (review-only DRAFT)

This intentionally does NOT execute contributor examples or declare rules approved.
Conflicting proposals are preserved separately and blocked pending adjudication,
positive fixtures, and harm tests on the refreshed gold sets.

Run from the repo root:
    python teams/01-data-a/spec/build_spec_v1.py
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEAM = ROOT / 'teams' / '01-data-a'
SUBMISSIONS = TEAM / 'medicines' / 'submissions'
DEST = TEAM / 'spec' / 'spec_v1.md'
INVENTORY = TEAM / 'spec' / 'spec_v1_sources.csv'
CONFLICTS = TEAM / 'spec' / 'spec_v1_conflicts.csv'

MEDICINE_HEADER = re.compile(r'(?m)^##\s+Medicine\s+\d+\b[^\n]*')
ROW_HEADER = re.compile(r'(?m)^##\s+Rows?\s+[^\n]*')
FIELD = re.compile(
    r'(?m)^[ \t]*(?:#{3,4}[ \t]+)?([1-5])\.[ \t]+'
    r'(?:\*\*[^*\n]{2,90}\*\*\s*:?[ \t]*|'
    r'(?:Disease|Medicine|Action|Harm[ -]test|Side effects)\b[^\n:]{0,60}:?[ \t]*)'
)
DISEASE = re.compile(r'\b[A-H][1-9]\b')
RULE_ID = re.compile(r'\bDA-[A-H][1-9]-\d{3}\b')
EMAIL = re.compile(r'(?<![\w@])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w@])')
TOKEN = re.compile(r'\b(?:ghp_|github_pat_|sk-|AKIA)[A-Za-z0-9_\-]{12,}\b')
PHONE = re.compile(r'(?<!\d)(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}(?!\d)')

# Verified source paths in g1-harm-test when the builder was updated.
# Additional medicine.md files are automatically discovered. Missing baseline
# files require an explicit checkout refresh/review, never partial silent build.
BASELINE_FILES = (
    'cadj-commits/kunal2016/medicine.md',
    'cadj-commits/pradeep-kumar-gs/medicine.md',
    'cadj-commits/sureshmantha/medicine.md',
    'cadj-stackexchange/smitasasindran/medicine.md',
    'code-cpp/TharunSivamani/medicine.md',
    'code-go/RaviNaik/medicine.md',
    'code-go/TEJASKUMAR-REDDY-J/medicine.md',
    'code-java/curioustushar/medicine.md',
    'code-java/vaibh27/medicine.md',
    'code-js-ts/AjaySnl/medicine.md',
    'code-js-ts/varshith2000/medicine.md',
    'code-python/saitej123/medicine.md',
    'code-rust/amukka/medicine.md',
    'en-dclm/mittalutkarsh/medicine.md',
    'en-dclm/shekar-maker/medicine.md',
    'en-fineweb-edu/deepjyotisaha/medicine.md',
    'en-nemotroncc-synth/AJJAPUSIVA/medicine.md',
    'en-nemotroncc-synth/maheshsv/medicine.md',
    'en-nemotroncc/HariniJasti/medicine.md',
    'math-finemath/SomaKorada07/medicine.md',
    'sci-finepdfs/jssunil/medicine.md',
)


@dataclass(frozen=True)
class Proposal:
    pack: str
    handle: str
    path: Path
    index: int
    disease: str
    rule_id: str
    heading: str
    fields: dict[int, str]
    raw: str
    structured: bool


def relative(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        # Also support synthetic fixtures outside the checked-out repository.
        return path.as_posix()


def digest(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def redact(text: str) -> str:
    """Defence-in-depth for public specs; reviewer must still check E3/F1."""
    text = TOKEN.sub('[REDACTED_SECRET]', text)
    text = EMAIL.sub('[REDACTED_EMAIL]', text)
    text = PHONE.sub('[REDACTED_PHONE]', text)
    # Keep source code viewable but NEVER automatically executable by harm_test.py:
    # unreviewed, unrelated contributor examples aren't one unified rule file.
    return re.sub(r'(?m)^([ \t]*```)(?:python|py)\b', r'\1text', text)


def clean_cell(value: str) -> str:
    return re.sub(r'\s+', ' ', value).strip()


def safe_cell(value: str) -> str:
    return clean_cell(value).replace('|', '\\|').replace('`', "'")


def is_template(raw: str) -> bool:
    return '# Medicine sheet: <pack_id>' in raw and '1. **Disease:** code, count in your pack' in raw


def sections(raw: str) -> list[tuple[str, str]]:
    """Get contributor Medicine sections, including files missing the first ## heading.

    Special row-level intervention headings are retained if a sheet has no
    ordinary numbered medicine sections. Do not mistake unrelated ## headings
    for a medicine.
    """
    found = list(MEDICINE_HEADER.finditer(raw))
    if not found:
        found = list(ROW_HEADER.finditer(raw))
    if not found:
        return []
    results: list[tuple[str, str]] = []
    prefix = raw[:found[0].start()]
    if not MEDICINE_HEADER.search(prefix):
        first_field = re.search(r'(?m)^1\.[ \t]+\*\*(?:The[ \t]+)?[Dd]isease', prefix)
        if first_field:
            results.append(('Medicine 1 (unnumbered heading)', prefix[first_field.start():].strip()))
    for i, heading in enumerate(found):
        until = found[i + 1].start() if i + 1 < len(found) else len(raw)
        text = raw[heading.end():until].strip()
        # Stop at non-medicine-level headings so appendices/notes are not
        # accidentally attributed to the last rule.
        end = re.search(r'(?m)^##[ \t]+(?!Medicine\s+\d+\b|Rows?\b)[^\n]+$', text)
        if end:
            text = text[:end.start()].strip()
        results.append((heading.group(0).strip(), text))
    return results


def read_fields(body: str) -> dict[int, str]:
    marks = list(FIELD.finditer(body))
    result = {}
    for i, mark in enumerate(marks):
        index = int(mark.group(1))
        if index in result:
            continue  # retain original section as source; do not overwrite a field
        stop = marks[i + 1].start() if i + 1 < len(marks) else len(body)
        result[index] = body[mark.end():stop].strip()
    return result


def disease_of(heading: str, fields: dict[int, str]) -> str:
    # Prefer the diagnosis field. The heading may include another code in a
    # related-rule title; never guess a disease when neither has one.
    source = fields.get(1, '')[:300]
    match = DISEASE.search(source) or DISEASE.search(heading)
    return match.group(0) if match else 'UNCLASSIFIED'


def extract_file(path: Path) -> tuple[list[Proposal], str, str]:
    raw = path.read_text(encoding='utf-8')
    if not raw.strip():
        return [], 'EMPTY', digest(raw)
    if is_template(raw):
        return [], 'TEMPLATE', digest(raw)
    pack, handle = path.relative_to(SUBMISSIONS).parts[:2]
    proposals = []
    for i, (heading, body) in enumerate(sections(raw), 1):
        fields = read_fields(body)
        disease = disease_of(heading, fields)
        ids = RULE_ID.findall(heading + '\n' + fields.get(2, ''))
        proposals.append(Proposal(pack, handle, path, i, disease,
                                  ids[0] if ids else '', heading, fields,
                                  body, set(fields) == {1, 2, 3, 4, 5}))
    return proposals, ('MEDICINES' if proposals else 'UNSTRUCTURED'), digest(raw)


def canonical(value: str) -> str:
    # Only normalize line endings and trailing whitespace. Python code is
    # case-/indentation-sensitive, so do NOT casefold/collapse inner spaces.
    return '\n'.join(line.rstrip() for line in value.replace('\r\n', '\n').split('\n')).strip()


def collide(proposals: list[Proposal]) -> tuple[str, str]:
    if len(proposals) == 1:
        return 'SINGLE', 'One proposal; pending official harm evidence'
    signatures = {(canonical(p.fields.get(2, '')), canonical(p.fields.get(3, ''))) for p in proposals}
    if len(signatures) == 1 and all(p.structured for p in proposals):
        return 'DUPLICATE', 'Equivalent text/action; deduplicate only after reviewer confirmation'
    return 'BLOCKED', 'Different or incomplete medicines: no executable rule selected until independent adjudication'


def audit_sources(paths: list[Path]) -> tuple[list[Proposal], list[dict]]:
    all_proposals, inventory = [], []
    for path in paths:
        if len(path.relative_to(SUBMISSIONS).parts) != 3:
            raise ValueError(f'Unexpected medicine path (expected <pack>/<handle>/medicine.md): {path}')
        proposals, state, sha = extract_file(path)
        all_proposals.extend(proposals)
        pack, handle = path.relative_to(SUBMISSIONS).parts[:2]
        inventory.append({'pack': pack, 'handle': handle, 'path': relative(path),
                          'sha256': sha, 'status': state,
                          'medicine_count': len(proposals),
                          'unclassified_count': sum(p.disease == 'UNCLASSIFIED' for p in proposals),
                          'incomplete_count': sum(not p.structured for p in proposals)})
    return all_proposals, inventory


def csv_data(rows: list[dict], columns: list[str]) -> str:
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=columns, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def render_proposal(p: Proposal, n: int, decision: str) -> list[str]:
    source = relative(p.path)
    title = p.heading.replace('## ', '').strip()
    link = f'https://github.com/patilvijay23/era-v5-lab/blob/g1-harm-test/{source}'
    lines = [f'### Medicine {n}: {p.pack} / {p.disease} · {p.handle}', '',
             f'> **Status:** {decision}; not approved. **Original section:** {redact(title)}.',
             f'> **Source:** [{source}]({link})', '']
    for num, label in [(1, 'Disease'), (2, 'Medicine'), (3, 'Action'), (4, 'Harm test'), (5, 'Side effects')]:
        value = p.fields.get(num, '').strip()
        if not value:
            value = ('Not supplied in a standard five-field format; inspect source. '
                     'No automatic executable decision is permitted.')
        if num == 4:
            lines.append('4. **Harm test:** **NOT_EVALUATED on regenerated gold.** ' 
                         'Any numbers below are source-reported/historical, not a fresh certification.')
            lines.append('')
            lines.append('   ' + redact(value).replace('\n', '\n   '))
        else:
            lines.append(f'{num}. **{label}:** {redact(value)}')
        lines.append('')
    return lines


def build(submissions: Path | None = None, dest: Path | None = None) -> dict[str, int]:
    global SUBMISSIONS
    submissions = Path(submissions) if submissions is not None else SUBMISSIONS
    dest = Path(dest) if dest is not None else DEST
    if not submissions.is_dir():
        raise FileNotFoundError(f'Missing medicine submissions directory: {submissions}')
    original_submissions = SUBMISSIONS
    SUBMISSIONS = submissions
    try:
        paths = sorted(submissions.rglob('medicine.md'), key=lambda p: p.relative_to(submissions).as_posix().casefold())
        if not paths:
            raise ValueError(f'No medicine.md files found recursively under {submissions}')
        if submissions.resolve() == (TEAM / 'medicines' / 'submissions').resolve():
            current = {p.relative_to(submissions).as_posix() for p in paths}
            missing = sorted(set(BASELINE_FILES) - current)
            if missing:
                raise FileNotFoundError(
                    'Incomplete local g1-harm-test medicine checkout. Missing: '
                    + ', '.join(missing)
                    + '. Restore/checkout these files before generating Spec v1.'
                )
        proposals, inventory = audit_sources(paths)
    finally:
        SUBMISSIONS = original_submissions
    # Generate links relative to the checkout root; tests may point to a
    # temporary directory instead, where inventory paths use its name.
    from collections import defaultdict
    groups: dict[tuple[str, str], list[Proposal]] = defaultdict(list)
    for p in proposals:
        groups[(p.pack, p.disease)].append(p)
    ledger = []
    for (pack, disease), items in sorted(groups.items()):
        decision, reason = collide(items)
        if len(items) > 1:
            ledger.append({'pack': pack, 'disease': disease, 'proposals': len(items),
                           'status': decision, 'resolution': reason,
                           'sources': '; '.join(relative(p.path) for p in items)})
    lines = [
        '# G1 Data A — Spec v1: Parent Medicine (DRAFT)', '',
        '> **Status:** NOT APPROVED / NOT FROZEN. All `medicine.md` submissions below',
        '> are inputs, not automatically executable or independently certified rules.',
        '> **G2 Indic:** PENDING team handoff; not implicitly integrated.', '',
        '## 1. Scope and source provenance', '',
        f'- Source directory: `{submissions.relative_to(ROOT).as_posix() if submissions.is_relative_to(ROOT) else submissions}` (recursive discovery).',
        f'- Found **{len(paths)} medicine files**, **{len(proposals)} proposed sections**, **{len(groups)} pack/disease groups**.',
        '- Every source is listed below, including unfilled templates and unstructured sheets.',
        '- The original Python examples are shown as non-executable text fences, never run by this builder.',
        '- Re-run harm tests on regenerated gold sets; historic and proxy PASS claims are not current approval.',
        '- Source excerpts are defensively redacted for obvious emails, phone numbers and token patterns;',
        '  reviewers must still check E3/F1 and other sensitive strings before publishing.', '',
        '| Pack | Contributor | Medicine sections | State | Source SHA-256 |',
        '|---|---|---:|---|---|',
    ]
    for entry in inventory:
        path = entry['path']
        lines.append(f'| {safe_cell(entry["pack"])} | {safe_cell(entry["handle"])} | '
                     f'{entry["medicine_count"]} | {entry["status"]} | `{entry["sha256"]}` |')
    lines += ['', '## 2. Conflict resolution and execution decisions', '',
              '**Safety resolution:** two or more distinct proposals for the same `(pack, disease)`',
              'are **BLOCKED** from executable consolidation until a human selects/combines',
              'an implementation and validates it against every applicable refreshed gold set.',
              'Equivalent wording is only marked DUPLICATE, not automatically approved.',
              'No rule is promoted to an approved pipeline by this generator.', '',
              '| Pack | Disease | Proposals | Decision | Resolution |',
              '|---|---|---:|---|---|']
    if not ledger:
        lines.append('| — | — | 0 | — | No multi-author same-disease groups |')
    for item in ledger:
        lines.append(f'| {safe_cell(item["pack"])} | {item["disease"]} | {item["proposals"]} '
                     f'| {item["status"]} | {safe_cell(item["resolution"])} |')
    lines += ['', '## 3. Five-field medicine records (source-based, not yet certified)', '']
    counter = 0
    for (pack, disease), items in sorted(groups.items()):
        decision, _ = collide(items)
        for proposal in items:
            counter += 1
            lines.extend(render_proposal(proposal, counter, decision if decision != 'SINGLE' else 'CANDIDATE'))
    lines += ['## 4. Pending and excluded inputs', '',
              '- **G2 Indic:** not integrated; team handoff pending.',
              '- **Harm evidence:** each candidate and the final ordered combined pipeline',
              '  must pass each applicable official gold set at 1% or below.',
              '- **Conflict selection:** BLOCKED groups need explicit owner/reviewer decisions and fixtures.',
              '- **Previously documented code precedence:** E3 drop before E3 masking to avoid hiding secrets;',
              '  revalidate before enabling. Do not infer executable ordering from raw contributor markdown.',
              '- **Previously reviewed English candidates:** C1/C5/F1 overlap was curated in separate',
              '  code/English summary sheets; those historical choices are not automatically carried over to',
              '  raw submission implementations without an explicit mapping and fresh harm tests.',
              '- **Unstructured and template submissions:** retained in the inventory but are not executable.',
              '- **G9 F2:** fingerprint dependency not assumed complete.', '']
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text('\n'.join(lines).rstrip() + '\n', encoding='utf-8')
    inventory_path = dest.with_name('spec_v1_sources.csv')
    conflicts_path = dest.with_name('spec_v1_conflicts.csv')
    inventory_path.write_text(csv_data(inventory,
        ['pack', 'handle', 'path', 'sha256', 'status', 'medicine_count', 'unclassified_count', 'incomplete_count']),
        encoding='utf-8')
    conflicts_path.write_text(csv_data(ledger,
        ['pack', 'disease', 'proposals', 'status', 'resolution', 'sources']), encoding='utf-8')
    print(f'Wrote {dest} — {len(paths)} medicine sources, {len(proposals)} sections, '
          f'{len(ledger)} multi-proposal groups; DRAFT / NOT FROZEN')
    return {'files': len(paths), 'sections': len(proposals), 'groups': len(groups),
            'multi_proposal_groups': len(ledger), 'blocked': sum(x['status'] == 'BLOCKED' for x in ledger)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--submissions', type=Path, default=SUBMISSIONS)
    parser.add_argument('--output', type=Path, default=DEST)
    options = parser.parse_args()
    build(options.submissions, options.output)
