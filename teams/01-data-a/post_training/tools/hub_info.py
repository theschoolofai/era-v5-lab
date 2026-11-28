"""Pin a Hub dataset: revision sha, licence tag, gated, files (count/bytes by ext), viewer row counts; save the card."""
import json, sys, urllib.request, os
from pathlib import Path
from huggingface_hub import HfApi, hf_hub_download
api = HfApi(); tok = os.environ.get("HF_TOKEN")
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
rows = []
for rid in sys.argv[2:]:
    r = {"id": rid}
    try:
        info = api.dataset_info(rid, files_metadata=True)
        r["sha"] = info.sha; r["last_modified"] = str(info.last_modified)[:10]
        cd = info.card_data.to_dict() if info.card_data else {}
        r["license"] = cd.get("license"); r["gated"] = info.gated
        exts = {}
        for s in info.siblings or []:
            e = s.rfilename.rsplit(".", 1)[-1] if "." in s.rfilename else "-"
            c, b = exts.get(e, (0, 0)); exts[e] = (c + 1, b + (s.size or 0))
        r["files"] = {k: f"{v[0]} files {v[1]/1e6:.1f} MB" for k, v in sorted(exts.items(), key=lambda kv: -kv[1][1])[:4]}
        cfgs = cd.get("configs") or []
        r["configs"] = [c.get("config_name") for c in cfgs][:12]
        try:
            p = hf_hub_download(rid, "README.md", repo_type="dataset", revision=info.sha, token=tok)
            (out / (rid.replace("/", "__") + ".md")).write_text(Path(p).read_text(encoding="utf-8"), encoding="utf-8")
        except Exception as e:
            r["card"] = f"no README ({type(e).__name__})"
    except Exception as e:
        r["error"] = f"{type(e).__name__}: {str(e)[:120]}"
    try:
        req = urllib.request.Request(f"https://datasets-server.huggingface.co/size?dataset={rid}",
                                     headers={"Authorization": f"Bearer {tok}"} if tok else {})
        sz = json.load(urllib.request.urlopen(req, timeout=30))["size"]
        r["viewer_rows"] = {f'{s["config"]}/{s["split"]}': s["num_rows"] for s in sz.get("splits", [])}
        if len(r["viewer_rows"]) > 10:
            r["viewer_rows"] = dict(list(r["viewer_rows"].items())[:10]) | {"...": len(sz["splits"])}
        r["viewer_total_rows"] = sz["dataset"].get("num_rows")
    except Exception as e:
        r["viewer"] = f"{type(e).__name__}"
    rows.append(r)
    print(json.dumps(r, ensure_ascii=False))
