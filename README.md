# genai-underwriting-support

LLM-based Generative AI Risk Analysis and Insurance Underwriting Support System

# LLM 기반 생성형 AI 리스크 분석 및 보험 인수심사 지원 시스템

## 프로젝트 개요

생성형 AI를 활용하는 기업의 운영 정보를 분석하여 주요 위험요소를 추출하고,
보험 인수심사에 필요한 정보를 제공하는 웹 기반 연구용 프로토타입이다.

## 주요 기능

- 기업의 생성형 AI 활용정보 자연어 입력
- LLM 기반 Feature Extraction
- 6개 생성형 AI Risk Module 복수 분류
- Rule-based Underwriting
- 5단계 보험가능성 Tier 판정
- 판단 근거 및 권고 통제사항 제공

## 개발 기술

- Python
- Streamlit
- OpenAI API
- pytest

## 시스템 흐름

자연어 입력  
→ LLM Feature Extraction  
→ Multi-label Risk Classification  
→ Rule-based Underwriting Engine  
→ Tier / 판단 근거 / 권고사항 출력

## 실행 방법

1. Python 가상환경을 생성한다.
2. 필요한 패키지를 설치한다.

```bash
pip install -r requirements.txt
```

3. Streamlit 앱을 실행한다.

```bash
streamlit run app.py
```

4. 실행된 화면의 사이드바에 OpenAI API Key를 입력하고 분석을 실행한다.

실제 API Key는 저장소에 커밋하지 않는다.

## 현재 진행상황

- [x] 생성형 AI 리스크 데이터 사전 분석
- [x] 6개 Risk Module 정의
- [x] 시스템 구조 설계
- [x] Feature 및 Risk Mapping 설계
- [x] 5단계 Underwriting Tier 규칙 설계
- [x] 테스트 시나리오 작성
- [x] Rule Engine 구현
- [x] LLM Feature Extraction 구현
- [x] Streamlit MVP 인터페이스 구현
- [ ] 실제 API 연동 테스트
- [ ] 테스트 결과 분석
- [ ] 논문용 결과 정리

## 주의사항

본 시스템은 연구용 프로토타입이며 실제 보험사의 최종 인수결정,
보험료 산출 또는 손해확률 예측을 수행하지 않는다.
