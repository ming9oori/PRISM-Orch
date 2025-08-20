#!/bin/bash

echo "PRISM API 간단 테스트"
echo "===================="

# API 엔드포인트
API_URL="http://localhost:8000/api/agents/instruction_rf/invoke"

# 테스트 쿼리
QUERY="3번 에칭 장비 압력 확인해주세요"

echo "요청: $QUERY"
echo ""

# curl 호출
response=$(curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d "{\"prompt\": \"$QUERY\"}")

echo "응답:"
echo "$response" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(json.dumps(data, indent=2, ensure_ascii=False))
except:
    # JSON이 아닌 경우 그대로 출력
    sys.stdin.seek(0)
    print(sys.stdin.read())
"