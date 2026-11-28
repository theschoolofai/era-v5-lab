"""local_trial/slice_sample.py: a fixed-seed slice of the sample with its own manifest, on made-up parts.

  python -m pytest teams/01-data-a/pipeline/tests/test_slice_sample.py -q      (from the repository root)
"""
import hashlib
import json
import sys

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from conftest import PIPELINE

sys.path.insert(0, str(PIPELINE / "local_trial"))
import clean_manifest  # noqa: E402
import slice_sample as sl  # noqa: E402


def raw_part(path, pack, split, n):
    rows = [dict(doc_id=f"{split}-{i:04d}", text=f"document {i} of {pack}", url="", lang_label="en", pack_id=pack,
                 source="made-up") for i in range(n)]
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(rows), path)
    return path


@pytest.fixture
def sample(tmp_path):
    """Three raw parts in the course download's layout (<pack>/Part_N/, <pack>/Heldout/) and their manifest."""
    files = {"train/en-x/part-00000.parquet": raw_part(tmp_path / "raw/en-x/Part_1/part-00000.parquet", "en-x", "train", 200),
             "train/en-x/part-00001.parquet": raw_part(tmp_path / "raw/en-x/Part_2/part-00000.parquet", "en-x", "train", 3),
             "heldout/en-x/part-00000.parquet": raw_part(tmp_path / "raw/en-x/Heldout/part-00000.parquet", "en-x", "heldout", 50)}
    shards = [dict(path=p, split=p.split("/")[0], pack_id="en-x", rows=pq.read_metadata(f).num_rows,
                   bytes=f.stat().st_size, sha256=sl.sha256(f)) for p, f in files.items()]
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(dict(name="made up", total_docs=sum(s["rows"] for s in shards), shards=shards)))
    return tmp_path, manifest, files


def test_each_part_keeps_its_share_of_rows_in_file_order_with_every_column(sample):
    tmp, manifest, files = sample
    path, data = sl.slice_sample(manifest, tmp / "raw", tmp / "out", 0.1, 7)
    rows = {e["path"]: e["rows"] for e in data["shards"]}
    assert rows == {"train/en-x/part-00000.parquet": 20, "train/en-x/part-00001.parquet": 1,   # at least one row
                    "heldout/en-x/part-00000.parquet": 5}
    for p, f in files.items():
        cut, whole = pq.read_table(tmp / "out" / p), pq.read_table(f)
        assert cut.schema == whole.schema
        ids = cut["doc_id"].to_pylist()
        assert ids == sorted(ids) and set(ids) <= set(whole["doc_id"].to_pylist())   # file order, a subset
    assert data["total_docs"] == 26 and data["source_manifest_sha256"] == sl.sha256(manifest)


def test_the_slice_manifest_passes_the_clean_jobs_check(sample):
    tmp, manifest, _ = sample
    path, data = sl.slice_sample(manifest, tmp / "raw", tmp / "out", 0.1, 7)
    checked = clean_manifest.validate(path, hashlib.sha256(path.read_bytes()).hexdigest(), {"train": 2, "heldout": 1})
    assert checked["total_docs"] == 26
    for e in data["shards"]:
        f = tmp / "out" / e["path"]
        assert (e["bytes"], e["sha256"]) == (f.stat().st_size, sl.sha256(f))


def test_the_same_seed_gives_the_same_bytes_and_another_seed_other_rows(sample):
    tmp, manifest, _ = sample
    _, a = sl.slice_sample(manifest, tmp / "raw", tmp / "a", 0.1, 7)
    _, b = sl.slice_sample(manifest, tmp / "raw", tmp / "b", 0.1, 7)
    _, c = sl.slice_sample(manifest, tmp / "raw", tmp / "c", 0.1, 8)
    assert (tmp / "a/sample_manifest.json").read_bytes() == (tmp / "b/sample_manifest.json").read_bytes()
    assert [e["sha256"] for e in a["shards"]] == [e["sha256"] for e in b["shards"]]
    assert [e["sha256"] for e in a["shards"]][0] != [e["sha256"] for e in c["shards"]][0]


def test_a_part_whose_bytes_are_not_the_manifests_is_not_used(sample):
    tmp, manifest, files = sample
    raw_part(files["heldout/en-x/part-00000.parquet"], "en-x", "heldout", 51)   # same place, other bytes
    with pytest.raises(sl.SliceError, match="no file with the size and sha256 of heldout/en-x/part-00000.parquet"):
        sl.slice_sample(manifest, tmp / "raw", tmp / "out", 0.1, 7)


def test_a_folder_that_is_not_empty_is_refused(sample):
    tmp, manifest, _ = sample
    (tmp / "out").mkdir()
    (tmp / "out" / "x").write_text("x")
    with pytest.raises(sl.SliceError, match="is not empty"):
        sl.slice_sample(manifest, tmp / "raw", tmp / "out", 0.1, 7)


@pytest.mark.parametrize("share", [0, -0.1, 1.5])
def test_a_share_outside_0_to_1_is_refused(sample, share):
    tmp, manifest, _ = sample
    with pytest.raises(sl.SliceError, match="--share"):
        sl.slice_sample(manifest, tmp / "raw", tmp / "out", share, 7)
