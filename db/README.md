# PRISM Orchestration Database

자율제조 구현을 위한 현장 작업자 친화적 혁신 AI 에이전트 데이터베이스 시스템

## 개요

이 프로젝트는 서울대학교 주관의 자율제조 AI 에이전트 시스템을 위한 통합 데이터베이스 환경을 제공합니다. 
오케스트레이션 에이전트, 모니터링 AI 에이전트, 예측 AI 에이전트, 자율제어 AI 에이전트가 협력하여 
현장 작업자 친화적인 제조 자동화를 구현할 수 있는 데이터 인프라를 구축합니다.

## 아키텍처

### 핵심 구성 요소

- **PostgreSQL**: 오케스트레이션 메타데이터 및 태스크 관리
- **Redis**: 에이전트 세션 관리 및 실시간 캐싱
- **Weaviate**: 벡터 기반 지식 베이스 및 AI 메모리
- **Apache Kafka**: 에이전트 간 비동기 메시징
- **InfluxDB**: 시계열 메트릭 및 성능 데이터
- **Prometheus**: 시스템 모니터링 및 알림
- **Grafana**: 실시간 대시보드 및 시각화

### AI 에이전트 유형

1. **오케스트레이션 에이전트**: 전체 태스크 조율 및 에이전트 간 협업 관리
2. **모니터링 AI 에이전트**: 실시간 상태 모니터링 및 이상 탐지
3. **예측 AI 에이전트**: 공정 상태 예측 및 위험 평가
4. **자율제어 AI 에이전트**: 자동 의사결정 및 제어 액션 실행

## 빠른 시작

### 사전 요구사항

- Docker & Docker Compose
- Python 3.8+
- Git

### 설치 및 실행

```bash
# 저장소 클론
git clone <repository-url>
cd PRISM-Orch/db

# 한 번에 배포 (권장)
./scripts/deploy.sh

# 또는 수동 실행
docker-compose up -d

# 초기화 스크립트 실행
python3 kafka/create_topics.py
python3 weaviate/schema_init.py
```

### 테스트 실행

```bash
# 전체 시스템 테스트
python3 scripts/test_all.py

# 개별 서비스 확인
docker-compose ps
docker-compose logs -f [서비스명]
```

## 설정 및 구성

### 환경 변수

주요 환경 변수들은 `docker-compose.yml`에서 설정됩니다:

```yaml
# PostgreSQL
POSTGRES_DB: prism_orchestration
POSTGRES_USER: prism_user
POSTGRES_PASSWORD: prism_password

# InfluxDB
DOCKER_INFLUXDB_INIT_ORG: prism-org
DOCKER_INFLUXDB_INIT_BUCKET: prism-metrics
```

### 서비스 접속 정보

| 서비스 | 포트 | 접속 정보 |
|--------|------|-----------|
| PostgreSQL | 5432 | `prism_user` / `prism_password` |
| Redis | 6379 | 패스워드 없음 (로컬만) |
| Weaviate | 8080 | http://localhost:8080 |
| Kafka | 9092 | localhost:9092 |
| InfluxDB | 8086 | http://localhost:8086 |
| Prometheus | 9090 | http://localhost:9090 |
| Grafana | 3000 | `admin` / `admin123` |

## 데이터베이스 스키마

### 핵심 테이블

1. **ORCH_TASK_MANAGE**: 오케스트레이션 태스크 생명주기 관리
2. **ORCH_USER_QUERY**: 사용자 질의 및 인텐트 파싱 결과
3. **ORCH_EXECUTION_PLAN**: AI 에이전트 실행 계획 및 DAG
4. **ORCH_AGENT_SUBTASK**: 개별 에이전트 서브태스크 실행 상태
5. **ORCH_CONSTRAINT_VIOLATION**: 제약조건 위반 감지 및 처리
6. **ORCH_USER_FEEDBACK**: 사용자 피드백 및 시스템 개선
7. **ORCH_EXTERNAL_KNOWLEDGE**: RAG용 외부 지식 문서
8. **ORCH_AGENT_MEMORY**: 에이전트 메모리 및 학습 데이터
9. **ORCH_PERFORMANCE_METRICS**: 성능 지표 및 KPI 추적

### 벡터 데이터베이스 (Weaviate)

- **ExternalKnowledge**: 제조 도메인 지식 및 문서
- **AgentMemory**: AI 에이전트 장단기 메모리
- **Instruction**: 재작성된 인스트럭션 저장소
- **ManufacturingKnowledge**: 공정별 전문 지식

## 모니터링 및 운영

### 대시보드

Grafana 대시보드 (`http://localhost:3000`)에서 다음 메트릭을 모니터링할 수 있습니다:

- 태스크 처리 현황 및 성공률
- 에이전트별 성능 지표
- 시스템 리소스 사용량
- 제약조건 위반 통계
- 사용자 만족도 점수

### 로그 관리

```bash
# 전체 로그 확인
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f postgres
docker-compose logs -f weaviate
docker-compose logs -f kafka
```

### 백업 및 복구

```bash
# PostgreSQL 백업
docker exec prism-postgres pg_dump -U prism_user prism_orchestration > backup.sql

# Redis 백업
docker exec prism-redis redis-cli SAVE
docker cp prism-redis:/data/dump.rdb ./redis_backup.rdb

# Weaviate 백업 (API 사용)
curl -X POST http://localhost:8080/v1/backups/filesystem
```

## 보안 고려사항

- 프로덕션 환경에서는 모든 기본 패스워드 변경 필수
- Redis AUTH 활성화 권장
- 네트워크 정책을 통한 접근 제어
- SSL/TLS 인증서 적용
- 정기적인 보안 패치 적용

## API 및 연동

### Python 클라이언트 예제

```python
import psycopg2
import redis
import weaviate
from kafka import KafkaProducer

# PostgreSQL 연결
conn = psycopg2.connect(
    host="localhost", port=5432, 
    database="prism_orchestration",
    user="prism_user", password="prism_password"
)

# Redis 연결
r = redis.Redis(host='localhost', port=6379)

# Weaviate 연결
client = weaviate.Client("http://localhost:8080")

# Kafka 프로듀서
producer = KafkaProducer(bootstrap_servers=['localhost:9092'])
```

---