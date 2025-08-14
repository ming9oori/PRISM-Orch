# 오케스트레이션 에이전트 DB Schema

## 핵심 테이블 구조

### 1. 테이블명: ORCH_TASK_MANAGE -- 오케스트레이션 태스크 관리 테이블

| 설명 | | | |
|------|------|------|------|
| 오케스트레이션 과업의 전체 생명주기 및 상태를 관리하는 중심 테이블. 사용자 질의로부터 생성된 태스크를 추적하고 관리 | | | |

| **필드명** | **데이터타입** | **필수여부** | **설명** |
|------------|----------------|--------------|----------|
| TASK_ID | VARCHAR(PK) | Y | 오케스트레이션 태스크 고유 ID |
| USER_ID | VARCHAR | Y | 사용자 식별자 |
| STATUS | VARCHAR | Y | 태스크 상태(ACTIVE/COMPLETED/FAILED/CANCELLED) |
| CREATED_AT | DATETIME | Y | 세션 시작 시각 |
| UPDATED_AT | DATETIME | Y | 최종 업데이트 시각 |
| TOTAL_DURATION | FLOAT | N | 총 소요 시간(초) |
| PRIORITY | VARCHAR | Y | 우선순위(HIGH/NORMAL/LOW) |
| ERROR_MESSAGE | TEXT | N | 오류 발생 시 메시지 |

### 2. 테이블명: ORCH_USER_QUERY -- 사용자 질의 관리 테이블

| **필드명** | **데이터타입** | **필수여부** | **설명** |
|------------|----------------|--------------|----------|
| QUERY_ID | VARCHAR(PK) | Y | 사용자 질의 고유 식별자 |
| TASK_ID | VARCHAR(FK) | Y | FK: ORCH_TASK_MANAGE.TASK_ID |
| QUERY_TEXT | TEXT | Y | 입력된 자연어 질의 원문 |
| QUERY_TYPE | VARCHAR | Y | 질의 유형(MONITORING/PREDICTION/CONTROL) |
| PARSED_INTENT | JSON | N | LLM이 파싱한 의도 구조체 |
| USER_CONSTRAINTS | VARCHAR | N | 사용자 정의 제약조건 |
| CREATED_AT | DATETIME | Y | 질의 입력 시각 |
| RESPONSE_TIME | FLOAT | N | 응답 소요 시간(초) |

### 3. 테이블명: ORCH_EXECUTION_PLAN -- 오케스트레이션 실행 계획 테이블

| **필드명** | **데이터타입** | **필수여부** | **설명** |
|------------|----------------|--------------|----------|
| PLAN_ID | VARCHAR(PK) | Y | 실행 계획 고유 ID |
| TASK_ID | VARCHAR(FK) | Y | FK: ORCH_TASK_MANAGE.TASK_ID |
| QUERY_ID | VARCHAR(FK) | Y | FK: ORCH_USER_QUERY.QUERY_ID |
| TASK_GRAPH | JSON | Y | 에이전트 실행 DAG(의존성 포함) |
| RISK_ASSESSMENT | VARCHAR | N | 위험도 평가(LOW/MEDIUM/HIGH) |
| CONSTRAINT_CHECK | JSON | N | 제약조건 검토 결과 |
| PLAN_STATUS | VARCHAR | Y | 계획 상태(PENDING/EXECUTING/COMPLETED/FAILED) |
| CREATED_AT | DATETIME | Y | 계획 생성 시각 |
| STARTED_AT | DATETIME | N | 실행 시작 시각 |
| COMPLETED_AT | DATETIME | N | 실행 완료 시각 |
| EMBEDDER_INFO | VARCHAR | Y | 임베더 정보 |

### 4. 테이블명: ORCH_AGENT_SUBTASK -- 에이전트 서브태스크 실행 테이블

