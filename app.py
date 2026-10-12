"""Streamlit prototype for PDF-based GenAI insurance underwriting support."""

from __future__ import annotations

import json

import streamlit as st

from src.evaluator import compare_with_ground_truth
from src.feature_extractor import extract_pdf_analysis, flatten_features
from src.pdf_parser import PDFExtractionError, build_document_preview, extract_pdf_document
from src.rule_engine import evaluate


st.set_page_config(
    page_title="GenAI Underwriting Support",
    page_icon="🛡️",
    layout="wide",
)

st.title("LLM 기반 생성형 AI 리스크 분석 및 보험 인수심사 지원 시스템")
st.caption(
    "기업이 제출한 보험 청약·인수심사 PDF를 LLM으로 분석하여 Feature와 근거를 추출하고, "
    "규칙 기반 엔진으로 Risk Module과 보험가능성 Tier를 제시하는 연구용 프로토타입"
)

with st.sidebar:
    st.header("실행 설정")
    mode = st.radio(
        "실행 모드",
        ["인수심사 모드", "연구 평가 모드"],
        help="평가 모드에서는 LLM 분석 후 별도 Ground Truth와 결과를 비교합니다.",
    )
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="입력한 키는 현재 Streamlit 세션에서만 사용되며 저장소에 저장되지 않습니다.",
    )
    model = st.text_input("Model", value="gpt-4.1-mini")

    st.divider()
    st.markdown(
        "**주의**\n\n"
        "본 시스템은 연구용 프로토타입이며 실제 보험사의 최종 인수결정, "
        "보험료 산출 또는 손해확률 예측을 수행하지 않습니다."
    )

st.subheader("기업 인수심사 제출자료")
uploaded_pdfs = st.file_uploader(
    "PDF 제출자료를 업로드하세요.",
    type=["pdf"],
    accept_multiple_files=True,
    help="텍스트가 포함된 PDF를 지원합니다. 현재 버전은 스캔 이미지 PDF OCR을 지원하지 않습니다.",
)

ground_truth_file = None
if mode == "연구 평가 모드":
    ground_truth_file = st.file_uploader(
        "Ground Truth JSON 업로드",
        type=["json"],
        accept_multiple_files=False,
        help="이 파일은 LLM에 전달되지 않고, 분석 완료 후 연구 평가에만 사용됩니다.",
    )

parsed_documents = []
if uploaded_pdfs:
    st.markdown("#### 업로드 문서 확인")
    for uploaded in uploaded_pdfs:
        try:
            document = extract_pdf_document(uploaded.getvalue(), uploaded.name)
            parsed_documents.append(document)
            st.success(
                f"{uploaded.name} · 전체 {document['page_count']}p · "
                f"텍스트 추출 {document['text_page_count']}p · "
                f"{document['character_count']:,}자"
            )
            with st.expander(f"{uploaded.name} 텍스트 미리보기"):
                st.text(build_document_preview(document))
        except PDFExtractionError as exc:
            st.error(str(exc))

analyze = st.button(
    "PDF 분석 및 인수심사 실행",
    type="primary",
    use_container_width=True,
)

