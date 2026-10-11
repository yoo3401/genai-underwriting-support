# Underwriting Tier Rules v0.1

## 1. 목적

본 문서는 생성형 AI 활용 기업의 위험평가 결과를 바탕으로
연구용 프로토타입에서 사용할 5단계 Underwriting Tier 판정 규칙을 정의한다.

본 Tier는 실제 보험사의 인수정책이나 보험료 산출기준을 재현하는 것이 아니라,
생성형 AI 활용 위험을 일관된 기준으로 구분하기 위한 연구용 의사결정 규칙이다.

또한 사전 실험에서 사용한 4단계
`PREFERRED / STANDARD / CONDITIONAL / DECLINE` 분류와는 구분한다.
사전 실험은 주요 분기 변수의 영향 확인을 위한 예비 실험이며,
최종 프로토타입에서는 아래 5단계 Tier 체계를 사용한다.

---

## 2. 최종 Tier 정의

### Tier 1: Insurable

위험요소가 제한적이며 주요 통제수단이 적용된 상태.

예시 조건:
- 고객에게 직접 노출되지 않음
- 개인정보 또는 민감정보 처리 없음
- Human Review 존재
- 자율적 출력 또는 자동 의사결정 없음
- 주요 기록(Log) 보관 가능

의미:
- 기본적으로 보험 인수 검토 가능
- 추가적인 기술적 검토 필요성이 낮음

---

### Tier 2: Conditionally Insurable

위험요소가 존재하지만 적절한 통제수단을 추가하거나 증빙할 경우
보험 인수 검토가 가능한 상태.

예시 조건:
- Customer Facing 서비스
- 개인정보 처리
- 외부 LLM 또는 SaaS 사용
- 합성 미디어 생성
- Human Decision Support 사용

단, 다음과 같은 통제가 일부 존재하는 경우:
- Human Review
- Logging
- 명확한 Vendor Contract
- 개인정보 보호조치

의미:
- 조건부 인수 가능
- 특정 통제조치 또는 증빙자료 요구

---

### Tier 3: Technical Referral

위험도가 높거나 입력정보가 불충분하여
자동 규칙만으로 판단하기 어려운 상태.

예시 조건:
- 중요 Feature가 여러 개 `unknown`
- 외부 Vendor를 사용하지만 계약 및 데이터 처리조건이 불명확
- 고객 대상 서비스이면서 Human Review가 없음
- Human Decision Support가 존재하면서 결과 검증 절차가 불충분
- 복수의 주요 Risk Module이 동시에 활성화

의미:
- 기술 전문가 또는 Underwriter의 추가 검토 필요
- 자동 인수판정 중단
- 추가 증빙 및 인터뷰 필요

---

### Tier 4: Deferred / Excluded

현재 상태로는 위험통제가 부족하여
즉시 인수하기 어려운 상태.

예시 조건:
- 개인정보 또는 민감정보를 처리하면서 적절한 통제수단이 없음
- Safety Critical Use에서 Human Review가 없음
- 고객 대상 자동 출력이 존재하고 Logging과 Human Review가 모두 없음
- 고위험 의사결정을 AI가 사실상 자동 수행

의미:
- 현재 조건에서는 인수 유보 또는 특정 위험 제외
- 통제 개선 후 재심사 가능

---

### Tier 5: Uninsurable / Prohibited

연구용 규칙상 보험으로 이전하기보다
사용 자체의 제한 또는 별도 법적·정책적 검토가 우선되어야 하는 상태.

예시 조건:
- 명백한 불법적 또는 기만적 목적의 합성 미디어 사용
- 안전에 중대한 영향을 주는 업무를 완전 자동화하면서 인간 통제가 없음
- 차별적 또는 불법적 의사결정을 의도적으로 자동화
- 시스템 입력 자체에서 금지 또는 비정상적 활용 목적이 확인됨

의미:
- 자동 인수 대상에서 제외
- 법률/컴플라이언스 검토 우선

---

## 3. Tier 판정 우선순위

Tier 판정은 낮은 위험에서 높은 위험으로 점수를 단순 합산하는 방식보다
명확한 고위험 조건을 먼저 확인하는 Rule Priority 방식을 사용한다.

판정 순서는 다음과 같다.

