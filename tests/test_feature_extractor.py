import json

from src.feature_extractor import (
    flatten_features,
    normalize_analysis,
    normalize_features,
    parse_analysis_json,
    parse_feature_json,
)


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


def test_document_analysis_preserves_page_evidence_and_conflict():
    raw = {
        "features": {
            "customer_facing": {
                "value": True,
                "evidence": [
                    {
                        "file": "proposal.pdf",
                        "page": 3,
                        "quote": "customer-facing support workflow",
                    }
                ],
                "note": "고객 대면 서비스",
            },
            "human_review": {
                "value": "conflict",
                "evidence": [
                    {
                        "file": "proposal.pdf",
                        "page": 4,
                        "quote": "sent without review",
                    },
                    {
                        "file": "control.pdf",
                        "page": 2,
                        "quote": "all responses require approval",
                    },
                ],
                "note": "두 자료가 상충함",
            },
        },
        "missing_information": [],
        "conflicts": [
            {
                "feature": "human_review",
                "evidence": [
                    {
                        "file": "proposal.pdf",
                        "page": 4,
                        "quote": "sent without review",
                    },
                    {
                        "file": "control.pdf",
                        "page": 2,
                        "quote": "all responses require approval",
                    },
                ],
                "details": "Human Review 여부가 상충함",
            }
        ],
        "follow_up_questions": ["실제 운영 절차를 확인하십시오."],
    }

    result = normalize_analysis(raw)
    flat = flatten_features(result)

    assert result["features"]["customer_facing"]["value"] is True
    assert result["features"]["customer_facing"]["evidence"][0]["page"] == 3
    assert result["features"]["human_review"]["value"] == "conflict"
    assert flat["human_review"] is None
    assert len(result["conflicts"]) == 1


def test_parse_analysis_json_handles_unknown_enum():
    raw = {
        "features": {
            "external_vendor": {
                "value": True,
                "evidence": [
                    {
                        "file": "proposal.pdf",
                        "page": 6,
                        "quote": "Commercial LLM API",
                    }
                ],
                "note": "",
            },
            "vendor_contract_clear": {
                "value": "unknown",
                "evidence": [],
                "note": "계약조건 설명 없음",
            },
        },
        "missing_information": [
            {
                "feature": "vendor_contract_clear",
                "reason": "계약조건이 제시되지 않음",
                "question": "외부 사업자 계약조건이 확인되었습니까?",
            }
        ],
        "conflicts": [],
        "follow_up_questions": [],
    }

    result = parse_analysis_json(json.dumps(raw, ensure_ascii=False))
    flat = flatten_features(result)

    assert flat["external_vendor"] is True
    assert flat["vendor_contract_clear"] == "unknown"
    assert result["missing_information"][0]["feature"] == "vendor_contract_clear"
