# genai-underwriting-support

LLM-based Generative AI Risk Analysis and Insurance Underwriting Support System

# LLM 기반 생성형 AI 리스크 분석 및 보험 인수심사 지원 시스템

## 프로젝트 개요

생성형 AI를 활용하는 기업이 제출한 여러 비정형 자료를 LLM으로 분석하여
보험 인수심사에 필요한 Feature와 근거를 추출하고,
규칙 기반 엔진을 통해 주요 리스크와 보험가능성 Tier를 제시하는
웹 기반 연구용 프로토타입이다.

## 주요 기능

- 기업 제출자료 3종 입력
  - AI 서비스·활용 설명
  - 개인정보·보안 정책
  - AI 운영·통제 정책
- LLM 기반 Feature Extraction
- Feature별 출처 및 근거 문장 제시
- 핵심 정보 누락 탐지 및 추가 확인질문 생성
- 문서 간 정보 불일치 탐지
- 6개 생성형 AI Risk Module 복수 분류
- Rule-based Underwriting
- 5단계 보험가능성 Tier 판정
- 문서 충돌 시 Tier 강제 확정 대신 Manual Review
- 판단 근거 및 권고 통제사항 제공

## 개발 기술

- Python
- Streamlit
- OpenAI API
- pytest

## 시스템 흐름

기업 제출자료 여러 건  
→ LLM 문서 분석  
→ Feature + Evidence 추출  
→ 누락정보 / 문서 간 불일치 탐지  
→ Multi-label Risk Classification  
→ Rule-based Underwriting Engine  
→ Tier / 판단 근거 / 권고사항 출력

문서 간 핵심 정보가 충돌하는 경우에는 Tier를 임의로 확정하지 않고
추가 확인이 필요한 Manual Review 상태로 보낸다.

## 실행 방법

1. Python 가상환경을 생성한다.
2. 필요한 패키지를 설치한다.

    pip install -r requirements.txt

3. Streamlit 앱을 실행한다.

    streamlit run app.py

4. 실행된 화면의 사이드바에 OpenAI API Key를 입력한다.
5. 기업 제출자료를 하나 이상 입력하고 분석을 실행한다.

실제 API Key는 저장소에 커밋하지 않는다.

## 현재 진행상황

- [x] 생성형 AI 리스크 데이터 사전 분석
- [x] 6개 Risk Module 정의
- [x] 시스템 구조 설계
- [x] Feature 및 Risk Mapping 설계
- [x] 5단계 Underwriting Tier 규칙 설계
- [x] Baseline Rule Engine 테스트 시나리오 작성
- [x] Rule Engine 구현
- [x] LLM Feature Extraction 구현
- [x] 다중 기업자료 입력 UI 구현
- [x] Feature별 Evidence 추출 구조 구현
- [x] 누락정보 및 문서 간 불일치 탐지 구조 구현
- [x] 충돌 시 Manual Review 처리 구현
- [ ] 실제 API 크레딧을 이용한 시나리오별 LLM 실험
- [ ] Feature Extraction 결과와 Ground Truth 비교
- [ ] 테스트 결과 분석
- [ ] 논문용 결과 정리

## 연구 범위

본 시스템에서 LLM은 비정형 기업자료의 이해, Feature 추출,
근거 식별, 누락 및 불일치 탐지를 담당한다.

최종 Risk Module 활성화와 보험가능성 Tier 판단은
설명가능성과 재현성을 위해 명시적인 Rule Engine이 담당한다.

## 주의사항

본 시스템은 연구용 프로토타입이며 실제 보험사의 최종 인수결정,
보험료 산출 또는 손해확률 예측을 수행하지 않는다.
