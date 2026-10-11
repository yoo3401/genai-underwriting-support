import json
from pathlib import Path

import pytest

from src.rule_engine import evaluate


SCENARIO_PATH = Path(__file__).with_name("test_scenarios.json")

with SCENARIO_PATH.open("r", encoding="utf-8") as f:
    SCENARIOS = json.load(f)


@pytest.mark.parametrize(
    "scenario",
    SCENARIOS,
    ids=[scenario["id"] for scenario in SCENARIOS],
)
def test_rule_engine_matches_expected_results(scenario):
    result = evaluate(scenario["expected_features"])

    assert set(result["risks"]) == set(scenario["expected_risks"])
    assert result["tier"] == scenario["expected_tier"]
    assert result["label"] == scenario["expected_label"]


def test_all_baseline_scenarios_exist():
    assert len(SCENARIOS) == 10
