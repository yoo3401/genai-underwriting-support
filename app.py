"""Streamlit prototype for LLM-assisted generative-AI underwriting support."""

from __future__ import annotations

import json

import streamlit as st

from src.feature_extractor import (
    DOCUMENT_LABELS,
    extract_document_analysis,
    flatten_features,
)
from src.rule_engine import evaluate


st.set_page_config(
    page_title="GenAI Underwriting Support",
    page_icon="🛡️",
    layout="wide",
)

st.title("LLM 기반 생성형 AI 리스크 분석 및 보험 인수심사 지원 시스템")
st.caption(
    "기업이 제출한 여러 자료를 LLM으로 분석해 인수심사 Feature와 근거를 추출하고, "
    "규칙 기반 엔진으로 리스크와 보험가능성 Tier를 제시하는 연구용 프로토타입"
)

with st.sidebar:
    st.header("실행 설정")
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="입력한 키는 현재 Streamlit 세션에서만 사용되며 저장소에 저장되지 않습니다.",
    )
    model = st.text_input("Model", value="gpt-4.1-mini")

    st.divider()
    st.markdown(
        "**주의**\n\n"
        "본 시스템은 연구용 프로토타입이며 실제 보험사의 "
        "최종 인수결정, 보험료 산출 또는 손해확률 예측을 수행하지 않습니다."
    )

st.subheader("기업 제출자료 입력")
st.write(
    "기업이 보험 가입 심사를 위해 제출했다고 가정한 자료를 입력하세요. "
    "자료에 없는 사실은 LLM이 추측하지 않고 미확인 정보로 처리합니다."
)

service_description = st.text_area(
    DOCUMENT_LABELS["ai_service_description"],
    value="",
    height=170,
    placeholder=(
        "예: 생성형 AI를 고객상담, 사내 문서작성, 이미지 생성 등에 "
        "어떻게 활용하는지 설명한 자료"
    ),
)

privacy_policy = st.text_area(
    DOCUMENT_LABELS["privacy_security_policy"],
    value="",
    height=170,
    placeholder=(
        "예: 개인정보·민감정보 처리, 외부 AI 사업자 사용, "
        "로그 저장 및 보안통제에 관한 자료"
    ),
)

operation_policy = st.text_area(
    DOCUMENT_LABELS["ai_operation_control_policy"],
    value="",
    height=170,
    placeholder=(
        "예: Human Review, 자동출력, 중요 의사결정 사용 여부 등 "
        "AI 운영·통제 절차에 관한 자료"
    ),
)

analyze = st.button(
    "LLM 문서 분석 및 인수심사 실행",
    type="primary",
    use_container_width=True,
)

if analyze:
    documents = {
        "ai_service_description": service_description,
        "privacy_security_policy": privacy_policy,
        "ai_operation_control_policy": operation_policy,
    }

    if not any(value.strip() for value in documents.values()):
        st.warning("분석할 기업 제출자료를 하나 이상 입력해 주세요.")
        st.stop()

    if not api_key:
        st.warning("왼쪽 사이드바에 OpenAI API Key를 입력해 주세요.")
        st.stop()

    try:
        with st.spinner(
            "LLM이 기업 제출자료의 특징, 근거, 누락 및 불일치를 분석하고 있습니다..."
        ):
            analysis = extract_document_analysis(
                documents,
                model=model.strip() or None,
                api_key=api_key,
            )

        features = flatten_features(analysis)
        result = evaluate(features, conflicts=analysis["conflicts"])

    except Exception as exc:
        message = str(exc)
        if "insufficient_quota" in message or "credit_balance_exhausted" in message:
            st.error(
                "OpenAI API 크레딧이 없어 요청을 실행하지 못했습니다. "
                "API Billing의 잔액을 확인한 뒤 다시 실행해 주세요."
            )
        else:
            st.error("분석 중 오류가 발생했습니다.")
            st.exception(exc)
        st.stop()

    st.divider()
    st.subheader("1. LLM 문서 분석 결과")

    feature_rows = []
    for feature_name, item in analysis["features"].items():
        value = item["value"]
        if value is None:
            value = "unknown"

        source_names = [
            DOCUMENT_LABELS.get(source, source)
            for source in item.get("sources", [])
        ]

        feature_rows.append(
            {
                "Feature": feature_name,
                "Value": value,
                "Source": ", ".join(source_names) if source_names else "-",
                "Evidence": " | ".join(item.get("evidence", [])) or "-",
            }
        )

    st.dataframe(feature_rows, use_container_width=True, hide_index=True)

    info_col, conflict_col = st.columns(2)

    with info_col:
        st.markdown("#### 미확인·추가 확인 정보")
        if analysis["missing_information"]:
            for item in analysis["missing_information"]:
                st.write(f"**{item['feature']}**")
                if item["reason"]:
                    st.write(f"- 사유: {item['reason']}")
                if item["question"]:
                    st.write(f"- 확인 질문: {item['question']}")
        else:
            st.success("LLM이 별도로 표시한 핵심 누락정보가 없습니다.")

    with conflict_col:
        st.markdown("#### 문서 간 불일치")
        if analysis["conflicts"]:
            for item in analysis["conflicts"]:
                st.warning(f"Feature: {item['feature']}")
                if item["details"]:
                    st.write(item["details"])
                if item["evidence"]:
                    for evidence in item["evidence"]:
                        st.write(f"- {evidence}")
        else:
            st.success("탐지된 문서 간 핵심 불일치가 없습니다.")

    if analysis["follow_up_questions"]:
        st.markdown("#### 추가 심사 질문")
        for index, question in enumerate(
            analysis["follow_up_questions"],
            start=1,
        ):
            st.write(f"{index}. {question}")

    st.divider()
    st.subheader("2. Rule-based 인수심사 결과")

    tier_col, risk_col = st.columns([1, 2])

    with tier_col:
        if result["tier"] == "Manual Review":
            st.warning("Tier 확정 보류")
            st.metric(
                label="심사 상태",
                value=result["label"],
            )
        else:
            st.metric(
                label=result["tier"],
                value=result["label"],
            )

        st.markdown("**적용된 규칙**")
        for rule in result["matched_rules"]:
            st.write(f"- {rule}")

    with risk_col:
        st.markdown("#### 활성화된 Risk Module")
        if result["risks"]:
            for risk in result["risks"]:
                st.write(f"- {risk}")
        else:
            st.success("현재 규칙에서 활성화된 주요 Risk Module이 없습니다.")

    reason_col, recommendation_col = st.columns(2)

    with reason_col:
        st.markdown("#### 주요 판단 근거")
        for reason in result["reasons"]:
            st.write(f"- {reason}")

    with recommendation_col:
        st.markdown("#### 권고·추가 확인사항")
        for recommendation in result["recommendations"]:
            st.write(f"- {recommendation}")

    st.divider()

    with st.expander("LLM 전체 문서 분석 JSON 보기", expanded=False):
        st.code(
            json.dumps(analysis, ensure_ascii=False, indent=2),
            language="json",
        )

    with st.expander("Rule Engine 입력 Feature 보기", expanded=False):
        st.json(features)

    with st.expander("전체 인수심사 결과 JSON 보기", expanded=False):
        st.code(
            json.dumps(result, ensure_ascii=False, indent=2),
            language="json",
        )
