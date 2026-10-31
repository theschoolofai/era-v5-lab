"""Local viewer for the week 1 data diagnosis: read a pack, confirm or edit labels, export labels.csv.

Usage:
    pip install pyarrow
    python review_server.py --pack <pack_id>.parquet [--labels my_labels.csv] [--port 8765]
    then open http://127.0.0.1:8765/

The server binds to 127.0.0.1 only, so the pack never leaves your machine. Each review is saved to
<pack_id>.reviews.json next to the pack (override with --reviews). /export.csv returns the label sheet:
your reviews, then the rows of --labels that you have not reviewed yet.
"""
import argparse, csv, io, json, os, re, threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

import pyarrow.parquet as pq

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
COLS = ["doc_id", "read", "verdict", "diseases", "evidence", "hex", "note"]
LOCK = threading.Lock()


def disease_codes(path):
    """Read the codes and names from the tables in diagnosis/DISEASES.md."""
    codes = {}
    for line in open(path, encoding="utf-8"):
        p = [x.strip() for x in line.split("|")]
        if len(p) > 3 and re.fullmatch(r"[A-H]\d", p[1]):
            codes[p[1]] = p[2]
    return codes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", required=True)
    ap.add_argument("--labels", help="an existing label sheet (labels.csv) to start from")
    ap.add_argument("--reviews", help="where to save reviews (default: <pack>.reviews.json)")
    ap.add_argument("--diseases", default=os.path.join(REPO, "diagnosis", "DISEASES.md"))
    ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args()

    docs = pq.read_table(a.pack, columns=["doc_id", "url", "text"]).to_pylist() \
        if "url" in pq.read_schema(a.pack).names else pq.read_table(a.pack, columns=["doc_id", "text"]).to_pylist()
    labels = {r["doc_id"]: r for r in csv.DictReader(open(a.labels, encoding="utf-8"))} if a.labels else {}
    reviews_path = a.reviews or re.sub(r"\.parquet$", "", a.pack) + ".reviews.json"
    data = json.dumps({
        "pack": os.path.basename(a.pack),
        "codes": disease_codes(a.diseases),
        "docs": [{"i": i, "doc_id": d["doc_id"], "url": d.get("url") or "", "text": d["text"],
                  "label": labels.get(d["doc_id"])} for i, d in enumerate(docs)],
    }, ensure_ascii=False).encode()

    def load():
        try:
            return json.load(open(reviews_path, encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kw):
            super().__init__(*args, directory=HERE, **kw)

        def do_GET(self):
            if self.path == "/":
                self.path = "/viewer.html"
            elif self.path == "/data.json":
                return self.send(data, "application/json")
            elif self.path == "/reviews":
                return self.send(json.dumps(load(), ensure_ascii=False).encode(), "application/json")
            elif self.path == "/export.csv":
                rev, buf = load(), io.StringIO()
                w = csv.writer(buf); w.writerow(COLS)
                for d in docs:
                    r = rev.get(d["doc_id"]) or labels.get(d["doc_id"])
                    if r:
                        w.writerow([str(r.get(c, "")).replace("\n", " ") for c in COLS])
                return self.send(buf.getvalue().encode(), "text/csv; charset=utf-8")
            elif self.path != "/viewer.html":
                return self.send_error(404)
            return super().do_GET()

        def do_POST(self):
            if self.path != "/save":
                return self.send_error(404)
            r = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            with LOCK:
                rev = load(); rev[r["doc_id"]] = r
                tmp = reviews_path + ".tmp"
                json.dump(rev, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                os.replace(tmp, reviews_path)
            self.send(json.dumps({"reviewed": len(rev)}).encode(), "application/json")

        def send(self, body, ctype):
            self.send_response(200)
            self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(body)))
            self.end_headers(); self.wfile.write(body)

        def log_message(self, *args):
            pass

    print(f"{len(docs)} documents, {len(labels)} labels, reviews -> {reviews_path}")
    print(f"open http://127.0.0.1:{a.port}/", flush=True)
    ThreadingHTTPServer(("127.0.0.1", a.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