| **필드명** | **데이터타입** | **필수여부** | **설명** |
|------------|----------------|--------------|----------|
| SUBTASK_ID | VARCHAR(PK) | Y | 서브태스크 고유 ID |
| PLAN_ID | VARCHAR(FK) | Y | FK: ORCH_EXECUTION_PLAN.PLAN_ID |
| AGENT_ID | VARCHAR | Y | 실행 에이전트 ID |
| AGENT_TYPE | VARCHAR | Y | 에이전트 유형(MONITORING/PREDICTION/CONTROL/ANALYSIS) |
| SEQUENCE_ORDER | INT | Y | 실행 순서 번호 |
| INPUT_DATA | JSON | N | 에이전트 입력 데이터 |
| OUTPUT_DATA | JSON | N | 에이전트 출력 결과 |
| SUBTASK_STATUS | VARCHAR | Y | 상태(QUEUED/RUNNING/SUCCESS/FAILED/SKIPPED) |
| ERROR_MESSAGE | TEXT | N | 오류 발생 시 메시지 |
| ACTUAL_DURATION | FLOAT | N | 실제 실행 시간(초) |
| STARTED_AT | DATETIME | N | 실행 시작 시각 |
| COMPLETED_AT | DATETIME | N | 실행 완료 시각 |
| RETRY_COUNT | INT | Y | 재시도 횟수 |

## 제약조건 및 피드백 관리 스키마

### 5. 테이블명: ORCH_CONSTRAINT_VIOLATION -- 제약조건 위반 관리 테이블

| **필드명** | **데이터타입** | **필수여부** | **설명** |
|------------|----------------|--------------|----------|
| VIOLATION_ID | VARCHAR(PK) | Y | 위반 고유 식별자 |
| PLAN_ID | VARCHAR(FK) | Y | FK: ORCH_EXECUTION_PLAN.PLAN_ID |
| SUBTASK_ID | VARCHAR(FK) | N | FK: ORCH_AGENT_SUBTASK.SUBTASK_ID |
| CONSTRAINT_TYPE | VARCHAR | Y | 제약 유형(RESOURCE/TIME/SAFETY/POLICY) |
| CONSTRAINT_NAME | VARCHAR | Y | 위반된 제약 조건 이름 |
| EXPECTED_VALUE | VARCHAR | N | 기대값 |
| ACTUAL_VALUE | VARCHAR | N | 실제값 |
| SEVERITY_LEVEL | VARCHAR | Y | 심각도(INFO/WARNING/ERROR/CRITICAL) |
| IS_BLOCKING | BOOLEAN | Y | 실행 차단 여부 |
| RESOLUTION_ACTION | VARCHAR | N | 해결 조치 내용 |
| DETECTED_AT | DATETIME | Y | 위반 감지 시각 |
| RESOLVED_AT | DATETIME | N | 해결 시각 |

### 6. 테이블명: ORCH_USER_FEEDBACK -- 사용자 피드백 관리 테이블

| **필드명** | **데이터타입** | **필수여부** | **설명** |
|------------|----------------|--------------|----------|
| FEEDBACK_ID | VARCHAR(PK) | Y | 피드백 고유 식별자 |
| TASK_ID | VARCHAR(FK) | Y | FK: ORCH_TASK_MANAGE.TASK_ID |
| PLAN_ID | VARCHAR(FK) | N | FK: ORCH_EXECUTION_PLAN.PLAN_ID |
| FEEDBACK_TYPE | VARCHAR | Y | 피드백 유형(MODIFICATION/CANCELLATION/APPROVAL/COMPLAINT) |
| FEEDBACK_CONTENT | TEXT | N | 자연어 피드백 내용 |
| ACTION_TAKEN | VARCHAR | Y | 조치사항(APPLIED/IGNORED/DEFERRED) |
| SYSTEM_RESPONSE | TEXT | N | 시스템 처리 결과 설명 |
| IMPACT_SCOPE | VARCHAR | N | 영향 범위(CURRENT_TASK/FUTURE_TASKS/GLOBAL_SETTINGS) |
| SUBMITTED_AT | DATETIME | Y | 피드백 제출 시각 |
| PROCESSED_AT | DATETIME | N | 피드백 처리 시각 |
| SATISFACTION_SCORE | INT | N | 만족도 점수(1-5) |

## 지식 베이스 및 메모리 관리 스키마

### 7. 테이블명: ORCH_EXTERNAL_KNOWLEDGE -- 외부 지식 관리 테이블

