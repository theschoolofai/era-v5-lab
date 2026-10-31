"""Build the Kaggle package: one zip to upload as a Kaggle Dataset, and one notebook that runs everything.

In simple words: Kaggle cannot see this laptop. This script packs the team folder into a zip and writes a
notebook. Upload the zip as a Dataset, import the notebook, attach the Dataset, press "Run all".
If the notebook has Internet on and no Dataset is attached, it clones the pushed branch instead.

    python support/kaggle/make_package.py            # from teams/07-infrastructure
Writes support/kaggle/dist/ (ignored by git; zips are not allowed in the repo):
    v5-infra-kaggle.zip       the team folder: the topic folders + support/ (no results, no caches)
    v5_gpu_checks.ipynb       the notebook (a copy is kept next to this script)
"""
import json
import os
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
TEAM = os.path.abspath(os.path.join(HERE, "..", ".."))
DIST = os.path.join(HERE, "dist")
REPO = "https://github.com/pradeep-kumar-gs/era-v5-lab.git"
BRANCH = "infrastructure"
TOP = "07-infrastructure"
SKIP_DIRS = {"__pycache__", ".pytest_cache", "dist", "results", ".ipynb_checkpoints"}
SKIP_EXT = {".pyc", ".zip", ".pt", ".bin", ".safetensors", ".parquet", ".gz"}


def build_zip(path):
    n = 0
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for d, dirs, files in os.walk(TEAM):
            dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS and not x.startswith("."))
            for f in sorted(files):
                if os.path.splitext(f)[1] in SKIP_EXT or f.startswith("."):
                    continue
                full = os.path.join(d, f)
                z.write(full, os.path.join(TOP, os.path.relpath(full, TEAM)))
                n += 1
    return n


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(True)}


def code(text):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": text.strip("\n").splitlines(True)}


def notebook():
    cells = [
        md("""
# V5 infrastructure: GPU checks on Kaggle 2 × T4

Settings (right panel): **Accelerator = GPU T4 x2**, **Add Input** → your `v5-infra-kaggle` Dataset. Then **Run all** (about 20–30 minutes).

Code comes from the attached Dataset (`v5-infra-kaggle.zip`), or, if none is attached and Internet is on,
from the `infrastructure` branch on GitHub. Results land in `/kaggle/working/gpu_results/` and in
`gpu_results.zip` (Output panel). No keys, tokens or personal data are used.
"""),
        code(f"""
# 1. find the code: attached Dataset first, else clone the branch
import glob, os, shutil, subprocess
WORK = "/kaggle/working/{TOP}"
shutil.rmtree(WORK, ignore_errors=True)
hits = glob.glob("/kaggle/input/**/{TOP}/README.md", recursive=True)
zips = glob.glob("/kaggle/input/**/v5-infra-kaggle.zip", recursive=True)
if hits:
    shutil.copytree(os.path.dirname(os.path.dirname(hits[0])), WORK)   # /kaggle/input is read-only
    print("code from Dataset:", hits[0])
elif zips:
    shutil.unpack_archive(zips[0], "/kaggle/working")
    print("code from zip:", zips[0])
else:
    print("No Dataset attached: Add Input -> your v5-infra-kaggle Dataset, or turn Internet on. Trying GitHub...")
    subprocess.run(["git", "clone", "-q", "--depth", "1", "-b", "{BRANCH}", "{REPO}", "/kaggle/working/repo"], check=True)
    shutil.copytree("/kaggle/working/repo/teams/{TOP}", WORK)
    print("code from GitHub branch {BRANCH}")
os.chdir(WORK)
print(sorted(os.listdir(".")))
"""),
        code("""
# 2. the machine: expect 2 x Tesla T4
!nvidia-smi --query-gpu=index,name,driver_version,memory.total --format=csv
import torch; print("torch", torch.__version__, "cuda", torch.version.cuda, "gpus", torch.cuda.device_count())
"""),
        code("""
# 3. run every GPU check (health, all-reduce, NCCL timeout, checkpoint tests on CUDA, save speed)
!python support/kaggle/run_gpu_checks.py
"""),
        code("""
# 4. show the results and pack them for download
from IPython.display import Markdown, display
display(Markdown(open("/kaggle/working/gpu_results/summary.md").read()))
shutil.make_archive("/kaggle/working/gpu_results", "zip", "/kaggle/working/gpu_results")
print("Download /kaggle/working/gpu_results.zip from the Output panel, unzip into support/kaggle/results/")
"""),
    ]
    return {"cells": cells, "nbformat": 4, "nbformat_minor": 5,
            "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                         "language_info": {"name": "python"}}}
    # no "kaggle" block: asking for Internet in the file fails the import on accounts without phone verification


def main():
    os.makedirs(DIST, exist_ok=True)
    z = os.path.join(DIST, "v5-infra-kaggle.zip")
    n = build_zip(z)
    nb = json.dumps(notebook(), indent=1) + "\n"
    for p in (os.path.join(DIST, "v5_gpu_checks.ipynb"), os.path.join(HERE, "v5_gpu_checks.ipynb")):
        open(p, "w").write(nb)
    print(f"{z}: {n} files, {os.path.getsize(z) // 1024} KB")
    print(f"{os.path.join(DIST, 'v5_gpu_checks.ipynb')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
