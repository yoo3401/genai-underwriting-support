import json

from src.feature_extractor import normalize_features, parse_feature_json


def test_parse_feature_json_normalizes_unknown_values():
    raw = {
        "customer_facing": True,
        "handles_pii": False,
        "handles_sensitive_data": False,
        "human_review": True,
        "autonomous_output": False,
        "external_vendor": True,
        "vendor_contract_clear": "unknown",
        "logging_enabled": True,
        "safety_critical_use": False,
        "human_decision_support": False,
        "media_generation": False,
        "copyright_content_use": "unknown",
        "prohibited_use": False,
    }

    result = parse_feature_json(json.dumps(raw))

    assert result["customer_facing"] is True
    assert result["vendor_contract_clear"] == "unknown"
    assert result["copyright_content_use"] == "unknown"
    assert result["prohibited_use"] is False


def test_missing_boolean_fields_become_none():
    result = normalize_features({})

    assert result["customer_facing"] is None
    assert result["human_review"] is None
    assert result["vendor_contract_clear"] == "unknown"
    assert result["copyright_content_use"] == "unknown"
    assert result["prohibited_use"] is False


def test_string_booleans_are_normalized():
    result = normalize_features(
        {
            "customer_facing": "true",
            "human_review": "false",
            "vendor_contract_clear": "true",
        }
    )

    assert result["customer_facing"] is True
    assert result["human_review"] is False
    assert result["vendor_contract_clear"] is True
