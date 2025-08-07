# PRISM Orchestration Database Setup

이 문서는 PRISM Orchestration Agent의 다중 데이터베이스 인프라 설정 및 운영 가이드입니다.

## 📋 개요

### 아키텍처
- **PostgreSQL**: 메인 트랜잭션 DB (ACID 보장)
- **Redis**: 캐싱 및 세션 관리
- **Weaviate**: 벡터 검색 및 RAG 시스템
- **Kafka**: 에이전트 간 메시지 큐

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

## 🚀 빠른 시작

### 1. 전체 배포
```bash
cd db
./scripts/deploy.sh
```

### 2. 개별 서비스 관리
```bash
cd db
# 서비스 시작
docker-compose up -d

# 서비스 중지
docker-compose down

# 로그 확인
docker-compose logs [service-name]
```

### 3. 테스트 실행
```bash
cd db
# 종합 테스트 (모든 DB 기능 검증)
uv run python scripts/test_all.py

# Python 의존성은 자동으로 설치됩니다 (pyproject.toml 사용)
```

## 🔧 서비스 접속 정보

### Database Connections
| Service | URL | Credentials |
|---------|-----|-------------|
| PostgreSQL | `localhost:5432` | user: `orch_user`, db: `orch_db`, password: `orch_password` |
| Redis | `localhost:6379` | password: `redis_password` |
| Weaviate | `http://localhost:8080` | 인증 없음 |
| Kafka | `localhost:9092` | 인증 없음 |

### Management UIs
| Service | URL | Credentials |
|---------|-----|-------------|
| pgAdmin | `http://localhost:8082` | admin@orch.com / admin_password |
| Redis Insight | `http://localhost:8001` | 인증 없음 |
| Kafka UI | `http://localhost:8081` | 인증 없음 |

### 🔍 모니터링 대시보드
| Service | URL | Credentials | 용도 |
|---------|-----|-------------|------|
| **Grafana** | `http://localhost:3000` | admin / admin_password | 📊 통합 모니터링 대시보드 |
| **Prometheus** | `http://localhost:9090` | 인증 없음 | 📈 메트릭 수집 및 쿼리 |
| cAdvisor | `http://localhost:8888` | 인증 없음 | 🐳 컨테이너 리소스 모니터링 |

## 📁 폴더 구조

```
db/
├── docker-compose.yml          # Docker Compose 설정
├── pyproject.toml              # uv 프로젝트 설정
├── uv.lock                     # 의존성 락 파일
├── .venv/                      # Python 가상환경
├── .python-version             # Python 버전 설정
├── README.md                   # DB 설정 가이드
├── init/
│   └── 01_create_tables.sql    # PostgreSQL 테이블 생성
├── redis/
│   └── redis.conf              # Redis 설정
├── weaviate/
│   ├── schema_init.py          # Weaviate 스키마 초기화
│   └── requirements.txt        # Python 의존성
├── kafka/
│   ├── create_topics.py        # Kafka 토픽 생성
│   └── requirements.txt        # Python 의존성
├── scripts/
│   ├── deploy.sh               # 전체 배포 스크립트
│   └── test_all.py            # 종합 테스트 스크립트
├── prometheus/                 # Prometheus 설정
│   └── prometheus.yml         # 메트릭 수집 설정
├── grafana/                   # Grafana 설정
│   ├── provisioning/          # 데이터소스 및 대시보드 프로비저닝
│   └── dashboards/           # 사전 구성된 대시보드
└── docs/
    └── README_DB.md           # 상세 운영 가이드
```

## 🧪 테스트 가이드

### 기본 기능 테스트
```bash
cd db

# 1. PostgreSQL CRUD 테스트
docker-compose exec -T postgresql psql -U orch_user -d orch_db -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"

# 2. Redis 연결 테스트
docker-compose exec -T redis redis-cli -a redis_password ping

# 3. Weaviate 연결 테스트
curl http://localhost:8080/v1/meta

# 4. Kafka 토픽 확인
docker-compose exec -T kafka kafka-topics --bootstrap-server localhost:9092 --list
```

