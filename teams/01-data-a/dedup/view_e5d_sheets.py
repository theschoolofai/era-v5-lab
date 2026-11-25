r"""E5d's reader viewer: one local web page where a bilingual reader labels their reader sheets (h3_e5d_sheets.py).

Each item of a sheet shows two texts in two languages, text_1 and text_2, one sentence per line. The reader decides
whether one is a translation of the other: yes, no or unsure, with an optional note. The sheets are blind (no score,
encoder, pack or doc_id), and the page adds nothing: it shows the item ID and the two texts only.

HOW TO RUN IT
=============
Python 3 only (standard library, nothing to install). Put the sheets you were sent in a folder of their own, then,
from the repository root:

    python3 teams/01-data-a/dedup/view_e5d_sheets.py --sheets ../my-e5d/sheets --name "Your Name"

On Windows use python instead of python3, and backslashes in the paths. Then open http://127.0.0.1:8000.

  --sheets      the folder with your sheets: <pair>_reader<k>.csv (e.g. sa-en_reader1.csv) and readers_guide.md
  --labels-dir  where your answers are saved (default: e5d_labels next to the sheets folder; created if missing)
  --name        your name, for the answer files (spaces become _)
  --port        default 8000; --host default 127.0.0.1, so the page is reachable from this computer only

THE PAGE
========
  - The sidebar lists your sheets, each with answered / total. Click one to open it.
  - Each item: text_1 and text_2 side by side, buttons yes / no / unsure (keys y, n, u), a note box.
  - Keys: right arrow or Enter = next item, left arrow = previous, j = next unanswered, Ctrl+S or Cmd+S = save.
  - "save" is orange while there are unsaved answers. Unsaved answers are also kept in the browser, so switching
    sheets or reloading the page loses nothing; they reach your answer files only when you save.
  - The sidebar marks sheets with unsaved answers. The readers' guide (what yes, no and unsure mean) is at the top of
    the page: open until you give a first answer, then folded (click it to open).

WHAT IT WRITES
==============
  <labels-dir>/<pair>-reader<k>-<name>.csv   item, translation, note: one row per item of the sheet, in its order,
                                             empty where not answered yet. No document text: these are the files to
                                             send back. Saving again rewrites the file (written to a temporary file,
                                             then renamed, so a crash cannot leave half a file).
Answers already in a sheet's own translation and note columns (typed in a spreadsheet) are loaded until the first save.

This is an interactive tool over one reader's sheets (tens to hundreds of items), not a pipeline stage: its plain
Python loops over a sheet's rows are fine for that.
"""
import sys
sys.dont_write_bytecode = True

import argparse, csv, io, json, os, re, secrets, tempfile, threading  # noqa: E401,E402
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer  # noqa: E402
from pathlib import Path  # noqa: E402
from urllib.parse import parse_qs, urlparse  # noqa: E402

SHEET_COLUMNS = ["item", "text_1", "text_2", "translation", "note"]   # h3_e5d_sheets.py's sheet
LABEL_COLUMNS = ["item", "translation", "note"]
ANSWERS = ("yes", "no", "unsure")
SHEET_NAME = re.compile(r"^(?P<pair>[a-z]{2,3}-[a-z]{2,3})_reader(?P<reader>\d+)\.csv$")
MAX_NOTE = 2000
MAX_BODY = 2_000_000
LOCAL_HOSTS = {"127.0.0.1", "localhost", "[::1]"}


class SheetError(ValueError):
    """A sheet, an answer file or an answer that cannot be used."""


def clean_name(name):
    name = re.sub(r"\s+", "_", (name or "").strip())
    if name and not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
        raise SheetError("--name may hold letters, digits, spaces, '.', '_' and '-' only")
    return name


def clean_answer(answer, where):
    """An answer as saved: translation lowercased (yes, no, unsure or empty), note as text."""
    if not isinstance(answer, dict):
        raise SheetError(f"{where}: an answer must be an object")
    t = str(answer.get("translation") or "").strip().lower()
    note = answer.get("note") or ""
    if t not in ("",) + ANSWERS:
        raise SheetError(f"{where}: translation must be yes, no or unsure, not {t!r}")
    if not isinstance(note, str) or len(note) > MAX_NOTE:
        raise SheetError(f"{where}: note must be text of at most {MAX_NOTE} characters")
    return {"translation": t, "note": note.replace("\r\n", "\n").replace("\r", "\n")}


