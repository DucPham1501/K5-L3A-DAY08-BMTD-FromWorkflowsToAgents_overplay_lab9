"""CP5 tests: the committed benchmark evidence matches what the ADR claims.

They read `reports/benchmark.json` and `reports/ablation_workflow_vs_orchestrator.json`
(both written by `lab8.benchmark`) and check the numbers the decision record relies on.
They run in the default host gate (`python -m pytest -q`).
"""

from __future__ import annotations

import json

import pytest

from lab8.config_loader import repo_path
from lab8.db import load_jsonl

SHAPES = ["workflow", "single", "orchestrator", "swarm"]
SEEDS = [11, 22, 33, 44, 55]
COMPARED = ("pass_rate", "pass_5", "seed_variance", "cost_per_success_vnd", "mean_tool_calls", "mean_model_calls")


def _load(name: str) -> dict:
    return json.loads(repo_path("reports", name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def bench() -> dict:
    return _load("benchmark.json")


@pytest.fixture(scope="module")
def ablation() -> dict:
    return _load("ablation_workflow_vs_orchestrator.json")


def test_benchmark_covers_four_shapes_five_seeds_all_public_claims(bench):
    claim_ids = [row["claim_id"] for row in load_jsonl(repo_path("data", "public_claims.jsonl"))]
    assert set(bench["by_shape"]) == set(SHAPES)
    assert bench["controlled_variables"]["seeds"] == SEEDS
    assert bench["controlled_variables"]["claim_ids"] == claim_ids
    for shape in SHAPES:
        trials = [t for t in bench["trials"] if t["shape"] == shape]
        assert len(trials) == len(claim_ids) * len(SEEDS)
        assert {(t["claim_id"], t["seed"]) for t in trials} == {(c, s) for c in claim_ids for s in SEEDS}


def test_benchmark_controls_model_and_prices(bench):
    controlled = bench["controlled_variables"]
    assert controlled["model_backend"] == "MockLLM"
    assert controlled["latency"] == "unavailable"
    assert controlled["pricing"]["simulated"] is True
    assert controlled["isolation"] == "fresh_sqlite_per_trial"


@pytest.mark.parametrize("shape", ["workflow", "single", "orchestrator"])
def test_student_shapes_pass_every_public_trial(bench, shape):
    stats = bench["by_shape"][shape]
    assert stats["pass_rate"] == 1.0
    assert stats["pass_5"] == 1.0
    assert stats["seed_variance"] == 0.0
    assert all(t["passed"] for t in bench["trials"] if t["shape"] == shape)


def test_swarm_only_fails_t02_at_seed_55(bench):
    failed = [(t["claim_id"], t["seed"]) for t in bench["trials"] if t["shape"] == "swarm" and not t["passed"]]
    assert failed == [("C-002", 55)]


def test_workflow_is_the_cheapest_shape_per_success(bench):
    cost = {shape: bench["by_shape"][shape]["cost_per_success_vnd"] for shape in SHAPES}
    assert cost["workflow"] == min(cost.values())
    assert cost["workflow"] < cost["single"] < cost["orchestrator"] < cost["swarm"]


def test_adr_states_the_chosen_shape_and_its_cost(bench):
    adr = repo_path("..", "report", "team", "decision_adr.md").read_text(encoding="utf-8")
    assert "- Shape chọn: workflow" in adr
    expected = f"{bench['by_shape']['workflow']['cost_per_success_vnd']:.2f}"
    line = next(line for line in adr.splitlines() if line.startswith("- Cost per success"))
    assert expected in line


@pytest.mark.parametrize("shape", ["workflow", "orchestrator"])
def test_ablation_reproduces_the_benchmark(bench, ablation, shape):
    """Same seeds and corpus give the same numbers, so the cost gap is not seed noise."""
    assert set(ablation["by_shape"]) == {"workflow", "orchestrator"}
    for key in COMPARED:
        assert ablation["by_shape"][shape][key] == pytest.approx(bench["by_shape"][shape][key])


def test_ablation_cost_gap_comes_from_tool_calls(ablation):
    stats = ablation["by_shape"]
    price = ablation["controlled_variables"]["pricing"]["tool_call_vnd"]
    gap = stats["orchestrator"]["cost_per_success_vnd"] - stats["workflow"]["cost_per_success_vnd"]
    tool_gap = (stats["orchestrator"]["mean_tool_calls"] - stats["workflow"]["mean_tool_calls"]) * price
    assert gap > 0
    assert tool_gap / gap > 0.9
