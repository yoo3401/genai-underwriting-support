"""Streamlit MVP for the generative-AI underwriting support system."""

from __future__ import annotations

import json

import streamlit as st

from src.feature_extractor import extract_features
from src.rule_engine import evaluate


st.set_page_config(
    page_title="GenAI Underwriting Support",
    page_icon="🛡️",
    layout="wide",
)

st.title("LLM 기반 생성형 AI 리스크 분석 및 보험 인수심사 지원 시스템")
st.caption(
    "기업의 생성형 AI 활용 설명을 구조화하고, "
    "규칙 기반 로직으로 리스크와 보험가능성 Tier를 제시하는 연구용 프로토타입"
)

with st.sidebar:
    st.header("실행 설정")
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="입력한 키는 화면 세션에서만 사용되며 저장소에 저장되지 않습니다.",
    )
    model = st.text_input("Model", value="gpt-4.1-mini")

    st.divider()
    st.markdown(
        "**주의**\n\n"
        "본 시스템은 연구용 프로토타입이며 실제 보험사의 "
        "최종 인수결정이나 보험료 산출을 수행하지 않습니다."
    )

example_text = (
    "외부 LLM API를 사용해 고객 문의에 대한 답변 초안을 생성한다. "
    "고객 이름과 계약정보가 입력될 수 있으며, "
    "상담원이 결과를 확인한 후 고객에게 전달한다. "
    "외부 사업자와 데이터 처리 및 보안 관련 계약조건을 확인했고, "
    "모든 입력과 출력 로그를 저장한다."
)

description = st.text_area(
    "기업의 생성형 AI 활용방식을 입력하세요.",
    value=example_text,
    height=180,
    placeholder=(
        "예: 생성형 AI가 고객 문의에 자동 답변하며 "
        "직원 검수 없이 바로 전송됩니다."
    ),
)

analyze = st.button("리스크 분석 실행", type="primary", use_container_width=True)

if analyze:
    if not description.strip():
        st.warning("분석할 내용을 입력해 주세요.")
        st.stop()

    if not api_key:
        st.warning("왼쪽 사이드바에 OpenAI API Key를 입력해 주세요.")
        st.stop()

    try:
        with st.spinner("LLM이 기업의 AI 활용정보를 구조화하고 있습니다..."):
            features = extract_features(
                description,
                model=model.strip() or None,
                api_key=api_key,
            )

        result = evaluate(features)

    except Exception as exc:
        st.error("분석 중 오류가 발생했습니다.")
        st.exception(exc)
        st.stop()

    tier_col, risk_col = st.columns([1, 2])

    with tier_col:
        st.subheader("보험가능성 Tier")
        st.metric(
            label=result["tier"],
            value=result["label"],
        )

        st.markdown("**적용된 규칙**")
        for rule in result["matched_rules"]:
            st.write(f"- {rule}")

    with risk_col:
        st.subheader("활성화된 Risk Module")
        if result["risks"]:
            for risk in result["risks"]:
                st.write(f"- {risk}")
        else:
            st.success("현재 규칙에서 활성화된 주요 Risk Module이 없습니다.")

    st.divider()

    reason_col, recommendation_col = st.columns(2)

    with reason_col:
        st.subheader("주요 판단 근거")
        for reason in result["reasons"]:
            st.write(f"- {reason}")

    with recommendation_col:
        st.subheader("권고 통제사항")
        for recommendation in result["recommendations"]:
            st.write(f"- {recommendation}")

    st.divider()

    with st.expander("LLM이 추출한 Feature 보기", expanded=False):
        st.json(features)

    with st.expander("전체 분석 결과 JSON 보기", expanded=False):
        st.code(
            json.dumps(result, ensure_ascii=False, indent=2),
            language="json",
        )