def read_sheet(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != SHEET_COLUMNS:
            raise SheetError(f"{path.name}: columns {reader.fieldnames}, not {SHEET_COLUMNS}")
        rows = list(reader)
    ids = [r["item"] for r in rows]
    if not rows or any(not i for i in ids) or len(set(ids)) != len(ids):
        raise SheetError(f"{path.name}: every item needs a distinct, nonempty ID")
    return rows


def read_labels(path):
    """{item: answer} from an answer file, or None if there is none yet."""
    if not path.is_file():
        return None
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != LABEL_COLUMNS:
            raise SheetError(f"{path}: columns {reader.fieldnames}, not {LABEL_COLUMNS}")
        return {r["item"]: clean_answer(r, f"{path.name} {r['item']}") for r in reader}


def labels_path(labels_dir, pair, reader, name):
    return Path(labels_dir) / (f"{pair}-reader{reader}" + (f"-{name}" if name else "") + ".csv")


def discover(sheets_dir, labels_dir, name):
    """The reader's sheets: [{key, pair, reader, items, answers, out}], in file-name order."""
    sheets = []
    for path in sorted(Path(sheets_dir).glob("*.csv")):          # the reader's sheet files
        m = SHEET_NAME.match(path.name)
        if not m:
            continue
        rows = read_sheet(path)
        out = labels_path(labels_dir, m["pair"], m["reader"], name)
        saved = read_labels(out)
        if saved is None:                                         # answers typed into the sheet count until a save
            saved = {r["item"]: clean_answer(r, f"{path.name} {r['item']}") for r in rows}
        ids = {r["item"] for r in rows}
        unknown = sorted(set(saved) - ids)
        if unknown:
            raise SheetError(f"{out}: items not in {path.name}: {unknown[:3]}")
        sheets.append({"key": path.stem, "pair": m["pair"], "reader": int(m["reader"]), "out": out,
                       "items": [{"item": r["item"], "text_1": r["text_1"], "text_2": r["text_2"]} for r in rows],
                       "answers": {r["item"]: saved.get(r["item"], {"translation": "", "note": ""}) for r in rows}})
    if not sheets:
        raise SheetError(f"no sheets (<pair>_reader<k>.csv) in {sheets_dir}")
    return sheets


def done(sheet):
    return sum(1 for a in sheet["answers"].values() if a["translation"])


def save(sheet, answers):
    """Merge answers into the sheet's and rewrite its answer file; returns how many items are answered."""
    if not isinstance(answers, dict):
        raise SheetError("answers must be an object {item: {translation, note}}")
    unknown = sorted(set(answers) - set(sheet["answers"]))
    if unknown:
        raise SheetError(f"items not in this sheet: {unknown[:3]}")
    merged = {**sheet["answers"], **{i: clean_answer(a, i) for i, a in answers.items()}}
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(LABEL_COLUMNS)
    for it in sheet["items"]:                                     # one row per item, in the sheet's order
        a = merged[it["item"]]
        w.writerow([it["item"], a["translation"], a["note"]])
    out = sheet["out"]
    out.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=out.parent, prefix=f".{out.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(buf.getvalue())
        os.replace(tmp, out)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    sheet["answers"] = merged
    return done(sheet)


class App:
    def __init__(self, sheets, guide):
        self.sheets, self.guide = sheets, guide
        self.by_key = {s["key"]: s for s in sheets}
        self.token = secrets.token_hex(16)
        self.lock = threading.Lock()


def make_handler(app):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, code, body, ctype):
            data = body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(data)

        def json(self, code, obj):
            self.reply(code, json.dumps(obj, ensure_ascii=False), "application/json; charset=utf-8")

        def local(self):
            host = (self.headers.get("Host") or "").rsplit(":", 1)[0]
            if host not in LOCAL_HOSTS:
                self.json(403, {"error": "open the page at http://127.0.0.1"})
                return False
            return True

        def do_GET(self):
            if not self.local():
                return
            url = urlparse(self.path)
            if url.path == "/":
                return self.reply(200, PAGE.replace("__TOKEN__", app.token), "text/html; charset=utf-8")
            if url.path == "/api/sheets":
                return self.json(200, {"guide": app.guide, "sheets": [
                    {"key": s["key"], "pair": s["pair"], "reader": s["reader"], "total": len(s["items"]),
                     "done": done(s), "file": s["out"].name} for s in app.sheets]})
            if url.path == "/api/sheet":
                s = app.by_key.get(parse_qs(url.query).get("key", [""])[0])
                if s is None:
                    return self.json(404, {"error": "no such sheet"})
                return self.json(200, {"key": s["key"], "pair": s["pair"], "items": s["items"],
                                       "answers": s["answers"], "file": s["out"].name})
            self.json(404, {"error": "not found"})

        def do_POST(self):
            if not self.local():
                return
            if urlparse(self.path).path != "/api/save":
                return self.json(404, {"error": "not found"})
            if self.headers.get("X-E5d-Token") != app.token:
                return self.json(403, {"error": "reload the page"})
            n = int(self.headers.get("Content-Length") or 0)
            if n > MAX_BODY:
                return self.json(413, {"error": "too large"})
            try:
                body = json.loads(self.rfile.read(n) or b"{}")
            except ValueError:
                return self.json(400, {"error": "not JSON"})
            s = app.by_key.get(body.get("key", "")) if isinstance(body, dict) else None
            if s is None:
                return self.json(404, {"error": "no such sheet"})
            try:
                with app.lock:
                    n_done = save(s, body.get("answers"))
            except SheetError as e:
                return self.json(400, {"error": str(e)})
            self.json(200, {"file": s["out"].name, "done": n_done, "total": len(s["items"])})
    return Handler