| **필드명** | **데이터타입** | **필수여부** | **설명** |
|------------|----------------|--------------|----------|
| KNOWLEDGE_ID | VARCHAR(PK) | Y | 지식 문서 고유 ID |
| DOCUMENT_TITLE | VARCHAR | Y | 문서 제목 |
| DOCUMENT_TYPE | VARCHAR | Y | 문서 유형(RESEARCH_PAPER/MANUAL/GUIDELINE/FAQ) |
| CONTENT_SUMMARY | TEXT | N | 문서 내용 요약 |
| EMBEDDING_VECTOR | VECTOR | Y | 문서 임베딩 벡터 |
| METADATA | JSON | N | 출처, 저자, 태그 등 메타데이터 |
| RELEVANCE_SCORE | FLOAT | N | 검색 관련성 점수(동적) |
| ACCESS_COUNT | INT | Y | 참조 횟수 |
| LAST_ACCESSED | DATETIME | N | 최종 접근 시각 |
| CREATED_AT | DATETIME | Y | 문서 추가 시각 |
| EMBEDDER_INFO | VARCHAR | Y | 임베더 정보 |
| VERSION | VARCHAR | N | 문서 버전 |

### 8. 테이블명: ORCH_AGENT_MEMORY -- 에이전트 메모리 관리 테이블

| **필드명** | **데이터타입** | **필수여부** | **설명** |
|------------|----------------|--------------|----------|
| MEMORY_ID | VARCHAR(PK) | Y | 메모리 항목 고유 ID |
| AGENT_ID | VARCHAR | Y | 에이전트 식별자 |
| MEMORY_TYPE | VARCHAR | Y | 메모리 유형(SHORT_TERM/LONG_TERM/EPISODIC) |
| CONTEXT_DATA | JSON | Y | 컨텍스트 정보 |
| EMBEDDING_VECTOR | VECTOR | N | 메모리 임베딩 벡터 |
| IMPORTANCE_SCORE | FLOAT | Y | 중요도 점수 |
| DECAY_RATE | FLOAT | Y | 감쇠율 |
| ACCESS_FREQUENCY | INT | Y | 접근 빈도 |
| CREATED_AT | DATETIME | Y | 생성 시각 |
| LAST_ACCESSED | DATETIME | N | 최종 접근 시각 |
| EXPIRY_DATE | DATETIME | N | 만료 예정일 |

### 9. 테이블명: ORCH_INSTRUCTION_REWRITE -- 인스트럭션 재작성 이력 테이블

| **필드명** | **데이터타입** | **필수여부** | **설명** |
|------------|----------------|--------------|----------|
| REWRITE_ID | VARCHAR(PK) | Y | 재작성 고유 ID |
| QUERY_ID | VARCHAR(FK) | Y | FK: ORCH_USER_QUERY.QUERY_ID |
| ORIGINAL_INSTRUCTION | TEXT | Y | 원본 인스트럭션 |
| REWRITTEN_INSTRUCTION | TEXT | Y | 재작성된 인스트럭션 |
| REWRITE_REASON | VARCHAR | N | 재작성 사유 |
| IMPROVEMENT_SCORE | FLOAT | N | 개선도 점수 |
| AGENT_COMPATIBILITY | JSON | N | 에이전트 호환성 정보 |
| CREATED_AT | DATETIME | Y | 재작성 시각 |
| VALIDATION_STATUS | VARCHAR | Y | 검증 상태 |

### 10. 테이블명: ORCH_SEARCH_AUGMENTATION -- 검색 증강 이력 테이블

| **필드명** | **데이터타입** | **필수여부** | **설명** |
|------------|----------------|--------------|----------|
| AUGMENTATION_ID | VARCHAR(PK) | Y | 증강 작업 고유 ID |
| PLAN_ID | VARCHAR(FK) | Y | FK: ORCH_EXECUTION_PLAN.PLAN_ID |
| SEARCH_QUERY | TEXT | Y | 검색 쿼리 |
| SEARCH_RESULTS | JSON | N | 검색 결과 |
| SELECTED_DOCUMENTS | JSON | N | 선택된 문서 목록 |
| RELEVANCE_SCORES | JSON | N | 관련성 점수 |
| AUGMENTATION_TYPE | VARCHAR | Y | 증강 유형(CONTEXT/KNOWLEDGE/EXAMPLE) |
| CREATED_AT | DATETIME | Y | 생성 시각 |
| USAGE_COUNT | INT | Y | 활용 횟수 |

## 모니터링 및 성능 관리 스키마

### 11. 테이블명: ORCH_PERFORMANCE_METRICS -- 성능 지표 관리 테이블

