# PRISM Orchestration Database Setup

이 문서는 PRISM Orchestration Agent의 다중 데이터베이스 인프라 설정 및 운영 가이드입니다.

## 📋 개요

### 아키텍처
- **PostgreSQL**: 메인 트랜잭션 DB (ACID 보장)
- **Redis**: 캐싱 및 세션 관리
- **Weaviate**: 벡터 검색 및 RAG 시스템
- **Kafka**: 에이전트 간 메시지 큐
- **Prometheus**: 메트릭 수집 및 모니터링
- **Grafana**: 데이터 시각화 및 대시보드

### 테이블 구조
```
orch_task_manage       → 태스크 관리
orch_user_query        → 사용자 쿼리
orch_execution_plan    → 실행 계획
orch_agent_subtask     → 에이전트 서브태스크
orch_constraint_violation → 제약조건 위반
orch_user_feedback     → 사용자 피드백
orch_knowledge_metadata → 외부 지식 메타데이터
```

##  빠른 시작

### 1. 전체 배포
```bash
# 모든 데이터베이스 서비스 배포 및 초기화
./scripts/deploy.sh
```

### 2. 개별 서비스 관리
```bash
# 서비스 시작
docker-compose up -d

# 서비스 중지
docker-compose down

# 로그 확인
docker-compose logs [service-name]
```

### 3. 테스트 실행
```bash
# 종합 테스트 (모든 DB 기능 검증)
python3 scripts/test_all.py

# Python 의존성 설치
pip install -r requirements.txt
```

##  서비스 접속 정보

### Database Connections
| Service | URL | Credentials |
|---------|-----|-------------|
| PostgreSQL | `localhost:5432` | user: `orch_user`, db: `orch_db`, password: `orch_password` |
| Redis | `localhost:6379` | password: `redis_password` |
| Weaviate | `http://localhost:8080` | API Key: `weaviate_api_key` |
| Kafka | `localhost:9092` | No auth |

### Management UIs
| Service | URL | Credentials |
|---------|-----|-------------|
| pgAdmin | `http://localhost:8082` | admin@orch.com / admin_password |
| Redis Insight | `http://localhost:8001` | No auth |
| Kafka UI | `http://localhost:8081` | No auth |
| Grafana | `http://localhost:3000` | admin / admin |
| Prometheus | `http://localhost:9090` | No auth |

## 📁 파일 구조

```
db/
├── init/
│   └── 01_create_tables.sql     # PostgreSQL 테이블 생성
├── redis/
│   └── redis.conf               # Redis 설정
├── weaviate/
│   ├── schema_init.py          # Weaviate 스키마 초기화
│   └── requirements.txt        # Python 의존성
└── kafka/
    ├── create_topics.py        # Kafka 토픽 생성
    └── requirements.txt        # Python 의존성

scripts/
├── deploy.sh                   # 전체 배포 스크립트
└── test_all.py                # 종합 테스트 스크립트
```

## 🧪 테스트 가이드

### 기본 기능 테스트
```bash
# 1. PostgreSQL CRUD 테스트
python3 -c "
import psycopg2
conn = psycopg2.connect(host='localhost', port=5432, database='orch_db', user='orch_user', password='orch_password')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = \"public\"')
print(f'Tables created: {cur.fetchone()[0]}')
conn.close()
"

# 2. Redis 연결 테스트
python3 -c "
import redis
r = redis.Redis(host='localhost', port=6379, password='redis_password', decode_responses=True)
r.set('test', 'hello')
print(f'Redis test: {r.get(\"test\")}')
r.delete('test')
"

# 3. Weaviate 연결 테스트
python3 -c "
import weaviate
client = weaviate.Client(url='http://localhost:8080', auth_client_secret=weaviate.AuthApiKey('weaviate_api_key'))
print(f'Weaviate ready: {client.is_ready()}')
"

# 4. Kafka 연결 테스트
python3 -c "
from kafka import KafkaProducer
producer = KafkaProducer(bootstrap_servers=['localhost:9092'])
print('Kafka connection successful')
producer.close()
"
```

### 종합 테스트 실행
```bash
# 모든 데이터베이스 기능 테스트
python3 scripts/test_all.py

# 출력 예시:
# ============================================================
# PRISM ORCHESTRATION DATABASE TEST RESULTS
# ============================================================
# postgresql_basic              ✅ PASSED
# postgresql_relationships      ✅ PASSED
# redis_operations              ✅ PASSED
# weaviate_operations           ✅ PASSED
# kafka_operations              ✅ PASSED
# integration_workflow          ✅ PASSED
# ------------------------------------------------------------
# Total Tests: 6
# Passed: 6
# Failed: 0
# Success Rate: 100.0%
# ============================================================
```

## 🛠 개별 초기화 스크립트

### Weaviate 스키마 초기화
```bash
cd db/weaviate
pip install -r requirements.txt
python3 schema_init.py
```

### Kafka 토픽 생성
```bash
cd db/kafka
pip install -r requirements.txt
python3 create_topics.py
```

## 📊 모니터링 및 유지보수

### Prometheus & Grafana 모니터링

#### Prometheus 메트릭 수집
```bash
# Prometheus 설정 확인
curl http://localhost:9090/api/v1/targets

# 메트릭 조회
curl http://localhost:9090/api/v1/query?query=up

# 주요 모니터링 메트릭
# - postgresql_up: PostgreSQL 서비스 상태
# - redis_up: Redis 서비스 상태  
# - kafka_brokers: Kafka 브로커 수
# - weaviate_objects_total: Weaviate 객체 총 개수
```

