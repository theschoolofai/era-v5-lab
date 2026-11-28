#!/usr/bin/env python3
"""The checkpoint loop as one restartable command: strip to weights, score the full copy, quantize and score each format, report the gap.

    python teams/12-quantization/scripts/run_loop.py --run-dir <store>/<run_id> [--step N] --manifest <G5 manifest.json> \\
        --tokenizer ./inputs/tokenizer.json --out ./out/loop --work ./work [--watcher-json <Team 9's v1 file>] \\
        [--scorer lm_eval_lab:team5 <Team 9's scorer arguments>] [--qe-args <quantize_eval.py arguments>]
    python teams/12-quantization/scripts/run_loop.py --weights model.safetensors --manifest manifest.json --tokenizer ... --out ...

Stages (each one writes <out>/stages/<name>.json when it is done; a rerun skips a stage whose marker has the same version and
the same key, so a changed setting or a bumped STAGES version reruns that stage and the ones after it, nothing before):
  strip       a store commit -> <out>/weights/model.safetensors with Team 7's export_safetensors (every key and the file hash
              checked), the way Team 9's run_lab_ckpt.py does it; or --weights, hashed and linked. The sha256 is recorded.
  score_full  run_lab_ckpt.py on the same commit (Team 9's scorer, eval-mini v1 JSON). Store input only. Compared with
              --watcher-json (the watcher's v1 file for this commit) when given; the report says so when it is absent.
  q_<format>  quantize_eval.py --formats <format> on the weights: export (test A1), bf16 GGUF, test A3, quantize, then the
              --eval items through llama-server. bf16 is the baseline of the gap.
  mini_<format>  eval-mini (G9's mini profile) on that GGUF through eval_mini/run_mini_gguf.py (llama-cpp-python, one runtime for
              every format, so the gap to bf16 is the quantization). Needs --mini-python, a venv with llama-cpp-python 0.3.36, lm_eval
              0.4.13 and datasets, and the datasets once from the network. The quantized GGUF is kept until its mini stage is done.
  report      always rebuilt: <out>/gap.md and gap.json (one row per format, one column per kind of item) and <out>/loop_log.jsonl.

KAS V2 checkpoints need --drop-head-bias --drop-router-bias (quantize_eval.py's flags); the table carries them as a label.
Other arguments of quantize_eval.py go after --qe-args; arguments this script does not know go to run_lab_ckpt.py.
"""
from __future__ import annotations

import argparse, hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEAMS = HERE.parents[1]
LAB = TEAMS / '09-evaluation' / 'harness_lab'
FORMATS = 'bf16,Q8_0,Q6_K,Q5_K_M,Q4_K_M'
EVAL_MINI = HERE.parent / 'eval_mini'
G9_HARNESS = TEAMS / '09-evaluation' / 'harness' / 'run_eval_mini.py'
# the English tasks of docs/bitwidth_proposal.md v2's evidence (eval_wide: MMLU, ARC-Challenge) that G9's mini profile also has;
# Belebele and MILU are not in that profile, and HellaSwag, GSM8K and TruthfulQA are in it but were not v2 evidence
MINI_TASKS = 'mmlu,arc_challenge'
STAGES = dict(strip=1, score_full=1, quantize=1, mini=1, report=1)   # bump a number when that stage's logic changes: only it and what follows rerun


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def key_of(*parts) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()[:16]


