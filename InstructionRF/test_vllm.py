from instruction_rf_client import InstructionRefinementClient
import json

# 베이스 URL만 넣기 (끝에 /v1 까지만)
client = InstructionRefinementClient(server_url="http://127.0.0.1:8000/v1", timeout=60)

# 연결 테스트는 /v1/models (GET)로 확인하도록 구현되어 있어야 안정적
test_result = client.test_api_connection()
print(f"연결 상태: {test_result.get('status')}")

if test_result.get('status') == 'success':
    # 실제 호출은 /v1/completions 또는 /v1/chat/completions 로 POST
    result = client.refine_instruction("생산 수율을 개선하고 싶은데 어떤 파라미터를 조정해야 할까?")  # 내부에서 model 등 세팅
    print(json.dumps(result, indent=2, ensure_ascii=False))
else:
    print(f"연결 실패: {test_result.get('error')}")