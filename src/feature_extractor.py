"""LLM analysis of PDF-based underwriting submissions.

The LLM reads page-labelled text extracted from one or more company-submitted
PDFs. It extracts underwriting features with page-level evidence and flags
missing or conflicting facts. Final risk classification and tier decisions are
made by src.rule_engine, not by the LLM.
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


SYSTEM_PROMPT = """You are an information-extraction module for a research prototype that supports commercial insurance underwriting for companies using generative AI.

You receive text extracted from one or more PDF underwriting submissions. Each page is explicitly labelled with its filename and page number.

Your job is NOT to decide whether insurance should be accepted. Your job is to:
1. extract underwriting facts,
2. cite page-level evidence,
3. identify material missing information,
4. identify material contradictions across the submitted documents.

Return ONLY one valid JSON object and no markdown.

Required top-level schema:
{
  "features": {
    "<feature_name>": {
      "value": true | false | "unknown" | "conflict",
      "evidence": [
        {"file": "exact filename", "page": 1, "quote": "short exact excerpt"}
      ],
      "note": "brief Korean explanation"
    }
  },
  "missing_information": [
    {
      "feature": "<feature_name>",
      "reason": "brief Korean reason",
      "question": "Korean follow-up underwriting question"
    }
  ],
  "conflicts": [
    {
      "feature": "<feature_name>",
      "evidence": [
        {"file": "exact filename", "page": 1, "quote": "excerpt"},
        {"file": "exact filename", "page": 2, "quote": "contradicting excerpt"}
      ],
      "details": "brief Korean explanation"
    }
  ],
  "follow_up_questions": ["Korean question"]
}

Rules:
1. Use only facts supported by the supplied PDF text. Never guess.
2. If a fact is not stated, use "unknown" rather than treating absence as false.
3. Use false only when the documents explicitly state that the activity/control is not used, not allowed, or not applicable.
4. If documents materially contradict each other for a feature, use "conflict" and add a conflicts item.
5. Evidence quotes must be short excerpts that appear in the supplied text. Do not invent quotes.
6. Evidence file names and page numbers must match the page labels provided in the input.
7. human_review means a person reviews or approves AI output BEFORE the relevant business action or external delivery.
8. autonomous_output means AI output is executed, delivered, or applied without a separate human approval step.
9. external_vendor means an outside LLM/API/cloud AI provider is used.
10. vendor_contract_clear is true only when the submission explicitly confirms relevant vendor contractual controls such as data processing, security, responsibility, reuse/training restrictions, or equivalent terms. Use false only when the submission explicitly states those terms are absent or inadequate; otherwise use "unknown".
11. prohibited_use is true only when clearly illegal, intentionally deceptive, or explicitly prohibited use is actually being performed. A policy banning prohibited uses supports false, not true.
12. copyright_content_use is true when copyrighted third-party content is actually used in a relevant way, false when the submission explicitly states that such use is not performed or is prohibited, otherwise "unknown".
13. follow_up_questions should focus on missing or ambiguous facts that could change underwriting.
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
        lines = text.splitlines()[1:]
        if lines and lines[-1].strip() == fence:
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return text


def _normalize_unknown(value: Any, enum_field: bool = False) -> Any:
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
    """Normalize a flat feature mapping for backward-compatible tests/helpers."""

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
    cleaned = _strip_code_fence(text)
    data = json.loads(cleaned)
    if not isinstance(data, dict):
        raise ValueError("LLM output must be a JSON object.")
    return normalize_features(data)