class Loop:
    def __init__(self, out: Path):
        self.out = out; out.mkdir(parents=True, exist_ok=True)
        (out / 'stages').mkdir(exist_ok=True)

    def note(self, **kw):
        with open(self.out / 'loop_log.jsonl', 'a', encoding='utf-8') as f:
            f.write(json.dumps(dict(ts=time.strftime('%Y-%m-%dT%H:%M:%S'), **kw)) + '\n')
        print(' '.join(f'{k}={v}' for k, v in kw.items()), flush=True)

    def marker(self, name: str) -> dict | None:
        p = self.out / 'stages' / f'{name}.json'
        return json.loads(p.read_text(encoding='utf-8')) if p.exists() else None

    def done(self, name: str, version: int, key: str) -> bool:
        m = self.marker(name)
        return bool(m and m['version'] == version and m['key'] == key and all((self.out / f).exists() for f in m['files']))

    def run(self, name: str, version: int, key: str, fn):
        """Run fn() -> dict (files, commands, facts) unless the stage's marker has this version and key and its files exist."""
        m = self.marker(name)
        if m and m['version'] == version and m['key'] == key and all((self.out / f).exists() for f in m['files']):
            self.note(stage=name, event='skip', reason='marker has the same version and key')
            return m
        why = 'no marker' if not m else ('version changed' if m['version'] != version else 'key changed' if m['key'] != key else 'files missing')
        self.note(stage=name, event='start', reason=why)
        t = time.time()
        done = dict(fn(), stage=name, version=version, key=key, seconds=round(time.time() - t, 1))
        tmp = self.out / 'stages' / f'{name}.json.tmp'
        tmp.write_text(json.dumps(done, indent=2) + '\n', encoding='utf-8')
        tmp.replace(self.out / 'stages' / f'{name}.json')   # written last and atomically: a killed stage leaves no marker
        self.note(stage=name, event='done', seconds=done['seconds'])
        return done


def sh(cmd: list, **kw) -> str:
    cmd = [str(c) for c in cmd]
    print('$', ' '.join(cmd), flush=True)
    if subprocess.run(cmd, **kw).returncode:
        sys.exit(f'stopped: {Path(cmd[1]).name} failed (exit code above); a rerun resumes at this stage')
    return ' '.join(cmd)


def strip(a, loop: Loop, rest: list) -> dict:
    """The weights file for the rest of the loop: out/weights/model.safetensors (+ manifest.json)."""
    w = loop.out / 'weights'; w.mkdir(exist_ok=True)
    dst = w / 'model.safetensors'
    if a.run_dir:
        import torch
        sys.path.insert(0, str(LAB))
        import run_lab_ckpt as rlc
        from ckpt.ckpt import export_safetensors
        scorer = rlc.SmokeScorer(a) if a.scorer == 'smoke' else rlc.load_scorer(a.scorer)(rest)
        run_dir = a.run_dir.resolve()
        facts = rlc.checkpoint_facts(run_dir, a.run_dir.as_posix().rstrip('/'), rlc.read_pointer(run_dir, a.step), None)
        scorer.check(facts['manifest'])
        os.environ.setdefault('V5_EVENTS_DIR', str(loop.out / 'events'))
        was = torch.are_deterministic_algorithms_enabled(); threads = torch.get_num_threads()
        torch.use_deterministic_algorithms(True); torch.set_num_threads(1)   # the settings the saved probe-loss bits were made with
        try:
            dst.unlink(missing_ok=True)
            info = export_safetensors(run_dir.as_posix(), scorer.factory, scorer.probe, str(dst), step=facts['checkpoint']['step'])
        finally:
            torch.use_deterministic_algorithms(was); torch.set_num_threads(threads)
        what = dict(source=str(a.run_dir), step=info['step'], model_revision=facts['model_revision'], via='ckpt.export_safetensors')
    else:
        dst.unlink(missing_ok=True); dst.symlink_to(a.weights.resolve())
        what = dict(source=str(a.weights), via='symlink to the given file')
    if a.manifest:
        (w / 'manifest.json').write_bytes(a.manifest.read_bytes())
    return dict(files=['weights/model.safetensors'], weights_sha256=sha256(dst), **what)


