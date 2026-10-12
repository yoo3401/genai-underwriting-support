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


def test_conflicting_documents_require_manual_review():
    features = {
        "customer_facing": True,
        "handles_pii": True,
        "handles_sensitive_data": False,
        "human_review": None,
        "autonomous_output": None,
        "external_vendor": True,
        "vendor_contract_clear": True,
        "logging_enabled": True,
        "safety_critical_use": False,
        "human_decision_support": False,
        "media_generation": False,
        "copyright_content_use": False,
        "prohibited_use": False,
    }

    conflicts = [
        {
            "feature": "human_review",
            "details": "서비스 설명과 운영정책이 상충함",
        }
    ]

    result = evaluate(features, conflicts=conflicts)

    assert result["tier"] == "Manual Review"
    assert result["label"] == "Additional Verification Required"
    assert "MR-1" in result["matched_rules"]
