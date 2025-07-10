import requests
import json

# --- 설정 ---
# 로컬에서 실행 중인 PRISM-Orch 애플리케이션의 주소
BASE_URL = "http://127.0.0.1:8000"
ORCHESTRATE_ENDPOINT = "/api/v1/orchestrate/"

def test_orchestration_api():
    """
    PRISM-Orch의 메인 오케스트레이션 API를 테스트합니다.
    """
    url = f"{BASE_URL}{ORCHESTRATE_ENDPOINT}"
    
    # API에 전송할 샘플 사용자 질의
    payload = {
        "query": "A-1 라인 압력에 이상이 생긴 것 같은데, 원인이 뭐야? 그리고 해결책도 추천해줘.",
        "session_id": "test_client_session_001",
        "user_preferences": {
            "urgency": "high",
            "output_format": "detailed"
        }
    }
    
    print("="*50)
    print(f"🚀 요청 전송: POST {url}")
    print(f"📋 요청 데이터:\n{json.dumps(payload, indent=2, ensure_ascii=False)}")
    print("="*50)

    try:
        # requests 라이브러리를 사용하여 POST 요청을 보냅니다.
        response = requests.post(url, json=payload, timeout=10)
        
        # 응답 상태 코드 확인
        response.raise_for_status()  # 2xx 상태 코드가 아니면 에러를 발생시킴
        
        print(f"✅ 요청 성공! (상태 코드: {response.status_code})")
        print("="*50)
        print("📦 서버 응답:\n")
        
        # 응답 받은 JSON 데이터를 예쁘게 출력
        response_json = response.json()
        print(json.dumps(response_json, indent=2, ensure_ascii=False))
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 요청 실패: {e}")
        print("---")
        print("애플리케이션이 실행 중인지 확인하세요.")
        print("  - 터미널에서 `python -m src.main` 명령어를 실행했는지 확인해주세요.")
        print(f"  - 애플리케이션이 {BASE_URL} 에서 실행되고 있어야 합니다.")
        
    print("="*50)


if __name__ == "__main__":
    # requests 라이브러리가 설치되지 않았다면 설치 안내 메시지를 출력합니다.
    try:
        import requests
    except ImportError:
        print("`requests` 라이브러리가 필요합니다.")
        print("터미널에서 `pip install requests` 또는 `pip install -r requirements.txt`를 실행해주세요.")
    else:
        test_orchestration_api() 