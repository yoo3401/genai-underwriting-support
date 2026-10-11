"""Rule-based risk classification and underwriting tier engine.

This module implements the first MVP version of the deterministic rules
defined in docs/feature_definition.md and docs/underwriting_tier_rules.md.

The engine is intentionally simple:
1. receive structured features extracted from a company AI-use description,
2. activate one or more risk modules,
3. apply prioritized underwriting rules,
4. return an explainable result.

This is a research prototype and is not an insurer's production underwriting
or pricing model.
"""

from __future__ import annotations

from typing import Any, Dict, List


TIER_LABELS = {
    "Tier 1": "Insurable",
    "Tier 2": "Conditionally Insurable",
    "Tier 3": "Technical Referral",
    "Tier 4": "Deferred / Excluded",
    "Tier 5": "Uninsurable / Prohibited",
}


def _is_true(features: Dict[str, Any], key: str) -> bool:
    return features.get(key) is True


def _is_false(features: Dict[str, Any], key: str) -> bool:
    return features.get(key) is False


def _is_unknown(value: Any) -> bool:
    return value is None or value == "unknown"


def classify_risks(features: Dict[str, Any]) -> List[str]:
    """Return activated generative-AI risk modules."""

    risks: List[str] = []

    # Fraud / Deepfake
    if (
        _is_true(features, "media_generation")
        or (
            _is_true(features, "customer_facing")
            and _is_false(features, "logging_enabled")
        )
    ):
        risks.append("Fraud / Deepfake")

    # Data Leakage / Privacy
    if (
        _is_true(features, "handles_pii")
        or _is_true(features, "handles_sensitive_data")
        or (
            _is_true(features, "external_vendor")
            and features.get("vendor_contract_clear") is not True
        )
    ):
        risks.append("Data Leakage / Privacy")

    # Physical Safety
    if _is_true(features, "safety_critical_use"):
        risks.append("Physical Safety")

    # IP / Copyright
    if (
        _is_true(features, "copyright_content_use")
        or _is_true(features, "media_generation")
        or (
            _is_true(features, "external_vendor")
            and features.get("vendor_contract_clear") is False
        )
    ):
        risks.append("IP / Copyright")

    # Hallucination / Misinformation
    if (
        _is_true(features, "customer_facing")
        or _is_true(features, "autonomous_output")
        or _is_true(features, "human_decision_support")
    ):
        risks.append("Hallucination / Misinformation")

    # Bias / Discrimination
    if (
        _is_true(features, "human_decision_support")
        or (
            _is_true(features, "customer_facing")
            and _is_false(features, "human_review")
        )
    ):
        risks.append("Bias / Discrimination")

    return risks


def _relevant_unknown_count(features: Dict[str, Any]) -> int:
    """Count unknown values only when the field is relevant to the case."""

    count = 0

    # Vendor contract status matters only when an external vendor is used.
    if _is_true(features, "external_vendor") and _is_unknown(
        features.get("vendor_contract_clear")
    ):
        count += 1

    # Copyright status is relevant when media/content generation is used.
    if (
        _is_true(features, "media_generation")
        and _is_unknown(features.get("copyright_content_use"))
    ):
        count += 1

    # Explicit null/unknown values in the core operational features.
    core_features = [
        "customer_facing",
        "handles_pii",
        "handles_sensitive_data",
        "human_review",
        "autonomous_output",
        "logging_enabled",
        "safety_critical_use",
        "human_decision_support",
        "media_generation",
    ]
    for key in core_features:
        if key in features and _is_unknown(features.get(key)):
            count += 1

    return count


