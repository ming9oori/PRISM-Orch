#!/bin/bash

# PRISM Orchestration Database Deployment Script
# 자율제조 AI 에이전트 데이터베이스 배포 스크립트

set -e

echo "PRISM Orchestration Database 배포를 시작합니다..."

# 현재 스크립트 위치 확인
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_DIR="$(dirname "$SCRIPT_DIR")"

cd "$DB_DIR"

echo "작업 디렉토리: $DB_DIR"

# Docker와 Docker Compose 설치 확인
if ! command -v docker &> /dev/null; then
    echo "Error: Docker가 설치되어 있지 않습니다. Docker를 먼저 설치해주세요."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose가 설치되어 있지 않습니다. Docker Compose를 먼저 설치해주세요."
    exit 1
fi

# 이전 컨테이너 정리
echo "기존 컨테이너 정리 중..."
docker-compose down --remove-orphans || true

# 네트워크 및 볼륨 정리 (선택사항)
# 환경 변수나 파라미터로 제어 가능
CLEAN_VOLUMES=${CLEAN_VOLUMES:-false}
if [ "$1" = "--clean" ] || [ "$CLEAN_VOLUMES" = "true" ]; then
    echo "기존 볼륨 삭제 중..."
    docker-compose down -v
    docker volume prune -f
else
    echo "기존 볼륨 유지 (--clean 옵션으로 삭제 가능)"
fi

# Docker Compose로 서비스 시작
echo "Docker 컨테이너 시작 중..."
docker-compose up -d

echo "데이터베이스 서비스 헬스 체크 중..."

# PostgreSQL 연결 확인
echo "PostgreSQL 연결 확인 중..."
for i in {1..30}; do
    if docker exec prism-postgres pg_isready -U prism_user -d prism_orchestration &>/dev/null; then
        echo "PostgreSQL 연결 성공"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Error: PostgreSQL 연결 실패"
        exit 1
    fi
    sleep 2
done

# Redis 연결 확인
echo "Redis 연결 확인 중..."
for i in {1..30}; do
    if docker exec prism-redis redis-cli ping &>/dev/null; then
        echo "Redis 연결 성공"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Error: Redis 연결 실패"
        exit 1
    fi
    sleep 2
done

# Kafka 연결 확인
echo "Kafka 연결 확인 중..."
for i in {1..30}; do
    if docker exec prism-kafka kafka-topics --bootstrap-server localhost:9092 --list &>/dev/null; then
        echo "Kafka 연결 성공"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Warning: Kafka 연결 확인 실패, 토픽 생성시 재시도됩니다"
        break
    fi
    sleep 2
done

# Weaviate 연결 확인
echo "Weaviate 연결 확인 중..."
for i in {1..60}; do
    if curl -s http://localhost:18080/v1/.well-known/ready &>/dev/null; then
        echo "Weaviate 연결 성공"
        break
    fi
    if [ $i -eq 60 ]; then
        echo "Error: Weaviate 연결 실패"
        exit 1
    fi
    sleep 2
done

# Python 환경 확인 및 패키지 설치
if command -v python3 &> /dev/null; then
    echo "Python 패키지 설치 중..."
    
    # Kafka topics 생성
    if [ -f "kafka/requirements.txt" ]; then
        python3 -m pip install -r kafka/requirements.txt --quiet
        echo "Kafka 토픽 생성 중..."
        python3 kafka/create_topics.py
    fi
    
    # Weaviate 스키마 초기화
    if [ -f "weaviate/requirements.txt" ]; then
        python3 -m pip install -r weaviate/requirements.txt --quiet
        echo "Weaviate 스키마 초기화 중..."
        python3 weaviate/schema_init.py
    fi
else
    echo "Warning: Python3가 설치되어 있지 않습니다. Kafka와 Weaviate 초기화를 수동으로 진행해주세요."
fi

# 서비스 상태 확인
echo ""
echo "서비스 상태:"
docker-compose ps

echo ""
echo "PRISM Orchestration Database 배포 완료!"
echo ""
echo "서비스 접속 정보:"
echo "  Grafana: http://localhost:13000 (admin/admin123)"
echo "  Prometheus: http://localhost:19090"
echo "  PostgreSQL: localhost:15432 (prism_user/prism_password)"
echo "  Redis: localhost:16379"
echo "  Weaviate: http://localhost:18080"
echo "  Kafka: localhost:19092"
echo "  InfluxDB: http://localhost:18086"
echo ""
echo "로그 확인: docker-compose logs -f [서비스명]"
echo "서비스 중지: docker-compose down"