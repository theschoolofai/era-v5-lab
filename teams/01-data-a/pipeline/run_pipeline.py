"""One command for Data A's pipeline: clean -> overlap -> dedup -> apply the remove list -> F2 -> survivor loss -> ledger -> shards.

  python -I teams/01-data-a/pipeline/run_pipeline.py --config teams/01-data-a/pipeline/pipeline.json [--plan]

It runs or adopts each stage in order, checks that each stage follows from the one before (counts and sha256 links), and
writes <out>/<run_id>/pipeline_manifest.json. It never reimplements a stage: clean (#244), overlap and dedup (#255) and F2
(run_f2.py, #35) are the team's scripts, called as they are; apply_dedup.py, survivor_loss.py and ledger.py are in this
folder.

STAGES
======
  clean          cleaned parts: <output>/train/**.parquet and/or <output>/heldout/**.parquet              (TSAI job, #244)
  overlap        overlap_summary.json, overlap_matches.csv, overlap_docs.parquet                          (TSAI job, #255)
  dedup          remove_list.csv, dedup_groups.csv, dedup_summary.json                                    (TSAI job, #255)
  apply          apply_dedup.py on clean's output with dedup's remove list  -> <run>/deduped
  f2             run_f2.py on <run>/deduped/<split>                           -> <run>/final/<split>
                 (one process per split; with "workers": N, up to N processes at once, one per pack folder)
  survivor_loss  survivor_loss.py on dedup_groups.csv and F2's reports        -> <run>/report
  ledger         ledger.py: one row per document with each stage's decision  -> <run>/ledger
  shards         optional, only with stages.shards: writes <run>/cleaning_pipeline.json (clean.py sha256, F2 set, dedup remove
                 list, overlap run and dedup settings: the processing behind the shards), then shards/run_shards.py on <run>/final   -> <run>/shards (or "out")
                 It runs after the manifest holds every earlier stage, which is what the shard writer reads; its own record is
                 added to the manifest afterwards. The stage stops the run if a part failed or was skipped, if no shard was
                 written, or if the summary is not this run's. "from": "shards" runs only this stage, into an out folder without shards.

clean, overlap and dedup take "mode": "adopt" (TSAI ran the job; "output" names the folder it returned) or "mode": "run".
A run stage names a "settings" file (settings only, no paths) and the runner works out the rest: its folder is <run>/<stage>
(or "output", below ./out), it reads the previous stage's folder, and stage_args.py turns that into the script's command. clean
gets a copy of its settings with the path keys filled in (clean: input_root from "input", output_root, and the input set's
description from the stage: manifest, manifest_sha256, expected_parts, sample; overlap: inputs, out; dedup: results, inputs,
out), written to <run>/cfg/<stage>.json and passed with --config. The clean stage's manifest defaults to sample_manifest.json in
its input folder, and its sha256 must equal manifest_sha256 (checked just before the job starts, not by --plan). "script" replaces the default script; "settings_sha256" pins the settings file
(checked, and the manifest records the file's sha256 either way). Escape hatch: "command" (the script and its arguments, run
with this Python from the repository root) with "output" (where that script writes) skips all of this.
--plan checks the config and prints each stage's folder and command, without running or writing anything. It is the only
option besides --config: every run parameter is in the config file, so a run is reproduced from that file alone.

RUN PARAMETERS (all in the config file; the manifest embeds the whole config)
  run_id                 names the run: its folders are <out>/<run_id>/ (the clean job refuses an existing folder, so a new run
                         needs a new run_id)
  "mode": "adopt"        on clean, overlap or dedup, with "output": the folder to use instead of running the stage
  to                     stop after this stage; only the stages up to it are checked
  from                   resume at this stage: the earlier stages must be recorded in the manifest with unchanged digests
  stages.clean.only      run the clean job on these sample parts only (a list, for trials); overlap then expects no packs
apply, f2, survivor_loss and ledger always run. f2 takes "script" (default teams/01-data-a/spec_v1/run_f2.py) and "workers"
(default 1; each run_f2.py process loads G9's full set, about 1.1 GB of memory, so N workers need about N × 1.1 GB plus the
documents in flight). shards takes "tokenizer" (required: G3's C3 tokenizer.json), and optionally "script" (default
teams/01-data-a/shards/run_shards.py), "out" (default <run>/shards), "tokens", "packs" (only these packs), "pack_table" and
"any_tokenizer" (tests only). apply takes "link" (default true: untouched parts are hard-linked, not copied) and "workers"
(default 4: parts checked and written at once, one row group in memory each). ledger takes "raw"
(optional: the raw parts the cleaner read; with it the ledger says keep / fix / drop per document, mode B, else the
cleaner's decision is "unknown", mode C); it reads dedup_log.jsonl when the dedup folder has one. Scripts run with
python -I, which ignores user site-packages and PYTHONPATH: install pyarrow and the rest into the environment itself.
Each script's output streams to <run>/logs/<stage>.log (F2: logs/f2_<split>[_<pack>].log).
Without stages.shards the run stops after the ledger, and "to": "shards" is an error.

CONFIG (JSON; keys starting with "_" are comments; paths relative to the repository root, or absolute)
=====================================================================================================
  run_id   name of this run;   out   folder for runs (default out/pipeline);   stages   as above
  hash_cache   true (default): every sha256 is computed once and kept in <run>/cache/sha256.json, keyed on each file's
               (device, inode, size, mtime, change time), so the digests reuse apply's hashes and a resumed run hashes
               nothing it has already hashed (hashing.py). false: hash everything again, for an audit
The whole config is checked before the first stage runs.

CHECKS (any failure stops the run; exit code 1)
==============================================
  overlap   status complete; documents_all = the cleaned rows; for every part it lists, its documents = that cleaned part's rows
  dedup     status complete; the overlap_matches.csv and overlap_docs.parquet it checked (overlap_run.checked_sha256) are
            the adopted overlap's files; documents_all = overlap's; removed = remove_list.csv rows; heldout_removed = 0
  apply     rows = the cleaned rows; removed = the remove list (apply_dedup.py also checks every listed row)
  f2        per split: its rows = apply's kept rows; every part's report names, as input_sha256, the sha256 apply wrote;
            one fingerprint set; kept + dropped + errors = rows; no errors; no stale Parquet under final/<split>
  survivor  groups = the groups in dedup_groups.csv
  ledger    its cleaned rows = the cleaned rows; removed_by_dedup = apply's removed; dropped_by_f2, f2_error and kept =
            F2's; one fingerprint set, F2's (ledger.py also checks every final part holds the ledger's kept docs in order);
            per pack and split, its cleaned rows and removed_by_dedup = apply_dedup_summary.json's by_pack
  from      every earlier stage's output still has the digest the manifest recorded for it

MANIFEST
========
<out>/<run_id>/pipeline_manifest.json: the git commit, Python and pyarrow versions; per stage its mode, command, the script's
sha256, its output folder's digest and file count, its counts, its checks and its seconds; all checks; totals (raw and dropped
by clean when the ledger ran in mode B, cleaned, removed by dedup, dropped by F2, final, and shards_written when the shard
stage ran), and by_pack: the same chain for every pack and split, from the ledger. At the end of a run the per-pack
table is also printed to stderr. A digest is the sha256 over the sorted relative path and sha256 of every file in the folder;
JSON summaries are hashed without the fields that change between identical runs (timings, absolute paths, skip flags), so two
runs on the same inputs give the same digests. The files are hashed in parallel threads, through the run's hash cache.
IDs, counts and hashes only.
"""
import sys
sys.dont_write_bytecode = True