if analyze:
    if not parsed_documents:
        st.warning("분석할 PDF를 하나 이상 업로드해 주세요.")
        st.stop()

    if not api_key:
        st.warning("왼쪽 사이드바에 OpenAI API Key를 입력해 주세요.")
        st.stop()

    if mode == "연구 평가 모드" and ground_truth_file is None:
        st.warning("연구 평가 모드에서는 Ground Truth JSON을 함께 업로드해 주세요.")
        st.stop()

    try:
        with st.spinner(
            "PDF 텍스트를 기반으로 LLM이 인수심사 Feature와 근거를 분석하고 있습니다..."
        ):
            analysis = extract_pdf_analysis(
                parsed_documents,
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
                "API Billing 잔액을 확인한 뒤 다시 실행해 주세요."
            )
        else:
            st.error("분석 중 오류가 발생했습니다.")
            st.exception(exc)
        st.stop()

    st.divider()
    st.subheader("1. LLM PDF 분석 결과")

    feature_rows = []
    for feature_name, item in analysis["features"].items():
        value = item["value"]
        if value is None:
            value = "unknown"

        evidence_labels = []
        for evidence in item.get("evidence", []):
            file_name = evidence.get("file") or "?"
            page = evidence.get("page")
            quote = evidence.get("quote") or ""
            location = f"{file_name} p.{page}" if page else file_name
            evidence_labels.append(f"{location}: {quote}")

        feature_rows.append(
            {
                "Feature": feature_name,
                "Value": value,
                "Evidence": " | ".join(evidence_labels) or "-",
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
        st.markdown("#### 문서 내·문서 간 불일치")
        if analysis["conflicts"]:
            for item in analysis["conflicts"]:
                st.warning(f"Feature: {item['feature']}")
                if item["details"]:
                    st.write(item["details"])
                for evidence in item.get("evidence", []):
                    file_name = evidence.get("file") or "?"
                    page = evidence.get("page")
                    quote = evidence.get("quote") or ""
                    st.write(f"- {file_name} p.{page}: {quote}")
        else:
            st.success("탐지된 핵심 불일치가 없습니다.")

    if analysis["follow_up_questions"]:
        st.markdown("#### 추가 심사 질문")
        for index, question in enumerate(analysis["follow_up_questions"], start=1):
            st.write(f"{index}. {question}")

    st.divider()
    st.subheader("2. Rule-based 인수심사 결과")

    tier_col, risk_col = st.columns([1, 2])

    with tier_col:
        if result["tier"] == "Manual Review":
            st.warning("Tier 확정 보류")
            st.metric(label="심사 상태", value=result["label"])
        else:
            st.metric(label=result["tier"], value=result["label"])

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

    if mode == "연구 평가 모드":
        try:
            ground_truth = json.loads(ground_truth_file.getvalue().decode("utf-8"))
            evaluation = compare_with_ground_truth(features, result, ground_truth)
        except Exception as exc:
            st.error("Ground Truth JSON을 읽거나 비교하는 중 오류가 발생했습니다.")
            st.exception(exc)
            st.stop()

        st.divider()
        st.subheader("3. 연구 평가 결과")
        st.caption(
            "Ground Truth는 LLM 요청에 포함되지 않았으며, "
            "LLM 분석과 Rule Engine 실행이 끝난 뒤에만 비교됩니다."
        )

        metric1, metric2, metric3 = st.columns(3)
        metric1.metric(
            "Feature Accuracy",
            f"{evaluation['feature_accuracy'] * 100:.1f}%",
            f"{evaluation['feature_correct']}/{evaluation['feature_total']}",
        )
        metric2.metric(
            "Risk Module",
            "일치" if evaluation["risk_match"] is True else "불일치",
        )
        metric3.metric(
            "Underwriting Tier",
            "일치" if evaluation["tier_match"] is True else "불일치",
        )

        comparison_rows = []
        for row in evaluation["feature_rows"]:
            comparison_rows.append(
                {
                    "Feature": row["feature"],
                    "Ground Truth": row["expected"],
                    "LLM Result": row["actual"],
                    "Match": "✓" if row["match"] else "✗",
                }
            )
        st.dataframe(comparison_rows, use_container_width=True, hide_index=True)

        if evaluation["risk_match"] is not None:
            st.write(f"**Expected Risks:** {evaluation['expected_risks']}")
            st.write(f"**Actual Risks:** {evaluation['actual_risks']}")
        if evaluation["tier_match"] is not None:
            st.write(
                f"**Expected Tier:** {evaluation['expected_tier']} / "
                f"**Actual Tier:** {evaluation['actual_tier']}"
            )

    st.divider()
    with st.expander("LLM 전체 분석 JSON 보기", expanded=False):
        st.code(json.dumps(analysis, ensure_ascii=False, indent=2), language="json")

    with st.expander("Rule Engine 입력 Feature 보기", expanded=False):
        st.json(features)

    with st.expander("전체 인수심사 결과 JSON 보기", expanded=False):
        st.code(json.dumps(result, ensure_ascii=False, indent=2), language="json")
