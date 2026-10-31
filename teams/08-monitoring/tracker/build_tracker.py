"""Diagnosis tracker: one row per student, built from the private roster and the open pull requests.

Usage:
  python -I build_tracker.py --roster <roster.csv> [--out <dir>] [--as-of 2026-10-27T23:59+05:30]

The roster is private and stays out of git. It is a CSV with columns `student,team,pack` (extra
columns are ignored; never put emails in it). Copy the pack table from the CAP plan sheet.

Each pull request is matched to a student by its `Name:` line, then by its `Pack:` line or folder
when only one student has that pack. With `--as-of`, the tracker reads the last commit of each
pull request made before that time, as the graders do at each due date.

Needs the `gh` CLI (logged in). Writes tracker.csv and tracker.md to --out (default ./out).
No email or other personal data is copied from the pull requests: the `Axiom email:` line is never read.
"""
import argparse, csv, io, json, os, re, subprocess, sys, time, unicodedata, urllib.error, urllib.request
from collections import defaultdict
from datetime import datetime, timezone

REPO = "theschoolofai/era-v5-lab"
VERDICTS = {"clean", "fix", "drop"}
SUB = re.compile(r"^diagnosis/submissions/([^/]+)/([^/]+)/(labels\.csv|medicine\.md)$")
# Personal data check on labels.csv: F1 and E3 evidence must give type and offset, never the value.
LEAK = re.compile(r"[\w.+-]+@[\w-]+\.[a-z]{2,}|(?<!\d)(?:\+91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)", re.I)


def gh(path, tries=4):
    for i in range(tries):
        p = subprocess.run(["gh", "api", "--paginate", path], capture_output=True, text=True)
        if p.returncode == 0:
            break
        time.sleep(2 ** i)  # the API drops some calls; retry with backoff
    else:
        sys.exit(f"gh api {path} failed: {p.stderr.strip()}")
    out = p.stdout
    # --paginate joins pages as `][`; turn them into one list.
    return json.loads(out.replace("]\n[", ",").replace("][", ","))


def raw(sha, path, cache):
    key = os.path.join(cache, sha + "_" + path.replace("/", "_"))
    if os.path.exists(key):
        return open(key, encoding="utf-8").read() or None
    url = f"https://raw.githubusercontent.com/{REPO}/{sha}/{path}"
    try:
        text = urllib.request.urlopen(url, timeout=30).read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
        text = ""
    open(key, "w", encoding="utf-8").write(text)  # commits never change, so the cache never goes stale
    return text or None


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z ]", " ", s).split()


def header(body, key):
    m = re.search(rf"^\W*{key}\W*:\s*(.*)$", body or "", re.M | re.I)
    v = m.group(1).strip().strip("*`").strip() if m else ""
    return "" if v.startswith("<") else v  # template placeholder left in


def match_name(name, roster):
    t = norm(name)
    if not t:
        return None
    exact = [r for r in roster if norm(r["student"]) == t]
    if len(exact) == 1:
        return exact[0]
    subset = [r for r in roster if set(t) <= set(norm(r["student"]))]
    return subset[0] if len(subset) == 1 else None