| **필드명** | **데이터타입** | **필수여부** | **설명** |
|------------|----------------|--------------|----------|
| METRIC_ID | VARCHAR(PK) | Y | 지표 고유 ID |
| TASK_ID | VARCHAR(FK) | Y | FK: ORCH_TASK_MANAGE.TASK_ID |
| METRIC_TYPE | VARCHAR | Y | 지표 유형(LATENCY/THROUGHPUT/ACCURACY/RESOURCE) |
| METRIC_NAME | VARCHAR | Y | 지표명 |
| METRIC_VALUE | FLOAT | Y | 측정값 |
| UNIT | VARCHAR | Y | 단위 |
| THRESHOLD_MIN | FLOAT | N | 최소 임계값 |
| THRESHOLD_MAX | FLOAT | N | 최대 임계값 |
| MEASURED_AT | DATETIME | Y | 측정 시각 |
| AGENT_ID | VARCHAR | N | 관련 에이전트 ID |

### 12. 테이블명: ORCH_ALERT_CONFIG -- 알람 설정 관리 테이블

| **필드명** | **데이터타입** | **필수여부** | **설명** |
|------------|----------------|--------------|----------|
| CONFIG_ID | VARCHAR(PK) | Y | 설정 고유 ID |
| ALERT_NAME | VARCHAR | Y | 알람명 |
| ALERT_TYPE | VARCHAR | Y | 알람 유형(PERFORMANCE/ERROR/CONSTRAINT/FEEDBACK) |
| CONDITION_RULE | JSON | Y | 발생 조건 규칙 |
| NOTIFICATION_CHANNEL | VARCHAR | Y | 알림 채널(EMAIL/SMS/SLACK/WEBHOOK) |
| RECIPIENT_LIST | JSON | Y | 수신자 목록 |
| SEVERITY | VARCHAR | Y | 심각도(LOW/MEDIUM/HIGH/CRITICAL) |
| IS_ENABLED | BOOLEAN | Y | 활성화 여부 |
| CREATED_AT | DATETIME | Y | 생성 시각 |
| UPDATED_AT | DATETIME | Y | 수정 시각 |

## 오케스트레이션 활용 시나리오

### 1. 작업 조율 및 실행 관리
- `ORCH_TASK_MANAGE` + `ORCH_EXECUTION_PLAN`을 통한 전체 작업 흐름 관리
- `ORCH_AGENT_SUBTASK`의 시퀀스 기반 에이전트 간 협업 조율

### 2. 제약조건 기반 최적화
- `ORCH_CONSTRAINT_VIOLATION`을 통한 실시간 제약 위반 감지
- 피드백 루프를 통한 동적 계획 수정 및 재실행

### 3. 지식 기반 의사결정
- `ORCH_EXTERNAL_KNOWLEDGE`와 `ORCH_SEARCH_AUGMENTATION`을 활용한 RAG 기반 증강
- `ORCH_AGENT_MEMORY`를 통한 과거 경험 학습 및 활용

### 4. 사용자 인터랙션 최적화
- `ORCH_USER_FEEDBACK`을 통한 지속적 개선
- `ORCH_INSTRUCTION_REWRITE`를 통한 자연어 명령 최적화

## 오케스트레이션별 주요 모니터링 포인트

### 태스크 관리
- **TOTAL_DURATION** 증가 → 병목 현상 발생
- **ERROR_MESSAGE** 빈도 → 시스템 안정성 저하
- **STATUS** 분포 → 성공률 모니터링

### 에이전트 협업
- **SEQUENCE_ORDER** 의존성 → 실행 순서 최적화
- **RETRY_COUNT** 증가 → 에이전트 신뢰성 문제
- **ACTUAL_DURATION** vs 예상 시간 → 성능 저하 감지

### 제약조건 관리
- **SEVERITY_LEVEL** 분포 → 위험도 평가
- **IS_BLOCKING** 빈도 → 작업 중단 원인 분석
- **RESOLUTION_ACTION** 패턴 → 자동 해결 방안 도출

### 지식 활용
- **RELEVANCE_SCORE** 하락 → 지식 베이스 업데이트 필요
- **ACCESS_COUNT** 패턴 → 자주 사용되는 지식 식별
- **DECAY_RATE** 조정 → 메모리 효율성 최적화