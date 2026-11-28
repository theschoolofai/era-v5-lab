"""dt/mask_anatomy.py on small made-up files in the released mask format, a Team 5 metrics.jsonl and llama-imatrix
GGUFs (CPU, no download)."""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("g10_mask_anatomy_test", HERE.parent / "mask_anatomy.py")
ma = importlib.util.module_from_spec(spec)
sys.modules["g10_mask_anatomy_test"] = ma
spec.loader.exec_module(ma)

SHAPE = (8, 16)            # [out, in] of every made-up gate matrix
HEAVY_AT = (1, 2)          # layer 1, expert 2 is the heavily deleted one


def made_up_deletions(layers=2, experts=4, seed=0):
    """{(layer, expert): bool[out, in] deleted}: one expert 60 of 128 deleted, the others 0 or 1."""
    rng = np.random.default_rng(seed)
    out = {}
    for L in range(layers):
        for E in range(experts):
            d = np.zeros(SHAPE, bool)
            n = 60 if (L, E) == HEAVY_AT else (L + E) % 2
            d.ravel()[rng.choice(d.size, n, replace=False)] = True
            out[L, E] = d
    # 63 deleted in all: 60 in the heavy expert, 1 each in 0:1, 0:3 and 1:0
    return out


def write_mask_dir(path: Path, dels: dict, zero_params_offset: int = 0) -> Path:
    """The official packbits_zstd layout: <name>.packed (zstd of np.packbits(keep)) and <name>.shape per matrix."""
    zstd = pytest.importorskip("zstandard")
    st = pytest.importorskip("safetensors.numpy")
    tensors = {}
    c = zstd.ZstdCompressor()
    for (L, E), d in dels.items():
        name = f"model.layers.{L}.mlp.experts.{E}.gate_proj.weight"
        packed = c.compress(np.packbits((~d).ravel().astype(np.uint8)).tobytes())
        tensors[name + ".packed"] = np.frombuffer(packed, np.uint8).copy()
        tensors[name + ".shape"] = np.array(d.shape, np.int64)
    path.mkdir()
    st.save_file(tensors, str(path / "model.safetensors"))
    total = sum(d.size for d in dels.values())
    zero = sum(int(d.sum()) for d in dels.values()) + zero_params_offset
    (path / "config.json").write_text(json.dumps({"format": "packbits_zstd", "total_params": total, "zero_params": zero}))
    return path


def test_decode_matches_the_written_mask_position_for_position(tmp_path):
    dels = made_up_deletions()
    got = {(L, E): d for L, E, d in ma.deleted_masks(write_mask_dir(tmp_path / "m", dels))}
    assert set(got) == set(dels)
    for k in dels:
        assert got[k].shape == SHAPE
        assert np.array_equal(got[k], dels[k]), k


def test_masks_reports_the_heavy_expert_and_its_share(tmp_path, capsys):
    ma.main(["masks", str(write_mask_dir(tmp_path / "m", made_up_deletions()))])
    out = capsys.readouterr().out
    assert "heavy experts (> 1% deleted): 1, 46.875% to 46.875%" in out   # 60 of 128
    assert "heavy (layer:expert): 1:2\n" in out
    assert "holding 95.2% of all deletions" in out                      # 60 of 63


def test_masks_partners_come_from_the_same_layer_and_are_not_heavy(tmp_path, capsys):
    ma.main(["masks", str(write_mask_dir(tmp_path / "m", made_up_deletions())), "--partners", "5"])
    line = [x for x in capsys.readouterr().out.splitlines() if x.startswith("heavy experts and partners")][0]
    heavy, partner = line.split(": ")[1].split()
    # layer 1's experts that are not heavy are 0, 1, 3, and np.random.default_rng(5).choice([0, 1, 3]) is 3
    # (layer 0's 0, 1, 2, 3 would give 2, and seed 6 would give 1)
    assert (heavy, partner) == ("1:2", "1:3")


def test_masks_partners_never_repeat_within_a_layer(tmp_path, capsys):
    dels = made_up_deletions()
    dels[1, 0] = dels[HEAVY_AT].copy()          # a second heavy expert in layer 1: 1:0 and 1:2, partners from 1, 3
    ma.main(["masks", str(write_mask_dir(tmp_path / "m", dels)), "--partners", "1"])
    line = [x for x in capsys.readouterr().out.splitlines() if x.startswith("heavy experts and partners")][0]
    picks = line.split(": ")[1].split()
    assert picks[0::2] == ["1:0", "1:2"]
    assert sorted(picks[1::2]) == ["1:1", "1:3"]


def test_masks_without_a_heavy_expert(tmp_path, capsys):
    dels = {k: (np.zeros(SHAPE, bool) if k == HEAVY_AT else d) for k, d in made_up_deletions().items()}
    ma.main(["masks", str(write_mask_dir(tmp_path / "m", dels))])
    assert "heavy experts (> 1% deleted): 0; max 0.7812%" in capsys.readouterr().out   # 1 of 128


def test_masks_stops_when_config_totals_do_not_match(tmp_path):
    with pytest.raises(SystemExit, match="decode mismatch"):
        ma.main(["masks", str(write_mask_dir(tmp_path / "m", made_up_deletions(), zero_params_offset=1))])


