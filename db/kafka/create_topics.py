#!/usr/bin/env python3
"""
Kafka Topics Creation for PRISM Orchestration
자율제조 AI 에이전트 메시징 시스템 토픽 생성
"""

from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError, NoBrokersAvailable
import logging
import time

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_topics():
    """오케스트레이션 에이전트용 Kafka 토픽들을 생성합니다."""
    
    # Kafka 연결 재시도 로직
    max_retries = 30
    retry_delay = 2
    admin_client = None
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Kafka 연결 시도 {attempt + 1}/{max_retries}")
            admin_client = KafkaAdminClient(
                bootstrap_servers=['localhost:19092'],
                client_id='prism_topic_creator'
            )
            logger.info("Kafka 연결 성공")
            break
        except NoBrokersAvailable:
            if attempt == max_retries - 1:
                logger.error("Kafka 브로커에 연결할 수 없습니다. 서비스가 시작되었는지 확인해주세요.")
                return
            logger.warning(f"Kafka 브로커를 찾을 수 없습니다. {retry_delay}초 후 재시도...")
            time.sleep(retry_delay)
        except Exception as e:
            logger.error(f"Kafka 연결 중 예상치 못한 오류: {e}")
            return
    
    if admin_client is None:
        logger.error("Kafka 클라이언트 생성 실패")
        return
    
    # 생성할 토픽들 정의
    topics = [
        # 에이전트 간 통신
        NewTopic(name='agent.orchestration.commands', 
                num_partitions=3, 
                replication_factor=1),
        
        NewTopic(name='agent.orchestration.responses', 
                num_partitions=3, 
                replication_factor=1),
        
        # 모니터링 에이전트
        NewTopic(name='agent.monitoring.events', 
                num_partitions=5, 
                replication_factor=1),
        
        NewTopic(name='agent.monitoring.alerts', 
                num_partitions=3, 
                replication_factor=1),
        
        # 예측 에이전트
        NewTopic(name='agent.prediction.requests', 
                num_partitions=3, 
                replication_factor=1),
        
        NewTopic(name='agent.prediction.results', 
                num_partitions=3, 
                replication_factor=1),
        
        # 자율제어 에이전트
        NewTopic(name='agent.control.actions', 
                num_partitions=5, 
                replication_factor=1),
        
        NewTopic(name='agent.control.feedback', 
                num_partitions=3, 
                replication_factor=1),
        
        # 사용자 인터페이스
        NewTopic(name='user.queries', 
                num_partitions=3, 
                replication_factor=1),
        
        NewTopic(name='user.feedback', 
                num_partitions=3, 
                replication_factor=1),
        
        # 시스템 메트릭스
        NewTopic(name='system.metrics', 
                num_partitions=5, 
                replication_factor=1),
        
        NewTopic(name='system.logs', 
                num_partitions=3, 
                replication_factor=1),
        
        # 제약조건 위반
        NewTopic(name='constraints.violations', 
                num_partitions=3, 
                replication_factor=1),
        
        # 지식 베이스 업데이트
        NewTopic(name='knowledge.updates', 
                num_partitions=3, 
                replication_factor=1),
    ]
    
    try:
        # 토픽들 생성
        fs = admin_client.create_topics(new_topics=topics, timeout_ms=30000)
        
        # 각 토픽 생성 결과 확인
        for topic, future in fs.items():
            try:
                future.result()  # 생성 완료까지 대기
                logger.info(f"토픽 '{topic}' 생성 완료")
            except TopicAlreadyExistsError:
                logger.warning(f"토픽 '{topic}'는 이미 존재합니다")
            except Exception as e:
                logger.error(f"토픽 '{topic}' 생성 실패: {e}")
                
    except Exception as e:
        logger.error(f"토픽 생성 중 오류 발생: {e}")
    
    finally:
        admin_client.close()

if __name__ == "__main__":
    create_topics()