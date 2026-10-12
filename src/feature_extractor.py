"""LLM-based document analysis for the underwriting support prototype.

The LLM analyzes multiple pieces of company-provided information, extracts
underwriting features with evidence, and flags missing or conflicting facts.

The LLM does not make the final underwriting decision. Deterministic rules in
src.rule_engine use the extracted features to produce the risk profile and tier.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from openai import OpenAI


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

ENUM_FIELDS = {"vendor_contract_clear", "copyright_content_use"}

DOCUMENT_LABELS = {
    "ai_service_description": "AI 서비스·활용 설명",
    "privacy_security_policy": "개인정보·보안 정책",
    "ai_operation_control_policy": "AI 운영·통제 정책",
}


SYSTEM_PROMPT = """You are an information-extraction module for a research prototype that supports insurance underwriting of companies using generative AI.

You will receive up to three company-provided documents:
1. AI service / usage description
2. Privacy / security policy
3. AI operation / control policy

Your job is NOT to decide whether insurance should be accepted.
Your job is to extract underwriting facts, show supporting evidence, and identify missing or conflicting information.

Return ONLY one valid JSON object and no markdown.

Required top-level schema:
{
  "features": {
    "<feature_name>": {
      "value": true | false | "unknown" | "conflict",
      "sources": ["document_key"],
      "evidence": ["short excerpt from the supplied documents"],
      "note": "brief Korean explanation"
    }
  },
  "missing_information": [
    {
      "feature": "<feature_name>",
      "reason": "brief Korean reason",
      "question": "Korean follow-up question"
    }
  ],
  "conflicts": [
    {
      "feature": "<feature_name>",
      "documents": ["document_key", "document_key"],
      "evidence": ["excerpt 1", "excerpt 2"],
      "details": "brief Korean explanation of the contradiction"
    }
  ],
  "follow_up_questions": ["Korean question"]
}

Rules:
1. Use only facts supported by the supplied documents. Do not guess.
2. For missing facts, use "unknown".
3. If two supplied documents materially contradict each other for a feature, use "conflict" and add an item to conflicts.
4. Evidence must be a short excerpt that actually appears in the supplied document. Do not invent evidence.
5. sources must use only these keys when present:
   - ai_service_description
   - privacy_security_policy
   - ai_operation_control_policy
6. human_review means a person reviews or approves AI output BEFORE it is used for the relevant business action or delivered externally.
7. autonomous_output means AI output is automatically executed, delivered, or applied without a separate human approval step.
8. external_vendor means an outside LLM/API/cloud AI provider is used.
9. vendor_contract_clear is true only when the documents explicitly say relevant data-processing, security, responsibility, or reuse terms have been checked or agreed; false only when explicitly inadequate; otherwise "unknown".
10. prohibited_use is true only when clearly illegal, intentionally deceptive, or explicitly prohibited use is actually described as being performed. A policy saying prohibited uses are banned is evidence for false, not true.
11. copyright_content_use is true when copyrighted material is actually used as input/output content in a relevant way, false when the documents explicitly state it is not used or is prohibited, otherwise "unknown".
12. If a feature is not relevant and the documents explicitly exclude that use, false is appropriate.
13. follow_up_questions should focus on facts that could change the underwriting result.
14. Include every required feature exactly once.

Required features:
- customer_facing
- handles_pii
- handles_sensitive_data
- human_review
- autonomous_output
- external_vendor
- vendor_contract_clear
- logging_enabled
- safety_critical_use
- human_decision_support
- media_generation
- copyright_content_use
- prohibited_use
"""


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    fence = "\x60\x60\x60"
    if text.startswith(fence):
        lines = text.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == fence:
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return text


def _normalize_unknown(value: Any, enum_field: bool = False) -> Any:
    """Normalize common model outputs into prototype values."""

    if value is None:
        return "unknown" if enum_field else None

    if isinstance(value, str):
        lowered = value.strip().lower()

        if lowered in {
            "unknown",
            "unclear",
            "not specified",
            "unspecified",
            "null",
            "none",
        }:
            return "unknown" if enum_field else None

        if lowered == "conflict":
            return "conflict"

        if lowered == "true":
            return True

        if lowered == "false":
            return False

    return value


def normalize_features(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Validate flat feature keys and normalize values."""

    result: Dict[str, Any] = {}

    for key in FEATURE_KEYS:
        value = raw.get(key)

        if key in ENUM_FIELDS:
            value = _normalize_unknown(value, enum_field=True)
            if value not in {True, False, "unknown", "conflict"}:
                value = "unknown"
        else:
            value = _normalize_unknown(value, enum_field=False)
            if value not in {True, False, None, "conflict"}:
                value = None

        result[key] = value

    if result["prohibited_use"] is None:
        result["prohibited_use"] = False

    return result


def parse_feature_json(text: str) -> Dict[str, Any]:
    """Parse the legacy flat-feature JSON format."""

    cleaned = _strip_code_fence(text)
    data = json.loads(cleaned)

    if not isinstance(data, dict):
        raise ValueError("LLM output must be a JSON object.")

    return normalize_features(data)