def labels_stats(text):
    rows = list(csv.DictReader(io.StringIO(text)))
    done = [r for r in rows if (r.get("verdict") or "").strip().lower() in VERDICTS]
    v = defaultdict(int)
    for r in done:
        v[r["verdict"].strip().lower()] += 1
    leak = sum(1 for r in rows if LEAK.search((r.get("evidence") or "") + " " + (r.get("note") or "")))
    return {"rows": len(rows), "labelled": len(done), "clean": v["clean"], "fix": v["fix"], "drop": v["drop"], "leak_rows": leak}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roster", required=True)
    ap.add_argument("--out", default="out")
    ap.add_argument("--as-of", help="ISO time; read each PR at its last commit before this")
    ap.add_argument("--target", type=int, default=150, help="rows needed for the first due date")
    a = ap.parse_args()
    as_of = datetime.fromisoformat(a.as_of) if a.as_of else None
    cache = os.path.join(a.out, "cache")
    os.makedirs(cache, exist_ok=True)

    roster = [r for r in csv.DictReader(open(a.roster, encoding="utf-8")) if r.get("student")]
    by_pack = defaultdict(list)
    for r in roster:
        by_pack[r["pack"]].append(r)
    template = raw("main", "diagnosis/templates/medicine_TEMPLATE.md", cache) or ""

    found, unmatched = defaultdict(list), []
    for pr in gh(f"repos/{REPO}/pulls?state=all&per_page=100"):
        if as_of and datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00")) > as_of:
            continue
        files = [f["filename"] for f in gh(f"repos/{REPO}/pulls/{pr['number']}/files?per_page=100")]
        subs = [m.groups() for m in map(SUB.match, files) if m]
        if not subs:
            continue  # team work, not a diagnosis submission
        pack, folder = subs[0][0], subs[0][1]
        sha = pr["head"]["sha"]
        if as_of:
            before = [c for c in gh(f"repos/{REPO}/pulls/{pr['number']}/commits?per_page=100")
                      if datetime.fromisoformat(c["commit"]["committer"]["date"].replace("Z", "+00:00")) <= as_of]
            if not before:
                continue
            sha = before[-1]["sha"]
        name, pack_line = header(pr["body"], "Name"), header(pr["body"], "Pack")
        st = match_name(name, roster)
        how = "name"
        if not st:
            only = by_pack.get(pack_line or pack, [])
            st, how = (only[0], "pack") if len(only) == 1 else (None, "")
        base = f"diagnosis/submissions/{pack}/{folder}/"
        lab = raw(sha, base + "labels.csv", cache)
        med = raw(sha, base + "medicine.md", cache)
        rec = {
            "pr": pr["number"], "author": pr["user"]["login"], "state": "draft" if pr["draft"] else pr["state"],
            "merged": bool(pr["merged_at"]), "sha": sha[:7], "pack_folder": pack, "matched_by": how,
            "header_ok": bool(name and pack_line), "folder_is_author": folder.lower() == pr["user"]["login"].lower(),
            "medicine": "missing" if not med else ("template" if med.strip() == template.strip() else f"{len(med)} B"),
            **(labels_stats(lab) if lab else {"rows": 0, "labelled": 0, "clean": 0, "fix": 0, "drop": 0, "leak_rows": 0}),
        }
        (found[st["student"]] if st else unmatched).append(rec)

    cols = ["student", "team", "pack", "status", "pr", "state", "author", "labelled", "rows", "clean", "fix", "drop",
            "medicine", "issues", "other_prs"]
    out = []
    for r in sorted(roster, key=lambda r: (r.get("team", ""), r["student"])):
        prs = sorted(found.get(r["student"], []), key=lambda p: (p["state"] == "closed", -p["labelled"], -p["pr"]))
        row = {"student": r["student"], "team": r.get("team", ""), "pack": r["pack"]}
        if not prs:
            out.append({**row, "status": "no PR"})
            continue
        p = prs[0]
        issues = []
        if r["pack"] and p["pack_folder"] != r["pack"]:
            issues.append(f"folder pack {p['pack_folder']}")
        if not p["header_ok"]:
            issues.append("header incomplete")
        if not p["folder_is_author"]:
            issues.append("folder is not the PR author")
        if p["leak_rows"]:
            issues.append(f"{p['leak_rows']} rows may hold an email or phone")
        if len([q for q in prs if q["state"] != "closed"]) > 1:
            issues.append("more than one open PR")
        status = "closed" if p["state"] == "closed" else ("on track" if p["labelled"] >= a.target else "behind")
        out.append({**row, "status": status, **{k: p[k] for k in ("pr", "state", "author", "labelled", "rows", "clean",
                    "fix", "drop", "medicine")}, "issues": "; ".join(issues),
                    "other_prs": " ".join(f"#{q['pr']}" for q in prs[1:])})

    with open(os.path.join(a.out, "tracker.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, cols)
        w.writeheader()
        w.writerows(out)

    count = defaultdict(int)
    for r in out:
        count[r["status"]] += 1
    when = a.as_of or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    md = [f"# Diagnosis tracker ({when})", "",
          f"{len(out)} students: " + ", ".join(f"{v} {k}" for k, v in sorted(count.items())) +
          f". On track means at least {a.target} labelled rows.", "",
          "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    md += ["| " + " | ".join(str(r.get(c, "")) for c in cols) + " |" for r in out]
    md += ["", f"## Pull requests not matched to a student ({len(unmatched)})", "",
           "| pr | author | pack_folder | labelled | state |", "|---|---|---|---|---|"]
    md += [f"| #{u['pr']} | {u['author']} | {u['pack_folder']} | {u['labelled']} | {u['state']} |" for u in unmatched]
    open(os.path.join(a.out, "tracker.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"{len(out)} students: {dict(count)}; unmatched PRs {len(unmatched)}; wrote {a.out}/tracker.csv and tracker.md")


if __name__ == "__main__":
    sys.exit(main())
