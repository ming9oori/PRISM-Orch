-- 오케스트레이션 에이전트 샘플 데이터 삽입
-- PRISM-Orch 시스템 테스트용 예시 데이터

-- 1. 태스크 관리 샘플 데이터
INSERT INTO ORCH_TASK_MANAGE (TASK_ID, USER_ID, STATUS, PRIORITY, TOTAL_DURATION, ERROR_MESSAGE) VALUES
('task_001', 'operator_001', 'COMPLETED', 'HIGH', 45.2, NULL),
('task_002', 'operator_002', 'ACTIVE', 'NORMAL', NULL, NULL),
('task_003', 'manager_001', 'FAILED', 'HIGH', 12.8, 'Connection timeout to manufacturing system'),
('task_004', 'operator_001', 'CANCELLED', 'LOW', 5.1, NULL),
('task_005', 'supervisor_001', 'ACTIVE', 'HIGH', NULL, NULL);

-- 2. 사용자 질의 샘플 데이터
INSERT INTO ORCH_USER_QUERY (QUERY_ID, TASK_ID, QUERY_TEXT, QUERY_TYPE, PARSED_INTENT, USER_CONSTRAINTS, RESPONSE_TIME) VALUES
('query_001', 'task_001', '생산라인 3번의 온도 센서 모니터링 결과를 보여줘', 'MONITORING', 
 '{"target": "production_line_3", "sensor_type": "temperature", "action": "monitor"}', 
 'real_time_update=true', 2.1),
('query_002', 'task_002', '내일 오전 설비 고장 예측 분석해줘', 'PREDICTION', 
 '{"timeframe": "tomorrow_morning", "target": "equipment", "action": "failure_prediction"}', 
 'confidence_level>=0.8', 5.7),
('query_003', 'task_003', '컨베이어 벨트 속도를 20% 증가시켜줘', 'CONTROL', 
 '{"target": "conveyor_belt", "action": "speed_control", "value": "increase_20_percent"}', 
 'safety_check=required', 1.9),
('query_004', 'task_004', 'AGV 로봇들의 현재 위치와 상태 확인', 'MONITORING', 
 '{"target": "agv_robots", "action": "status_check", "data": ["location", "status"]}', 
 NULL, 3.2),
('query_005', 'task_005', '품질검사 결과 이상치 탐지 및 분석', 'PREDICTION', 
 '{"target": "quality_inspection", "action": "anomaly_detection"}', 
 'alert_threshold=0.05', 4.8);

-- 3. 실행 계획 샘플 데이터
INSERT INTO ORCH_EXECUTION_PLAN (PLAN_ID, TASK_ID, QUERY_ID, TASK_GRAPH, RISK_ASSESSMENT, CONSTRAINT_CHECK, PLAN_STATUS, EMBEDDER_INFO, STARTED_AT, COMPLETED_AT) VALUES
('plan_001', 'task_001', 'query_001', 
 '{"agents": [{"id": "monitor_agent_01", "type": "MONITORING", "sequence": 1}, {"id": "data_agent_01", "type": "ANALYSIS", "sequence": 2}], "dependencies": [{"from": 1, "to": 2}]}', 
 'LOW', '{"safety_constraints": "passed", "resource_constraints": "sufficient"}', 'COMPLETED', 'openai_ada_v2', 
 CURRENT_TIMESTAMP - INTERVAL '1 hour', CURRENT_TIMESTAMP - INTERVAL '30 minutes'),
('plan_002', 'task_002', 'query_002', 
 '{"agents": [{"id": "predict_agent_01", "type": "PREDICTION", "sequence": 1}, {"id": "ml_agent_01", "type": "ANALYSIS", "sequence": 2}], "dependencies": [{"from": 1, "to": 2}]}', 
 'MEDIUM', '{"safety_constraints": "passed", "resource_constraints": "moderate"}', 'EXECUTING', 'openai_ada_v2', 
 CURRENT_TIMESTAMP - INTERVAL '10 minutes', NULL),
('plan_003', 'task_003', 'query_003', 
 '{"agents": [{"id": "control_agent_01", "type": "CONTROL", "sequence": 1}, {"id": "safety_agent_01", "type": "MONITORING", "sequence": 2}], "dependencies": [{"from": 1, "to": 2}]}', 
 'HIGH', '{"safety_constraints": "failed", "resource_constraints": "sufficient"}', 'FAILED', 'openai_ada_v2', 
 CURRENT_TIMESTAMP - INTERVAL '2 hours', CURRENT_TIMESTAMP - INTERVAL '1 hour 45 minutes');