1. Tier 5 금지/비정상 사용 여부 확인
2. Tier 4 즉시 인수 곤란 조건 확인
3. Tier 3 추가 검토 필요 조건 확인
4. Tier 2 조건부 인수 조건 확인
5. 위 조건에 해당하지 않을 경우 Tier 1

즉, 여러 Tier 조건이 동시에 충족되면 더 높은 위험의 Tier를 우선 적용한다.

---

## 4. 1차 판정 규칙

### Rule T5-1
`prohibited_use = true`

→ Tier 5

※ prohibited_use는 추후 LLM 입력분석 단계에서 별도 Flag로 추가할 수 있다.

### Rule T4-1
`safety_critical_use = true`
AND `human_review = false`

→ Tier 4

### Rule T4-2
`handles_sensitive_data = true`
AND `logging_enabled = false`
AND `human_review = false`

→ Tier 4

### Rule T4-3
`customer_facing = true`
AND `autonomous_output = true`
AND `human_review = false`
AND `logging_enabled = false`

→ Tier 4

### Rule T3-1
`external_vendor = true`
AND `vendor_contract_clear = unknown`

→ Tier 3

### Rule T3-2
`human_decision_support = true`
AND `human_review = false`

→ Tier 3

### Rule T3-3
활성화된 주요 Risk Module이 3개 이상이고,
명확한 통제수단이 부족한 경우

→ Tier 3

### Rule T3-4
주요 Feature 중 `unknown` 값이 3개 이상인 경우

→ Tier 3

### Rule T2-1
`customer_facing = true`
AND `human_review = true`

→ Tier 2

### Rule T2-2
`handles_pii = true`
AND `logging_enabled = true`
AND `human_review = true`

→ Tier 2

### Rule T2-3
`external_vendor = true`
AND `vendor_contract_clear = true`

→ Tier 2

### Rule T2-4
`media_generation = true`
AND `human_review = true`

→ Tier 2

### Rule T1-1
위 Tier 2~5 조건에 해당하지 않고
다음 조건을 대체로 만족하는 경우

- customer_facing = false
- handles_pii = false
- handles_sensitive_data = false
- autonomous_output = false
- safety_critical_use = false
- human_decision_support = false

→ Tier 1

---

## 5. Risk Module 수와 Tier 관계

Risk Module 개수만으로 Tier를 결정하지 않는다.

예를 들어 Privacy와 Hallucination Risk가 동시에 활성화되어도
Human Review와 Logging이 충분히 적용되어 있다면 Tier 2가 가능하다.

반대로 Risk Module이 하나뿐이더라도
Physical Safety 위험이 존재하고 Human Review가 없다면 Tier 4가 될 수 있다.

따라서 최종 Tier는 다음을 함께 고려한다.

- 위험 유형
- 위험의 중요도
- Human Review
- Logging
- 개인정보 처리
- 외부 Vendor 관리
- 자율적 출력 여부
- 입력정보의 완전성

---

## 6. 출력 설명 방식

시스템은 Tier만 출력하지 않고
판정에 사용된 주요 Rule을 함께 제시한다.

예시:

```text
Underwriting Tier: Tier 3 - Technical Referral

판단 근거:
- 외부 LLM 서비스를 사용함
- Vendor 계약 및 데이터 처리조건이 확인되지 않음
- 고객에게 직접 AI 출력이 제공됨

추가 요구사항:
- Vendor 계약조건 확인
- 데이터 저장 및 재사용 정책 확인
- Human Review 절차 증빙
```

이를 통해 규칙 기반 시스템의 설명가능성을 확보한다.

---

## 7. 구현 시 필요한 추가 항목

현재 Feature 정의에 아래 항목을 추가할지 구현 단계에서 검토한다.

- prohibited_use
- privacy_control
- access_control
- data_retention_policy
- output_validation

다만 MVP의 복잡도를 줄이기 위해
초기 구현에서는 기존 Feature를 우선 사용하고,
필요한 경우에만 최소한으로 추가한다.

---

## 8. 다음 단계

다음 단계에서는 다음 작업을 수행한다.

1. 테스트용 기업 AI 활용 시나리오 작성
2. 각 시나리오의 기대 Risk Module 및 Tier 정의
3. Python Rule Engine 구현
4. Rule Engine 결과와 기대 결과 비교
5. 이후 LLM Feature Extraction과 연결
