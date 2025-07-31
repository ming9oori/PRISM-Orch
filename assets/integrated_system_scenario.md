# **시나리오: 사용자 문의 기반 이상 탐지 및 해결 방안 권고**

이 문서는 사용자의 문의로부터 시작하여, 여러 에이전트가 협력하여 문제의 원인을 분석하고 **최적의 해결 방안을 시뮬레이션하여 사용자에게 최종 권고**하는 과정을 상세히 기술합니다.

### **등장 요소 (Participants)**

1.  **사용자 (User):** 최종 의사결정 및 조치를 수행하는 공정 엔지니어 또는 오퍼레이터.
2.  **플랫폼 (Platform):** 사용자와 시스템 간의 상호작용을 위한 UI/UX.
3.  **모니터링 에이전트 (Monitoring Agent):** 장비 데이터의 실시간 수집 및 이상 상태 감지 담당.
4.  **오케스트레이션 에이전트 (Orchestration Agent):** 전체 분석 및 시뮬레이션 과정을 지휘하고, 최종 권고안을 종합하는 총괄 에이전트.
5.  **예측 에이전트 (Prediction Agent):** 데이터 심층 분석, 근본 원인 추론, 미래 상태 예측 담당.
6.  **자율제어 에이전트 (Autonomous Control Agent):** 제어 방안의 효과와 영향을 **시뮬레이션**하는 역할 담당.

### **전제 조건 (Prerequisites)**

- 모든 에이전트는 정상 작동 중입니다.
- 반도체 엣칭 장비 (`Etching_Machine_#3`)는 공정을 수행 중입니다.

---

## **Phase 1: 문의 접수 및 이상 탐지**

**1. [사용자 → 플랫폼] 이상 여부 문의**
- **Action:** 사용자가 플랫폼을 통해 `Etching_Machine_#3`의 압력 상태에 대한 확인을 요청합니다.
- **Message (User Input):** `"3번 엣칭 장비 압력이 좀 이상한데, 확인해 줄 수 있나요?"`

**2. [플랫폼 → 오케스트레이션 에이전트] 분석 요청 생성**
- **Action:** 플랫폼은 사용자 문의를 해석하여 공식 분석 요청을 생성하고 오케스트레이션 에이전트에게 전달합니다.
- **Message (`REQUEST_INVESTIGATION`):**
  ```json
  {
    "type": "USER_INQUIRY",
    "target_equipment": "Etching_Machine_#3",
    "parameter_of_interest": "Pressure"
  }
  ```

**3. [오케스트레이션 에이전트 → 모니터링 에이전트] 이상치 탐지 및 분석 요청**
- **Action:** 오케스트레이션 에이전트는 사용자 쿼리를 분석하여 모니터링 에이전트가 이해하기 쉬운 이상치 탐지 및 분석 쿼리를 요청합니다.
- **Message (`REQUEST_ANOMALY_ANALYSIS`):
  ```json
  {
    "type": "REQUEST_ANOMALY_ANALYSIS",
    "target_equipment": "Etching_Machine_#3",
    "parameter": "Pressure"
  }
  ```

**4. [모니터링 에이전트 → 오케스트레이션 에이전트] 분석 결과 송부**
- **Action:** 모니터링 에이전트는 요청에 따라 해당 장비의 압력 센서 데이터를 분석하여 이상 상태에 대한 결과물을 오케스트레이션 에이전트에게 송부합니다.
- **Message (`ANOMALY_ANALYSIS_RESULT`):
  ```json
  {
    "is_anomaly": true,
    "anomaly_details": {
      "current_value": 151,
      "normal_range": [110, 120]
    },
    "related_data": { ... }
  }
  ```

## **Phase 2: 원인 추론 및 미래 예측**

**5. [오케스트레이션 에이전트 → 예측 에이전트] 원인 분석 및 미래 예측 요청**
- **Action:** 오케스트레이션 에이전트는 이상 상태를 확인하고, 근본 원인과 이 상태가 지속될 경우의 미래 영향을 예측하도록 예측 에이전트에게 요청합니다.
- **Message (`REQUEST_FORECAST`):
  ```json
  {
    "type": "REQUEST_FORECAST",
    "incident_id": "INC-00125",
    "anomaly_data": { ... }
  }
  ```

**6. [예측 에이전트 → 오케스트레이션 에이전트] 분석 및 예측 결과 보고**
- **Action:** 예측 에이전트는 데이터를 심층 분석하여 근본 원인을 추론하고, 조치를 하지 않았을 경우의 미래 상태를 예측하여 오케스트레이션 에이전트에게 보고합니다.
- **Message (`PREDICTION_REPORT`):
  ```json
  {
    "incident_id": "INC-00125",
    "root_cause": {
      "description": "Gas_Valve_A stuck, causing excessive gas flow.",
      "confidence_score": 0.95
    },
    "future_prediction": {
      "description": "If no action, wafer yield will drop by 15% in 30 mins.",
      "risk_level": "High"
    }
  }
  ```