def score_full(a, loop: Loop, rest: list, weights_sha: str) -> dict:
    out = loop.out / 'score_full.v1.json'
    cmd = [sys.executable, LAB / 'run_lab_ckpt.py', '--run-dir', a.run_dir, '--scorer', a.scorer, '--out', out, '--device', 'cpu',
           *(['--step', a.step] if a.step is not None else []), *rest]
    if a.scorer == 'smoke': cmd += ['--config', a.config, '--tiny', a.tiny, '--steps', a.steps]
    return dict(files=['score_full.v1.json'], command=sh(cmd), weights_sha256=weights_sha)


def quantize(a, loop: Loop, fmt: str, weights: Path, qe_args: list) -> dict:
    scores = f'q/{fmt}/scores.json'
    (loop.out / 'q' / fmt).mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, HERE / 'quantize_eval.py', '--checkpoint', weights, '--tokenizer', a.tokenizer, '--eval', a.eval,
           '--formats', fmt, '--work', a.work, '--runs-csv', loop.out / 'runs.csv', '--scores-out', loop.out / scores,
           '--verify', a.verify, '--name', 'loop', *([] if a.hold_gguf else ['--cleanup']),
           *(['--spec', loop.out / 'weights' / 'manifest.json'] if a.manifest else []),
           *(['--tokenizer-sha256', a.tokenizer_sha256] if a.tokenizer_sha256 else []),
           *(['--drop-router-bias'] if a.drop_router_bias else []), *(['--drop-head-bias'] if a.drop_head_bias else []), *qe_args]
    return dict(files=[scores], command=sh(cmd))


def mini(a, loop: Loop, fmt: str, key: str) -> dict:
    """eval-mini on one GGUF (the file quantize_eval.py measured; its sha256 is in the key)."""
    q = json.loads((loop.out / f'q/{fmt}/scores.json').read_text(encoding='utf-8'))['formats'][0]
    gguf = Path(q['file'])
    out = loop.out / 'mini'; fdir = out / fmt
    kf = fdir / 'key.txt'
    if not (kf.exists() and kf.read_text() == key):   # a partial run of the same key resumes task by task; any other leftovers are stale
        shutil.rmtree(fdir, ignore_errors=True); fdir.mkdir(parents=True); kf.write_text(key)
    guard = subprocess.run([a.mini_python, str(EVAL_MINI / 'test_llamacpp_lm.py'), str(gguf)], capture_output=True, text=True)
    tail = (guard.stdout + guard.stderr).strip().splitlines()[-3:]
    cmd = [a.mini_python, EVAL_MINI / 'run_mini_gguf.py', '--gguf', gguf, '--format', fmt, '--out', out, '--g9-harness', a.g9_harness,
           '--tasks', *a.mini_tasks.split(','), '--n-gpu-layers', a.mini_ngl, '--model', f'lab:{q["sha256"][:8]}', '--revision', q['sha256'],
           *(['--limit', a.mini_limit] if a.mini_limit is not None else [])]
    return dict(files=[f'mini/{fmt}/summary.json'], command=sh(cmd), gguf_sha256=q['sha256'], guard_exit=guard.returncode, guard_tail=tail)


def guard_label(a) -> str:
    drops = [f for f, on in (('--drop-router-bias', a.drop_router_bias), ('--drop-head-bias', a.drop_head_bias)) if on]
    return 'strict: nothing set aside' if not drops else f'RELAXED: {" ".join(drops)} (the GGUF is not the checkpoint as trained; every gap is against the bf16 GGUF of the same export)'


def v1_records(path: Path) -> dict:
    return {(r['task'], r['metric'], r['filter']): r['value'] for r in json.loads(path.read_text(encoding='utf-8'))['records']}


