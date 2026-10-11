# Feature Definition v0.1

## 1. 목적

본 문서는 LLM이 기업의 생성형 AI 활용 설명에서 추출할 주요 Feature를 정의하고,
각 Feature가 6개 Risk Module과 어떻게 연결되는지 정리하기 위한 설계 문서이다.

본 단계에서는 실제 보험사의 최종 인수기준을 재현하는 것이 아니라,
연구용 프로토타입에서 일관된 위험평가를 수행하기 위한 최소 Feature 집합을 정의한다.

---

## 2. Feature 목록

### 2.1 customer_facing

- 의미: 생성형 AI의 출력이 외부 고객에게 직접 제공되는지 여부
- 타입: boolean
- 값:
  - true: 고객에게 직접 노출됨
  - false: 내부 업무에서만 사용됨
- 추출 예시:
  - "고객 문의에 AI가 자동 답변한다" → true
  - "사내 보고서 초안 작성에만 사용한다" → false
- 주요 연계 Risk:
  - Hallucination / Misinformation
  - Bias / Discrimination
  - Fraud / Deepfake

### 2.2 handles_pii

- 의미: AI 입력 또는 처리 과정에 개인식별정보가 포함되는지 여부
- 타입: boolean
- 예시 정보:
  - 이름
  - 연락처
  - 주민등록번호
  - 고객번호
  - 계약정보
- 주요 연계 Risk:
  - Data Leakage / Privacy

### 2.3 handles_sensitive_data

- 의미: 일반 개인정보보다 민감도가 높은 정보가 처리되는지 여부
- 타입: boolean
- 예시:
  - 건강정보
  - 금융정보
  - 생체정보
  - 법률 관련 민감정보
- 주요 연계 Risk:
  - Data Leakage / Privacy

### 2.4 human_review

- 의미: AI 출력이 실제 업무에 사용되기 전에 사람이 검토하는 절차가 존재하는지 여부
- 타입: boolean
- 값:
  - true: Human-in-the-Loop 존재
  - false: 검토 없이 AI 출력 사용
- 주요 연계 Risk:
  - Hallucination / Misinformation
  - Bias / Discrimination
  - Physical Safety

### 2.5 autonomous_output

- 의미: AI의 출력이 별도의 인간 승인 없이 외부 시스템이나 업무결과에 직접 반영되는지 여부
- 타입: boolean
- 예시:
  - 자동 이메일 발송
  - 자동 승인/거절
  - 자동 주문/처리
- 주요 연계 Risk:
  - Hallucination / Misinformation
  - Physical Safety
  - Bias / Discrimination

### 2.6 external_vendor

- 의미: 자체 모델이 아닌 외부 생성형 AI 서비스 또는 API를 사용하는지 여부
- 타입: boolean
- 예시:
  - 외부 LLM API 사용
  - SaaS 형태의 생성형 AI 서비스 사용
- 주요 연계 Risk:
  - Data Leakage / Privacy
  - IP / Copyright

### 2.7 vendor_contract_clear

- 의미: 외부 AI 사업자와 데이터 처리, 책임, 보안, 로그 등에 대한 계약 또는 정책이 명확한지 여부
- 타입: enum
- 값:
  - true
  - false
  - unknown
- 적용 조건:
  - external_vendor = true 인 경우에만 평가
- 주요 연계 Risk:
  - Data Leakage / Privacy
  - IP / Copyright

### 2.8 logging_enabled

- 의미: 생성형 AI의 주요 입력 및 출력 기록을 사후 검토할 수 있도록 저장하는지 여부
- 타입: boolean
- 주요 연계 Risk:
  - Fraud / Deepfake
  - Data Leakage / Privacy
  - Hallucination / Misinformation
  - Bias / Discrimination

### 2.9 safety_critical_use

- 의미: AI의 오류가 사람의 생명, 신체 또는 물리적 안전에 직접 영향을 줄 수 있는 업무에 사용되는지 여부
- 타입: boolean
- 예시:
  - 의료 의사결정 지원
  - 산업설비 제어
  - 운송/안전 관련 시스템
- 주요 연계 Risk:
  - Physical Safety

### 2.10 human_decision_support

- 의미: AI의 출력이 채용, 대출, 보험, 평가 등 사람에게 중대한 영향을 미치는 의사결정에 사용되는지 여부
- 타입: boolean
- 주요 연계 Risk:
  - Bias / Discrimination
  - Hallucination / Misinformation

### 2.11 media_generation