### 종합 테스트 실행
```bash
cd db
uv run python scripts/test_all.py

# 출력 예시:
# ============================================================
# PRISM ORCHESTRATION DATABASE TEST RESULTS
# ============================================================
# postgresql_basic              ✅ PASSED
# postgresql_relationships      ✅ PASSED
# redis_operations              ✅ PASSED
# weaviate_operations           ❌ FAILED (minor issue)
# kafka_operations              ✅ PASSED
# integration_workflow          ✅ PASSED
# ------------------------------------------------------------
# Total Tests: 6
# Passed: 5
# Failed: 1
# Success Rate: 83.3%
# ============================================================
```

## 🛠 개별 초기화 스크립트

### Weaviate 스키마 초기화
```bash
cd db/weaviate
uv run --project .. python schema_init.py
```

### Kafka 토픽 생성
```bash
cd db/kafka
uv run --project .. python create_topics.py
```

## 📊 모니터링 및 관찰성

### 🔍 모니터링 대시보드 사용법

#### 1. Grafana 대시보드 접속
```bash
# 서비스 시작 후 브라우저에서 접속
open http://localhost:3000

# 로그인: admin / admin_password
# 자동으로 "PRISM Orchestration DB Monitoring" 대시보드가 로드됩니다
```

#### 2. 주요 모니터링 지표
- **Service Status**: 각 서비스 Up/Down 상태 실시간 확인
- **Container Resources**: CPU, 메모리 사용량 모니터링
- **Database Metrics**: 
  - PostgreSQL: 연결 수, 쿼리 성능, 테이블 크기
  - Redis: 메모리 사용량, 히트율, 키 수
  - Kafka: 토픽 상태, 메시지 처리량, 컨슈머 랙
  - Weaviate: API 응답 시간, 인덱스 상태

#### 3. 알람 설정
```bash
# Prometheus에서 메트릭 확인
curl http://localhost:9090/api/v1/query?query=up

# 서비스별 상태 확인
curl http://localhost:9090/api/v1/query?query=up{job="postgresql"}
curl http://localhost:9090/api/v1/query?query=up{job="redis"}
curl http://localhost:9090/api/v1/query?query=up{job="kafka"}
curl http://localhost:9090/api/v1/query?query=up{job="weaviate"}
```

### 로그 확인
```bash
cd db
# 모든 서비스 로그
docker-compose logs

# 특정 서비스 로그
docker-compose logs postgresql
docker-compose logs redis
docker-compose logs weaviate
docker-compose logs kafka
```

### 데이터 백업
```bash
cd db
# PostgreSQL 백업
docker-compose exec postgresql pg_dump -U orch_user orch_db > ../backups/backup_$(date +%Y%m%d).sql

# Redis 백업 (자동 저장)
docker-compose exec redis redis-cli -a redis_password BGSAVE
```

### 서비스 상태 확인
```bash
cd db
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
   ```

2. **Docker 관련**
   ```bash
   cd db
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

## 📈 성능 최적화

### PostgreSQL
- 인덱스 활용: GIN 인덱스 (JSONB), 복합 인덱스 (자주 조회되는 컬럼 조합)
- 커넥션 풀링: `max_connections` 설정 확인
- 쿼리 최적화: `EXPLAIN ANALYZE` 활용

### Redis
- 메모리 관리: `maxmemory` 설정 (현재 2GB)
- 캐시 정책: `allkeys-lru` (사용량 기반 삭제)
- 지속성: AOF + RDB 하이브리드

### Weaviate
- 스키마 최적화: 불필요한 vectorizer 비활성화
- 검색 최적화: BM25 키워드 검색 활용
- 배치 처리: 대량 데이터 삽입 시 배치 활용

### Kafka
- 파티션 수: 동시 처리 성능 고려
- 복제 팩터: 가용성 vs 성능 균형
- 배치 처리: producer `batch.size`, `linger.ms` 조정

## 📝 추가 참조

- [PostgreSQL 공식 문서](https://www.postgresql.org/docs/)
- [Redis 공식 문서](https://redis.io/documentation)
- [Weaviate 공식 문서](https://weaviate.io/developers/weaviate)
- [Kafka 공식 문서](https://kafka.apache.org/documentation/)
- [Docker Compose 문서](https://docs.docker.com/compose/)

---

**📞 문의사항이 있으시면 개발팀에 연락해 주세요.**