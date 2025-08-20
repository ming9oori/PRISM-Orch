#!/usr/bin/env python3
"""
PRISM Orchestration Test Data Generator
자율제조 AI 에이전트 시스템을 위한 테스트 데이터 생성기
"""

import time
import random
import json
import logging
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import threading

# Database connections
import psycopg2
import redis
from kafka import KafkaProducer
import requests
from influxdb import InfluxDBClient

# Prometheus metrics
from prometheus_client import start_http_server, Gauge, Counter, Histogram

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Prometheus 메트릭 정의
agent_task_duration = Histogram('prism_agent_task_duration_seconds', 'Agent task execution time', ['agent_type', 'task_type'])
agent_success_rate = Gauge('prism_agent_success_rate', 'Agent task success rate', ['agent_type'])
manufacturing_efficiency = Gauge('prism_manufacturing_efficiency_percent', 'Manufacturing process efficiency', ['process_name'])
quality_score = Gauge('prism_quality_score', 'Product quality score', ['product_type'])
resource_utilization = Gauge('prism_resource_utilization_percent', 'Resource utilization percentage', ['resource_type'])
error_count = Counter('prism_errors_total', 'Total number of errors', ['error_type', 'component'])
active_agents = Gauge('prism_active_agents', 'Number of active agents', ['agent_type'])
throughput = Gauge('prism_throughput_units_per_hour', 'Manufacturing throughput', ['line_id'])