-- 4. 에이전트 서브태스크 샘플 데이터
INSERT INTO ORCH_AGENT_SUBTASK (SUBTASK_ID, PLAN_ID, AGENT_ID, AGENT_TYPE, SEQUENCE_ORDER, INPUT_DATA, OUTPUT_DATA, SUBTASK_STATUS, ACTUAL_DURATION, STARTED_AT, COMPLETED_AT, RETRY_COUNT) VALUES
('subtask_001', 'plan_001', 'monitor_agent_01', 'MONITORING', 1, 
 '{"sensor_id": "temp_sensor_L3_01", "monitoring_duration": 300}', 
 '{"temperature_readings": [{"time": "2024-01-15T10:00:00Z", "value": 85.2}, {"time": "2024-01-15T10:05:00Z", "value": 86.1}], "status": "normal"}', 
 'SUCCESS', 15.3, CURRENT_TIMESTAMP - INTERVAL '1 hour', CURRENT_TIMESTAMP - INTERVAL '45 minutes', 0),
('subtask_002', 'plan_001', 'data_agent_01', 'ANALYSIS', 2, 
 '{"temperature_data": "from_monitor_agent_01", "analysis_type": "trend"}', 
 '{"trend": "stable", "anomalies": [], "recommendation": "continue_monitoring"}', 
 'SUCCESS', 8.7, CURRENT_TIMESTAMP - INTERVAL '45 minutes', CURRENT_TIMESTAMP - INTERVAL '30 minutes', 0),
('subtask_003', 'plan_002', 'predict_agent_01', 'PREDICTION', 1, 
 '{"equipment_ids": ["CNC_001", "CNC_002", "ROBOT_ARM_01"], "prediction_window": "24h"}', 
 NULL, 'RUNNING', NULL, CURRENT_TIMESTAMP - INTERVAL '10 minutes', NULL, 0),
('subtask_004', 'plan_003', 'control_agent_01', 'CONTROL', 1, 
 '{"target": "conveyor_belt_main", "action": "speed_increase", "percentage": 20}', 
 NULL, 'FAILED', 2.1, CURRENT_TIMESTAMP - INTERVAL '2 hours', CURRENT_TIMESTAMP - INTERVAL '1 hour 58 minutes', 2),
('subtask_005', 'plan_003', 'safety_agent_01', 'MONITORING', 2, 
 '{"safety_check": "pre_control_validation", "target": "conveyor_belt_main"}', 
 '{"safety_status": "violation", "blocked_reason": "personnel_in_danger_zone"}', 
 'SUCCESS', 1.5, CURRENT_TIMESTAMP - INTERVAL '1 hour 58 minutes', CURRENT_TIMESTAMP - INTERVAL '1 hour 56 minutes', 0);

-- 5. 제약조건 위반 샘플 데이터
INSERT INTO ORCH_CONSTRAINT_VIOLATION (VIOLATION_ID, PLAN_ID, SUBTASK_ID, CONSTRAINT_TYPE, CONSTRAINT_NAME, EXPECTED_VALUE, ACTUAL_VALUE, SEVERITY_LEVEL, IS_BLOCKING, RESOLUTION_ACTION, DETECTED_AT, RESOLVED_AT) VALUES
('violation_001', 'plan_003', 'subtask_005', 'SAFETY', 'danger_zone_clear', 'no_personnel', 'personnel_detected', 'CRITICAL', true, 'wait_for_zone_clear', CURRENT_TIMESTAMP - INTERVAL '1 hour 56 minutes', NULL),
('violation_002', 'plan_002', NULL, 'RESOURCE', 'cpu_usage_limit', '<80%', '92%', 'WARNING', false, 'resource_scaling', CURRENT_TIMESTAMP - INTERVAL '15 minutes', NULL);

-- 6. 사용자 피드백 샘플 데이터
INSERT INTO ORCH_USER_FEEDBACK (FEEDBACK_ID, TASK_ID, PLAN_ID, FEEDBACK_TYPE, FEEDBACK_CONTENT, ACTION_TAKEN, SYSTEM_RESPONSE, IMPACT_SCOPE, SUBMITTED_AT, PROCESSED_AT, SATISFACTION_SCORE) VALUES
('feedback_001', 'task_001', 'plan_001', 'APPROVAL', '모니터링 결과가 정확하고 유용했습니다.', 'APPLIED', '피드백이 성공적으로 기록되었습니다.', 'CURRENT_TASK', CURRENT_TIMESTAMP - INTERVAL '25 minutes', CURRENT_TIMESTAMP - INTERVAL '20 minutes', 5),
('feedback_002', 'task_003', 'plan_003', 'MODIFICATION', '안전 확인 후 속도 조절을 다시 시도해주세요.', 'APPLIED', '새로운 안전 확인 절차가 추가되었습니다.', 'FUTURE_TASKS', CURRENT_TIMESTAMP - INTERVAL '1 hour 30 minutes', CURRENT_TIMESTAMP - INTERVAL '1 hour 25 minutes', 4);