def _normalize_string_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def normalize_analysis(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize the multi-document analysis returned by the LLM."""

    raw_features = raw.get("features", {})
    if not isinstance(raw_features, dict):
        raw_features = {}

    features: Dict[str, Dict[str, Any]] = {}

    for key in FEATURE_KEYS:
        item = raw_features.get(key, {})
        if not isinstance(item, dict):
            item = {"value": item}

        enum_field = key in ENUM_FIELDS
        value = _normalize_unknown(item.get("value"), enum_field=enum_field)

        if enum_field:
            if value not in {True, False, "unknown", "conflict"}:
                value = "unknown"
        else:
            if value not in {True, False, None, "conflict"}:
                value = None

        if key == "prohibited_use" and value is None:
            value = False

        sources = [
            source
            for source in _normalize_string_list(item.get("sources"))
            if source in DOCUMENT_LABELS
        ]

        features[key] = {
            "value": value,
            "sources": sources,
            "evidence": _normalize_string_list(item.get("evidence")),
            "note": str(item.get("note") or "").strip(),
        }

    missing_information = raw.get("missing_information", [])
    if not isinstance(missing_information, list):
        missing_information = []

    normalized_missing = []
    for item in missing_information:
        if not isinstance(item, dict):
            continue
        feature = str(item.get("feature") or "").strip()
        if feature not in FEATURE_KEYS:
            continue
        normalized_missing.append(
            {
                "feature": feature,
                "reason": str(item.get("reason") or "").strip(),
                "question": str(item.get("question") or "").strip(),
            }
        )

    conflicts = raw.get("conflicts", [])
    if not isinstance(conflicts, list):
        conflicts = []

    normalized_conflicts = []
    for item in conflicts:
        if not isinstance(item, dict):
            continue
        feature = str(item.get("feature") or "").strip()
        if feature not in FEATURE_KEYS:
            continue
        normalized_conflicts.append(
            {
                "feature": feature,
                "documents": [
                    doc
                    for doc in _normalize_string_list(item.get("documents"))
                    if doc in DOCUMENT_LABELS
                ],
                "evidence": _normalize_string_list(item.get("evidence")),
                "details": str(item.get("details") or "").strip(),
            }
        )

    follow_up_questions = _normalize_string_list(raw.get("follow_up_questions"))

    return {
        "features": features,
        "missing_information": normalized_missing,
        "conflicts": normalized_conflicts,
        "follow_up_questions": follow_up_questions,
    }


def parse_analysis_json(text: str) -> Dict[str, Any]:
    """Parse and normalize the structured multi-document LLM response."""

    cleaned = _strip_code_fence(text)
    data = json.loads(cleaned)

    if not isinstance(data, dict):
        raise ValueError("LLM output must be a JSON object.")

    return normalize_analysis(data)


def flatten_features(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Convert evidence-rich feature objects into values for the rule engine."""

    flat: Dict[str, Any] = {}

    for key in FEATURE_KEYS:
        item = analysis.get("features", {}).get(key, {})
        value = item.get("value") if isinstance(item, dict) else None

        if value == "conflict":
            flat[key] = "unknown" if key in ENUM_FIELDS else None
        elif value is None and key in ENUM_FIELDS:
            flat[key] = "unknown"
        else:
            flat[key] = value

    if flat.get("prohibited_use") is None:
        flat["prohibited_use"] = False

    return flat


def extract_document_analysis(
    documents: Dict[str, str],
    *,
    model: str | None = None,
    api_key: str | None = None,
) -> Dict[str, Any]:
    """Analyze multiple company documents with one LLM call."""

    cleaned_documents = {
        key: value.strip()
        for key, value in documents.items()
        if key in DOCUMENT_LABELS and isinstance(value, str) and value.strip()
    }

    if not cleaned_documents:
        raise ValueError("At least one company document must be provided.")

    selected_model = model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    selected_api_key = api_key or os.getenv("OPENAI_API_KEY")

    if not selected_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to your environment before running LLM document analysis."
        )

    payload = {
        key: {
            "document_name": DOCUMENT_LABELS[key],
            "content": value,
        }
        for key, value in cleaned_documents.items()
    }

    client = OpenAI(api_key=selected_api_key)

    response = client.responses.create(
        model=selected_model,
        instructions=SYSTEM_PROMPT,
        input=(
            "다음 기업 제출자료를 분석하세요.\n\n"
            + json.dumps(payload, ensure_ascii=False, indent=2)
        ),
    )

    return parse_analysis_json(response.output_text)


def extract_features(
    description: str,
    *,
    model: str | None = None,
    api_key: str | None = None,
) -> Dict[str, Any]:
    """Backward-compatible helper for a single natural-language description."""

    analysis = extract_document_analysis(
        {"ai_service_description": description},
        model=model,
        api_key=api_key,
    )
    return flatten_features(analysis)