def write_metrics(path: Path) -> Path:
    """Team 5 run-record rows: two without expert_load, four with [layer][expert] counts (2 layers x 3 experts)."""
    rows = [{"step": 10, "loss": 3.0},
            {"step": 50, "expert_load": [[5, 5, 5], [5, 5, 5]]},          # outside --last 3: expert 0:1 not yet idle
            {"step": 100, "expert_load": [[9, 0, 6], [8, 8, 0]]},
            {"step": 150, "loss": 2.5},
            {"step": 200, "expert_load": [[9, 0, 6], [8, 8, 1]]},
            {"step": 250, "expert_load": [[300, 0, 300], [299, 300, 1]]}]  # even share 200; 1:2 has 1 (< 1%)
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return path


def test_load_lists_experts_idle_in_every_recent_snapshot(tmp_path, capsys):
    ma.main(["load", str(write_metrics(tmp_path / "metrics.jsonl")), "--last", "3"])
    out = capsys.readouterr().out
    assert "3 snapshots, steps 100 to 250; 2 layers x 3 experts" in out
    assert "experts at 0 tokens in all 3 snapshots: 0:1\n" in out
    assert "  0:1: 0, 0, 0 (even share 200)" in out
    assert "  1:2: 0, 1, 1 (even share 200)" in out
    assert "1:0:" not in out and "0:0:" not in out


def test_load_expected_step0_deletion_for_unseen_experts(tmp_path, capsys):
    # 768x512 gate, eta 1/2048: 191 marked weights deleted with Phi(3), the other 393,025 with Phi(-3) -> 0.1834%.
    # 2 layers x (3 routed + 1 shared) = 8 matrices; one idle expert: official (7 x 0.1834% + 50%) / 8 = 6.411%,
    # keep (7 x 0.1834% + 0.135%) / 8 = 0.177%; both listed experts: 12.638% and 0.171%.
    ma.main(["load", str(write_metrics(tmp_path / "metrics.jsonl")), "--last", "3", "--gate", "768x512"])
    out = capsys.readouterr().out
    assert "one masked 768x512 gate per routed expert and 1 shared, 8 in all; a calibrated one 0.1834%" in out
    assert "if the experts at 0 in every snapshot (1) get no calibration token: official 6.411%, keep 0.177%" in out
    assert "if all experts listed above (2) get no calibration token: official 12.638%, keep 0.171%" in out


def test_load_needs_at_least_one_snapshot(tmp_path):
    with pytest.raises(SystemExit, match="--last must be at least 1"):
        ma.main(["load", str(write_metrics(tmp_path / "metrics.jsonl")), "--last", "0"])


def test_load_window_includes_older_snapshots_when_asked(tmp_path, capsys):
    ma.main(["load", str(write_metrics(tmp_path / "metrics.jsonl")), "--last", "4"])
    assert "experts at 0 tokens in all 4 snapshots: none" in capsys.readouterr().out


def write_imatrix(path: Path, counts: np.ndarray) -> Path:
    """A llama-imatrix-like GGUF: per layer blk.L.ffn_gate_exps.weight.counts (shape [experts, 1]) and a dense tensor."""
    gguf = pytest.importorskip("gguf")
    w = gguf.GGUFWriter(str(path), "imatrix")
    for L, row in enumerate(counts):
        w.add_tensor(f"blk.{L}.ffn_gate_exps.weight.counts", np.asarray(row, np.float32).reshape(-1, 1))
        w.add_tensor(f"blk.{L}.attn_k.weight.counts", np.array([123.0], np.float32))
    w.write_header_to_file()
    w.write_kv_data_to_file()
    w.write_tensors_to_file()
    w.close()
    return path


def test_routing_sums_parts_and_matches_zero_token_experts_to_heavy_ones(tmp_path, capsys):
    mask = write_mask_dir(tmp_path / "m", made_up_deletions())
    a = write_imatrix(tmp_path / "a.gguf", np.array([[5, 0, 7, 2], [3, 4, 0, 0]]))
    b = write_imatrix(tmp_path / "b.gguf", np.array([[1, 0, 1, 1], [3, 1, 0, 1]]))
    ma.main(["routing", str(mask), str(a), str(b)])
    out = capsys.readouterr().out
    # summed: layer 0 [6, 0, 8, 3], layer 1 [6, 5, 0, 1]; heavy is 1:2 (0 tokens); 0:1 is 0 but not heavy; 1:3 has 1
    assert "experts with zero calibration tokens: 2; heavy experts: 1; heavy with zero tokens: 1; " \
           "zero-token experts that are not heavy: 1" in out
    assert "  heavy 1:2: 0 tokens (layer median 3), 46.875% deleted" in out
    assert "  not heavy, 0 tokens 0:1:" in out


def test_revive_the_regulariser_alone_moves_an_unscored_gate_under_g10_mask_py(capsys):
    pytest.importorskip("torch")
    ma.main(["revive", "--gate", "64x32", "--steps", "40", "--at", "20", "--grad-scale", "1", "0.001"])
    rows = {tuple(x.split()[:2]): [float(v.rstrip("%")) for v in x.split()[2:]]
            for x in capsys.readouterr().out.splitlines()[2:]}
    full, tiny = rows["1", "official"], rows["0.001", "official"]
    assert 40 < full[0] < 60 and full[0] == tiny[0]           # official: about half deleted at step 0
    assert full[-1] < full[0] - 10                              # the regulariser revives weights with no task gradient
    assert full[-1] < tiny[-1]                                  # a smaller gradient (near Adam's eps) revives fewer
    assert rows["1", "keep"][0] < 1.0                           # keep starts at the Phi(-3) tail