def report(a, loop: Loop, formats: list, strip_m: dict) -> dict:
    rows, kinds = [], set()
    for f in formats:
        m = loop.marker(f'q_{f}')
        if not m: continue
        s = json.loads((loop.out / m['files'][0]).read_text(encoding='utf-8'))
        r = s['formats'][0]; kinds |= set(r['score_by_kind'])
        rows.append(dict(format=f, score=r['score'], by_kind=r['score_by_kind'], size_gb=r['size_gb'], bpw=r['bpw'], tok_s=r['gen_tok_s'],
                         n_items=r['n_items'], sha256=r['sha256'], source=m['files'][0], command=m['command'],
                         a1=(s.get('export_a1') or {}).get('passed'), a1_zero=(s.get('export_a1_zero_router_bias') or {}).get('passed'), a3=(s.get('gguf_a3') or {}).get('passed')))
    base = next((r for r in rows if r['format'] == 'bf16'), None)
    for r in rows:
        r['gap'] = None if not base else round(r['score'] - base['score'], 4)
        r['gap_by_kind'] = {k: None if not base else round(r['by_kind'].get(k, 0) - base['by_kind'].get(k, 0), 4) for k in sorted(kinds)}
    mini_doc, mini_tasks = {}, []
    for r in rows:
        m = loop.marker(f'mini_{r["format"]}')
        if not m: continue
        recs = json.loads((loop.out / m['files'][0]).read_text(encoding='utf-8'))['records']
        for x in recs:
            if x.get('primary'):
                if x['task'] not in mini_tasks: mini_tasks.append(x['task'])
                mini_doc.setdefault(x['task'], {})[r['format']] = dict(metric=x['metric'], value=x['value'], stderr=x['stderr'], n_items=x['n_items'],
                                                                      command=m['command'], guard_exit=m['guard_exit'], source=m['files'][0])
    for task, d in mini_doc.items():
        b = d.get('bf16')
        for f, x in d.items():
            x['gap'] = None if not b or f == 'bf16' else round(x['value'] - b['value'], 4)
            x['gap_se_unpaired'] = None if x['gap'] is None or None in (x['stderr'], b['stderr']) else round((x['stderr'] ** 2 + b['stderr'] ** 2) ** .5, 4)
    full = None
    if (loop.out / 'score_full.v1.json').exists():
        full = v1_records(loop.out / 'score_full.v1.json')
    watcher = None
    if a.watcher_json:
        w = v1_records(a.watcher_json)
        if full is None: watcher = dict(status='not compared: this run has no score_full (needs a store input)', file=str(a.watcher_json))
        else:
            diffs = {f'{k[0]}/{k[1]}/{k[2]}': (full[k], w.get(k)) for k in full}
            watcher = dict(status='match' if all(v[1] == v[0] for v in diffs.values()) else 'DIFFERENT', file=str(a.watcher_json),
                           loop_vs_watcher=diffs, source='score_full.v1.json vs the watcher file')
    else:
        watcher = dict(status='no watcher score given (--watcher-json): not compared')
    doc = dict(weights_sha256=strip_m['weights_sha256'], guards=guard_label(a), formats=rows, score_full=({f'{k[0]}/{k[1]}/{k[2]}': v for k, v in full.items()} if full else None),
               watcher=watcher, eval_mini=mini_doc, model_note=a.model_note, eval=str(a.eval), eval_sha256=sha256(Path(a.eval)))
    (loop.out / 'gap.json').write_text(json.dumps(doc, indent=2) + '\n', encoding='utf-8')
    kl = sorted(kinds)
    md = [f'# Gap table', '', *([f'> {a.model_note}', ''] if a.model_note else []), f'weights sha256 `{doc["weights_sha256"]}` (stages/strip.json)', f'guards: {doc["guards"]}',
          f'own 20 items (G12 own, through llama-server; NOT eval-mini): `{a.eval}` sha256 `{doc["eval_sha256"][:16]}`; score = fraction correct, gap = format minus bf16 GGUF, from each q/<format>/scores.json', '',
          '| format | size GB | bpw | n | score | gap | ' + ' | '.join(f'{k} gap' for k in kl) + ' | tok/s | A1 as trained | A1 router_bias zeroed | A3 |',
          '|' + '---|' * (10 + len(kl))]
    for r in rows:
        md.append(f'| {r["format"]} | {r["size_gb"]} | {r["bpw"]} | {r["n_items"]} | {r["score"]} | {r["gap"]:+} | ' +
                  ' | '.join(f'{r["gap_by_kind"][k]:+}' for k in kl) + f' | {r["tok_s"]} | {r["a1"]} | {r["a1_zero"]} | {r["a3"]} |' if base else f'| {r["format"]} | no bf16 row |')
    if mini_doc:
        md += ['', f'## eval-mini (G9 mini profile via eval_mini/run_mini_gguf.py, llama-cpp-python, one runtime for every format; gap = format minus bf16 GGUF, '
               'se = the standard error eval-mini reports; the gap se is the unpaired sqrt(se_format^2 + se_bf16^2))', '',
               '| task | metric | format | n | score | se | gap | gap se | guard exit |', '|---|---|---|---|---|---|---|---|---|']
        for task in mini_tasks:
            for f, x in mini_doc[task].items():
                g = lambda v: '-' if v is None else v
                md.append(f'| {task} | {x["metric"]} | {f} | {x["n_items"]} | {x["value"]} | {g(x["stderr"])} | {g(x["gap"])} | {g(x["gap_se_unpaired"])} | {x["guard_exit"]} |')
        md += ['', 'Commands: ' + '; '.join(f'`{mini_doc[mini_tasks[0]][f]["command"]}`' for f in mini_doc[mini_tasks[0]])]
    md += ['', f'Full copy (Team 9 scorer, score_full.v1.json): {doc["score_full"] or "not scored (needs a store input)"}',
           f'Watcher: {watcher["status"]}' + (f' {watcher.get("loop_vs_watcher", "")}' if watcher.get('loop_vs_watcher') else ''), '', 'Commands:']
    md += [f'- {r["format"]}: `{r["command"]}`' for r in rows]
    (loop.out / 'gap.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))
    return dict(files=['gap.md', 'gap.json'])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0], epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument('--run-dir', type=Path, help='a store run folder (latest.json, commits.jsonl), as run_lab_ckpt.py reads it')
    src.add_argument('--weights', type=Path, help='a model.safetensors of a G5 model (needs --manifest)')
    ap.add_argument('--step', type=int); ap.add_argument('--manifest', type=Path, help="the run's manifest.json (config.model): quantize_eval.py's --spec")
    ap.add_argument('--scorer', default='smoke', help='run_lab_ckpt.py --scorer (its other arguments go through as they are)')
    ap.add_argument('--config', type=Path, default=TEAMS / '05-architecture/configs/config_v0.yaml'); ap.add_argument('--tiny', type=Path, default=TEAMS / '05-architecture/configs/small/tiny_moe.yaml')
    ap.add_argument('--steps', type=int, default=200)
    ap.add_argument('--tokenizer', required=True); ap.add_argument('--tokenizer-sha256')
    ap.add_argument('--eval', default=str(HERE.parent / 'prompts/eval_own_20.json'))
    ap.add_argument('--formats', default=FORMATS, help='bf16 first; one stage each')
    ap.add_argument('--stages', help='default: strip,score_full,quantize,report, and mini when --mini-python is given'); ap.add_argument('--verify', type=int, default=16)
    ap.add_argument('--mini-python', help="a venv's python with llama-cpp-python==0.3.36, lm_eval==0.4.13, datasets (the mini stage runs in it)")
    ap.add_argument('--mini-tasks', default=MINI_TASKS, help='comma list from G9\'s mini profile; default: the English tasks of the bit-width proposal v2 evidence')
    ap.add_argument('--mini-limit', type=int, help='override every task\'s item limit (smoke tests only)'); ap.add_argument('--mini-ngl', type=int, default=0, help='layers on the GPU (0: CPU)')
    ap.add_argument('--g9-harness', default=str(G9_HARNESS)); ap.add_argument('--keep-gguf', action='store_true', help='keep every quantized GGUF after its stages')
    ap.add_argument('--model-note', help='one line printed on top of the gap table, e.g. that the model is too weak for the scores to mean anything')
    ap.add_argument('--drop-router-bias', action='store_true'); ap.add_argument('--drop-head-bias', action='store_true')
    ap.add_argument('--watcher-json', type=Path, help="Team 9's eval-mini v1 file for this checkpoint")
    ap.add_argument('--out', type=Path, required=True); ap.add_argument('--work', default=str(Path.home() / '.cache/era-v5-quant'))
    ap.add_argument('--qe-args', nargs=argparse.REMAINDER, default=[])
    a, rest = ap.parse_known_args(argv)
    formats = a.formats.split(',')
    if formats[0] != 'bf16': ap.error('--formats must start with bf16: it is the baseline of the gap')
    todo = (a.stages or 'strip,score_full,quantize,report' + (',mini' if a.mini_python else '')).split(',')
    if 'mini' in todo and not a.mini_python: ap.error('the mini stage needs --mini-python')
    a.hold_gguf = a.keep_gguf or 'mini' in todo   # the mini stage reads the quantized GGUF; the loop deletes it after that stage
    loop = Loop(a.out)
    loop.note(event='loop', guards=guard_label(a), formats=a.formats)
    tok = sha256(Path(a.tokenizer))
    src_key = (str(a.run_dir or a.weights), a.step, sha256(a.weights) if a.weights else None)   # a store's commits are keyed by what strip reads
    if a.run_dir:
        ptr = json.loads((a.run_dir / 'latest.json').read_text()) if a.step is None else {}   # the commit it names, not the claim's timestamps
        src_key += (ptr.get('path'), ptr.get('step'))
    s = loop.run('strip', STAGES['strip'], key_of(src_key, a.scorer, rest), lambda: strip(a, loop, rest)) if 'strip' in todo else loop.marker('strip')
    if a.run_dir and 'score_full' in todo:
        loop.run('score_full', STAGES['score_full'], key_of(s['weights_sha256'], a.scorer, rest), lambda: score_full(a, loop, rest, s['weights_sha256']))
    if 'quantize' in todo:
        for f in formats:
            qk = key_of(s['weights_sha256'], f, tok, sha256(Path(a.eval)), a.verify, a.drop_router_bias, a.drop_head_bias, a.qe_args, a.manifest and sha256(a.manifest))
            qk = key_of(qk, a.hold_gguf)
            runq = lambda f=f, qk=qk: loop.run(f'q_{f}', STAGES['quantize'], qk, lambda: quantize(a, loop, f, loop.out / 'weights' / 'model.safetensors', a.qe_args))
            runq()
            if 'mini' in todo:
                def mini_key():
                    q = json.loads((loop.out / f'q/{f}/scores.json').read_text(encoding='utf-8'))['formats'][0]
                    return q, key_of(q['sha256'], a.mini_tasks, a.mini_limit, a.mini_ngl, sha256(Path(a.g9_harness)),
                                     [sha256(EVAL_MINI / n) for n in ('run_mini_gguf.py', 'llamacpp_lm.py', 'test_llamacpp_lm.py')])
                q, mk = mini_key()
                if not loop.done(f'mini_{f}', STAGES['mini'], mk) and not Path(q['file']).exists():   # a changed mini setting after the GGUF was deleted
                    (loop.out / 'stages' / f'q_{f}.json').unlink(); runq(); q, mk = mini_key()   # rebuild it (bf16 is still there); the new file's sha is in the key
                loop.run(f'mini_{f}', STAGES['mini'], mk, lambda f=f, mk=mk: mini(a, loop, f, mk))
                if f != 'bf16' and not a.keep_gguf: Path(q['file']).unlink(missing_ok=True)   # bf16 stays: every format is made from it
    if 'report' in todo:
        report(a, loop, formats, s)
        loop.note(stage='report', event='done')
    return 0


if __name__ == '__main__':
    sys.exit(main())
