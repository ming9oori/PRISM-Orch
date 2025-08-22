#!/bin/bash

echo "🚀 PRISM-Orch 실제 연동 테스트를 위한 서비스 시작"
echo "================================================"

# Weaviate 시작
echo ""
echo "🔧 1. Weaviate Vector DB 시작 중..."
if docker ps --format 'table {{.Names}}' | grep -q weaviate; then
    echo "✅ Weaviate가 이미 실행 중입니다."
else
    echo "🚀 Weaviate 시작 중..."
    docker-compose up -d weaviate
    
    if [ $? -eq 0 ]; then
        echo "⏳ Weaviate 초기화 대기 중 (30초)..."
        sleep 30
        
        # Weaviate 상태 확인
        if curl -s http://localhost:8080/v1/meta > /dev/null; then
            echo "✅ Weaviate가 성공적으로 시작되었습니다."
        else
            echo "⚠️  Weaviate 시작을 확인할 수 없습니다."
        fi
    else
        echo "❌ Weaviate 시작 실패"
    fi
fi

# Ollama 확인
echo ""
echo "🤖 2. Ollama LLM 서비스 확인 중..."
if command -v ollama &> /dev/null; then
    echo "✅ Ollama가 설치되어 있습니다."
    
    # Ollama 서비스 시작
    if pgrep -f "ollama serve" > /dev/null; then
        echo "✅ Ollama 서비스가 이미 실행 중입니다."
    else
        echo "🚀 Ollama 서비스 시작 중..."
        ollama serve &
        sleep 5
    fi
    
    # 모델 확인 및 다운로드
    echo "📥 Ollama 모델 확인 중..."
    if ollama list | grep -q llama3.2; then
        echo "✅ llama3.2 모델이 이미 설치되어 있습니다."
    else
        echo "📥 llama3.2 모델 다운로드 중... (시간이 오래 걸릴 수 있습니다)"
        ollama pull llama3.2
        
        if [ $? -eq 0 ]; then
            echo "✅ llama3.2 모델 다운로드 완료"
        else
            echo "❌ llama3.2 모델 다운로드 실패"
        fi
    fi
else
    echo "⚠️  Ollama가 설치되지 않았습니다."
    echo "💡 설치 방법:"
    echo "   curl -fsSL https://ollama.ai/install.sh | sh"
fi

# OpenAI API 키 확인
echo ""
echo "🔑 3. OpenAI API 키 확인 중..."
if [ -n "$OPENAI_API_KEY" ]; then
    echo "✅ OPENAI_API_KEY가 설정되어 있습니다."
else
    echo "⚠️  OPENAI_API_KEY가 설정되지 않았습니다."
    echo "💡 설정 방법:"
    echo "   export OPENAI_API_KEY=your-api-key-here"
fi

# 서비스 상태 요약
echo ""
echo "================================================"
echo "📊 서비스 상태 요약"
echo "================================================"

# Weaviate 확인
if curl -s http://localhost:8080/v1/meta > /dev/null; then
    echo "✅ Weaviate Vector DB: 실행 중 (http://localhost:8080)"
else
    echo "❌ Weaviate Vector DB: 연결 실패"
fi

# Ollama 확인
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama LLM: 실행 중 (http://localhost:11434)"
else
    echo "❌ Ollama LLM: 연결 실패"
fi

# OpenAI API 확인
if [ -n "$OPENAI_API_KEY" ]; then
    echo "✅ OpenAI API: 키 설정됨"
else
    echo "❌ OpenAI API: 키 미설정"
fi

echo ""
echo "🎯 실제 연동 테스트 실행:"
echo "   python test_real_integration.py"
echo ""
echo "🛠️  문제 해결:"
echo "   - Weaviate: docker-compose logs weaviate"
echo "   - Ollama: ollama serve 또는 systemctl status ollama"
echo "   - OpenAI: export OPENAI_API_KEY=your-key" 