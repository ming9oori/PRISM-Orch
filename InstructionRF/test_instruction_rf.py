#!/usr/bin/env python3
"""
InstructionRF 클라이언트 테스트 스크립트 (직접 API 호출 버전)
"""

import os
import sys
import json
import requests
import time
from datetime import datetime


def test_basic_functionality():
    """기본 기능 테스트"""
    print("=== InstructionRF 기본 기능 테스트 ===")
    
    try:
        # API URL 설정
        api_url = os.getenv('LLM_API_URL', 'http://localhost:8000/api/agents/instruction_rf/invoke')
        print(f"API URL: {api_url}")
        
        # 기본 서버 연결 테스트
        print("\n=== 기본 서버 연결 테스트 ===")
        try:
            response = requests.get("http://localhost:8000/api/agents", timeout=10)
            print(f"기본 연결 상태: {response.status_code}")
            if response.status_code == 200:
                agents = response.json()
                print(f"사용 가능한 에이전트: {len(agents)}개")
                for agent in agents:
                    if agent.get('name') == 'instruction_rf':
                        print(f"   instruction_rf 에이전트 발견")
        except Exception as e:
            print(f"기본 연결 실패: {type(e).__name__}: {e}")
        
        # API 연결 테스트
        print("\n=== API 연결 테스트 ===")
        start_time = time.time()
        try:
            test_payload = {"prompt": "연결 테스트"}
            response = requests.post(api_url, json=test_payload, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                print(f"API 연결 성공 (응답시간: {response_time:.2f}초)")
                
                # 실제 쿼리 변환 테스트
                print("\n=== 쿼리 변환 테스트 ===")
                test_queries = [
                    "3번 에칭 장비 상태 확인해주세요",
                    "생산 수율이 떨어지고 있어요",
                    "온도 센서 이상 감지",
                    "전체 생산라인 효율성 분석"
                ]
                
                for i, query in enumerate(test_queries, 1):
                    print(f"\n테스트 쿼리 {i}: {query}")
                    try:
                        payload = {"prompt": query}
                        response = requests.post(api_url, json=payload, timeout=10)
                        
                        if response.status_code == 200:
                            result = response.json()
                            text = result.get('text', '')
                            print(f"변환 성공!")
                            print(f"   응답 길이: {len(text)} characters")
                            
                            # JSON 패턴 찾기
                            if 'operation' in text and 'ANOMALY_CHECK' in text:
                                print(f"   ANOMALY_CHECK 패턴 감지")
                            elif 'operation' in text and 'PREDICTION' in text:
                                print(f"   PREDICTION 패턴 감지")
                            elif 'operation' in text and 'OPTIMIZATION' in text:
                                print(f"   OPTIMIZATION 패턴 감지")
                            else:
                                print(f"   응답 미리보기: {text[:100]}...")
                                
                        else:
                            print(f"변환 실패 (상태코드: {response.status_code})")
                            
                    except Exception as e:
                        print(f"요청 실패: {e}")
                        
            else:
                print(f"API 연결 실패 (상태코드: {response.status_code})")
                
        except Exception as e:
            print(f"API 연결 실패: {e}")
        
        # API 문서 확인
        print("\n=== API 문서 확인 ===")
        try:
            docs_response = requests.get("http://localhost:8000/docs", timeout=5)
            if docs_response.status_code == 200:
                print("API 문서 접근 가능: http://localhost:8000/docs")
            else:
                print(f"API 문서 응답 코드: {docs_response.status_code}")
        except Exception as e:
            print(f"API 문서 접근 실패: {type(e).__name__}")
            
    except Exception as e:
        print(f"테스트 실패: {e}")
        import traceback
        traceback.print_exc()


def test_examples():
    """사용 예제"""
    print("\n" + "="*50)
    print("=== 사용 예제 ===")
    
    print("기본 사용법:")
    print("```python")
    print("import requests")
    print("import json")
    print("")
    print("api_url = 'http://localhost:8000/api/agents/instruction_rf/invoke'")
    print("payload = {'prompt': '3번 에칭 장비 압력 확인해주세요'}")
    print("response = requests.post(api_url, json=payload)")
    print("result = response.json()")
    print("print(result['text'])")
    print("```")
    
    print("\n예상 JSON 출력 형식:")
    example_json = {
        "operation": "ANOMALY_CHECK",
        "parameters": [
            {"name": "장비ID", "value": "3"},
            {"name": "압력", "value": "5000"},
            {"name": "시간 범위", "value": "9000-10000"}
        ]
    }
    print(json.dumps(example_json, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    test_basic_functionality()
    test_examples()
    
    print("\n" + "="*50)
    print("테스트 완료!")
    print("실제 사용 시에는 다음과 같이 하세요:")
    print("1. export LLM_API_URL='http://localhost:8000/api/agents/instruction_rf/invoke'")
    print("2. requests.post(API_URL, json={'prompt': 'your_query'})")