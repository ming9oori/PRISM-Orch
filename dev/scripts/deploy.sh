#!/bin/bash
# vLLM 서버 배포 스크립트

set -e

echo "=== vLLM High-Performance Inference Server Deployment ==="

# 환경 변수 설정
export MODEL_NAME=${MODEL_NAME:-"microsoft/DialoGPT-large"}
export TENSOR_PARALLEL_SIZE=${TENSOR_PARALLEL_SIZE:-1}
export GPU_COUNT=${GPU_COUNT:-1}

# GPU 확인
echo "Checking GPU availability..."
nvidia-smi

# CUDA 버전 확인
echo "CUDA Version:"
nvcc --version

# Docker 이미지 빌드
echo "Building Docker image..."
docker build -f docker/Dockerfile.vllm -t vllm-inference-server .

# 기존 컨테이너 정리
echo "Cleaning up existing containers..."
docker-compose down

# 새 서비스 시작
echo "Starting services..."
docker-compose up -d

# 서비스 상태 확인
echo "Checking service status..."
sleep 30
docker-compose ps

# 헬스체크
echo "Health check..."
for i in {1..10}; do
    if curl -f http://localhost:8000/health; then
        echo "✅ Server is healthy!"
        break
    else
        echo "⏳ Waiting for server to be ready... ($i/10)"
        sleep 10
    fi
done

# 성능 테스트
echo "Running performance test..."
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "monitoring",
    "prompt": "센서 온도가 195도입니다. 정상 범위는 150-200도인데 상황을 분석해주세요.",
    "max_tokens": 256
  }'

echo ""
echo "✅ Deployment complete!"
echo "📊 Server URL: http://localhost:8000"
echo "🏥 Health Check: http://localhost:8000/health"
echo "📈 Stats: http://localhost:8000/api/v1/stats"
echo "🔍 Grafana: http://localhost:3000 (admin/admin)" 