"""LLM-based feature extraction for the underwriting support prototype.

The extractor converts a natural-language company AI-use description into the
structured features consumed by src.rule_engine.

The LLM is used only for information extraction. Final risk classification and
underwriting tier decisions are made by deterministic rules.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict

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


SYSTEM_PROMPT = """You extract structured underwriting features from a company description of how it uses generative AI.

Return ONLY one valid JSON object and no markdown.

Rules:
1. Extract only information supported by the user description.
2. Do not guess missing facts.
3. For boolean fields, use true, false, or null when the information is unknown.
4. For vendor_contract_clear and copyright_content_use, use true, false, or "unknown".
5. prohibited_use should be true only when the description explicitly indicates clearly illegal, intentionally deceptive, or explicitly prohibited use.
6. human_review means a person reviews or approves AI output before it is used for the relevant business action or delivered externally.
7. autonomous_output means AI output is automatically executed, delivered, or applied without a separate human approval step.

Required keys:
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

Return exactly these keys.
"""


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return text


def _normalize_unknown(value: Any, enum_field: bool = False) -> Any:
    """Normalize common model outputs into the prototype expected values."""

    if value is None:
        return "unknown" if enum_field else None

    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"unknown", "unclear", "not specified", "unspecified", "null"}:
            return "unknown" if enum_field else None
        if lowered == "true":
            return True
        if lowered == "false":
            return False

    return value


def normalize_features(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Validate keys and normalize values returned by the LLM."""

    result: Dict[str, Any] = {}

    for key in FEATURE_KEYS:
        value = raw.get(key)

        if key in {"vendor_contract_clear", "copyright_content_use"}:
            value = _normalize_unknown(value, enum_field=True)
            if value not in {True, False, "unknown"}:
                value = "unknown"
        else:
            value = _normalize_unknown(value, enum_field=False)
            if value not in {True, False, None}:
                value = None

        result[key] = value

    if result["prohibited_use"] is None:
        result["prohibited_use"] = False

    return result


def parse_feature_json(text: str) -> Dict[str, Any]:
    """Parse and normalize a JSON response from the model."""

    cleaned = _strip_code_fence(text)
    data = json.loads(cleaned)

    if not isinstance(data, dict):
        raise ValueError("LLM output must be a JSON object.")

    return normalize_features(data)


def extract_features(
    description: str,
    *,
    model: str | None = None,
    api_key: str | None = None,
) -> Dict[str, Any]:
    """Extract structured features from a natural-language AI-use description."""

    if not description or not description.strip():
        raise ValueError("description must not be empty")

    selected_model = model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    selected_api_key = api_key or os.getenv("OPENAI_API_KEY")

    if not selected_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to your environment before running LLM feature extraction."
        )

    client = OpenAI(api_key=selected_api_key)

    response = client.responses.create(
        model=selected_model,
        instructions=SYSTEM_PROMPT,
        input=description.strip(),
    )

    return parse_feature_json(response.output_text)
