"""Team5Scorer.check against the run's manifest.json: model settings, tokenizer and table, and the Team 5 code loaded.

The question in the Team 9 group (25 Nov): the weights hash cannot catch a settings change such as rope_theta, nor a scorer that
builds the model with other Team 5 code. No checkpoint, dataset or lm-eval run is needed:

    pytest teams/09-evaluation/harness_lab/tests/test_lm_eval_lab_run_manifest.py -q
"""
import copy
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from lm_eval_lab import (HARNESS05, Team5Scorer, code_differences, differences, loaded_team5_files,  # noqa: E402
                         read_run_manifest, records_for, week2)

TOK = "e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b"
ART = {"tokenizer_sha256": TOK, "table_file_sha256": "e19a" * 16, "table_content_sha256": "2107" * 16,
       "vocab_size": 131072, "pos_dim": 32, "bos_id": 1, "pad_id": 0}
MODEL = {"n_layer": 2, "n_embd": 64, "rope_theta": 10000.0, "head_mode": "dense", "moe": {"bias": True, "n_experts": 4}}
STORE = {"schema": "v5-ckpt/2", "run_id": "dryrun2-1234", "step": 0,
         "env": {"tokenizer_sha": "unknown", "git_sha": "abc1234"}}       # a Team 7 MANIFEST.json, as #608 writes it


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.fixture(scope="module", autouse=True)
def team5_loaded():
    """What Team5Scorer.__init__ has done before check(): Team 5's week2 imported from the checkout."""
    pytest.importorskip("tokenizers")
    week2()


def team5_sources() -> dict:
    """``sources`` exactly as train_week2.py writes it into manifest.json (lines 446-447, Team 5's own sha256)."""
    from week2.artifacts import sha256

    return {f.name: sha256(f) for f in [HARNESS05 / "train_week2.py", *(HARNESS05 / "week2").glob("*.py")]}


def run_manifest(**top) -> dict:
    """A Team 5 run's manifest.json with the fields the check reads."""
    doc = {"run_id": "dryrun2-1234", "config": {"model": copy.deepcopy(MODEL)}, "artifacts": dict(ART),
           "sources": team5_sources(), "team7_checkpoint": {"store": "/shared/ckpt", "run_id": "dryrun2-1234"}}
    doc.update(top)
    return doc


def scorer(run=None, derived_from=None) -> Team5Scorer:
    """A Team5Scorer with the fields check() reads, without the tokenizer, byte table and lm-eval it loads."""
    s = object.__new__(Team5Scorer)
    s.a = SimpleNamespace(tokenizer_sha256=TOK, derived_from=derived_from)
    s.m = copy.deepcopy(MODEL)
    s.art = SimpleNamespace(identity=lambda: dict(ART))
    s.run_manifest, s.unchecked = run, []
    return s


def test_run_only_artifacts_are_reported_as_unchecked(capsys):
    doc = run_manifest(artifacts={**ART, "training_sha256": "a" * 64})
    check = scorer(doc)
    check.check(STORE)
    assert check.unchecked == ["run artifacts without a local identity: training_sha256"]
    assert "NOT CHECKED: run artifacts without a local identity: training_sha256" in capsys.readouterr().out


# ---- the pieces --------------------------------------------------------------------------------------------------

def test_our_hashes_of_the_loaded_files_are_team5s():
    files = loaded_team5_files()
    assert {"__init__.py", "artifacts.py", "raw_vocab.py", "model.py"} <= set(files)
    assert all(p.parent == HARNESS05 / "week2" or p == HARNESS05 / "train_week2.py" for p in files.values())
    assert code_differences(team5_sources(), files) == []


def test_a_changed_file_and_a_file_the_run_did_not_have_are_named(tmp_path):
    (tmp_path / "model.py").write_bytes(b"x = 2\n")
    (tmp_path / "new.py").write_bytes(b"y = 1\n")
    run, here = sha(b"x = 1\n"), sha(b"x = 2\n")
    found = code_differences({"model.py": run}, {"model.py": tmp_path / "model.py", "new.py": tmp_path / "new.py"})
    assert found == [f"Team 5 model.py: run {run[:12]}, here {here[:12]}",
                     "Team 5 new.py: loaded here, not in the run's sources"]


