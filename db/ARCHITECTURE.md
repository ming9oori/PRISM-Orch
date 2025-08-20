# PRISM Orchestration Database Architecture

## 1. 시스템 개요

PRISM Orchestration Database는 자율제조 AI 에이전트를 위한 통합 데이터베이스 시스템입니다. 여러 종류의 데이터베이스를 조합하여 각각의 특성에 맞는 데이터를 효율적으로 관리합니다.

## 2. 시스템 아키텍처

### 2.1 전체 구조도

```
┌─────────────────────────────────────────────────────────────────┐
│                         Application Layer                         │
│                    (AI Agents & Orchestration)                   │
└────────┬────────────────────────────────────────────┬───────────┘
         │                                            │
         ▼                                            ▼
┌─────────────────┐                          ┌─────────────────┐
│   Kafka Broker  │◄─────────────────────────│    Monitoring   │
│   (Port 19092)  │                          │   (Prometheus)  │
└────────┬────────┘                          └────────┬────────┘
         │                                            │
         ├──────────────┬─────────────┬──────────────┤
         ▼              ▼             ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  PostgreSQL  │ │    Redis     │ │   Weaviate   │ │   InfluxDB   │
│ (Port 15432) │ │ (Port 16379) │ │ (Port 18080) │ │ (Port 18086) │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
     │                 │                 │                 │
     ▼                 ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Data Storage Layer                       │
│                    (Persistent Volumes in Docker)                │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 네트워크 구성

모든 서비스는 `prism-network` Docker 브리지 네트워크를 통해 통신합니다:
- 내부 통신: 서비스명으로 직접 통신 (예: `prism-postgres:5432`)
- 외부 접근: 호스트 포트 매핑을 통한 접근

## 3. 데이터베이스 컴포넌트 상세

### 3.1 PostgreSQL (관계형 데이터베이스)
- **포트**: 15432
- **역할**: 구조화된 데이터 저장
- **저장 데이터**:
  - 에이전트 정의 및 설정
  - 워크플로우 정의
  - 태스크 큐 및 실행 이력
  - 사용자 및 권한 관리
  - 제약조건 및 규칙

### 3.2 Redis (인메모리 캐시)
- **포트**: 16379
- **역할**: 고속 캐싱 및 실시간 데이터 처리
- **저장 데이터**:
  - 세션 정보
  - 임시 상태 저장
  - 실시간 메트릭스
  - 에이전트 간 공유 메모리
  - 분산 락(Lock) 관리

### 3.3 Weaviate (벡터 데이터베이스)
- **포트**: 18080
- **역할**: AI 모델용 벡터 임베딩 저장 및 검색
- **저장 데이터**:
  - 외부 지식 문서
  - 에이전트 메모리 (단기/장기/에피소딕)
  - 인스트럭션 템플릿
  - 제조 공정 지식베이스
  - 의미론적 검색 인덱스

### 3.4 Kafka (메시지 브로커)
- **포트**: 19092
- **역할**: 에이전트 간 비동기 통신
- **토픽 구조**:
  ```
  agent.orchestration.commands    - 오케스트레이션 명령
  agent.orchestration.responses   - 명령 응답
  agent.monitoring.events         - 모니터링 이벤트
  agent.monitoring.alerts         - 경고 메시지
  agent.prediction.requests       - 예측 요청
  agent.prediction.results        - 예측 결과
  agent.control.actions          - 제어 액션
  agent.control.feedback         - 제어 피드백
  user.queries                   - 사용자 쿼리
  user.feedback                  - 사용자 피드백
  system.metrics                 - 시스템 메트릭
  system.logs                    - 시스템 로그
  constraints.violations         - 제약조건 위반
  knowledge.updates              - 지식베이스 업데이트
  ```

### 3.5 InfluxDB (시계열 데이터베이스)
- **포트**: 18086
- **역할**: 시계열 메트릭 및 성능 데이터 저장
- **저장 데이터**:
  - 제조 공정 센서 데이터
  - 성능 메트릭스
  - 리소스 사용량
  - 이벤트 타임라인

### 3.6 Prometheus (모니터링)
- **포트**: 19090
- **역할**: 메트릭 수집 및 모니터링
- **수집 대상**:
  - 각 데이터베이스 상태
  - 컨테이너 리소스 사용량
  - 애플리케이션 메트릭

### 3.7 Grafana (시각화)
- **포트**: 13000
- **역할**: 데이터 시각화 및 대시보드
- **기본 계정**: admin/admin123
- **대시보드**:
  - 시스템 전체 상태
  - 데이터베이스 성능
  - 에이전트 활동 모니터링

## 4. 데이터 흐름

### 4.1 에이전트 태스크 실행 흐름
```
1. 사용자 요청 → Kafka (user.queries)
2. 오케스트레이터 → PostgreSQL (태스크 생성)
3. 오케스트레이터 → Kafka (agent.orchestration.commands)
4. 에이전트 → Redis (상태 업데이트)
5. 에이전트 → Weaviate (지식 검색)
6. 에이전트 → Kafka (agent.orchestration.responses)
7. 결과 → PostgreSQL (이력 저장)
8. 메트릭 → InfluxDB (성능 데이터)
```

### 4.2 모니터링 데이터 흐름
```
1. 각 서비스 → Prometheus (메트릭 수집)
2. Prometheus → Grafana (시각화)
3. 이상 감지 → Kafka (agent.monitoring.alerts)
4. 알림 처리 → Redis (알림 큐)
```

## 5. 실행 및 운영

### 5.1 시스템 시작
```bash
# 전체 시스템 시작 (데이터 유지)
./scripts/deploy.sh