## **Phase 3: 해결 방안 시뮬레이션**

**7. [오케스트레이션 에이전트 → 자율제어 에이전트] 해결 방안 시뮬레이션 요청**
- **Action:** 오케스트레이션 에이전트는 추론된 원인을 해결할 수 있는 제어 방안들의 효과를 시뮬레이션하여 결과를 보고하도록 자율제어 에이전트에게 요청합니다.
- **Message (`REQUEST_SOLUTION_SIMULATION`):
  ```json
  {
    "incident_id": "INC-00125",
    "root_cause": "Gas_Valve_A stuck",
    "actions_to_simulate": ["Recalibrate_Gas_Valve_A", "Decrease_Pressure_Param"]
  }
  ```

**8. [자율제어 에이전트 → 오케스트레이션 에이전트] 시뮬레이션 결과 보고**
- **Action:** 자율제어 에이전트는 요청받은 제어 방안들을 가상 환경에서 실행하고, 각 방안의 예상 결과, 성공 확률, 부작용 등을 분석하여 오케스트레이션 에이전트에게 전달합니다.
- **Message (`SIMULATION_RESULT_REPORT`):
  ```json
  {
    "incident_id": "INC-00125",
    "simulation_results": [
      {
        "action": "Recalibrate_Gas_Valve_A",
        "expected_outcome": "Pressure returns to normal range within 2 mins.",
        "success_probability": 0.98,
        "side_effects": "None"
      },
      {
        "action": "Decrease_Pressure_Param",
        "expected_outcome": "Pressure temporarily lowered, but root cause remains.",
        "success_probability": 0.60,
        "side_effects": "Potential process quality degradation."
      }
    ]
  }
  ```

## **Phase 4: 최종 권고안 종합 및 전달**

**9. [오케스트레이션 에이전트] 최적 해결 방안 종합**
- **Action:** 오케스트레이션 에이전트는 모든 에이전트(모니터링, 예측, 자율제어)의 보고를 종합합니다. 근본 원인, 미래 예측, 각 해결책의 시뮬레이션 결과를 바탕으로 사용자에게 권고할 최적의 행동 방안(`Recalibrate_Gas_Valve_A`)을 최종적으로 선택합니다.

**10. [오케스트레이션 에이전트 → 플랫폼] 최종 권고안 전달**
- **Action:** 오케스트레이션 에이전트는 사용자가 쉽고 정확하게 의사결정을 내릴 수 있도록, 분석된 모든 정보와 최적의 해결책을 담은 최종 권고안을 플랫폼으로 전달합니다.
- **Message (`FINAL_RECOMMENDATION`):
  ```json
  {
    "incident_id": "INC-00125",
    "summary": {
      "problem": "Etching_Machine_#3의 압력이 151 Torr로 급등 (정상: 110-120 Torr).",
      "root_cause": "가스 밸브 A의 오작동으로 추정됨 (신뢰도 95%).",
      "risk": "방치 시 30분 내 수율 15% 감소 예상."
    },
    "recommendation": {
      "action": "Recalibrate_Gas_Valve_A",
      "description": "'가스 밸브 A 재보정' 조치를 권고합니다.",
      "simulated_result": "실행 시 2분 내 압력 정상화, 부작용 없음 (성공 확률 98%)."
    },
    "alternatives": [
      { ... } 
    ]
  }
  ```

**11. [플랫폼 → 사용자] 최종 권고안 제시**
- **Action:** 플랫폼은 오케스트레이션 에이전트로부터 받은 최종 권고안을 사용자에게 명확하고 이해하기 쉬운 형태로 시각화하여 제시합니다. 사용자는 이 정보를 바탕으로 직접 장비를 조치하거나 관련 부서에 작업을 요청하는 등 후속 조치를 결정합니다.
- **Message (UI/UX):**
  > **[문제 발생] 3번 엣칭 장비 압력 이상**
  > **원인:** 가스 밸브 A 오작동 (신뢰도 95%)
  > **예상 위험:** 방치 시 30분 내 수율 15% 감소
  >
  > **[시스템 권고 조치]**
  > **▶ 가스 밸브 A 재보정 (성공 확률 98%)**
  >    - 예상 결과: 2분 내 정상화, 부작용 없음
  >
  > *사용자께서는 위 내용을 바탕으로 조치 여부를 결정해 주시기 바랍니다.*