-- 7. 외부 지식 샘플 데이터
INSERT INTO ORCH_EXTERNAL_KNOWLEDGE (KNOWLEDGE_ID, DOCUMENT_TITLE, DOCUMENT_TYPE, CONTENT_SUMMARY, METADATA, RELEVANCE_SCORE, ACCESS_COUNT, EMBEDDER_INFO, VERSION) VALUES
('knowledge_001', '스마트 팩토리 안전 가이드라인', 'GUIDELINE', '제조 현장에서의 안전 절차 및 위험 요소 관리 방법에 대한 종합 가이드', 
 '{"author": "한국산업안전보건공단", "publication_date": "2024-01-01", "tags": ["safety", "manufacturing", "guidelines"]}', 
 0.95, 15, 'openai_ada_v2', 'v2.1'),
('knowledge_002', '예측 유지보수 모범 사례', 'RESEARCH_PAPER', '머신러닝을 활용한 설비 고장 예측 및 예방적 유지보수 전략', 
 '{"author": "김철수 외 3명", "publication_date": "2023-11-15", "tags": ["predictive_maintenance", "machine_learning", "equipment"]}', 
 0.87, 8, 'openai_ada_v2', 'v1.0'),
('knowledge_003', 'AGV 운영 매뉴얼', 'MANUAL', 'AGV(무인운반차) 시스템의 운영, 제어 및 문제해결 가이드', 
 '{"manufacturer": "로보틱스코리아", "model": "AGV-2024", "tags": ["agv", "automation", "manual"]}', 
 0.92, 12, 'openai_ada_v2', 'v3.2');

-- 8. 에이전트 메모리 샘플 데이터
INSERT INTO ORCH_AGENT_MEMORY (MEMORY_ID, AGENT_ID, MEMORY_TYPE, CONTEXT_DATA, IMPORTANCE_SCORE, DECAY_RATE, ACCESS_FREQUENCY, CREATED_AT, LAST_ACCESSED, EXPIRY_DATE) VALUES
('memory_001', 'monitor_agent_01', 'SHORT_TERM', 
 '{"sensor_patterns": {"temp_sensor_L3_01": {"normal_range": [80, 90], "alert_threshold": 95}}, "recent_alerts": []}', 
 0.8, 0.1, 5, CURRENT_TIMESTAMP - INTERVAL '1 day', CURRENT_TIMESTAMP - INTERVAL '1 hour', CURRENT_TIMESTAMP + INTERVAL '7 days'),
('memory_002', 'predict_agent_01', 'LONG_TERM', 
 '{"equipment_failure_patterns": {"CNC_001": {"mtbf": 720, "common_failures": ["spindle_wear", "coolant_leak"]}, "maintenance_history": {"last_service": "2024-01-10"}}}', 
 0.95, 0.01, 12, CURRENT_TIMESTAMP - INTERVAL '30 days', CURRENT_TIMESTAMP - INTERVAL '10 minutes', CURRENT_TIMESTAMP + INTERVAL '365 days'),
('memory_003', 'safety_agent_01', 'EPISODIC', 
 '{"safety_incidents": [{"date": "2024-01-10", "type": "near_miss", "location": "line_3", "description": "operator_almost_in_robot_path"}], "lessons_learned": ["increase_warning_time", "add_visual_alerts"]}', 
 0.9, 0.05, 3, CURRENT_TIMESTAMP - INTERVAL '5 days', CURRENT_TIMESTAMP - INTERVAL '2 hours', CURRENT_TIMESTAMP + INTERVAL '90 days');

-- 9. 인스트럭션 재작성 샘플 데이터
INSERT INTO ORCH_INSTRUCTION_REWRITE (REWRITE_ID, QUERY_ID, ORIGINAL_INSTRUCTION, REWRITTEN_INSTRUCTION, REWRITE_REASON, IMPROVEMENT_SCORE, AGENT_COMPATIBILITY, VALIDATION_STATUS) VALUES
('rewrite_001', 'query_002', '내일 오전 설비 고장 예측 분석해줘', 
 '다음 24시간 동안 CNC_001, CNC_002, ROBOT_ARM_01 설비에 대한 고장 예측 분석을 수행하고, 신뢰도 80% 이상의 결과만 보고하시오.', 
 '명확한 시간 범위 및 대상 설비 명시, 신뢰도 기준 추가', 0.85, 
 '{"compatible_agents": ["predict_agent_01", "ml_agent_01"], "required_capabilities": ["time_series_analysis", "failure_prediction"]}', 'VALIDATED'),
