# System Design v0.1

## 1. 시스템 목적

본 시스템은 기업의 생성형 AI 활용 사례를 자연어 형태로 입력받아 보험 인수심사에 필요한 주요 위험요소를 구조화하고, 관련 리스크 유형과 보험가능성 수준을 제시하는 것을 목표로 한다.

본 시스템은 실제 보험사의 최종 인수결정을 자동화하는 시스템이 아니라, 초기 인수심사 과정에서 활용할 수 있는 의사결정 지원용 프로토타입이다.

## 2. 전체 처리 흐름

1. 사용자가 기업의 생성형 AI 활용 사례를 자연어로 입력한다.
2. LLM이 입력문에서 인수심사에 필요한 주요 Feature를 추출한다.
3. 추출된 Feature를 바탕으로 생성형 AI 리스크를 복수 분류한다.
4. Rule-based Underwriting Engine이 위험요소와 통제수준을 평가한다.
5. 보험가능성 Tier, 주요 위험, 판단 근거 및 권고 통제사항을 출력한다.

## 3. 시스템 입력

사용자는 기업이 생성형 AI를 어떤 업무에 활용하는지 자연어로 입력한다.

예시:

> 당사는 생성형 AI를 이용해 고객 문의에 자동 답변한다. 고객의 이름과 계약정보가 입력될 수 있으며, AI의 답변은 직원 검수 없이 고객에게 바로 제공된다.

## 4. LLM Feature Extraction

LLM은 입력문에서 다음과 같은 주요 Feature를 구조화하여 추출한다.

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

추출 결과는 이후 Risk Classification 및 Underwriting Engine에서 활용할 수 있도록 JSON 형식으로 변환한다.

## 5. Risk Classification

하나의 기업 AI 활용 사례에는 복수의 위험이 동시에 존재할 수 있으므로 Multi-label 방식으로 분류한다.

분류 대상은 다음 6개 리스크 모듈이다.

1. Fraud / Deepfake
2. Data Leakage / Privacy
3. Physical Safety
4. IP / Copyright
5. Hallucination / Misinformation
6. Bias / Discrimination

## 6. Rule-based Underwriting Engine

최종 보험가능성 판단은 LLM이 직접 수행하지 않고, 사전에 정의한 규칙 기반 로직을 사용한다.

현재 검토 중인 최종 출력 Tier는 다음과 같다.

- Tier 1: Insurable
- Tier 2: Conditionally Insurable
- Tier 3: Technical Referral
- Tier 4: Deferred / Excluded
- Tier 5: Uninsurable / Prohibited

각 Tier의 세부 판정 기준은 Feature 정의 및 Risk Mapping을 확정한 뒤 별도 규칙 문서에서 구체화한다.

## 7. 시스템 출력

시스템은 사용자에게 다음 정보를 제공한다.

- 추출된 주요 Feature
- 관련 Risk Module
- 보험가능성 Tier
- 주요 판단 근거
- 필요한 통제사항 및 증빙자료

## 8. 구현 범위

본 연구에서는 연구용 프로토타입 구현을 목표로 한다.

구현 범위는 다음과 같다.

- Streamlit 기반 단일 웹 화면
- 자연어 입력
- LLM 기반 Feature Extraction
- 6개 Risk Module 분류
- Rule-based Underwriting
- 결과 및 권고사항 출력

다음 기능은 본 프로토타입의 범위에서 제외한다.

- 실제 보험료 산출
- 보험사의 최종 인수결정 자동화
- 회원가입 및 사용자 관리
- 복잡한 데이터베이스 구축
- 상용 서비스 수준의 배포 및 보안 기능

## 9. 다음 설계 단계

다음 단계에서는 다음 항목을 구체화한다.

1. Feature 정의 및 입력값 형식 확정
2. Feature와 6개 Risk Module 간 Mapping 설계
3. Underwriting Tier 판정 규칙 설계
4. 테스트 시나리오 정의
5. Streamlit 프로토타입 구현