def test_a_crlf_checkout_matches_a_run_made_on_linux(tmp_path):
    path = tmp_path / "model.py"
    path.write_bytes(b"a = 1\r\nb = 2\r\n")
    lf = b"a = 1\nb = 2\n"
    assert code_differences({"model.py": sha(lf)}, {"model.py": path}) == []                    # Linux run
    assert code_differences({"model.py": sha(path.read_bytes())}, {"model.py": path}) == []     # run on this checkout


def test_a_file_the_scorer_does_not_load_is_not_compared(tmp_path):
    path = tmp_path / "model.py"
    path.write_bytes(b"m = 1\n")
    assert code_differences({"model.py": sha(b"m = 1\n"), "data.py": "0" * 64}, {"model.py": path}) == []


def test_differences_name_each_key_with_both_values():
    run = {"rope_theta": 10000.0, "moe": {"bias": True, "top_k": 2}, "n_layer": 8, "gone": 1}
    here = {"rope_theta": 500000.0, "moe": {"bias": False, "top_k": 2}, "n_layer": 8.0}
    assert differences(run, here, "config.model.") == ["config.model.gone: run 1, here missing",
                                                       "config.model.moe.bias: run True, here False",
                                                       "config.model.rope_theta: run 10000.0, here 500000.0"]
    assert differences({"a": 1, "b": 2}, {"a": 1, "b": 3, "c": 4}, keys={"a"}) == []


def test_only_a_team5_manifest_is_a_run_manifest(tmp_path):
    (tmp_path / "manifest.json").write_text(json.dumps({"config": {"model": MODEL}}), encoding="utf-8")
    (tmp_path / "model.json").write_text(json.dumps(MODEL), encoding="utf-8")
    (tmp_path / "G10_MODEL_CONFIG.json").write_text(json.dumps({"head_mode": "dense", "model_spec": MODEL}),
                                                    encoding="utf-8")
    (tmp_path / "arm.yaml").write_text("model: {}\n", encoding="utf-8")
    assert read_run_manifest(tmp_path / "manifest.json") == {"config": {"model": MODEL}}
    assert [read_run_manifest(tmp_path / n) for n in ("model.json", "G10_MODEL_CONFIG.json", "arm.yaml")] == [None] * 3


# ---- Team5Scorer.check -------------------------------------------------------------------------------------------

def test_team5_run_folder_whose_manifest_matches_is_scored(capsys):
    s = scorer()
    s.check(run_manifest(team7_checkpoint=None))      # --team5-run: the folder's own manifest.json, no store
    out = capsys.readouterr().out
    assert "run manifest check ok: config.model; artifacts bos_id, pad_id, pos_dim" in out and "Team 5 __init__.py" in out
    assert s.unchecked == [] and "NOT CHECKED" not in out


def test_team5_run_folder_trained_with_other_settings_is_refused():
    doc = run_manifest()
    doc["config"]["model"]["rope_theta"] = 500000.0
    with pytest.raises(SystemExit, match=r"config\.model\.rope_theta: run 500000\.0, here 10000\.0"):
        scorer().check(doc)


def test_a_store_needs_the_manifest_of_its_own_run(capsys):
    scorer(run_manifest()).check(STORE)
    assert "run manifest check ok: run_id dryrun2-1234 (config.model read from this manifest.json); artifacts" in (
        capsys.readouterr().out)
    with pytest.raises(SystemExit, match=r"run_id: --model-config is run 'dryrun1-muon-1234', the checkpoint is run "
                                         r"'dryrun2-1234'"):
        scorer(run_manifest(team7_checkpoint={"run_id": "dryrun1-muon-1234"})).check(STORE)
    with pytest.raises(SystemExit, match="run_id: --model-config is run missing"):
        scorer(run_manifest(team7_checkpoint=None)).check(STORE)   # a run without a Team 7 store