#### Grafana 대시보드
```bash
# Grafana 접속: http://localhost:3000
# 기본 로그인: admin / admin

# 미리 구성된 대시보드:
# - Database Overview: 전체 DB 서비스 상태
# - PostgreSQL Metrics: 쿼리 성능, 연결 수, 테이블 크기
# - Redis Metrics: 메모리 사용량, 키 개수, 히트율
# - Kafka Metrics: 토픽별 메시지 수, 컨슈머 지연
# - Weaviate Metrics: 벡터 검색 성능, 인덱스 크기
```

#### 알림 설정
```bash
# Grafana 알림 채널 설정 (Slack, Email 등)
# 임계값 기반 알림:
# - PostgreSQL 연결 수 > 80%
# - Redis 메모리 사용량 > 90%
# - Kafka 컨슈머 지연 > 1000ms
# - Weaviate 응답시간 > 500ms
```

### 로그 확인
```bash
# 모든 서비스 로그
docker-compose logs

# 특정 서비스 로그
docker-compose logs postgresql
docker-compose logs redis
docker-compose logs weaviate
docker-compose logs kafka
docker-compose logs prometheus
docker-compose logs grafana
```

### 데이터 백업
```bash
# PostgreSQL 백업
docker-compose exec postgresql pg_dump -U orch_user orch_db > backup_$(date +%Y%m%d).sql

# Redis 백업 (자동 저장)
docker-compose exec redis redis-cli -a redis_password BGSAVE
```

### 서비스 상태 확인
```bash
# 모든 서비스 상태
docker-compose ps

# 개별 서비스 헬스체크
docker-compose exec postgresql pg_isready -U orch_user -d orch_db
docker-compose exec redis redis-cli -a redis_password ping
curl http://localhost:8080/v1/meta
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list
```

## 🚨 트러블슈팅

### 일반적인 문제들

1. **포트 충돌**
   ```bash
   # 포트 사용 확인
   lsof -i :5432  # PostgreSQL
   lsof -i :6379  # Redis
   lsof -i :8080  # Weaviate
   lsof -i :9092  # Kafka
   lsof -i :3000  # Grafana
   lsof -i :9090  # Prometheus
   ```

2. **Docker 관련**
   ```bash
   # 컨테이너 재시작
   docker-compose restart [service-name]
   
   # 볼륨 초기화 (데이터 삭제 주의!)
   docker-compose down -v
   docker-compose up -d
   ```

3. **권한 문제**
   ```bash
   # 스크립트 실행 권한
   chmod +x scripts/deploy.sh
   chmod +x scripts/test_all.py
   ```

### 서비스별 문제 해결

#### PostgreSQL
```bash
# 연결 테스트
docker-compose exec postgresql psql -U orch_user -d orch_db -c "SELECT version();"

# 테이블 확인
docker-compose exec postgresql psql -U orch_user -d orch_db -c "\dt"
```

#### Weaviate
```bash
# 스키마 확인
curl http://localhost:8080/v1/schema

# 객체 수 확인
curl http://localhost:8080/v1/objects
```

#### Kafka
```bash
# 토픽 목록 확인
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# 컨슈머 그룹 확인
docker-compose exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --list
```

#### Prometheus & Grafana
```bash
# Prometheus 타겟 상태 확인
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[].health'

# Grafana 데이터소스 연결 테스트
curl -u admin:admin http://localhost:3000/api/datasources/proxy/1/api/v1/query?query=up

# 메트릭 수집 상태 확인
curl http://localhost:9090/api/v1/query?query=prometheus_tsdb_symbol_table_size_bytes
```

##  성능 최적화

### PostgreSQL
- 인덱스 활용: GIN 인덱스 (JSONB), 복합 인덱스 (자주 조회되는 컬럼 조합)
- 커넥션 풀링: `max_connections` 설정 확인
- 쿼리 최적화: `EXPLAIN ANALYZE` 활용

### Redis
- 메모리 관리: `maxmemory` 설정 (현재 2GB)
- 캐시 정책: `allkeys-lru` (사용량 기반 삭제)
- 지속성: AOF + RDB 하이브리드

### Weaviate
- 벡터 인덱스: HNSW 파라미터 튜닝
- 배치 처리: 대량 데이터 삽입 시 배치 활용
- 하이브리드 검색: alpha 값 조정 (벡터 vs 키워드 가중치)

### Kafka
- 파티션 수: 동시 처리 성능 고려
- 복제 팩터: 가용성 vs 성능 균형
- 배치 처리: producer `batch.size`, `linger.ms` 조정

### Prometheus
- 메트릭 보존 기간: `--storage.tsdb.retention.time` (기본 15일)
- 메모리 사용량: `--storage.tsdb.max-block-duration` 최적화
- 스크래핑 간격: 모니터링 부하 vs 정확도 균형

### Grafana
- 대시보드 성능: 쿼리 최적화 및 적절한 시간 범위 설정
- 알림 정책: 임계값 및 평가 주기 조정
- 데이터 소스: Prometheus 쿼리 캐싱 활용

##  추가 참조

- [PostgreSQL 공식 문서](https://www.postgresql.org/docs/)
- [Redis 공식 문서](https://redis.io/documentation)
- [Weaviate 공식 문서](https://weaviate.io/developers/weaviate)
- [Kafka 공식 문서](https://kafka.apache.org/documentation/)
- [Prometheus 공식 문서](https://prometheus.io/docs/)
- [Grafana 공식 문서](https://grafana.com/docs/)
- [Docker Compose 문서](https://docs.docker.com/compose/)

---

** 문의사항이 있으시면 개발팀에 연락해 주세요.**