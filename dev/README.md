# vLLM High-Performance Inference Server

제조업 Multi-Agent 시스템용 고성능 vLLM 추론 서버

## 📋 개요

이 프로젝트는 제조업 현장의 AI 에이전트들을 위한 고성능 텍스트 생성 서버입니다. vLLM을 기반으로 하여 높은 처리량과 낮은 지연시간을 제공합니다.

## 🏗️ 프로젝트 구조

```
dev/
├── src/                    # 메인 소스 코드
│   ├── __init__.py
│   ├── main.py            # 애플리케이션 진입점
│   ├── models/            # 데이터 모델
│   │   ├── __init__.py
│   │   └── schemas.py
│   ├── core/              # 핵심 vLLM 엔진
│   │   ├── __init__.py
│   │   └── vllm_manager.py
│   └── api/               # FastAPI 애플리케이션
│       ├── __init__.py
│       ├── app.py
│       └── routes.py
├── config/                # 설정 파일
│   ├── models.yaml        # 모델 설정
│   └── optimization.yaml  # 성능 최적화 설정
├── docker/                # Docker 관련 파일
│   └── Dockerfile.vllm
├── nginx/                 # Nginx 설정
│   └── nginx.conf
├── scripts/               # 배포 스크립트
│   └── deploy.sh
├── tools/                 # 유틸리티 도구
│   ├── benchmark.py       # 성능 벤치마크
│   └── monitor.py         # 서버 모니터링
├── docker-compose.yml     # Docker Compose 설정
├── requirements-vllm.txt  # Python 의존성
└── README.md
```

## 🚀 빠른 시작

### 1. 환경 요구사항

- NVIDIA GPU (CUDA 12.1+)
- Docker & Docker Compose
- Python 3.8+

### 2. 배포

```bash
# 저장소 클론
git clone <repository-url>
cd dev

# 배포 스크립트 실행
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### 3. 서버 확인

```bash
# 헬스체크
curl http://localhost:8000/health

# 테스트 요청
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "monitoring",
    "prompt": "센서 온도가 195도입니다. 상황을 분석해주세요.",
    "max_tokens": 256
  }'
```

## 📊 API 엔드포인트

### 기본 엔드포인트

- `GET /` - 서버 정보
- `GET /health` - 헬스체크
- `GET /api/v1/models` - 모델 정보
- `GET /api/v1/stats` - 성능 통계

### 추론 엔드포인트

- `POST /api/v1/generate` - 단일 텍스트 생성
- `POST /api/v1/batch_generate` - 배치 텍스트 생성

## 🎯 지원 에이전트 타입

- `orchestration` - AI 오케스트레이션 시스템
- `monitoring` - 제조 공정 모니터링
- `prediction` - 예측 분석
- `control` - 자율제어

## 🔧 설정

### 모델 설정 (`config/models.yaml`)

다양한 크기의 모델 설정을 지원합니다:
- `small` - 개발/테스트용
- `medium` - 일반 운영용
- `large` - 고성능 요구시
- `xlarge` - 최고 성능

### 성능 최적화 (`config/optimization.yaml`)

하드웨어별 최적화 설정을 제공합니다:
- A100 80GB (단일/듀얼/쿼드)
- RTX 4090 (개발용)

## 📈 모니터링

### Grafana 대시보드
- URL: http://localhost:3000
- 계정: admin/admin

### 실시간 모니터링
```bash
python tools/monitor.py
```

### 성능 벤치마크
```bash
python tools/benchmark.py
```

## 🐳 Docker 구성

서비스 구성:
- `vllm-server` - 메인 추론 서버
- `redis` - 캐싱
- `nginx` - 로드 밸런서
- `prometheus` - 메트릭 수집
- `grafana` - 모니터링 대시보드

## 🔍 문제 해결

### 일반적인 문제

1. **GPU 메모리 부족**
   - `config/optimization.yaml`에서 `gpu_memory_utilization` 값 조정

2. **모델 로딩 실패**
   - 모델 캐시 디렉토리 확인: `/root/.cache/huggingface`

3. **성능 이슈**
   - `tensor_parallel_size` 설정 확인
   - 배치 크기 조정

### 로그 확인

```bash
# 서버 로그
docker-compose logs vllm-server

# 전체 서비스 로그
docker-compose logs
```

## 📝 라이선스

MIT License

## 🤝 기여

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request 