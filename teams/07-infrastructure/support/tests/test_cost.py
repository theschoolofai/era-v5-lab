"""Cost checks. Run: python -m pytest -q support/tests/test_cost.py"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, ".."), os.path.join(HERE, "..", "..")]
from cost import cost_model, find_unmanaged  # noqa: E402


def test_unmanaged_and_untagged():
    inst = json.load(open(os.path.join(HERE, "fixtures", "cost", "ec2.json")))
    nodes = find_unmanaged.slurm_nodes(os.path.join(HERE, "fixtures", "cost", "sinfo.txt"))
    r = find_unmanaged.check(inst, nodes, {"p6-b200.48xlarge": 113.93, "p5.48xlarge": 55.04})
    assert {x["id"] for x in r["unmanaged"]} == {"i-0ccc", "i-0ddd"}   # forgotten box; running but "powered down"
    assert [x["id"] for x in r["untagged"]] == ["i-0ccc"]
    assert r["usd_per_day_at_risk"] == round(24 * (55.04 + 113.93), 2)


def test_young_and_waste():
    assert round(cost_model.young(60, 775 * 60) / 60) == 39          # Session 15 worked example: 39 min
    w = cost_model.waste_share(1800, 1, 300, 600 * 3600)
    assert 0 < w < 0.01