import argparse, hashlib, json, platform, subprocess, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE))
import stage_args  # noqa: E402  (how clean, overlap and dedup get their paths)
from hashing import HashCache, code_sha256  # noqa: E402  (every sha256 once, in parallel)
STAGES = ("clean", "overlap", "dedup", "apply", "f2", "survivor_loss", "ledger", "shards", "reconcile")
OPTIONAL = ("shards", "reconcile")  # run only when configured (reconcile also needs shards)
EXTERNAL = ("clean", "overlap", "dedup")
NEEDED = {"overlap": ("overlap_summary.json", "overlap_matches.csv", "overlap_docs.parquet"),
          "dedup": ("remove_list.csv", "dedup_groups.csv", "dedup_summary.json")}
DEFAULT_F2 = "teams/01-data-a/spec_v1/run_f2.py"
DEFAULT_SHARDS = "teams/01-data-a/shards/run_shards.py"
POOL = "teams/01-data-a/pipeline/f2_pool.py"
SPLITS = ("train", "heldout")
RESERVED = ("deduped", "final", "report", "ledger", "shards", "reconcile", "cfg", "logs", "cache")  # folders of the run that no stage output may take
VOLATILE = {"seconds", "input", "path", "cleaned", "skipped"}  # JSON fields that differ between identical runs


class Stop(Exception):
    """A check failed: the message says which and where."""


_CACHE = HashCache()  # in memory, for digest() called without the run's cache
FOOTER_WORKERS = 16  # threads reading Parquet footers


def sha256(path):
    return _CACHE.sha256(path)


def stable(obj):
    if isinstance(obj, dict):
        return {k: stable(v) for k, v in obj.items() if k not in VOLATILE}
    if isinstance(obj, list):
        return [stable(v) for v in obj]
    return obj


def json_hash(p):
    """sha256 of a JSON file's content without the volatile fields, or None when it is not valid JSON."""
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None
    return hashlib.sha256(json.dumps(stable(data), sort_keys=True).encode("utf-8")).hexdigest()


def file_hash(p, cache=None):
    """sha256 of a file; for JSON, of its content without the volatile fields."""
    if p.suffix == ".json":
        h = json_hash(p)
        if h is not None:
            return h
    return (cache or _CACHE).sha256(p)


def digest(folder, cache=None):
    """(digest over every file's relative path and hash, file count). The data files are hashed through `cache`, in
    parallel threads, so a file another stage already hashed (or a hard link to it) is not read again."""
    folder, cache = Path(folder), cache or _CACHE
    files = sorted(p for p in folder.rglob("*") if p.is_file() and not p.name.endswith(".tmp"))
    hashes = {p: json_hash(p) for p in files if p.suffix == ".json"}
    hashes.update(cache.sha256_many([p for p in files if hashes.get(p) is None]))
    h = hashlib.sha256()
    for p in files:
        h.update(f"{p.relative_to(folder).as_posix()}\t{hashes[p]}\n".encode("utf-8"))
    return h.hexdigest(), len(files)


def path(p):
    p = Path(p)
    return p if p.is_absolute() else REPO / p


def run_script(script, args, stage, log):
    """Run a script with this Python from the repository root, its output streamed to log. Returns the exit code."""
    log.parent.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-I", str(path(script)), *map(str, args)]
    with open(log, "w", encoding="utf-8", errors="replace") as f:
        f.write("$ " + " ".join(cmd) + "\n")
        f.flush()
        return subprocess.run(cmd, cwd=REPO, stdout=f, stderr=subprocess.STDOUT).returncode


def tail(log, n=5):
    try:
        return " | ".join(Path(log).read_text(encoding="utf-8", errors="replace").strip().splitlines()[-n:])
    except OSError:
        return ""


def parquet_rows(folder):
    """{"rows", "by_split", "by_part" ({"<split>/<part>": rows})} from the Parquet footers."""
    import pyarrow.parquet as pq
    files = [(split, f) for split in SPLITS if (folder / split).is_dir() for f in sorted((folder / split).rglob("*.parquet"))]

    def rows(item):
        split, f = item
        try:
            return pq.read_metadata(f).num_rows
        except Exception as e:  # not Parquet, truncated, unreadable
            raise Stop(f"clean: {split}/{f.relative_to(folder / split).as_posix()} cannot be read as Parquet ({type(e).__name__})")

    with ThreadPoolExecutor(max_workers=max(1, min(FOOTER_WORKERS, len(files)))) as pool:  # thousands of footers
        counts = list(pool.map(rows, files))
    by_split, by_part = {}, {}
    for (split, f), n in zip(files, counts):
        by_part[f"{split}/{f.relative_to(folder / split).as_posix()}"] = n
        by_split[split] = by_split.get(split, 0) + n
    if not by_split:
        raise Stop(f"clean: {folder} has no Parquet parts under train/ or heldout/")
    return {"rows": sum(by_split.values()), "by_split": by_split, "by_part": by_part}


