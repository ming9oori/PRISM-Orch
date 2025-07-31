"""
메인 애플리케이션 진입점
"""

import argparse
import logging
import torch
import uvicorn

from .api import create_app

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="vLLM High-Performance Inference Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host address")
    parser.add_argument("--port", type=int, default=8000, help="Port number")
    parser.add_argument("--model", default="microsoft/DialoGPT-large", help="Model name")
    parser.add_argument("--tensor-parallel", type=int, default=0, help="Tensor parallel size (0=auto)")
    parser.add_argument("--max-model-len", type=int, default=4096, help="Max model length")
    parser.add_argument("--gpu-memory-util", type=float, default=0.9, help="GPU memory utilization")
    
    args = parser.parse_args()
    
    # 텐서 병렬 크기 자동 설정
    if args.tensor_parallel == 0:
        args.tensor_parallel = torch.cuda.device_count() if torch.cuda.is_available() else 1
    
    logger.info(f"Starting vLLM server with model: {args.model}")
    logger.info(f"Tensor parallel size: {args.tensor_parallel}")
    logger.info(f"GPU count: {torch.cuda.device_count()}")
    
    # FastAPI 앱 생성
    app = create_app()
    
    # 서버 실행
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        workers=1,  # vLLM은 단일 워커에서 내부적으로 병렬 처리
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main() 