class TestDataGenerator:
    def __init__(self):
        self.running = False
        self.setup_connections()
        
    def setup_connections(self):
        """데이터베이스 연결 설정"""
        try:
            # PostgreSQL 연결
            self.pg_conn = psycopg2.connect(
                host='localhost',
                port=15432,
                database='prism_orchestration',
                user='prism_user',
                password='prism_password'
            )
            logger.info("PostgreSQL 연결 성공")
            
            # Redis 연결
            self.redis_client = redis.Redis(host='localhost', port=16379, decode_responses=True)
            logger.info("Redis 연결 성공")
            
            # Kafka Producer
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=['localhost:19092'],
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8')
            )
            logger.info("Kafka 연결 성공")
            
            # InfluxDB 연결
            self.influx_client = InfluxDBClient(host='localhost', port=18086, database='prism_metrics')
            logger.info("InfluxDB 연결 성공")
            
        except Exception as e:
            logger.error(f"데이터베이스 연결 실패: {e}")
    
    def generate_agent_data(self):
        """에이전트 활동 데이터 생성"""
        agent_types = ['monitoring', 'prediction', 'control', 'orchestration']
        task_types = ['data_analysis', 'decision_making', 'execution', 'optimization']
        
        while self.running:
            try:
                agent_type = random.choice(agent_types)
                task_type = random.choice(task_types)
                
                # 태스크 실행 시간 시뮬레이션
                execution_time = random.uniform(0.5, 5.0)
                agent_task_duration.labels(agent_type=agent_type, task_type=task_type).observe(execution_time)
                
                # 성공률 시뮬레이션
                success_rate = random.uniform(0.85, 0.99)
                agent_success_rate.labels(agent_type=agent_type).set(success_rate)
                
                # 활성 에이전트 수
                active_count = random.randint(3, 12)
                active_agents.labels(agent_type=agent_type).set(active_count)
                
                # 에러 발생 시뮬레이션 (가끔)
                if random.random() < 0.1:
                    error_types = ['timeout', 'connection_failed', 'invalid_data', 'resource_exhausted']
                    error_count.labels(error_type=random.choice(error_types), component=agent_type).inc()
                
                # Kafka 메시지 전송
                event_data = {
                    'timestamp': datetime.now().isoformat(),
                    'agent_id': f"{agent_type}_agent_{random.randint(1, 5)}",
                    'task_type': task_type,
                    'execution_time': execution_time,
                    'success': random.random() > 0.1,
                    'resource_usage': {
                        'cpu': random.uniform(10, 80),
                        'memory': random.uniform(100, 500),
                        'disk_io': random.uniform(1, 20)
                    }
                }
                
                self.kafka_producer.send('agent.monitoring.events', event_data)
                
                # Redis에 실시간 상태 저장
                agent_key = f"agent:{event_data['agent_id']}"
                self.redis_client.hset(agent_key, mapping={
                    'status': 'active',
                    'last_task': task_type,
                    'last_updated': datetime.now().isoformat(),
                    'cpu_usage': event_data['resource_usage']['cpu'],
                    'memory_usage': event_data['resource_usage']['memory']
                })
                self.redis_client.expire(agent_key, 300)  # 5분 TTL
                
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                logger.error(f"에이전트 데이터 생성 오류: {e}")
                time.sleep(1)
    
    def generate_manufacturing_data(self):
        """제조 공정 데이터 생성"""
        processes = ['cnc_milling', 'assembly', 'quality_check', 'packaging']
        product_types = ['component_a', 'component_b', 'finished_product']
        
        while self.running:
            try:
                process = random.choice(processes)
                product = random.choice(product_types)
                
                # 제조 효율성
                efficiency = random.uniform(75, 95)
                manufacturing_efficiency.labels(process_name=process).set(efficiency)
                
                # 품질 점수
                quality = random.uniform(85, 99)
                quality_score.labels(product_type=product).set(quality)
                
                # 처리량
                line_id = f"line_{random.randint(1, 3)}"
                throughput_value = random.randint(80, 150)
                throughput.labels(line_id=line_id).set(throughput_value)
                
                # 리소스 사용률
                resources = ['equipment', 'labor', 'material', 'energy']
                for resource in resources:
                    utilization = random.uniform(60, 90)
                    resource_utilization.labels(resource_type=resource).set(utilization)
                
                # InfluxDB에 시계열 데이터 저장
                points = []
                current_time = datetime.utcnow()
                
                # 센서 데이터 시뮬레이션
                sensor_data = {
                    'temperature': random.uniform(20, 35),
                    'humidity': random.uniform(40, 60),
                    'vibration': random.uniform(0.1, 0.8),
                    'pressure': random.uniform(1.0, 1.5),
                    'flow_rate': random.uniform(50, 100)
                }
                
                for sensor, value in sensor_data.items():
                    point = {
                        "measurement": "manufacturing_sensors",
                        "tags": {
                            "process": process,
                            "line_id": line_id,
                            "sensor_type": sensor
                        },
                        "time": current_time,
                        "fields": {
                            "value": value,
                            "efficiency": efficiency,
                            "quality": quality
                        }
                    }
                    points.append(point)
                
                self.influx_client.write_points(points)
                
                # PostgreSQL에 생산 기록 저장
                with self.pg_conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO production_records (process_name, product_type, efficiency, quality_score, timestamp)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, (process, product, efficiency, quality, current_time))
                    self.pg_conn.commit()
                
                # 이상 상황 시뮬레이션
                if efficiency < 80 or quality < 90:
                    alert_data = {
                        'timestamp': current_time.isoformat(),
                        'alert_type': 'performance_degradation',
                        'process': process,
                        'efficiency': efficiency,
                        'quality': quality,
                        'severity': 'medium' if efficiency > 75 else 'high'
                    }
                    self.kafka_producer.send('agent.monitoring.alerts', alert_data)
                
                time.sleep(random.uniform(2, 5))
                
            except Exception as e:
                logger.error(f"제조 데이터 생성 오류: {e}")
                time.sleep(1)
    
    def generate_user_activity(self):
        """사용자 활동 데이터 생성"""
        query_types = ['status_check', 'performance_report', 'process_optimization', 'alert_investigation']
        
        while self.running:
            try:
                query_type = random.choice(query_types)
                
                # 사용자 쿼리 시뮬레이션
                query_data = {
                    'timestamp': datetime.now().isoformat(),
                    'user_id': f"user_{random.randint(1, 10)}",
                    'query_type': query_type,
                    'parameters': {
                        'process_filter': random.choice(['all', 'cnc_milling', 'assembly']),
                        'time_range': random.choice(['1h', '24h', '7d']),
                        'priority': random.choice(['low', 'medium', 'high'])
                    }
                }
                
                self.kafka_producer.send('user.queries', query_data)
                
                # 응답 시뮬레이션
                response_time = random.uniform(0.1, 2.0)
                time.sleep(response_time)
                
                response_data = {
                    'timestamp': datetime.now().isoformat(),
                    'query_id': f"query_{random.randint(1000, 9999)}",
                    'response_time': response_time,
                    'success': random.random() > 0.05,
                    'data_points': random.randint(10, 1000)
                }
                
                self.kafka_producer.send('user.feedback', response_data)
                
                time.sleep(random.uniform(5, 15))
                
            except Exception as e:
                logger.error(f"사용자 활동 데이터 생성 오류: {e}")
                time.sleep(1)
    
    def setup_database_schema(self):
        """데이터베이스 스키마 설정"""
        try:
            with self.pg_conn.cursor() as cursor:
                # 생산 기록 테이블 생성
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS production_records (
                        id SERIAL PRIMARY KEY,
                        process_name VARCHAR(100),
                        product_type VARCHAR(100),
                        efficiency FLOAT,
                        quality_score FLOAT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 인덱스 생성
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_production_timestamp 
                    ON production_records(timestamp)
                """)
                
                self.pg_conn.commit()
                logger.info("PostgreSQL 스키마 설정 완료")
                
            # InfluxDB 데이터베이스 생성
            try:
                self.influx_client.create_database('prism_metrics')
                logger.info("InfluxDB 데이터베이스 설정 완료")
            except:
                pass  # 이미 존재할 수 있음
                
        except Exception as e:
            logger.error(f"데이터베이스 스키마 설정 오류: {e}")
    
    def start(self):
        """테스트 데이터 생성 시작"""
        logger.info("테스트 데이터 생성 시작")
        self.running = True
        
        # 데이터베이스 스키마 설정
        self.setup_database_schema()
        
        # Prometheus 메트릭 서버 시작
        start_http_server(8000)
        logger.info("Prometheus 메트릭 서버 시작 (포트 8000)")
        
        # 각 데이터 생성기를 별도 스레드에서 실행
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(self.generate_agent_data),
                executor.submit(self.generate_manufacturing_data),
                executor.submit(self.generate_user_activity)
            ]
            
            try:
                # 모든 스레드 실행
                for future in futures:
                    future.result()
            except KeyboardInterrupt:
                logger.info("키보드 인터럽트 감지, 정리 중...")
            finally:
                self.stop()
    
    def stop(self):
        """테스트 데이터 생성 중지"""
        logger.info("테스트 데이터 생성 중지")
        self.running = False
        
        # 연결 정리
        try:
            self.kafka_producer.close()
            self.pg_conn.close()
            self.redis_client.close()
        except:
            pass

def main():
    generator = TestDataGenerator()
    
    try:
        generator.start()
    except KeyboardInterrupt:
        logger.info("프로그램 종료")
    finally:
        generator.stop()

if __name__ == "__main__":
    main()