def make_server(app, host="127.0.0.1", port=8000):
    return ThreadingHTTPServer((host, port), make_handler(app))


PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>E5d reader sheets</title>
<style>
  :root { --bg:#fafafa; --fg:#1d1d1f; --muted:#6b6b70; --line:#d9d9de; --card:#fff; --accent:#2f6fde;
          --yes:#1f8a4c; --no:#c0392b; --unsure:#8a6d1f; --warn:#d18616; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--fg);
         font:15px/1.5 system-ui, -apple-system, "Segoe UI", "Noto Sans", "Noto Sans Devanagari", sans-serif; }
  header { display:flex; gap:12px; align-items:center; padding:10px 16px; border-bottom:1px solid var(--line);
           background:var(--card); position:sticky; top:0; z-index:2; flex-wrap:wrap; }
  header h1 { font-size:16px; margin:0 12px 0 0; }
  #progress { color:var(--muted); }
  #save { margin-left:auto; padding:6px 14px; border:1px solid var(--line); border-radius:6px; background:var(--card);
          cursor:pointer; font:inherit; }
  #save.unsaved { background:var(--warn); border-color:var(--warn); color:#000; font-weight:600; }
  #layout { display:grid; grid-template-columns:220px 1fr; min-height:calc(100vh - 52px); }
  nav { border-right:1px solid var(--line); padding:12px; background:var(--card); }
  nav button { display:block; width:100%; text-align:left; padding:8px 10px; margin:0 0 6px; border:1px solid var(--line);
               border-radius:6px; background:var(--card); cursor:pointer; font:inherit; }
  nav button.current { border-color:var(--accent); box-shadow:inset 3px 0 0 var(--accent); }
  nav .count { color:var(--muted); font-size:13px; }
  nav .unsavedmark { color:var(--warn); font-weight:600; }
  main { padding:16px; max-width:1400px; }
  details { background:var(--card); border:1px solid var(--line); border-radius:8px; padding:8px 12px; margin-bottom:14px; }
  details pre { white-space:pre-wrap; font:inherit; margin:8px 0 0; }
  #itemhead { display:flex; gap:12px; align-items:baseline; margin-bottom:10px; }
  #itemhead b { font-size:17px; }
  #texts { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
  .text { background:var(--card); border:1px solid var(--line); border-radius:8px; padding:12px 14px; min-height:200px; }
  .text h2 { font-size:13px; color:var(--muted); margin:0 0 6px; text-transform:uppercase; letter-spacing:.04em; }
  .text div { white-space:pre-wrap; font-size:17px; line-height:1.7; overflow-wrap:anywhere; }
  #answer { display:flex; gap:10px; margin:14px 0 8px; flex-wrap:wrap; }
  #answer button { padding:8px 18px; border-radius:6px; border:2px solid var(--line); background:var(--card); cursor:pointer;
                   font:inherit; font-weight:600; }
  #answer button[data-v=yes].on { background:var(--yes); border-color:var(--yes); color:#fff; }
  #answer button[data-v=no].on { background:var(--no); border-color:var(--no); color:#fff; }
  #answer button[data-v=unsure].on { background:var(--unsure); border-color:var(--unsure); color:#fff; }
  textarea { width:100%; min-height:60px; font:inherit; padding:8px; border:1px solid var(--line); border-radius:6px; }
  #navbtns { display:flex; gap:8px; margin-top:10px; flex-wrap:wrap; }
  #navbtns button { padding:6px 12px; border:1px solid var(--line); border-radius:6px; background:var(--card); cursor:pointer; font:inherit; }
  #msg { color:var(--muted); margin-left:8px; }
  kbd { border:1px solid var(--line); border-bottom-width:2px; border-radius:4px; padding:0 4px; font-size:12px; }
  @media (max-width: 900px) { #layout { grid-template-columns:1fr; } nav { border-right:0; border-bottom:1px solid var(--line); }
                              #texts { grid-template-columns:1fr; } }
</style></head>
<body>
<header><h1>E5d reader sheets</h1><span id="sheetname"></span><span id="progress"></span>
  <button id="save" title="Ctrl+S / Cmd+S">save</button></header>
<div id="layout">
  <nav id="sheets"></nav>
  <main>
    <details id="guidebox"><summary>What to write: the readers' guide</summary><pre id="guide"></pre></details>
    <div id="itemhead"><b id="item"></b><span id="pos"></span></div>
    <div id="texts">
      <div class="text"><h2>text_1</h2><div id="t1"></div></div>
      <div class="text"><h2>text_2</h2><div id="t2"></div></div>
    </div>
    <div id="answer">
      <button data-v="yes">yes <kbd>y</kbd></button>
      <button data-v="no">no <kbd>n</kbd></button>
      <button data-v="unsure">unsure <kbd>u</kbd></button>
    </div>
    <textarea id="note" placeholder="note (optional), e.g. only the first half is translated"></textarea>
    <div id="navbtns">
      <button id="prev">&larr; previous</button><button id="next">next &rarr;</button>
      <button id="nextopen">next unanswered <kbd>j</kbd></button><span id="msg"></span>
    </div>
  </main>
</div>
<script>
const TOKEN = "__TOKEN__";
const $ = id => document.getElementById(id);
let sheets = [], cur = null, items = [], saved = {}, answers = {}, pos = 0;
const lsKey = k => "e5d-unsaved:" + k;
const same = (a, b) => a.translation === b.translation && a.note === b.note;
const copy = o => JSON.parse(JSON.stringify(o));
function dirtyItems() { return items.map(i => i.item).filter(id => !same(answers[id], saved[id])); }
function keep() {
  const d = {}; dirtyItems().forEach(id => d[id] = answers[id]);
  try { Object.keys(d).length ? localStorage.setItem(lsKey(cur), JSON.stringify(d)) : localStorage.removeItem(lsKey(cur)); }
  catch (e) {}
}
function answeredCount() { return items.filter(i => answers[i.item].translation).length; }
function unsavedIn(key) {
  if (key === cur) return dirtyItems().length;
  try { return Object.keys(JSON.parse(localStorage.getItem(lsKey(key)) || "{}")).length; } catch (e) { return 0; }
}
function drawSheets() {
  const nav = $("sheets"); nav.textContent = "";
  sheets.forEach(s => {
    const b = document.createElement("button");
    b.className = s.key === cur ? "current" : "";
    const n = s.key === cur ? answeredCount() : s.done, u = unsavedIn(s.key);
    b.textContent = s.pair + "  (reader " + s.reader + ")";
    const c = document.createElement("div"); c.className = "count"; c.textContent = n + " / " + s.total + " answered";
    if (u) { const w = document.createElement("span"); w.className = "unsavedmark"; w.textContent = " ● " + u + " unsaved";
             c.appendChild(w); }
    b.appendChild(c); b.onclick = () => openSheet(s.key); nav.appendChild(b);
  });
}
function draw() {
  const it = items[pos], a = answers[it.item];
  $("item").textContent = it.item; $("pos").textContent = "item " + (pos + 1) + " of " + items.length;
  $("t1").textContent = it.text_1; $("t2").textContent = it.text_2;
  document.querySelectorAll("#answer button").forEach(b => b.classList.toggle("on", b.dataset.v === a.translation));
  if (document.activeElement !== $("note")) $("note").value = a.note;
  $("progress").textContent = answeredCount() + " / " + items.length + " answered";
  const n = dirtyItems().length, s = $("save");
  s.classList.toggle("unsaved", n > 0); s.textContent = n ? "save (" + n + " unsaved)" : "saved";
  drawSheets();
}
async function openSheet(key) {
  const r = await fetch("/api/sheet?key=" + encodeURIComponent(key)); const j = await r.json();
  cur = key; items = j.items; saved = copy(j.answers); answers = copy(j.answers);
  try { Object.assign(answers, JSON.parse(localStorage.getItem(lsKey(key)) || "{}")); } catch (e) {}
  items.forEach(i => { if (!answers[i.item]) answers[i.item] = {translation: "", note: ""}; });
  $("sheetname").textContent = j.pair + " → " + j.file;
  const open = items.findIndex(i => !answers[i.item].translation); pos = open < 0 ? 0 : open; draw();
}
function setAnswer(v) { const id = items[pos].item; answers[id] = {...answers[id], translation: v}; keep(); draw(); }
function go(d) { pos = Math.max(0, Math.min(items.length - 1, pos + d)); draw(); }
function nextOpen() {
  for (let k = 1; k <= items.length; k++) { const p = (pos + k) % items.length;
    if (!answers[items[p].item].translation) { pos = p; draw(); return; } }
  $("msg").textContent = "every item is answered";
}
async function save() {
  const r = await fetch("/api/save", {method: "POST", headers: {"Content-Type": "application/json", "X-E5d-Token": TOKEN},
                                      body: JSON.stringify({key: cur, answers})});
  const j = await r.json();
  if (!r.ok) { $("msg").textContent = "not saved: " + j.error; return; }
  saved = copy(answers); keep(); sheets.find(s => s.key === cur).done = j.done;
  $("msg").textContent = "saved to " + j.file; draw();
}
document.querySelectorAll("#answer button").forEach(b => b.onclick = () => setAnswer(b.dataset.v));
$("note").oninput = e => { const id = items[pos].item; answers[id] = {...answers[id], note: e.target.value}; keep(); draw(); };
$("prev").onclick = () => go(-1); $("next").onclick = () => go(1); $("nextopen").onclick = nextOpen; $("save").onclick = save;
document.addEventListener("keydown", e => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") { e.preventDefault(); save(); return; }
  if (e.target.tagName === "TEXTAREA") return;
  if (e.key === "y") setAnswer("yes"); else if (e.key === "n") setAnswer("no"); else if (e.key === "u") setAnswer("unsure");
  else if (e.key === "ArrowRight" || e.key === "Enter") go(1); else if (e.key === "ArrowLeft") go(-1);
  else if (e.key === "j") nextOpen();
});
window.addEventListener("beforeunload", e => { if (cur && dirtyItems().length) { e.preventDefault(); e.returnValue = ""; } });
(async () => {
  const j = await (await fetch("/api/sheets")).json();
  sheets = j.sheets; $("guide").textContent = j.guide || "(no readers_guide.md in the sheets folder)";
  $("guidebox").open = Boolean(j.guide) && !sheets.some(s => s.done || unsavedIn(s.key));   // open until a first answer
  await openSheet(sheets[0].key);
})();
</script></body></html>
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sheets", required=True, type=Path, help="the folder with your sheets")
    ap.add_argument("--labels-dir", type=Path, help="where your answers are saved (default: e5d_labels beside it)")
    ap.add_argument("--name", default="", help="your name, for the answer files")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args(argv)
    try:
        name = clean_name(args.name)
        if not args.sheets.is_dir():
            raise SheetError(f"no folder {args.sheets}")
        labels_dir = args.labels_dir or args.sheets.resolve().parent / "e5d_labels"
        sheets = discover(args.sheets, labels_dir, name)
    except SheetError as e:
        sys.exit(f"ERROR: {e}")
    guide_path = args.sheets / "readers_guide.md"
    guide = guide_path.read_text(encoding="utf-8") if guide_path.is_file() else ""
    server = make_server(App(sheets, guide), args.host, args.port)
    for s in sheets:
        print(f"{s['pair']} reader {s['reader']}: {len(s['items'])} items, {done(s)} answered; saves to {s['out']}")
    print(f"open http://127.0.0.1:{server.server_address[1]}  (Ctrl+C to stop)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
