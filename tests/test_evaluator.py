from src.evaluator import compare_with_ground_truth


def test_compare_with_ground_truth_reports_feature_and_tier_accuracy():
    features = {
        "customer_facing": True,
        "handles_pii": True,
        "handles_sensitive_data": False,
        "human_review": True,
        "autonomous_output": False,
        "external_vendor": True,
        "vendor_contract_clear": True,
        "logging_enabled": True,
        "safety_critical_use": False,
        "human_decision_support": False,
        "media_generation": False,
        "copyright_content_use": False,
        "prohibited_use": False,
    }
    result = {
        "risks": ["Data Leakage / Privacy", "Hallucination / Misinformation"],
        "tier": "Tier 2",
        "label": "Conditionally Insurable",
    }
    ground_truth = {
        "case_id": "C01-PRO",
        "expected_features": features.copy(),
        "expected_risks": [
            "Data Leakage / Privacy",
            "Hallucination / Misinformation",
        ],
        "expected_tier": "Tier 2",
        "expected_label": "Conditionally Insurable",
    }

    evaluation = compare_with_ground_truth(features, result, ground_truth)

    assert evaluation["feature_accuracy"] == 1.0
    assert evaluation["feature_correct"] == 13
    assert evaluation["risk_match"] is True
    assert evaluation["tier_match"] is True
    assert evaluation["label_match"] is True