- 의미: 이미지, 음성, 영상 등 합성 미디어를 생성하는 기능을 사용하는지 여부
- 타입: boolean
- 주요 연계 Risk:
  - Fraud / Deepfake
  - IP / Copyright

### 2.12 copyright_content_use

- 의미: 저작권이 있는 콘텐츠를 학습, 입력, 변환 또는 생성 과정에서 사용하는지 여부
- 타입: enum
- 값:
  - true
  - false
  - unknown
- 주요 연계 Risk:
  - IP / Copyright

---

## 3. LLM Extraction 출력 형식

LLM의 출력은 아래 JSON Schema 형태를 기본으로 한다.

```json
{
  "customer_facing": true,
  "handles_pii": true,
  "handles_sensitive_data": false,
  "human_review": false,
  "autonomous_output": true,
  "external_vendor": true,
  "vendor_contract_clear": "unknown",
  "logging_enabled": false,
  "safety_critical_use": false,
  "human_decision_support": false,
  "media_generation": false,
  "copyright_content_use": "unknown"
}
```

입력문에 명시되지 않은 정보는 임의로 추정하지 않고,
가능한 경우 `unknown`으로 처리한다.

boolean Feature는 정보가 불충분한 경우 추후 구현 단계에서
`null` 허용 여부를 검토한다.

---

## 4. Feature - Risk Mapping

| Feature | Fraud / Deepfake | Privacy | Physical Safety | IP / Copyright | Hallucination | Bias |
|---|---:|---:|---:|---:|---:|---:|
| customer_facing | O |  |  |  | O | O |
| handles_pii |  | O |  |  |  |  |
| handles_sensitive_data |  | O |  |  |  |  |
| human_review = false |  |  | O |  | O | O |
| autonomous_output |  |  | O |  | O | O |
| external_vendor |  | O |  | O |  |  |
| vendor_contract_clear = false |  | O |  | O |  |  |
| logging_enabled = false | O | O |  |  | O | O |
| safety_critical_use |  |  | O |  |  |  |
| human_decision_support |  |  |  |  | O | O |
| media_generation | O |  |  | O |  |  |
| copyright_content_use |  |  |  | O |  |  |

이 Mapping은 Risk Module 활성화의 기본 조건으로 사용하며,
실제 위험수준은 하나의 Feature만으로 결정하지 않고
여러 Feature의 조합을 이용해 산출한다.

---

## 5. 1차 Risk Rule 예시

### Fraud / Deepfake

다음 조건 중 하나 이상을 만족하면 활성화 후보로 판단한다.

- media_generation = true
- customer_facing = true AND logging_enabled = false

### Data Leakage / Privacy

다음 조건 중 하나 이상을 만족하면 활성화한다.

- handles_pii = true
- handles_sensitive_data = true
- external_vendor = true AND vendor_contract_clear != true

### Physical Safety

다음 조건을 중심으로 판단한다.

- safety_critical_use = true

위 조건에서 human_review = false 또는 autonomous_output = true이면
위험도를 추가로 높이는 요소로 사용한다.

### IP / Copyright

다음 조건 중 하나 이상을 만족하면 활성화 후보로 판단한다.

- copyright_content_use = true
- media_generation = true
- external_vendor = true AND vendor_contract_clear = false

### Hallucination / Misinformation

다음 조건 중 하나 이상을 만족하면 활성화 후보로 판단한다.

- customer_facing = true
- autonomous_output = true
- human_decision_support = true

위 조건에서 human_review = false이면 위험도를 추가로 높인다.

### Bias / Discrimination

다음 조건을 중심으로 판단한다.

- human_decision_support = true
- customer_facing = true AND human_review = false

---

## 6. 설계 원칙

1. LLM은 자연어 입력을 구조화하는 역할에 집중한다.
2. 최종 Risk 및 Tier 판단은 규칙 기반 로직에서 수행한다.
3. 입력에 없는 정보는 임의로 사실처럼 생성하지 않는다.
4. 하나의 사례에 여러 Risk Module을 동시에 부여할 수 있다.
5. 위험 여부와 보험가능성 Tier는 서로 분리하여 판단한다.
6. 실제 보험료 또는 손해확률을 예측하는 모델로 해석하지 않는다.

---

## 7. 다음 단계

다음 설계 단계에서는 아래 항목을 구체화한다.

1. Risk Module별 위험수준 산정 방식 정의
2. 각 Feature의 가중치 또는 조건 조합 설계
3. 5단계 Underwriting Tier 판정 규칙 확정
4. 예시 기업 시나리오 작성
5. Python Rule Engine 구현
