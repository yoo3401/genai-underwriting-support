"""Research evaluation utilities for comparing prototype output with ground truth."""

from __future__ import annotations

from typing import Any, Dict, List


FEATURE_KEYS = [
    "customer_facing",
    "handles_pii",
    "handles_sensitive_data",
    "human_review",
    "autonomous_output",
    "external_vendor",
    "vendor_contract_clear",
    "logging_enabled",
    "safety_critical_use",
    "human_decision_support",
    "media_generation",
    "copyright_content_use",
    "prohibited_use",
]


def compare_with_ground_truth(
    extracted_features: Dict[str, Any],
    underwriting_result: Dict[str, Any],
    ground_truth: Dict[str, Any],
) -> Dict[str, Any]:
    """Compare LLM/rule-engine outputs with researcher-defined expected values."""

    expected_features = ground_truth.get("expected_features")
    if not isinstance(expected_features, dict):
        raise ValueError("Ground Truth JSON에 expected_features 객체가 필요합니다.")

    rows: List[Dict[str, Any]] = []
    correct = 0

    for key in FEATURE_KEYS:
        expected = expected_features.get(key)
        actual = extracted_features.get(key)
        matched = actual == expected
        if matched:
            correct += 1
        rows.append(
            {
                "feature": key,
                "expected": expected,
                "actual": actual,
                "match": matched,
            }
        )

    total = len(FEATURE_KEYS)
    accuracy = correct / total if total else 0.0

    expected_risks = ground_truth.get("expected_risks")
    actual_risks = underwriting_result.get("risks", [])
    risk_match = None
    if isinstance(expected_risks, list):
        risk_match = set(expected_risks) == set(actual_risks)

    expected_tier = ground_truth.get("expected_tier")
    tier_match = None
    if expected_tier is not None:
        tier_match = underwriting_result.get("tier") == expected_tier

    expected_label = ground_truth.get("expected_label")
    label_match = None
    if expected_label is not None:
        label_match = underwriting_result.get("label") == expected_label

    return {
        "case_id": ground_truth.get("case_id"),
        "case_name": ground_truth.get("case_name"),
        "feature_correct": correct,
        "feature_total": total,
        "feature_accuracy": accuracy,
        "feature_rows": rows,
        "risk_match": risk_match,
        "expected_risks": expected_risks,
        "actual_risks": actual_risks,
        "tier_match": tier_match,
        "expected_tier": expected_tier,
        "actual_tier": underwriting_result.get("tier"),
        "label_match": label_match,
        "expected_label": expected_label,
        "actual_label": underwriting_result.get("label"),
    }