# 전체 시스템 시작 (데이터 초기화)
./scripts/deploy.sh --clean
```

### 5.2 서비스 관리
```bash
# 서비스 상태 확인
docker-compose ps

# 특정 서비스 로그 확인
docker-compose logs -f [서비스명]

# 서비스 재시작
docker-compose restart [서비스명]

# 전체 시스템 중지
docker-compose down

# 시스템 중지 및 데이터 삭제
docker-compose down -v
```

### 5.3 데이터베이스 접속
```bash
# PostgreSQL 접속
psql -h localhost -p 15432 -U prism_user -d prism_orchestration

# Redis 접속
redis-cli -h localhost -p 16379

# Kafka 토픽 확인
docker exec prism-kafka kafka-topics --bootstrap-server localhost:9092 --list

# Weaviate REST API
curl http://localhost:18080/v1/schema
```

### 5.4 백업 및 복구

#### PostgreSQL 백업
```bash
# 백업
docker exec prism-postgres pg_dump -U prism_user prism_orchestration > backup.sql

# 복구
docker exec -i prism-postgres psql -U prism_user prism_orchestration < backup.sql
```

#### Redis 백업
```bash
# 백업
docker exec prism-redis redis-cli SAVE
docker cp prism-redis:/data/dump.rdb ./redis-backup.rdb

# 복구
docker cp ./redis-backup.rdb prism-redis:/data/dump.rdb
docker-compose restart prism-redis
```

## 6. 성능 최적화

### 6.1 PostgreSQL 튜닝
- `shared_buffers`: 메모리의 25% 할당
- `effective_cache_size`: 메모리의 50-75% 할당
- 인덱스 최적화: 자주 조회되는 컬럼에 인덱스 생성

### 6.2 Redis 최적화
- `maxmemory-policy`: allkeys-lru 설정
- 적절한 TTL 설정으로 메모리 관리
- 파이프라이닝 사용으로 네트워크 오버헤드 감소

### 6.3 Kafka 최적화
- 파티션 수 조정: 처리량에 따라 3-5개 파티션
- `batch.size`: 배치 처리로 처리량 향상
- `compression.type`: snappy 압축 사용

## 7. 장애 대응

### 7.1 헬스체크
모든 서비스는 Docker Compose의 헬스체크 기능을 통해 모니터링됩니다:
- PostgreSQL: `pg_isready` 명령
- Redis: `redis-cli ping`
- Kafka: 토픽 리스트 조회
- Weaviate: REST API 상태 확인

### 7.2 자동 재시작
Docker Compose의 `restart: unless-stopped` 정책으로 장애 시 자동 재시작

### 7.3 로그 분석
```bash
# 에러 로그 필터링
docker-compose logs | grep ERROR

# 특정 시간 이후 로그
docker-compose logs --since "2024-01-01T00:00:00"
```

## 8. 보안 고려사항

### 8.1 네트워크 격리
- Docker 브리지 네트워크로 서비스 간 격리
- 필요한 포트만 호스트에 노출

### 8.2 인증 및 권한
- PostgreSQL: 사용자별 권한 관리
- Redis: 패스워드 설정 (프로덕션 환경)
- Grafana: 기본 패스워드 변경 필수

### 8.3 데이터 암호화
- 전송 중 암호화: TLS/SSL 설정 (프로덕션)
- 저장 시 암호화: 볼륨 암호화 고려

## 9. 확장성

### 9.1 수평 확장
- Kafka: 브로커 추가로 처리량 증가
- Redis: 클러스터 모드 지원
- Weaviate: 샤딩을 통한 분산 저장

### 9.2 수직 확장
- Docker Compose의 리소스 제한 조정
- 호스트 시스템 리소스 증설