def _normalize_evidence(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        return []

    evidence: List[Dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        file_name = str(item.get("file") or "").strip()
        quote = str(item.get("quote") or "").strip()
        try:
            page = int(item.get("page"))
        except (TypeError, ValueError):
            page = None

        if file_name or quote or page is not None:
            evidence.append({"file": file_name, "page": page, "quote": quote})
    return evidence


def normalize_analysis(raw: Dict[str, Any]) -> Dict[str, Any]:
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

        features[key] = {
            "value": value,
            "evidence": _normalize_evidence(item.get("evidence")),
            "note": str(item.get("note") or "").strip(),
        }

    missing_information = []
    raw_missing = raw.get("missing_information", [])
    if isinstance(raw_missing, list):
        for item in raw_missing:
            if not isinstance(item, dict):
                continue
            feature = str(item.get("feature") or "").strip()
            if feature not in FEATURE_KEYS:
                continue
            missing_information.append(
                {
                    "feature": feature,
                    "reason": str(item.get("reason") or "").strip(),
                    "question": str(item.get("question") or "").strip(),
                }
            )

    conflicts = []
    raw_conflicts = raw.get("conflicts", [])
    if isinstance(raw_conflicts, list):
        for item in raw_conflicts:
            if not isinstance(item, dict):
                continue
            feature = str(item.get("feature") or "").strip()
            if feature not in FEATURE_KEYS:
                continue
            conflicts.append(
                {
                    "feature": feature,
                    "evidence": _normalize_evidence(item.get("evidence")),
                    "details": str(item.get("details") or "").strip(),
                }
            )

    questions = raw.get("follow_up_questions", [])
    if isinstance(questions, str):
        questions = [questions]
    if not isinstance(questions, list):
        questions = []
    follow_up_questions = [str(q).strip() for q in questions if str(q).strip()]

    return {
        "features": features,
        "missing_information": missing_information,
        "conflicts": conflicts,
        "follow_up_questions": follow_up_questions,
    }


def parse_analysis_json(text: str) -> Dict[str, Any]:
    cleaned = _strip_code_fence(text)
    data = json.loads(cleaned)
    if not isinstance(data, dict):
        raise ValueError("LLM output must be a JSON object.")
    return normalize_analysis(data)


def flatten_features(analysis: Dict[str, Any]) -> Dict[str, Any]:
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


def _build_pdf_payload(documents: List[Dict[str, Any]]) -> str:
    blocks: List[str] = []
    for document in documents:
        filename = str(document.get("filename") or "unknown.pdf")
        blocks.append(f"===== FILE: {filename} =====")
        for page in document.get("pages", []):
            page_number = page.get("page")
            text = str(page.get("text") or "").strip()
            if not text:
                continue
            blocks.append(f"--- FILE: {filename} | PAGE: {page_number} ---\n{text}")
    return "\n\n".join(blocks)


def extract_pdf_analysis(
    documents: List[Dict[str, Any]],
    *,
    model: str | None = None,
    api_key: str | None = None,
) -> Dict[str, Any]:
    """Analyze page-labelled PDF text with one LLM call."""

    if not documents:
        raise ValueError("At least one parsed PDF document must be provided.")

    payload = _build_pdf_payload(documents)
    if not payload.strip():
        raise ValueError("No extractable PDF text was provided.")

    selected_model = model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    selected_api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not selected_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it before running LLM PDF analysis."
        )

    client = OpenAI(api_key=selected_api_key)
    response = client.responses.create(
        model=selected_model,
        instructions=SYSTEM_PROMPT,
        input=(
            "다음 보험 인수심사 제출 PDF에서 추출된 텍스트를 분석하세요. "
            "Ground Truth나 정답 정보는 제공되지 않았습니다.\n\n" + payload
        ),
    )
    return parse_analysis_json(response.output_text)


def extract_features(
    description: str,
    *,
    model: str | None = None,
    api_key: str | None = None,
) -> Dict[str, Any]:
    """Backward-compatible single-text helper."""

    if not description or not description.strip():
        raise ValueError("description must not be empty")

    document = {
        "filename": "manual_input.txt",
        "pages": [{"page": 1, "text": description.strip()}],
    }
    return flatten_features(
        extract_pdf_analysis([document], model=model, api_key=api_key)
    )