def test_a_post_training_store_is_checked_against_its_base_run(capsys):
    """Team 10's keep_weights folders hold weights made from dry run 2 under their own run_id."""
    g10 = {**STORE, "run_id": "g10-dr2-full"}
    with pytest.raises(SystemExit, match="run_id: --model-config is run 'dryrun2-1234', the checkpoint is run "
                                         "'g10-dr2-full'"):
        scorer(run_manifest()).check(g10)
    scorer(run_manifest(), derived_from="dryrun2-1234").check(g10)
    assert "run_id dryrun2-1234 (config.model read from this manifest.json; checkpoint run g10-dr2-full derived from " \
           "it)" in capsys.readouterr().out
    with pytest.raises(SystemExit, match="run_id: --model-config is run 'dryrun2-1234', --derived-from says 'other'"):
        scorer(run_manifest(), derived_from="other").check(g10)
    doc = run_manifest()
    doc["sources"]["model.py"] = "0" * 64           # the code and inputs are still checked
    with pytest.raises(SystemExit, match="Team 5 model.py"):
        scorer(doc, derived_from="dryrun2-1234").check(g10)


def test_derived_from_is_refused_where_it_means_nothing():
    with pytest.raises(SystemExit, match="--derived-from: for a Team 7 store"):
        scorer(derived_from="dryrun2-1234").check(STORE)                       # no run manifest given
    with pytest.raises(SystemExit, match="--derived-from: for a Team 7 store"):
        scorer(derived_from="dryrun2-1234").check(run_manifest())               # a --team5-run folder


@pytest.mark.parametrize("key", ["tokenizer_sha256", "table_file_sha256"])
def test_a_run_with_another_tokenizer_or_table_is_refused(key):
    doc = run_manifest()
    doc["artifacts"][key] = "f" * 64
    with pytest.raises(SystemExit, match=f"artifacts.{key}: run 'ffff"):
        scorer(doc).check(STORE)


def test_the_store_tokenizer_still_counts():
    with pytest.raises(SystemExit, match="env.tokenizer_sha: checkpoint 15468e66457b"):
        scorer().check({**STORE, "env": {"tokenizer_sha": "15468e66457b43af"}})


def test_every_problem_is_listed_in_one_error_with_the_fix():
    doc = run_manifest(team7_checkpoint={"run_id": "other"})
    doc["artifacts"]["tokenizer_sha256"] = "f" * 64
    doc["sources"]["model.py"] = "0" * 64
    store = {**STORE, "env": {**STORE["env"], "tokenizer_sha": "15468e66457b43af"}}
    with pytest.raises(SystemExit) as e:
        scorer(doc).check(store)
    msg = str(e.value)
    assert [line.split(":")[0].strip() for line in msg.splitlines()[1:-1]] == [
        "env.tokenizer_sha", "run_id", "artifacts.tokenizer_sha256", "Team 5 model.py"]
    assert msg.endswith("Score from the commit the run trained with (MANIFEST.json env.git_sha abc1234).")


def test_in_a_store_the_settings_are_read_from_the_manifest_not_compared():
    """The store's model map comes from this manifest.json itself (load_model_config), so only its run_id ties it to the
    run; Team 7's MANIFEST.json records no Team 5 settings to compare with."""
    doc = run_manifest()
    doc["config"]["model"]["rope_theta"] = 500000.0
    s = scorer(doc)
    s.m = copy.deepcopy(doc["config"]["model"])      # what load_model_config read from the same file
    s.check(STORE)
    assert s.unchecked == []


def test_without_the_run_manifest_the_scores_say_so(capsys):
    s = scorer()                                        # --run-dir with an arm YAML or a model map
    s.check(STORE)
    assert "NOT CHECKED: model settings and Team 5 code not checked" in capsys.readouterr().out
    entry = {"task": "mmlu", "role": "freeze", "primary": "acc", "num_fewshot": 0, "limit": 10}
    res = {"results": {"mmlu": {"acc,none": 0.25}}, "n": {"mmlu": {"effective": 570, "original": 570}}}
    group = {"items": "limit", "profile": "lab", "seed": {"random": 0}}
    (rec,) = records_for(entry, res, group, "x", {"freeze": "freeze set"}, None, s.unchecked, {})
    assert rec["notes"] == ["freeze set", s.unchecked[0]]


def test_a_run_manifest_without_sources_marks_only_the_code(capsys):
    doc = run_manifest()
    del doc["sources"]
    s = scorer(doc)
    s.check(STORE)
    out = capsys.readouterr().out
    assert "run manifest check ok: run_id dryrun2-1234" in out and "Team 5 " not in out.split("NOT CHECKED")[0]
    assert s.unchecked == ["Team 5 code not checked: the run's manifest.json has no sources"]
    assert "NOT CHECKED: Team 5 code not checked" in out
