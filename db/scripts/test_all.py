#!/usr/bin/env python3
"""
PRISM Orchestration Database Test Suite
자율제조 AI 에이전트 데이터베이스 전체 테스트
"""

import asyncio
import json
import time
import psycopg2
import redis
import requests
import logging
from typing import Dict, Any

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseTester:
    def __init__(self):
        self.test_results = {}
        
    async def test_postgresql(self) -> bool:
        """PostgreSQL 연결 및 기본 쿼리 테스트"""
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="prism_orchestration",
                user="prism_user",
                password="prism_password"
            )
            cursor = conn.cursor()
            
            # 테이블 존재 확인
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name LIKE 'orch_%'
            """)
            tables = cursor.fetchall()
            logger.info(f"발견된 테이블: {len(tables)}개")
            
            # 기본 CRUD 테스트
            cursor.execute("""
                INSERT INTO ORCH_TASK_MANAGE (USER_ID, STATUS, PRIORITY) 
                VALUES (%s, %s, %s) RETURNING TASK_ID
            """, ("test_user", "ACTIVE", "NORMAL"))
            
            task_id = cursor.fetchone()[0]
            logger.info(f"테스트 태스크 생성: {task_id}")
            
            # 데이터 조회
            cursor.execute("SELECT COUNT(*) FROM ORCH_TASK_MANAGE")
            count = cursor.fetchone()[0]
            logger.info(f"총 태스크 수: {count}")
            
            # 뷰 테스트
            cursor.execute("SELECT * FROM TASK_STATUS_SUMMARY")
            summary = cursor.fetchall()
            logger.info(f"태스크 상태 요약: {summary}")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("PostgreSQL 테스트 통과")
            return True
            
        except Exception as e:
            logger.error(f"PostgreSQL 테스트 실패: {e}")
            return False
    
    def test_redis(self) -> bool:
        """Redis 연결 및 기본 작업 테스트"""
        try:
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            
            # 연결 테스트
            ping_result = r.ping()
            if not ping_result:
                raise Exception("Redis ping 실패")
            
            # 기본 Set/Get 테스트
            test_key = "test:agent:session"
            test_data = {
                "agent_id": "test_agent_001",
                "session_data": {"status": "active", "last_ping": time.time()}
            }
            
            r.setex(test_key, 300, json.dumps(test_data))  # 5분 TTL
            retrieved_data = json.loads(r.get(test_key))
            
            assert retrieved_data["agent_id"] == test_data["agent_id"]
            
            # 리스트 테스트 (메시지 큐 시뮬레이션)
            queue_name = "test:message:queue"
            r.lpush(queue_name, json.dumps({"message": "test_message", "timestamp": time.time()}))
            
            message = r.brpop([queue_name], timeout=1)
            if message:
                parsed_message = json.loads(message[1])
                assert parsed_message["message"] == "test_message"
            
            # 정리
            r.delete(test_key, queue_name)
            
            logger.info("Redis 테스트 통과")
            return True
            
        except Exception as e:
            logger.error(f"Redis 테스트 실패: {e}")
            return False
    
    def test_weaviate(self) -> bool:
        """Weaviate 연결 및 기본 작업 테스트"""
        try:
            # Health check
            response = requests.get("http://localhost:8080/v1/.well-known/ready")
            if response.status_code != 200:
                raise Exception(f"Weaviate health check 실패: {response.status_code}")
            
            # 스키마 확인
            schema_response = requests.get("http://localhost:8080/v1/schema")
            if schema_response.status_code == 200:
                schema = schema_response.json()
                classes = [cls['class'] for cls in schema.get('classes', [])]
                logger.info(f"Weaviate 클래스: {classes}")
            
            # 간단한 데이터 추가/검색 테스트 (실제 weaviate-client 사용 권장)
            test_object = {
                "class": "ManufacturingKnowledge",
                "properties": {
                    "process_name": "테스트 공정",
                    "description": "테스트용 제조 공정 설명",
                    "parameters": {"temperature": "25C", "pressure": "1atm"},
                    "constraints": {"max_temp": "100C"},
                    "best_practices": "안전 수칙 준수",
                    "troubleshooting": "온도 조절 필요"
                }
            }
            
            create_response = requests.post(
                "http://localhost:8080/v1/objects",
                json=test_object
            )
            
            if create_response.status_code in [200, 201]:
                logger.info("테스트 객체 생성 성공")
            
            logger.info("Weaviate 테스트 통과")
            return True
            
        except Exception as e:
            logger.error(f"Weaviate 테스트 실패: {e}")
            return False
    
    def test_kafka(self) -> bool:
        """Kafka 연결 및 토픽 테스트"""
        try:
            # Kafka 관리자 API를 통한 간단한 확인
            # 실제로는 kafka-python 라이브러리 사용 권장
            
            # 토픽 목록 확인 (간접적 방법)
            import subprocess
            result = subprocess.run(
                ["docker", "exec", "prism-kafka", "kafka-topics", "--bootstrap-server", "localhost:9092", "--list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                topics = result.stdout.strip().split('\n')
                logger.info(f"Kafka 토픽 목록: {topics}")
                
                # 예상 토픽들이 있는지 확인
                expected_topics = ['agent.orchestration.commands', 'system.metrics', 'user.queries']
                for topic in expected_topics:
                    if topic in topics:
                        logger.info(f"토픽 '{topic}' 확인됨")
                
                logger.info("Kafka 테스트 통과")
                return True
            else:
                raise Exception(f"Kafka 토픽 조회 실패: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Kafka 테스트 실패: {e}")
            return False
    
    def test_prometheus_grafana(self) -> bool:
        """Prometheus 및 Grafana 연결 테스트"""
        try:
            # Prometheus health check
            prom_response = requests.get("http://localhost:9090/-/ready")
            if prom_response.status_code != 200:
                raise Exception(f"Prometheus 연결 실패: {prom_response.status_code}")
            
            # Grafana health check
            grafana_response = requests.get("http://localhost:3000/api/health")
            if grafana_response.status_code != 200:
                raise Exception(f"Grafana 연결 실패: {grafana_response.status_code}")
            
            logger.info("Prometheus & Grafana 테스트 통과")
            return True
            
        except Exception as e:
            logger.error(f"Prometheus & Grafana 테스트 실패: {e}")
            return False
    
    def test_influxdb(self) -> bool:
        """InfluxDB 연결 테스트"""
        try:
            response = requests.get("http://localhost:8086/health")
            if response.status_code != 200:
                raise Exception(f"InfluxDB 연결 실패: {response.status_code}")
            
            health_data = response.json()
            if health_data.get("status") == "pass":
                logger.info("InfluxDB 테스트 통과")
                return True
            else:
                raise Exception(f"InfluxDB 상태 불량: {health_data}")
                
        except Exception as e:
            logger.error(f"InfluxDB 테스트 실패: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """모든 데이터베이스 테스트 실행"""
        logger.info("PRISM Orchestration Database 테스트 시작")
        
        tests = {
            "PostgreSQL": self.test_postgresql,
            "Redis": self.test_redis, 
            "Weaviate": self.test_weaviate,
            "Kafka": self.test_kafka,
            "Prometheus & Grafana": self.test_prometheus_grafana,
            "InfluxDB": self.test_influxdb
        }
        
        results = {}
        for test_name, test_func in tests.items():
            logger.info(f"{test_name} 테스트 중...")
            if asyncio.iscoroutinefunction(test_func):
                results[test_name] = await test_func()
            else:
                results[test_name] = test_func()
            
            time.sleep(1)  # 테스트 간 간격
        
        # 결과 요약
        logger.info("\n" + "="*50)
        logger.info("테스트 결과 요약:")
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "PASS" if result else "FAIL"
            logger.info(f"  {test_name}: {status}")
            if result:
                passed += 1
        
        logger.info(f"\n총 {passed}/{total}개 테스트 통과")
        
        if passed == total:
            logger.info("모든 테스트가 성공적으로 통과했습니다!")
        else:
            logger.warning(f"Warning: {total - passed}개 테스트가 실패했습니다.")
        
        return results

async def main():
    tester = DatabaseTester()
    results = await tester.run_all_tests()
    return results

if __name__ == "__main__":
    asyncio.run(main())