('rewrite_002', 'query_004', 'AGV 로봇들의 현재 위치와 상태 확인', 
 'AGV-001부터 AGV-005까지의 현재 좌표(x,y), 배터리 잔량, 작업 상태, 목적지 정보를 실시간으로 조회하여 대시보드 형태로 표시하시오.', 
 '구체적인 AGV ID 범위 및 조회할 상태 정보 세부 명시', 0.78, 
 '{"compatible_agents": ["monitor_agent_01", "agv_tracker_01"], "required_capabilities": ["real_time_tracking", "dashboard_display"]}', 'VALIDATED');

-- 10. 검색 증강 샘플 데이터
INSERT INTO ORCH_SEARCH_AUGMENTATION (AUGMENTATION_ID, PLAN_ID, SEARCH_QUERY, SEARCH_RESULTS, SELECTED_DOCUMENTS, RELEVANCE_SCORES, AUGMENTATION_TYPE, USAGE_COUNT) VALUES
('augment_001', 'plan_003', '컨베이어 벨트 속도 조절 안전 절차', 
 '{"total_results": 15, "search_time": 0.3}', 
 '["knowledge_001", "safety_procedure_conveyor_v2.1"]', 
 '{"knowledge_001": 0.95, "safety_procedure_conveyor_v2.1": 0.88}', 'CONTEXT', 3),
('augment_002', 'plan_002', '설비 고장 예측 머신러닝 모델', 
 '{"total_results": 8, "search_time": 0.5}', 
 '["knowledge_002", "ml_model_maintenance_v1.3"]', 
 '{"knowledge_002": 0.92, "ml_model_maintenance_v1.3": 0.85}', 'KNOWLEDGE', 1);

-- 11. 성능 지표 샘플 데이터
INSERT INTO ORCH_PERFORMANCE_METRICS (METRIC_ID, TASK_ID, METRIC_TYPE, METRIC_NAME, METRIC_VALUE, UNIT, THRESHOLD_MIN, THRESHOLD_MAX, AGENT_ID) VALUES
('metric_001', 'task_001', 'LATENCY', 'response_time', 2.1, 'seconds', 0.0, 5.0, 'monitor_agent_01'),
('metric_002', 'task_001', 'ACCURACY', 'sensor_reading_accuracy', 99.2, 'percent', 95.0, 100.0, 'monitor_agent_01'),
('metric_003', 'task_002', 'THROUGHPUT', 'predictions_per_minute', 15.7, 'count/min', 10.0, 50.0, 'predict_agent_01'),
('metric_004', 'task_002', 'RESOURCE', 'cpu_usage', 75.3, 'percent', 0.0, 80.0, 'predict_agent_01'),
('metric_005', 'task_003', 'LATENCY', 'control_response_time', 1.9, 'seconds', 0.0, 3.0, 'control_agent_01');

-- 12. 추가 알람 설정 샘플 데이터
INSERT INTO ORCH_ALERT_CONFIG (CONFIG_ID, ALERT_NAME, ALERT_TYPE, CONDITION_RULE, NOTIFICATION_CHANNEL, RECIPIENT_LIST, SEVERITY, IS_ENABLED) VALUES
('config_002', 'Critical Safety Violation', 'CONSTRAINT', 
 '{"constraint_type": "SAFETY", "severity_level": "CRITICAL", "is_blocking": true}', 
 'SLACK', '["#safety-alerts", "#operations"]', 'CRITICAL', true),
('config_003', 'High Response Time Alert', 'PERFORMANCE', 
 '{"metric_type": "LATENCY", "threshold": 5.0, "consecutive_violations": 3}', 
 'EMAIL', '["ops-team@prism-orch.com"]', 'MEDIUM', true),
('config_004', 'AGV Battery Low', 'PERFORMANCE', 
 '{"metric_type": "RESOURCE", "metric_name": "battery_level", "threshold": 20.0}', 
 'WEBHOOK', '["http://agv-management.internal/webhook"]', 'HIGH', true);

-- 인덱스 통계 업데이트
ANALYZE ORCH_TASK_MANAGE;
ANALYZE ORCH_USER_QUERY;
ANALYZE ORCH_EXECUTION_PLAN;
ANALYZE ORCH_AGENT_SUBTASK;
ANALYZE ORCH_CONSTRAINT_VIOLATION;
ANALYZE ORCH_USER_FEEDBACK;
ANALYZE ORCH_EXTERNAL_KNOWLEDGE;
ANALYZE ORCH_AGENT_MEMORY;
ANALYZE ORCH_PERFORMANCE_METRICS;
ANALYZE ORCH_ALERT_CONFIG;