def determine_tier(
    features: Dict[str, Any], risks: List[str]
) -> Dict[str, Any]:
    """Apply prioritized underwriting rules and return an explainable tier."""

    matched_rules: List[str] = []
    reasons: List[str] = []
    recommendations: List[str] = []

    # Tier 5: prohibited / abnormal use
    if _is_true(features, "prohibited_use"):
        matched_rules.append("T5-1")
        reasons.append("금지 또는 비정상적 활용 목적이 확인됨")
        recommendations.append("법률·컴플라이언스 검토를 우선 수행")
        return _tier_result(
            "Tier 5", matched_rules, reasons, recommendations
        )

    # Tier 4: currently difficult to insure
    if _is_true(features, "safety_critical_use") and _is_false(
        features, "human_review"
    ):
        matched_rules.append("T4-1")
        reasons.append("안전 중요 업무에서 Human Review가 없음")
        recommendations.append("사람의 승인 또는 검토 절차 도입")

    if (
        _is_true(features, "handles_sensitive_data")
        and _is_false(features, "logging_enabled")
        and _is_false(features, "human_review")
    ):
        matched_rules.append("T4-2")
        reasons.append("민감정보를 처리하면서 검토 및 로그 통제가 부족함")
        recommendations.extend(
            ["Human Review 절차 도입", "입력·출력 로그 보관"]
        )

    if (
        _is_true(features, "customer_facing")
        and _is_true(features, "autonomous_output")
        and _is_false(features, "human_review")
        and _is_false(features, "logging_enabled")
    ):
        matched_rules.append("T4-3")
        reasons.append(
            "고객 대상 자동출력이 Human Review와 Logging 없이 사용됨"
        )
        recommendations.extend(
            ["고객 제공 전 Human Review 적용", "입력·출력 로그 보관"]
        )

    if matched_rules:
        return _tier_result(
            "Tier 4", matched_rules, reasons, recommendations
        )

    # Tier 3: technical referral
    if (
        _is_true(features, "external_vendor")
        and _is_unknown(features.get("vendor_contract_clear"))
    ):
        matched_rules.append("T3-1")
        reasons.append("외부 Vendor의 계약 및 데이터 처리조건이 불명확함")
        recommendations.append(
            "Vendor 계약, 데이터 저장·재사용 및 책임범위 확인"
        )

    if _is_true(features, "human_decision_support") and _is_false(
        features, "human_review"
    ):
        matched_rules.append("T3-2")
        reasons.append(
            "중요 의사결정에 AI 결과가 사용되지만 Human Review가 없음"
        )
        recommendations.append("의사결정 전 사람의 검토 및 승인 절차 도입")

    weak_controls = (
        _is_false(features, "human_review")
        or _is_false(features, "logging_enabled")
    )
    if len(risks) >= 3 and weak_controls:
        matched_rules.append("T3-3")
        reasons.append("복수의 주요 Risk Module이 활성화되고 통제가 부족함")
        recommendations.append("활성화된 위험별 추가 통제수단 검토")

    unknown_count = _relevant_unknown_count(features)
    if unknown_count >= 3:
        matched_rules.append("T3-4")
        reasons.append("핵심 입력정보가 충분하지 않아 자동 판단이 어려움")
        recommendations.append("부족한 기업 운영정보 및 증빙자료 추가 확인")

    if matched_rules:
        return _tier_result(
            "Tier 3", matched_rules, reasons, recommendations
        )

    # Tier 2: conditionally insurable
    if _is_true(features, "customer_facing") and _is_true(
        features, "human_review"
    ):
        matched_rules.append("T2-1")
        reasons.append("고객 대상 AI 서비스이나 Human Review가 적용됨")
        recommendations.append("Human Review 절차의 지속 운영 및 증빙")

    if (
        _is_true(features, "handles_pii")
        and _is_true(features, "logging_enabled")
        and _is_true(features, "human_review")
    ):
        matched_rules.append("T2-2")
        reasons.append("개인정보를 처리하지만 Logging과 Human Review가 적용됨")
        recommendations.append("개인정보 보호 및 접근통제 절차 유지")

    if (
        _is_true(features, "external_vendor")
        and features.get("vendor_contract_clear") is True
    ):
        matched_rules.append("T2-3")
        reasons.append("외부 Vendor를 사용하지만 계약조건이 확인됨")
        recommendations.append("Vendor 계약 및 데이터 처리조건 정기 점검")

    if _is_true(features, "media_generation") and _is_true(
        features, "human_review"
    ):
        matched_rules.append("T2-4")
        reasons.append("합성 미디어를 생성하지만 공개 전 Human Review가 적용됨")
        recommendations.append("저작권 및 합성 미디어 검토 절차 유지")

    if matched_rules:
        return _tier_result(
            "Tier 2", matched_rules, reasons, recommendations
        )

    # Tier 1: default low-risk case
    matched_rules.append("T1-1")
    reasons.append("고위험 조건 또는 추가 검토 조건이 확인되지 않음")
    recommendations.append("현재 통제수준 유지 및 정기적 재평가")

    return _tier_result("Tier 1", matched_rules, reasons, recommendations)


def _tier_result(
    tier: str,
    matched_rules: List[str],
    reasons: List[str],
    recommendations: List[str],
) -> Dict[str, Any]:
    """Create a normalized tier result and remove duplicate recommendations."""

    return {
        "tier": tier,
        "label": TIER_LABELS[tier],
        "matched_rules": matched_rules,
        "reasons": reasons,
        "recommendations": list(dict.fromkeys(recommendations)),
    }


def evaluate(features: Dict[str, Any]) -> Dict[str, Any]:
    """Run full risk classification and underwriting evaluation."""

    risks = classify_risks(features)
    tier_result = determine_tier(features, risks)

    return {
        "features": features,
        "risks": risks,
        **tier_result,
    }