def csv_column(file, column):
    """One column of a CSV, every value a string, read by pyarrow (a remove list can hold millions of rows)."""
    import pyarrow as pa, pyarrow.csv as pcsv
    try:
        return pcsv.read_csv(file, parse_options=pcsv.ParseOptions(newlines_in_values=True),
                             convert_options=pcsv.ConvertOptions(include_columns=[column], column_types={column: pa.string()},
                                                                 strings_can_be_null=False)).column(column)
    except (pa.ArrowInvalid, KeyError) as e:
        raise Stop(f"{file}: cannot be read as CSV with a {column} column ({e})")


def csv_rows(file):
    """Records of a CSV, without the header (a quoted value may hold a newline, so lines are not records)."""
    with open(file, encoding="utf-8", newline="") as f:
        first = f.readline().rstrip("\r\n").split(",")[0]
    return len(csv_column(file, first)) if first else 0


def load_json(file):
    return json.loads(Path(file).read_text(encoding="utf-8"))


class Run:
    def __init__(self, cfg_path):
        """Every run parameter is in the config file: run_id, the stages (each run from a settings file or adopted), and the
        optional "from", "to" and stages.clean.only (see the docstring)."""
        self.cfg_path = Path(cfg_path)
        self.cfg = load_json(self.cfg_path)
        if not self.cfg.get("run_id"):
            raise Stop(f"{cfg_path}: run_id is missing")
        self.stages = self.cfg.setdefault("stages", {})
        clean = self.stages.get("clean")
        self.only = (clean.get("only") or []) if isinstance(clean, dict) else []
        if not isinstance(self.only, list) or not all(isinstance(p, str) for p in self.only):
            raise Stop("config: stages.clean.only must be a list of sample parts, e.g. [\"train/code-go/part-00000.parquet\"]")
        self.dir = path(self.cfg.get("out", "out/pipeline")) / self.cfg["run_id"]
        self.manifest_path = self.dir / "pipeline_manifest.json"
        if not isinstance(self.cfg.get("hash_cache", True), bool):
            raise Stop("config: hash_cache must be true or false")
        self.cache = HashCache(self.dir / "cache" / "sha256.json", enabled=self.cfg.get("hash_cache", True))
        self.done, self.checks = {}, []

    def output(self, stage):
        if stage in EXTERNAL:
            spec = self.stages.get(stage) or {}
            return path(spec["output"]) if spec.get("output") else self.dir / stage  # default: inside the run folder
        if stage == "shards":
            return path(self.stages["shards"]["out"]) if self.stages.get("shards", {}).get("out") else self.dir / "shards"
        return self.dir / {"apply": "deduped", "f2": "final", "survivor_loss": "report", "ledger": "ledger",
                           "reconcile": "reconcile"}[stage]

    def last_stage(self):
        """Where a run stops without "to": reconcile when configured (with shards), else shards when configured, else the ledger."""
        if "shards" in self.stages and "reconcile" in self.stages:
            return "reconcile"
        return "shards" if "shards" in self.stages else "ledger"

    def shown(self, p):
        """A path as the manifest and the plan show it: relative to the repository when inside it, else absolute."""
        p = Path(p).resolve()
        try:
            return p.relative_to(REPO.resolve()).as_posix()
        except ValueError:
            return p.as_posix()

    def stage_command(self, stage, write):
        """None for an adopted stage; else {command, settings, settings_sha256, config, config_sha256} (stage_args.build, or the
        run config's own "command"). write=False checks and names the generated config without writing it."""
        spec = self.stages[stage]
        if spec.get("mode", "adopt") != "run":
            return None
        if spec.get("command"):
            return {"command": spec["command"], "settings": None, "settings_sha256": None, "config": None, "config_sha256": None}
        try:
            return stage_args.build(stage, spec, {s: self.output(s) for s in EXTERNAL}, self.dir / "cfg", REPO, write, self.only)
        except stage_args.ConfigError as e:
            raise Stop(f"config: {stage}: {e}")

    def validate(self, upto):
        """The config of every stage up to `upto`, before anything runs."""
        active = [s for s in EXTERNAL if STAGES.index(s) <= STAGES.index(upto)]
        if self.only:
            clean = self.stages.get("clean") or {}
            if clean.get("mode", "adopt") != "run" or clean.get("command"):
                raise Stop("config: stages.clean.only limits the clean job to some parts, so clean must run from a settings file (not adopted, not a command)")
        for stage in active:
            spec = self.stages.get(stage)
            if not isinstance(spec, dict):
                raise Stop(f"config: stages.{stage} is missing")
            mode = spec.get("mode", "adopt")
            if mode not in ("adopt", "run"):
                raise Stop(f"config: stages.{stage}.mode is {mode!r}, expected adopt or run")
            if mode == "adopt" and not spec.get("output"):
                raise Stop(f"config: stages.{stage}.output is missing (an adopted stage needs the folder that was returned)")
            if mode == "run":
                cmd = spec.get("command")
                if "command" in spec and (not cmd or not isinstance(cmd, list)):
                    raise Stop(f"config: stages.{stage}.command (a list: script, then arguments) is missing for mode run")
                if cmd and not spec.get("output"):
                    raise Stop(f"config: stages.{stage}.output is missing: with a command, say where it writes")
                if cmd and not path(cmd[0]).is_file():
                    raise Stop(f"config: stages.{stage}.command script {cmd[0]} not found")
                script = spec.get("script", stage_args.DEFAULT_SCRIPT.get(stage))
                if not cmd and script and not path(script).is_file():
                    raise Stop(f"config: stages.{stage} script {script} not found")
                self.stage_command(stage, write=False)
        for stage, default in (("f2", 1), ("apply", 4)):
            workers = self.stages.get(stage, {}).get("workers", default)
            if not isinstance(workers, int) or isinstance(workers, bool) or workers < 1:
                raise Stop(f"config: stages.{stage}.workers is {workers!r}, expected a whole number >= 1")
        if not isinstance(self.stages.get("f2", {}).get("pool", False), bool):
            raise Stop("config: stages.f2.pool must be true or false")
        if "reconcile" in self.stages and "shards" not in self.stages:
            raise Stop("config: stages.reconcile needs stages.shards: it reconciles the shards with the ledger")
        if upto == "reconcile" and "reconcile" not in self.stages:
            raise Stop("config: \"to\": \"reconcile\" needs stages.reconcile (it runs only when configured)")
        if STAGES.index(upto) >= STAGES.index("f2"):
            script = self.stages.get("f2", {}).get("script", DEFAULT_F2)
            if not path(script).is_file():
                raise Stop(f"config: f2 script {script} not found (run_f2.py is teams/01-data-a/spec_v1/run_f2.py; set stages.f2.script)")
        raw = self.stages.get("ledger", {}).get("raw")
        if STAGES.index(upto) >= STAGES.index("ledger") and raw is not None and not path(raw).is_dir():
            raise Stop(f"config: stages.ledger.raw {raw} is not a folder")
        if "shards" in self.stages or upto == "shards":
            self.validate_shards(upto)
        outs = {stage: self.output(stage).resolve() for stage in active}
        r = self.dir.resolve()
        for stage, o in outs.items():
            if o == r or o in r.parents:
                raise Stop(f"config: stages.{stage}.output and the run folder {self.dir} overlap")
            if r in o.parents and o.relative_to(r).parts[0] in RESERVED:
                raise Stop(f"config: stages.{stage}.output {o} is a folder of the run itself ({', '.join(RESERVED)})")
        for a, b in [(a, b) for i, a in enumerate(active) for b in active[i + 1:]]:
            if outs[a] == outs[b] or outs[a] in outs[b].parents or outs[b] in outs[a].parents:
                raise Stop(f"config: stages.{a}.output and stages.{b}.output overlap")

    def validate_shards(self, upto):
        spec = self.stages.get("shards")
        if STAGES.index(upto) < STAGES.index("shards"):
            return
        if not isinstance(spec, dict):
            raise Stop("config: stages.shards is not configured (it needs at least a tokenizer); the run stops after the ledger without it")
        if not spec.get("tokenizer") or not path(spec["tokenizer"]).is_file():
            raise Stop(f"config: stages.shards.tokenizer {spec.get('tokenizer')!r} is missing or not a file")
        script = spec.get("script", DEFAULT_SHARDS)
        if not path(script).is_file():
            raise Stop(f"config: shards script {script} not found")
        tokens = spec.get("tokens")
        if tokens is not None and (not isinstance(tokens, int) or isinstance(tokens, bool) or tokens < 1):
            raise Stop(f"config: stages.shards.tokens is {tokens!r}, expected a whole number >= 1")
        packs = spec.get("packs", [])
        if not isinstance(packs, list) or not all(isinstance(p, str) for p in packs):
            raise Stop("config: stages.shards.packs must be a list of pack ids")
        if spec.get("pack_table") and not path(spec["pack_table"]).is_file():
            raise Stop(f"config: stages.shards.pack_table {spec['pack_table']} not found")

    def plan(self, to=None):
        """What a run would do, as text: each stage's mode, output folder and command, with every path resolved. The config is
        checked first, as for a run; nothing is run or written."""
        to = to or self.cfg.get("to") or self.last_stage()
        if to not in STAGES:
            raise Stop(f"unknown stage {to!r}; stages are {', '.join(STAGES)}")
        self.validate(to)
        lines = [f"run folder: {self.shown(self.dir)}   manifest: {self.shown(self.manifest_path)}"]
        for n, stage in enumerate(STAGES[: STAGES.index(to) + 1], start=1):
            out = self.shown(self.output(stage))
            if stage in EXTERNAL:
                built = self.stage_command(stage, write=False)
                if built is None:
                    lines.append(f"{n:02d} {stage:13} adopt  {out}")
                    continue
                lines.append(f"{n:02d} {stage:13} run    {out}")
                lines.append("     $ python -I " + " ".join(built["command"]).replace(str(REPO) + "/", ""))
                if built["settings"]:
                    lines.append(f"     settings {built['settings']} (sha256 {built['settings_sha256'][:12]}…)")
                if built["config"]:
                    lines.append(f"     generated config {self.shown(built['config'])}: " + ", ".join(
                        f"{k} = {v}" for k, v in stage_args.generated_values(stage, {s: self.output(s) for s in EXTERNAL}, REPO, self.stages[stage]).items()
                        if k in stage_args.PATH_KEYS))
            elif stage == "f2":
                f2 = self.stages.get("f2", {})
                how = (f"{POOL} (the set loaded once) calling {f2.get('script', DEFAULT_F2)}" if f2.get("pool")
                       else f2.get("script", DEFAULT_F2))
                lines.append(f"{n:02d} {stage:13} run    {out}   {how}, workers {f2.get('workers', 1)}")
            elif stage == "shards":
                spec = self.stages["shards"]
                lines.append(f"{n:02d} {stage:13} run    {out}   {spec.get('script', DEFAULT_SHARDS)}, tokenizer {spec['tokenizer']}")
            else:
                lines.append(f"{n:02d} {stage:13} run    {out}")
        return "\n".join(lines)

    def check(self, name, ok, detail):
        self.checks.append({"check": name, "ok": bool(ok), "detail": detail})
        if not ok:
            raise Stop(f"check failed: {name}: {detail}")

    # --- the stages -------------------------------------------------------------------------------------------------
    def stage_external(self, stage):
        spec = self.stages[stage]
        mode = spec.get("mode", "adopt")
        built = self.stage_command(stage, write=True)
        command = built["command"] if built else None
        if command:
            log = self.dir / "logs" / f"{stage}.log"
            rc = run_script(command[0], command[1:], stage, log)
            if rc != 0:
                raise Stop(f"{stage}: {Path(command[0]).name} failed with exit code {rc}: {tail(log)}")
        out = self.output(stage)
        for name in NEEDED.get(stage, ()):
            if not (out / name).is_file():
                raise Stop(f"{stage}: {out} has no {name}")
        counts = getattr(self, f"counts_{stage}")(out)
        rec = {"mode": mode, "command": command, "code_sha256": sha256(path(command[0])) if command else None,
               "output": self.shown(out), "counts": counts}
        if self.only and stage == "clean":
            rec["only"] = self.only
        if built and built["settings"]:  # a stage run from a settings file: which file, and the config it was run with
            rec.update(settings=built["settings"], settings_sha256=built["settings_sha256"],
                       config=Path(built["config"]).relative_to(self.dir).as_posix() if built["config"] else None,
                       config_sha256=built["config_sha256"])
        return rec

    def counts_clean(self, out):
        return parquet_rows(out)

    def counts_overlap(self, out):
        s = load_json(out / "overlap_summary.json")
        clean = self.done["clean"]["counts"]
        self.check("overlap finished", s.get("status") == "complete", f"status {s.get('status')!r}")
        self.check("overlap read every cleaned row", s.get("documents_all") == clean["rows"],
                   f"overlap documents_all {s.get('documents_all')}, cleaned rows {clean['rows']}")
        listed = {p["part"].replace("\\", "/"): p["documents"] for p in s.get("inputs", {}).get("parts", [])}
        if listed:
            diff = sorted(p for p in set(listed) | set(clean["by_part"]) if listed.get(p) != clean["by_part"].get(p))
            self.check("overlap read these cleaned parts", not diff,
                       f"{len(diff)} part(s) differ in name or row count, e.g. {diff[0] if diff else ''}")
        files = {}
        for name in ("overlap_matches.csv", "overlap_docs.parquet"):
            files[name] = sha256(out / name)
            want = s.get("outputs", {}).get(name, {}).get("sha256")
            if want:
                self.check(f"{name} matches overlap's summary", files[name] == want, f"{files[name][:12]}… vs {want[:12]}…")
        return {"documents_all": s.get("documents_all"), "parts": len(listed), "files_sha256": files}

    def counts_dedup(self, out):
        s = load_json(out / "dedup_summary.json")
        ov = self.done["overlap"]["counts"]
        import pyarrow.compute as pc
        groups = pc.count_distinct(csv_column(out / "dedup_groups.csv", "group_id")).as_py()
        counts = {"remove_list_rows": csv_rows(out / "remove_list.csv"), "removed": s.get("removed"),
                  "heldout_removed": s.get("heldout_removed"), "groups": groups}
        self.check("dedup finished", s.get("status") == "complete", f"status {s.get('status')!r}")
        checked = s.get("overlap_run", {}).get("checked_sha256", {})
        self.check("dedup used this overlap run", checked == ov["files_sha256"],
                   f"dedup checked {sorted((k, v[:12]) for k, v in checked.items())}, "
                   f"the adopted overlap has {sorted((k, v[:12]) for k, v in ov['files_sha256'].items())}")
        self.check("dedup saw overlap's documents", s.get("documents_all") == ov["documents_all"],
                   f"dedup documents_all {s.get('documents_all')}, overlap {ov['documents_all']}")
        self.check("dedup summary matches its remove list", counts["removed"] == counts["remove_list_rows"],
                   f"summary removed {counts['removed']}, remove_list.csv rows {counts['remove_list_rows']}")
        self.check("dedup removed no held-out doc", counts["heldout_removed"] == 0,
                   f"heldout_removed {counts['heldout_removed']} (rule 0)")
        return counts

    def stage_apply(self):
        import apply_dedup
        out, clean = self.output("apply"), self.done["clean"]["counts"]
        try:
            s = apply_dedup.apply(self.output("clean"), self.output("dedup") / "remove_list.csv", out,
                                  splits=tuple(sp for sp in SPLITS if sp in clean["by_split"]),
                                  link=bool(self.stages.get("apply", {}).get("link", True)),
                                  workers=self.stages.get("apply", {}).get("workers", apply_dedup.DEFAULT_WORKERS),
                                  cache=self.cache)
        except apply_dedup.Stop as e:
            raise Stop(f"apply: {e}")
        counts = dict(s["totals"])
        counts["kept_by_split"] = {}
        for p in s["parts"]:
            counts["kept_by_split"][p["split"]] = counts["kept_by_split"].get(p["split"], 0) + p["kept"]
        self.check("apply read every cleaned row", counts["rows"] == clean["rows"],
                   f"apply rows {counts['rows']}, cleaned rows {clean['rows']}")
        self.check("apply removed the remove list", counts["removed"] == self.done["dedup"]["counts"]["remove_list_rows"],
                   f"apply removed {counts['removed']}, remove list {self.done['dedup']['counts']['remove_list_rows']}")
        self.apply_parts = {(p["split"], p["part"]): p["output_sha256"] for p in s["parts"]}
        return {"mode": "run", "command": ["teams/01-data-a/pipeline/apply_dedup.py"],
                "code_sha256": s["code_sha256"], "output": "deduped", "counts": counts}

    def f2_units(self, src, split, workers, pool=False):
        """The F2 work units of one split: the whole split with one worker or with the pool (f2_pool.py shares the parts
        out itself), else one unit per pack folder (plus one for Parquet files sitting directly in the split folder).
        Each unit: (name, inputs, out)."""
        out = self.output("f2") / split
        if workers <= 1 or pool:
            return [(split, [src / split], out)]
        units = [(f"{split}/{d.name}", [d], out / d.name) for d in sorted((src / split).iterdir())
                 if d.is_dir() and any(d.rglob("*.parquet"))]
        loose = sorted(f for f in (src / split).glob("*.parquet") if f.is_file())
        if loose:
            units.append((f"{split}/(files)", loose, out))
        return units

    def stage_f2(self):
        from concurrent.futures import ThreadPoolExecutor
        spec = self.stages.get("f2", {})
        script, workers, pool = spec.get("script", DEFAULT_F2), int(spec.get("workers", 1)), bool(spec.get("pool", False))
        src, out = self.output("apply"), self.output("f2")
        parts = getattr(self, "apply_parts", None)
        if parts is None:  # apply was recorded by an earlier run
            s = load_json(src / "apply_dedup_summary.json")
            parts = {(p["split"], p["part"]): p["output_sha256"] for p in s["parts"]}
        kept_by_split = self.done["apply"]["counts"]["kept_by_split"]
        splits = [sp for sp in SPLITS if (src / sp).is_dir()]
        for split in splits:  # before any F2 runs
            mine = {p for (sp, p) in parts if sp == split}
            if (out / split).is_dir():
                stale = sorted(f.relative_to(out / split).as_posix() for f in (out / split).rglob("*.parquet")
                               if f.relative_to(out / split).as_posix() not in mine)
                self.check(f"no stale F2 output in final/{split}", not stale,
                           f"{len(stale)} Parquet file(s) from an earlier run, e.g. {stale[0] if stale else ''}")
        units = [u for sp in splits for u in self.f2_units(src, sp, workers, pool)]

        def one(unit):
            name, inputs, dst = unit
            log = self.dir / "logs" / ("f2_" + name.replace("/", "_").replace("(", "").replace(")", "") + ".log")
            if pool:  # one f2_pool.py per split: the set loaded once, the split's parts shared out among the workers
                rc = run_script(POOL, ["--inputs", *inputs, "--out", dst, "--workers", workers, "--script", path(script)], "f2", log)
            else:
                rc = run_script(script, ["--inputs", *inputs, "--out", dst], "f2", log)
            return name, dst, rc, log

        t0 = time.time()
        with ThreadPoolExecutor(max_workers=1 if pool else max(1, workers)) as threads:  # each thread waits on its own process
            results = list(threads.map(one, units))
        failed = [(n, rc, log) for n, dst, rc, log in results if rc != 0 and not (dst / "f2_summary.json").is_file()]
        if failed:
            n, rc, log = failed[0]
            raise Stop(f"f2: {len(failed)} of {len(units)} unit(s) failed without a summary, e.g. {n} "
                       f"(exit code {rc}): {tail(log)}. Rerun with from = f2: finished files are skipped")

        totals = {"rows": 0, "kept": 0, "dropped_by_f2": 0, "errors": 0}
        by_split, sets = {sp: dict.fromkeys(totals, 0) for sp in splits}, set()
        for name, dst, rc, log in results:
            s = load_json(dst / "f2_summary.json")
            sets.add(s.get("set_sha256"))
            errors = s.get("errors", 0)
            errors = len(errors) if isinstance(errors, list) else errors
            split = name.split("/")[0]
            for k, v in (("rows", s.get("rows", 0)), ("kept", s.get("kept", 0)),
                         ("dropped_by_f2", s.get("dropped_by_f2", 0)), ("errors", errors)):
                by_split[split][k] += v
                totals[k] += v
            self.check(f"F2 reported no errors on {name}", errors == 0 and rc == 0,
                       f"{errors} docs raised during the check, exit code {rc}; see {log.name}")
        for split in splits:
            self.check(f"F2 read every deduplicated row of {split}", by_split[split]["rows"] == kept_by_split.get(split),
                       f"F2 rows {by_split[split]['rows']}, apply kept {kept_by_split.get(split)}")
            wrong = []
            for part in sorted(p for (sp, p) in parts if sp == split):
                rep = out / split / (part + ".f2.json")
                got = load_json(rep).get("input_sha256") if rep.is_file() else None
                if got != parts[(split, part)]:
                    wrong.append(part)
            self.check(f"F2 read what apply wrote in {split}", not wrong,
                       f"{len(wrong)} part(s) without a matching F2 report, e.g. {wrong[0] if wrong else ''}")
        self.check("F2 used one fingerprint set", len(sets) == 1 and None not in sets, f"set_sha256 values {sorted(map(str, sets))}")
        self.check("F2 counts add up", totals["kept"] + totals["dropped_by_f2"] + totals["errors"] == totals["rows"], f"{totals}")
        return {"mode": "run", "command": [script, "--inputs", "<run>/deduped/<split>[/<pack>]", "--out", "<run>/final/<split>[/<pack>]"],
                "code_sha256": sha256(path(script)), "output": "final", "set_sha256": sets.pop(),
                "pool": pool, "pool_code_sha256": sha256(path(POOL)) if pool else None,
                "workers": workers, "units": len(units), "wall_seconds": round(time.time() - t0, 1),
                "counts": {**totals, "by_split": by_split}}

    def stage_survivor_loss(self):
        import survivor_loss
        out = self.output("survivor_loss")
        try:
            s = survivor_loss.report(self.output("dedup") / "dedup_groups.csv", self.output("f2"), out)
        except survivor_loss.Stop as e:
            raise Stop(f"survivor_loss: {e}")
        self.check("survivor loss saw every dedup group", s["groups"]["total"] == self.done["dedup"]["counts"]["groups"],
                   f"report {s['groups']['total']}, dedup_groups.csv {self.done['dedup']['counts']['groups']}")
        return {"mode": "run", "command": ["teams/01-data-a/pipeline/survivor_loss.py"], "code_sha256": s["code_sha256"],
                "output": "report", "counts": {**s["groups"], "survivors_dropped_by_f2": s["survivors_dropped_by_f2"]}}

    def stage_ledger(self):
        import ledger
        raw = self.stages.get("ledger", {}).get("raw")
        dedup = self.output("dedup")
        log = dedup / "dedup_log.jsonl"
        try:
            s = ledger.build(self.output("clean"), dedup / "remove_list.csv", dedup / "dedup_groups.csv",
                             self.output("f2"), self.output("ledger"), log=log if log.is_file() else None,
                             raw=path(raw) if raw is not None else None)
        except ledger.Stop as e:
            raise Stop(f"ledger: {e}")
        t, c = s["totals"], {st: self.done[st]["counts"] for st in ("clean", "apply", "f2")}
        self.check("ledger holds every cleaned row", t["rows_cleaned"] == c["clean"]["rows"],
                   f"ledger {t['rows_cleaned']}, cleaned rows {c['clean']['rows']}")
        self.check("ledger removed_by_dedup = apply's removed", t["removed_by_dedup"] == c["apply"]["removed"],
                   f"ledger {t['removed_by_dedup']}, apply {c['apply']['removed']}")
        self.check("ledger dropped_by_f2 = F2's", t["dropped_by_f2"] == c["f2"]["dropped_by_f2"],
                   f"ledger {t['dropped_by_f2']}, F2 {c['f2']['dropped_by_f2']}")
        self.check("ledger f2_error = F2's errors", t["f2_error"] == c["f2"]["errors"],
                   f"ledger {t['f2_error']}, F2 {c['f2']['errors']}")
        self.check("ledger kept = F2's kept", t["kept"] == c["f2"]["kept"], f"ledger {t['kept']}, F2 {c['f2']['kept']}")
        self.check("ledger used F2's fingerprint set", s["inputs"]["set_sha256"] == self.done["f2"]["set_sha256"],
                   f"{str(s['inputs']['set_sha256'])[:12]}… vs {str(self.done['f2']['set_sha256'])[:12]}…")
        by_pack = {pack: {split: pack_chain(c_, s["clean_mode"]) for split, c_ in splits.items()}
                   for pack, splits in s["by_pack"].items()}
        applied = load_json(self.output("apply") / "apply_dedup_summary.json").get("by_pack", {})
        mine = {(pk, sp): (r["cleaned"], r["removed_by_dedup"]) for pk, sps in by_pack.items() for sp, r in sps.items()}
        theirs = {(pk, sp): (r["rows"], r["removed"]) for pk, sps in applied.items() for sp, r in sps.items()}
        # a pack/split the cleaner emptied (mode B) is in the ledger with 0 rows and absent from apply: both mean (0, 0)
        diff = sorted(k for k in set(mine) | set(theirs) if mine.get(k, (0, 0)) != theirs.get(k, (0, 0)))
        self.check("ledger per pack = apply per pack", not diff,
                   f"{len(diff)} pack/split(s) differ in cleaned rows or removed, e.g. "
                   f"{diff[0][0] + '/' + diff[0][1] + ': ledger ' + str(mine.get(diff[0])) + ', apply ' + str(theirs.get(diff[0])) if diff else ''}")
        bad = sorted(f"{pk}/{sp}" for pk, sps in s["by_pack"].items() for sp, r in sps.items()
                     if r["rows_cleaned"] - r["removed_by_dedup"] - r["dropped_by_f2"] - r["f2_error"] != r["kept"]
                     or r["rows"] - r["dropped_by_clean"] != r["rows_cleaned"])
        self.check("every per-pack row adds up", not bad,
                   f"{len(bad)} pack/split(s) where raw - clean != cleaned or cleaned - dedup - f2 - errors != final, "
                   f"e.g. {bad[0] if bad else ''}")
        sums = {k: sum(r[k] for sps in by_pack.values() for r in sps.values())
                for k in ("cleaned", "removed_by_dedup", "dropped_by_f2", "final")}
        stage = {"cleaned": c["clean"]["rows"], "removed_by_dedup": c["apply"]["removed"],
                 "dropped_by_f2": c["f2"]["dropped_by_f2"], "final": c["f2"]["kept"]}
        self.check("per-pack table adds up to the stages' counts", sums == stage, f"table {sums}, stages {stage}")
        return {"mode": "run", "command": ["teams/01-data-a/pipeline/ledger.py"], "code_sha256": s["code_sha256"],
                "output": "ledger", "clean_mode": s["clean_mode"],
                "counts": {k: v for k, v in t.items() if v is not None}, "by_pack": by_pack}

    def stage_shards(self):
        """The cleaning_pipeline.json of the run, then run_shards.py on final/. The manifest on disk (written after the earlier
        stages) is what the shard writer reads; this stage's own record is added to the manifest afterwards."""
        spec = self.stages["shards"]
        script, out = spec.get("script", DEFAULT_SHARDS), self.output("shards")
        sys.path.insert(0, str(HERE.parent / "shards"))
        import provenance
        try:
            record_path, record = provenance.write_record(self.manifest_path, REPO)
        except provenance.Stop as e:
            raise Stop(f"shards: {e}")
        args = ["--input", self.output("f2"), "--manifest", self.manifest_path, "--tokenizer", path(spec["tokenizer"]), "--out", out]
        if spec.get("tokens"):
            args += ["--tokens", spec["tokens"]]
        for pack in spec.get("packs", []):
            args += ["--pack", pack]
        if spec.get("pack_table"):
            args += ["--pack-table", path(spec["pack_table"])]
        if spec.get("any_tokenizer"):
            args.append("--any-tokenizer")
        log = self.dir / "logs" / "shards.log"
        rc = run_script(script, args, "shards", log)
        summary_path = out / "shards_summary.json"
        if not summary_path.is_file():
            raise Stop(f"shards: {Path(script).name} failed with exit code {rc} and wrote no shards_summary.json: {tail(log)}")
        s = load_json(summary_path)
        counts, record_sha = s["counts"], sha256(record_path)
        self.check("shards: no part failed or was skipped", counts["failed"] == 0 and counts["skipped"] == 0,
                   f"{counts}; see logs/shards.log")
        self.check("shards: run_shards.py exited 0", rc == 0, f"exit code {rc}; see logs/shards.log")
        self.check("shards: at least one shard written", counts["written"] > 0, f"{counts}")
        self.check("shards: the summary is this run's, made with this run's cleaning_pipeline.json",
                   s.get("run_id") == self.cfg["run_id"] and s.get("cleaning_pipeline_sha256") == record_sha,
                   f"summary run_id {s.get('run_id')}, cleaning_pipeline_sha256 {str(s.get('cleaning_pipeline_sha256'))[:12]}…")
        return {"mode": "run", "command": [script, "--input", "<run>/final", "--manifest", "<run>/pipeline_manifest.json", "--out", "<out>"],
                "code_sha256": sha256(path(script)), "output": spec.get("out") or "shards", "cleaning_pipeline_sha256": record_sha,
                "counts": {**counts, "parts": len(s["parts"])}}

    def stage_reconcile(self):
        """reconcile_shards.py: every kept document of the ledger is in exactly one shard, or left out for a stated reason."""
        import reconcile_shards
        out, packs = self.output("reconcile"), self.stages.get("shards", {}).get("packs") or None
        try:  # on a failed check, reconcile_shards.py has written its summary and per-document statuses before stopping
            r = reconcile_shards.reconcile(self.output("ledger"), self.output("shards"), out, packs)
        except reconcile_shards.Stop as e:
            raise Stop(f"reconcile: {e}. See {self.shown(out)}/reconcile_summary.json and reconcile_docs.parquet (shard_status)")
        for c in r["checks"]:
            self.check(f"reconcile: {c['check']}", c["ok"], c["detail"])
        return {"mode": "run", "command": ["teams/01-data-a/pipeline/reconcile_shards.py"], "code_sha256": r["code_sha256"],
                "output": "reconcile", "counts": {"kept": r["kept"], "in_shards": r["in_shards"], **r["totals"]}}

    # --- the run ----------------------------------------------------------------------------------------------------
    def execute(self, start=None, to=None):
        start = start or self.cfg.get("from") or STAGES[0]
        to = to or self.cfg.get("to") or self.last_stage()
        for s in (start, to):
            if s not in STAGES:
                raise Stop(f"unknown stage {s!r}; stages are {', '.join(STAGES)}")
        if STAGES.index(start) > STAGES.index(to):
            raise Stop(f"\"from\": {start} comes after \"to\": {to}")
        self.validate(to)
        old = {s["stage"]: s for s in load_json(self.manifest_path)["stages"]} if self.manifest_path.is_file() else {}
        sys.path.insert(0, str(HERE))
        for stage in STAGES[: STAGES.index(to) + 1]:
            out = self.output(stage)
            if STAGES.index(stage) < STAGES.index(start):
                if stage not in old:
                    raise Stop(f"\"from\": {start}: stage {stage} has no record in {self.manifest_path}; run it first")
                if not out.exists() or digest(out, self.cache)[0] != old[stage]["digest"]:
                    raise Stop(f"{stage}: {out} changed after the manifest recorded it; rerun from {stage}")
                self.done[stage] = old[stage]
                continue
            t0, self.checks = time.time(), []
            rec = self.stage_external(stage) if stage in EXTERNAL else getattr(self, f"stage_{stage}")()
            rec["digest"], rec["files"] = digest(out, self.cache)
            self.done[stage] = {"stage": stage, **rec, "checks": self.checks, "seconds": round(time.time() - t0, 1)}
            self.write()
            self.cache.save()  # a resumed run reuses every hash so far
            print(f"{stage}: {json.dumps({k: v for k, v in self.done[stage]['counts'].items() if k != 'by_part'})}",
                  file=sys.stderr, flush=True)
        m = self.write()
        table = pack_table(m.get("by_pack") or {})
        if table:
            print(table, file=sys.stderr, flush=True)
        return m

    def write(self):
        c = {s: self.done[s]["counts"] for s in self.done}
        totals = {}
        if "clean" in c:
            totals["cleaned"] = c["clean"]["rows"]
        if "apply" in c:
            totals["removed_by_dedup"] = c["apply"]["removed"]
        if "f2" in c:
            totals["dropped_by_f2"] = c["f2"]["dropped_by_f2"]
            totals["final"] = c["f2"]["kept"]
        if "shards" in c:
            totals["shards_written"] = c["shards"]["written"]
        if "ledger" in c and self.done["ledger"].get("clean_mode") == "B":
            totals = {"raw": c["ledger"]["rows"], "dropped_by_clean": c["ledger"]["dropped_by_clean"], **totals}
        stages = [self.done[s] for s in STAGES if s in self.done]
        by_pack = self.done.get("ledger", {}).get("by_pack")
        manifest = {"tool": "run_pipeline.py", "run_id": self.cfg["run_id"], "config": self.cfg,
                    "code_sha256": code_sha256(Path(__file__), _CACHE, ("stage_args.py",))[0], "git_commit": git_commit(),
                    "python": platform.python_version(), "pyarrow": pyarrow_version(), "stages": stages,
                    "checks": [dict(ch, stage=s["stage"]) for s in stages for ch in s.get("checks", [])], "totals": totals}
        if by_pack:
            manifest["by_pack"] = by_pack
        self.dir.mkdir(parents=True, exist_ok=True)
        tmp = self.manifest_path.with_name(self.manifest_path.name + ".tmp")
        tmp.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
        tmp.replace(self.manifest_path)
        return manifest


