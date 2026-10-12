# genai-underwriting-support

LLM-based Generative AI Risk Analysis and Insurance Underwriting Support System

# LLM 기반 생성형 AI 리스크 분석 및 보험 인수심사 지원 시스템

## 프로젝트 개요

생성형 AI를 활용하는 기업이 보험 인수심사를 위해 제출한 PDF 자료를 분석하여
보험심사에 필요한 Feature와 페이지별 근거를 LLM으로 추출하고,
규칙 기반 엔진을 통해 주요 Risk Module과 보험가능성 Tier를 제시하는
웹 기반 연구용 프로토타입이다.

## 핵심 설계

LLM이 최종 인수결정을 직접 내리지 않는다.

PDF 제출자료  
→ PDF 페이지별 텍스트 추출  
→ LLM Feature + Evidence 추출  
→ 누락정보 / 문서 내·문서 간 불일치 탐지  
→ Multi-label Risk Classification  
→ Rule-based Underwriting Engine  
→ Tier / 판단 근거 / 권고사항

최종 Risk 및 Tier 판단은 설명가능성과 재현성을 위해
명시적인 Rule Engine이 담당한다.

## 주요 기능

- 기업 보험 청약·인수심사 PDF 다중 업로드
- PDF 페이지별 텍스트 추출
- 13개 Underwriting Feature 추출
- Feature별 파일명·페이지·근거 문장 제시
- 핵심 정보 누락 탐지
- 추가 확인질문 생성
- 문서 내·문서 간 불일치 탐지
- 6개 생성형 AI Risk Module 복수 분류
- Rule-based Underwriting
- 5단계 보험가능성 Tier 판정
- 자료 충돌 시 Tier 강제 확정 대신 Manual Review

## 연구 평가 모드

Streamlit 사이드바에서 다음 두 모드를 선택할 수 있다.

### 1. 인수심사 모드

PDF 제출자료만 분석하여 실제 프로토타입의 심사 결과를 확인한다.

### 2. 연구 평가 모드

PDF와 별도의 Ground Truth JSON을 함께 입력한다.

중요하게도 Ground Truth는 LLM 요청에 포함하지 않는다.
먼저 PDF만으로 LLM 분석 및 Rule Engine 실행을 완료한 뒤,
연구자가 사전에 정의한 정답과 사후 비교한다.

평가 항목:

- Feature Extraction Accuracy
- Risk Module 일치 여부
- Underwriting Tier 일치 여부
- Feature별 오분류 확인

## 개발 기술

- Python
- Streamlit
- OpenAI API
- pypdf
- pytest

## 실행 방법

1. Python 가상환경을 생성한다.
2. 필요한 패키지를 설치한다.

    pip install -r requirements.txt

3. Streamlit 앱을 실행한다.

    streamlit run app.py

4. 사이드바에 OpenAI API Key를 입력한다.
5. 텍스트가 포함된 PDF를 업로드하고 분석한다.
6. 논문 실험 시에는 연구 평가 모드를 선택하고 Ground Truth JSON도 업로드한다.

실제 API Key는 저장소에 커밋하지 않는다.

## PDF 지원 범위

현재 프로토타입은 PDF 내부에 텍스트 레이어가 존재하는 문서를 지원한다.

스캔 이미지로만 구성된 PDF는 현재 OCR 대상에서 제외한다.
이는 초기 연구 프로토타입의 범위를 명확히 하기 위한 제한이다.

## 현재 진행상황

- [x] 생성형 AI 리스크 데이터 사전 분석
- [x] 6개 Risk Module 정의
- [x] 시스템 구조 설계
- [x] Feature 및 Risk Mapping 설계
- [x] 5단계 Underwriting Tier 규칙 설계
- [x] Rule Engine 구현
- [x] LLM Feature Extraction 구현
- [x] 문서 근거 및 불일치 탐지 구조 구현
- [x] PDF 업로드 및 페이지별 텍스트 추출 구현
- [x] 파일명·페이지 기반 Evidence 출력 구현
- [x] Ground Truth 비교용 연구 평가 모드 구현
- [ ] 실제 Case 01 PDF API 실험
- [ ] Case 01 Feature Extraction 결과 분석
- [ ] 추가 기업보험 테스트 케이스 설계
- [ ] 논문용 실험 결과 정리

## 연구 범위

본 시스템에서 LLM은 비정형 보험 인수심사 자료의 이해,
Feature 추출, 근거 식별, 누락 및 불일치 탐지를 담당한다.

최종 Risk Module 활성화와 보험가능성 Tier 판단은 Rule Engine이 담당한다.

본 연구의 정확도 평가는 실제 보험사의 인수결정 정확도를 의미하지 않으며,
연구자가 설계한 가상 기업보험 제출사례에 대한 프로토타입 기능 검증이다.

## 주의사항

본 시스템은 연구용 프로토타입이며 실제 보험사의 최종 인수결정,
보험료 산출 또는 손해확률 예측을 수행하지 않는다.
