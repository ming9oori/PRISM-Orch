# **Orchestration Agent 내부 동작 시나리오**

이 문서는 `orch_Agent_pipeline.png` 아키텍처를 기반으로, **Orchestration Agent**의 내부 모듈들이 어떻게 상호작용하여 사용자 질의를 해결하고 최적의 조치를 추천하는지 기술합니다.

### **Orchestration Agent 내부 모듈**

- **멀티 에이전트 관리 모듈:** 전체 워크플로우를 시작하고 조율하는 컨트롤 타워
- **에이전트 친화적 인스트럭션 수정 모듈:** 자연어 질의를 구조화된 명령으로 변환
- **에이전트 메모리 검색 모듈:** 내부 '에이전트 메모리 DB'에서 과거 유사 사례를 검색
- **외부 리서치 검색 모듈:** 외부 문서/지식 DB에서 관련 정보를 검색
- **검색 증강 과업 생성 모듈:** 검색된 정보를 활용하여, 다른 에이전트에게 시킬 구체적인 과업(Task)을 생성하고 계획을 수립
- **자율제어 액션 추천 모듈:** 모든 분석 결과를 종합하여 사용자에게 제시할 최종 조치(Action)를 생성 및 추천
- **메모리 편집 모듈:** 해결된 인시던트의 결과를 '에이전트 메모리 DB'에 저장하여 학습

---

## **Phase 1: 질의 해석 및 정보 수집**

**1. [외부 → Orchestration Agent] 사용자 질의 접수**
- 멀티 에이전트 관리 모듈이 플랫폼의 대화형 인터페이스를 통해 사용자 질의("3번 엣칭 장비 압력이 좀 이상한데, 확인해 줄 수 있나요?")를 수신합니다.
- 수신된 질의를 에이전트 친화적 인스트럭션 수정 모듈로 전달하여 해석을 요청합니다.