def pack_chain(c, clean_mode):
    """One pack and split of the ledger summary as the manifest's chain: (raw, dropped_by_clean,) cleaned, removed by
    dedup, dropped by F2, final. F2 errors have no column: the runner stops when F2 reports any ("F2 reported no errors"),
    so a finished run has none; stage_ledger's "every per-pack row adds up" check still counts them."""
    chain = {"raw": c["rows"], "dropped_by_clean": c["dropped_by_clean"]} if clean_mode == "B" else {}
    chain.update(cleaned=c["rows_cleaned"], removed_by_dedup=c["removed_by_dedup"], dropped_by_f2=c["dropped_by_f2"],
                 final=c["kept"])
    return chain


def pack_table(by_pack):
    """The per-pack chain as a plain-text table, with a total row ("" when there is nothing to show)."""
    first = next((r for sps in by_pack.values() for r in sps.values()), None)
    if first is None:
        return ""
    cols = list(first)
    head = {"raw": "raw", "dropped_by_clean": "-clean", "cleaned": "cleaned", "removed_by_dedup": "-dedup",
            "dropped_by_f2": "-f2", "final": "final"}
    rows = [(pack, split, [r[c] for c in cols]) for pack in sorted(by_pack)
            for split, r in sorted(by_pack[pack].items(), key=lambda kv: SPLITS.index(kv[0]) if kv[0] in SPLITS else 9)]
    rows.append(("total", "", [sum(r[2][i] for r in rows) for i in range(len(cols))]))
    w = max(len("pack"), *(len(r[0]) for r in rows))
    nums = [max(len(head[c]), *(len(f"{r[2][i]:,}") for r in rows)) for i, c in enumerate(cols)]
    line = lambda a, b, vals: f"{a:<{w}}  {b:<7}  " + "  ".join(f"{v:>{n}}" for v, n in zip(vals, nums))
    out = [line("pack", "split", [head[c] for c in cols])]
    out += [line(a, b, [f"{v:,}" for v in vals]) for a, b, vals in rows]
    return "\n".join(out)


def git_commit():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip() or None
    except OSError:
        return None


def pyarrow_version():
    try:
        import pyarrow
        return pyarrow.__version__
    except ImportError:
        return None


def run(config, start=None, to=None):
    """start and to default to the config's "from" and "to"; the arguments are for tests and scripts, not the command line."""
    return Run(config).execute(start, to)


def plan(config, to=None):
    return Run(config).plan(to)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, required=True, help="the run config (JSON): every run parameter is in this file")
    ap.add_argument("--plan", action="store_true", help="check the config and print every stage's folder and command; run nothing")
    args = ap.parse_args()
    try:
        if args.plan:
            print(plan(args.config))
            return
        m = run(args.config)
    except Stop as e:
        sys.exit(f"run_pipeline: {e}")
    print(json.dumps(m["totals"]))


if __name__ == "__main__":
    main()
