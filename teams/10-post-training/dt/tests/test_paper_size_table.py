"""dt/paper_size_table.py: the copied paper numbers agree with each other, and the derived columns (CPU, no download)."""
import importlib.util
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("g10_paper_size_table_test", HERE.parent / "paper_size_table.py")
pst = importlib.util.module_from_spec(spec)
sys.modules["g10_paper_size_table_test"] = pst
spec.loader.exec_module(pst)


@pytest.mark.parametrize("model", ["Qwen 0.5B", "Qwen 3B", "Qwen 7B"])
def test_table8_means_reproduce_table1(model):
    # Table 1's SimpleRL-Zoo number is the mean of Table 8's six benchmarks, for FFT and for DT
    row = [r for r in pst.ROWS if r[1] == model and "Table 1" in r[0]][0]
    fft8, dt8 = pst.TABLE8[model]
    assert sum(fft8) / 6 == pytest.approx(row[3], abs=0.006)
    assert sum(dt8) / 6 == pytest.approx(row[8], abs=0.006)


def test_small_sets_are_whole_problems():
    for fft8, dt8 in pst.TABLE8.values():
        for b, n in pst.PROBLEMS.items():
            i = pst.BENCH.index(b)
            for v in (fft8[i], dt8[i]):
                assert v / 100 * n == pytest.approx(round(v / 100 * n), abs=0.01), (b, v)


def test_printed_columns(capsys):
    pst.main()
    out = capsys.readouterr().out
    assert "Qwen 3B         37.73  44.35          44.16  41.98   -2.37   94.7%                 64.2%" in out
    assert "Llama 8B        60.27  83.24          83.38  83.55   +0.31  100.4%                101.3%           3,647x" in out
    assert "Qwen 3B               +0.16           +0.00           -0.37           -0.67      -3.34 (-1)     -10.00 (-4)  -2.37" in out


def test_sweeps_main_settings_match_table1_and_spreads(capsys):
    # the main DT setting (eta 1/2048, lambda 1e-5, lr 3e-4) is the 4th entry of each sweep and equals Table 1
    for model, sw in pst.SWEEPS.items():
        row = [r for r in pst.ROWS if r[1] == model][0]
        assert sw["dt"][3] == row[8] and sw["fft_main"] == row[3]
    pst.main()
    out = capsys.readouterr().out
    assert "Llama 8B  DT 12 settings 82.03 to 83.55 (spread 1.52); FFT 4 settings 81.89 to 83.24 (spread 1.35); DT settings at or above the main FFT number 83.24: 3" in out