**2. [Orchestration Agent 내부] 질의 구조화 및 컨텍스트 검색**
- 에이전트 친화적 인스트럭션 수정 모듈이 자연어 질의를 분석하여 구조화된 명령(task: Check_Anomaly, target: Etching_Machine_#3, parameter: Pressure)을 생성합니다.
- 멀티 에이전트 관리 모듈은 이 구조화된 명령을 바탕으로, 문제 해결에 필요한 컨텍스트를 확보하기 위해 검색 모듈들을 동시에 호출합니다.
  - 에이전트 메모리 검색 모듈: 'Etching Machine Pressure Anomaly'와 관련된 과거 인시던트가 있었는지 에이전트 메모리 DB를 검색합니다.
  - 외부 리서치 검색 모듈: 해당 장비의 압력 이상에 대한 표준운영절차(SOP)나 기술 문서가 있는지 외부 리서치 벡터 DB를 검색합니다.

## **Phase 2: 과업 생성 및 순차적 실행**

**3. [Orchestration Agent 내부] 검색 증강 과업 생성**
- 검색 증강 과업 생성 모듈이 구조화된 명령과 함께, 검색 모듈들이 찾아낸 정보(유사 과거 사례, 관련 기술 문서 등)를 입력받습니다.
- 이 모든 정보를 종합하여, 문제 해결을 위한 구체적인 실행 계획(과업 리스트)을 생성합니다.
  - Plan: [Task-1: 모니터링 에이전트에 현재 상태 분석 요청] -> [Task-2: 예측 에이전트에 원인 및 미래 예측 요청] -> [Task-3: 자율제어 에이전트에 해결책 시뮬레이션 요청]

**4. [Orchestration Agent 내부] 과업 실행 및 결과 취합**
- 멀티 에이전트 관리 모듈이 생성된 계획에 따라, 각 과업을 순차적으로 실행하고 그 결과를 중앙 컨텍스트(State)에 지속적으로 취합합니다.

  **4.1. Task-1 실행: 현상 분석 (vs. 모니터링 에이전트)**
  - Action: 멀티 에이전트 관리 모듈이 계획의 첫 번째 과업을 시작합니다. 모니터링 에이전트에게 현재 장비의 상태 분석을 요청합니다.
  - Message (REQUEST_DATA_ANALYSIS):
    ```json
    { "task_id": "Task-1", "target": "Etching_Machine_#3", "parameter": "Pressure" }
    ```
  - Response (DATA_ANALYSIS_REPORT): 모니터링 에이전트로부터 이상 상태가 확정된 상세 보고서를 수신합니다.
    ```json
    { "task_id": "Task-1", "status": "Completed", "is_anomaly": true, "details": { ... } }
    ```
  - Result Aggregation: 멀티 에이전트 관리 모듈은 이 결과를 현재 인시던트의 컨텍스트에 저장합니다. (Fact: 압력 이상 확정)

  **4.2. Task-2 실행: 원인 추론 (vs. 예측 에이전트)**
  - Action: 멀티 에이전트 관리 모듈이 Task-1의 성공적인 완료를 확인하고, 두 번째 과업을 시작합니다. 예측 에이전트에게 원인 분석을 요청하며, 이전 단계에서 확보한 이상 데이터를 근거로 제공합니다.
  - Message (REQUEST_ROOT_CAUSE_ANALYSIS):
    ```json
    { "task_id": "Task-2", "anomaly_data": { "is_anomaly": true, "details": { ... } } }
    ```
  - Response (ROOT_CAUSE_ANALYSIS_REPORT): 예측 에이전트로부터 근본 원인에 대한 가설과 방치 시의 미래 예측 결과를 수신합니다.
    ```json
    { "task_id": "Task-2", "status": "Completed", "root_cause": { "description": "Gas_Valve_A stuck" }, "prediction": { "risk": "Yield drop" } }
    ```
  - Result Aggregation: 멀티 에이전트 관리 모듈은 이 결과를 컨텍스트에 추가합니다. (Hypothesis: 가스 밸브 오작동, Risk: 수율 저하)

  **4.3. Task-3 실행: 해결 방안 시뮬레이션 (vs. 자율제어 에이전트)**
  - Action: 멀티 에이전트 관리 모듈이 Task-2의 결과를 바탕으로, 세 번째 과업을 시작합니다. 자율제어 에이전트에게 추론된 원인을 해결할 수 있는 조치들의 효과를 시뮬레이션 하도록 요청합니다.
  - Message (REQUEST_ACTION_SIMULATION):
    ```json
    { "task_id": "Task-3", "root_cause": "Gas_Valve_A stuck", "target": "Etching_Machine_#3" }
    ```
  - Response (ACTION_SIMULATION_REPORT): 자율제어 에이전트로부터 각 조치 방안에 대한 시뮬레이션 결과를 수신합니다.
    ```json
    { "task_id": "Task-3", "status": "Completed", "simulation_results": [ { "action": "Recalibrate_Gas_Valve_A", "result": "2분 내 정상화", "success_rate": 0.98 }, { ... } ] }
    ```
  - Result Aggregation: 멀티 에이전트 관리 모듈은 시뮬레이션 결과를 컨텍스트에 추가합니다. (Solution: 밸브 재보정 시 98% 확률로 정상화)

## **Phase 3: 최종 조치 추천 및 학습**

**5. [Orchestration Agent 내부] 자율제어 액션 추천 생성**
- 자율제어 액션 추천 모듈이 멀티 에이전트 관리 모듈이 취합한 모든 분석/예측/시뮬레이션 결과를 전달받습니다.
- 모든 정보를 종합하여, 사용자에게 제시할 가장 안전하고(Safe) 효과적인 최종 '자율제어 액션 추천' 메시지를 생성합니다.

**6. [Orchestration Agent → 외부] 최종 액션 추천 전달**
- 멀티 에이전트 관리 모듈이 생성된 최종 추천안을 '대화형 인터페이스'로 전달하여 사용자에게 제시하도록 합니다.

**7. [Orchestration Agent 내부] 사후 처리: 메모리 편집 (학습)**
- 사용자가 추천된 조치를 수행하여 문제가 해결된 후, 그 결과가 피드백으로 시스템에 다시 입력됩니다.
- 메모리 편집 모듈이 이번 인시던트의 전체 과정(사용자 질의, 분석 결과, 추천 조치, 최종 결과)을 하나의 학습 데이터로 정리합니다.
- 정리된 데이터를 에이전트 메모리 DB에 저장하여, 향후 더 빠르고 정확한 문제 해결에 사용될 수 있도록 합니다.