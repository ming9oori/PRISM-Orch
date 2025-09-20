import json
import uuid
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import requests


class InstructionRefinementClient:
    """
    제조업 AI 에이전트 오케스트레이션을 위한 자연어 쿼리를 구조화된 명령어로 변환하는 클라이언트
    연구실 서버 (Qwen 1.5B) 연동 버전
    """
    
    def __init__(self, config_path: str = None, server_url: str = None, timeout: int = 30):
        """
        클라이언트 초기화
        
        Args:
            config_path: 설정 파일 경로 (기본: ../config.json)
            server_url: 직접 지정할 서버 URL (설정 파일보다 우선)
            timeout: API 호출 타임아웃 (초)
        """
        self.config = self._load_config(config_path)
        self.server_url = server_url or os.getenv('LLM_API_URL') or self.config.get('server', {}).get('llm_api_url')
        self.timeout = timeout or self.config.get('server', {}).get('timeout', 30)
        
        if not self.server_url or self.server_url == "http://YOUR_SERVER_IP/api/agents":
            raise ValueError("서버 URL이 설정되지 않았습니다. config.json 파일을 확인하거나 LLM_API_URL 환경변수를 설정해주세요.")
        
        self.system_prompt = self._load_system_prompt()
        self.prompt_manager = getattr(self, 'prompt_manager', None)
        print(f"✅ InstructionRF 클라이언트 초기화 완료")
    
    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        """설정 파일 로드"""
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  설정 파일을 찾을 수 없습니다: {config_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"⚠️  설정 파일 JSON 파싱 오류: {e}")
            return {}
    
    def _load_system_prompt(self) -> str:
        """InstructionRF 프롬프트 로드"""
        try:
            from prompt_manager import PromptManager
            self.prompt_manager = PromptManager()
            return self.prompt_manager.get_system_prompt()
        except ImportError:
            # 백워드 호환성: prompt_manager가 없으면 기존 방식 사용
            try:
                prompt_path = os.path.join(os.path.dirname(__file__), 'refine_prompt.md')
                with open(prompt_path, "r", encoding="utf-8") as f:
                    return f.read()
            except FileNotFoundError:
                raise FileNotFoundError("프롬프트 파일을 찾을 수 없습니다. prompts.yaml 또는 refine_prompt.md가 필요합니다.")
        except Exception as e:
            raise Exception(f"프롬프트 로드 중 오류: {str(e)}")
    
    def _test_connection(self) -> bool:
        """
        서버 연결 테스트
        
        Returns:
            연결 성공 여부
        """
        try:
            base_url = self.server_url.rstrip('/api/agents')
            response = requests.get(f"{base_url}/", timeout=5)
            if response.status_code == 200:
                print("✅ 서버 연결 확인됨")
                return True
            else:
                print(f"⚠️  서버 응답 코드: {response.status_code}")
                return False
        except Exception as e:
            print(f"⚠️  서버 연결 확인 실패: {type(e).__name__}")
            print("API 호출은 계속 시도됩니다.")
            return False
    
    def _call_llm_api(self, prompt: str, use_agent: bool = False, agent_name: str = "instruction_rf") -> str:
        """
        연구실 서버 LLM API 호출
        
        Args:
            prompt: 전송할 프롬프트
            use_agent: 에이전트 사용 여부 (기본: False)
            agent_name: 사용할 에이전트 이름
            
        Returns:
            LLM 응답
        """
        base_url = self.server_url.rstrip('/api/agents')
        
        if use_agent:
            # 에이전트를 통한 호출: POST /api/agents/{agent_name}/invoke
            endpoint = f"{base_url}/api/agents/{agent_name}/invoke"
        else:
            # 직접 텍스트 생성: POST /api/generate
            endpoint = f"{base_url}/api/generate"
        
        payload = {
            "prompt": prompt,
            "max_tokens": 2000,
            "temperature": 0.1
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            # API 응답 구조에 따라 적절한 필드 반환
            return result.get("response", result.get("generated_text", result.get("text", str(result))))
            
        except requests.exceptions.Timeout:
            raise Exception(f"API 호출 타임아웃 ({self.timeout}초)")
        except requests.exceptions.ConnectionError:
            raise Exception(f"서버 연결 실패: {endpoint}")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP 에러: {e.response.status_code} - {endpoint}")
        except Exception as e:
            raise Exception(f"API 호출 중 오류 발생: {str(e)}")
    
    def register_agent(self, agent_name: str = "instruction_rf", description: str = None) -> Dict[str, Any]:
        """
        InstructionRF 전용 에이전트 등록
        
        Args:
            agent_name: 등록할 에이전트 이름
            description: 에이전트 설명
            
        Returns:
            등록 결과
        """
        base_url = self.server_url.rstrip('/api/agents')
        endpoint = f"{base_url}/api/agents"
        
        # 구조화된 프롬프트 매니저 사용
        if self.prompt_manager:
            role_prompt = self.prompt_manager.get_agent_role_prompt()
        else:
            role_prompt = """당신은 제조업 AI 에이전트 오케스트레이션을 위한 명령어 변환 전문가입니다. 
사용자의 자연어 쿼리를 구조화된 JSON 명령어로 변환하여 제조 시스템의 다양한 AI 에이전트들이 실행할 수 있도록 합니다.
반드시 유효한 JSON 형식으로만 응답하며, 제조업 도메인 지식을 바탕으로 정확한 의도 분류와 작업 분해를 수행합니다."""
        
        payload = {
            "name": agent_name,
            "description": description or "제조업 AI 에이전트 오케스트레이션을 위한 자연어 쿼리 변환 전문가",
            "role_prompt": role_prompt
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ 에이전트 '{agent_name}' 등록 성공")
            return result
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:  # Conflict - 이미 존재
                print(f"ℹ️  에이전트 '{agent_name}'가 이미 존재합니다.")
                return {"status": "already_exists", "agent_name": agent_name}
            else:
                raise Exception(f"에이전트 등록 실패: HTTP {e.response.status_code}")
        except Exception as e:
            raise Exception(f"에이전트 등록 중 오류 발생: {str(e)}")
    
    def refine_instruction(self, user_query: str) -> Dict[str, Any]:
        """
        자연어 쿼리를 구조화된 JSON 명령어로 변환
        
        Args:
            user_query: 사용자의 자연어 쿼리
            
        Returns:
            구조화된 JSON 명령어
        """
        # Qwen 1.5B에 최적화된 간단한 프롬프트 생성
        prompt = f"""Convert this manufacturing query to JSON format:
Query: {user_query}

Required JSON format:
{{
  "instruction_id": "inst_[timestamp]",
  "original_query": "{user_query}",
  "intent_type": "ANOMALY_CHECK or PREDICTION or CONTROL or INFORMATION or OPTIMIZATION",
  "priority": "HIGH or MEDIUM or LOW",
  "target": {{
    "equipment_id": "equipment identifier",
    "parameter": "parameter name",
    "process": "process name"
  }},
  "tasks": [
    {{
      "task_id": "task_001",
      "agent": "MONITORING or PREDICTION or CONTROL or ORCHESTRATION",
      "action": "specific action",
      "parameters": {{}},
      "dependencies": [],
      "expected_output": "output description"
    }}
  ]
}}

Respond with valid JSON only:"""
        
        try:
            # 에이전트를 통한 전문적인 변환 시도
            try:
                response_content = self._call_llm_api(prompt, use_agent=True, agent_name="instruction_rf")
                print("✅ 전문 에이전트를 통한 변환")
            except Exception:
                # 에이전트 호출 실패 시 직접 생성 API 사용
                response_content = self._call_llm_api(prompt, use_agent=False)
                print("ℹ️  직접 생성 API 사용")
            
            # JSON 응답 파싱 (Qwen 1.5B 모델의 응답 특성 고려)
            json_start = response_content.find('{')
            
            if json_start != -1:
                # 첫 번째 완전한 JSON 객체 추출
                brace_count = 0
                json_end = json_start
                for i, char in enumerate(response_content[json_start:], json_start):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break
                
                if json_end > json_start:
                    json_content = response_content[json_start:json_end]
                    try:
                        parsed_json = json.loads(json_content)
                    except json.JSONDecodeError:
                        # JSON 파싱 실패 시 더 관대한 추출 시도
                        return self._create_fallback_instruction(user_query, f"JSON 파싱 실패: {json_content[:100]}...")
                else:
                    return self._create_fallback_instruction(user_query, "완전한 JSON 구조를 찾을 수 없음")
                
                # 기본 필드 검증 및 보완
                if "instruction_id" not in parsed_json:
                    parsed_json["instruction_id"] = f"inst_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
                
                if "original_query" not in parsed_json:
                    parsed_json["original_query"] = user_query
                
                # 구조화된 검증 수행
                if self.prompt_manager:
                    validation_errors = self.prompt_manager.validate_output_schema(parsed_json)
                    if validation_errors:
                        print(f"⚠️  스키마 검증 경고: {', '.join(validation_errors)}")
                
                return parsed_json
            else:
                # JSON 파싱 실패 시 기본 구조 반환
                return self._create_fallback_instruction(user_query, "JSON 파싱 실패")
                
        except json.JSONDecodeError as e:
            return self._create_fallback_instruction(user_query, f"JSON 디코딩 오류: {str(e)}")
        except Exception as e:
            return self._create_fallback_instruction(user_query, f"명령어 변환 중 오류: {str(e)}")
    
    def _create_fallback_instruction(self, user_query: str, error_msg: str) -> Dict[str, Any]:
        """
        오류 발생 시 기본 명령어 구조 생성
        
        Args:
            user_query: 원본 쿼리
            error_msg: 오류 메시지
            
        Returns:
            기본 명령어 구조
        """
        return {
            "instruction_id": f"fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}",
            "original_query": user_query,
            "intent_type": "INFORMATION",
            "priority": "MEDIUM",
            "target": {},
            "tasks": [
                {
                    "task_id": "fallback_task",
                    "agent": "ORCHESTRATION",
                    "action": "manual_review_required",
                    "parameters": {
                        "error": error_msg,
                        "query": user_query
                    },
                    "dependencies": [],
                    "expected_output": "manual_instruction"
                }
            ],
            "context_requirements": {
                "historical_data": False,
                "real_time_data": False,
                "external_knowledge": False,
                "simulation_needed": False
            },
            "constraints": {
                "safety_requirements": ["manual_review_required"],
                "regulatory_compliance": []
            },
            "error": error_msg
        }
    
    def batch_refine(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        여러 쿼리를 배치로 처리
        
        Args:
            queries: 처리할 쿼리 목록
            
        Returns:
            변환된 명령어 목록
        """
        results = []
        for query in queries:
            try:
                result = self.refine_instruction(query)
                results.append(result)
            except Exception as e:
                results.append({
                    "error": str(e),
                    "original_query": query,
                    "instruction_id": str(uuid.uuid4())
                })
        return results
    
    def test_api_connection(self) -> Dict[str, Any]:
        """
        API 연결 및 응답 테스트
        
        Returns:
            테스트 결과
        """
        test_query = "API 연결 테스트입니다."
        
        try:
            start_time = datetime.now()
            
            # 간단한 테스트 프롬프트로 API 호출
            test_prompt = f"다음 메시지에 'API 연결 성공'이라고 응답해주세요: {test_query}"
            response = self._call_llm_api(test_prompt, use_agent=False)
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            return {
                "status": "success",
                "response_time_seconds": response_time,
                "test_query": test_query,
                "llm_response": response[:200] + "..." if len(response) > 200 else response,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "test_query": test_query,
                "timestamp": datetime.now().isoformat()
            }
    
    def setup_agent(self) -> Dict[str, Any]:
        """
        InstructionRF 에이전트 설정 (등록 + 테스트)
        
        Returns:
            설정 결과
        """
        try:
            # 1. 에이전트 등록
            register_result = self.register_agent()
            
            # 2. 에이전트를 통한 테스트 호출
            test_prompt = """다음 쿼리를 JSON 명령어로 변환해주세요:
테스트용 간단한 장비 상태 확인

반드시 유효한 JSON 형식으로만 응답하세요."""
            
            try:
                response = self._call_llm_api(test_prompt, use_agent=True, agent_name="instruction_rf")
                return {
                    "status": "success",
                    "agent_registration": register_result,
                    "agent_test": "success",
                    "test_response": response[:200] + "..." if len(response) > 200 else response
                }
            except Exception as e:
                return {
                    "status": "partial_success",
                    "agent_registration": register_result,
                    "agent_test": "failed",
                    "agent_test_error": str(e)
                }
                
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def validate_instruction(self, instruction: Dict[str, Any]) -> bool:
        """
        생성된 명령어의 유효성 검증
        
        Args:
            instruction: 검증할 명령어
            
        Returns:
            유효성 여부
        """
        required_fields = [
            "instruction_id", "original_query", "intent_type", 
            "priority", "tasks", "context_requirements"
        ]
        
        for field in required_fields:
            if field not in instruction:
                return False
        
        # intent_type 검증
        valid_intents = ["ANOMALY_CHECK", "PREDICTION", "CONTROL", "INFORMATION", "OPTIMIZATION"]
        if instruction["intent_type"] not in valid_intents:
            return False
        
        # priority 검증
        valid_priorities = ["HIGH", "MEDIUM", "LOW"]
        if instruction["priority"] not in valid_priorities:
            return False
        
        # tasks 검증
        if not isinstance(instruction["tasks"], list) or len(instruction["tasks"]) == 0:
            return False
        
        for task in instruction["tasks"]:
            required_task_fields = ["task_id", "agent", "action", "parameters", "dependencies", "expected_output"]
            for field in required_task_fields:
                if field not in task:
                    return False
        
        return True


# 사용 예제 클래스
class InstructionRFExample:
    """InstructionRF 사용 예제"""
    
    @staticmethod
    def example_usage():
        """기본 사용 예제 - 연구실 서버 연동 버전"""
        print("=== InstructionRF 연구실 서버 연동 사용 예제 ===")
        
        # 클라이언트 초기화
        print("\n1. 클라이언트 초기화:")
        print("client = InstructionRefinementClient()")
        print("# 기본 서버: http://localhost/api/agents")
        
        # API 연결 테스트
        print("\n2. API 연결 테스트:")
        print("test_result = client.test_api_connection()")
        print("print(test_result)")
        
        # 예제 쿼리들
        example_queries = [
            "3번 엣칭 장비 압력이 좀 이상한데, 확인해 줄 수 있나요?",
            "생산 수율을 개선하고 싶은데 어떤 파라미터를 조정해야 할까?",
            "CVD 장비의 온도 센서가 고장난 것 같아요",
            "전체 생산라인의 에너지 효율성을 분석해주세요"
        ]
        
        print("\n3. 단일 쿼리 처리 예제:")
        print(f"입력: {example_queries[0]}")
        print("instruction = client.refine_instruction(query)")
        print("print(json.dumps(instruction, indent=2, ensure_ascii=False))")
        
        print("\n4. 배치 처리 예제:")
        for i, query in enumerate(example_queries, 1):
            print(f"쿼리 {i}: {query}")
        print("instructions = client.batch_refine(example_queries)")
        print("for inst in instructions:")
        print("    print(f\"ID: {inst['instruction_id']}, Type: {inst['intent_type']}\")")
        
        print("\n5. 실제 사용 코드:")
        print("""
try:
    client = InstructionRefinementClient()
    
    # API 연결 테스트
    test_result = client.test_api_connection()
    if test_result['status'] == 'success':
        print(f"API 연결 성공 (응답시간: {test_result['response_time_seconds']:.2f}초)")
        
        # 쿼리 변환
        query = "3번 엣칭 장비 상태 확인해주세요"
        instruction = client.refine_instruction(query)
        
        if 'error' not in instruction:
            print("명령어 변환 성공!")
            print(f"Intent: {instruction['intent_type']}")
            print(f"Priority: {instruction['priority']}")
        else:
            print(f"변환 실패: {instruction['error']}")
    else:
        print(f"API 연결 실패: {test_result['error']}")
        
except Exception as e:
    print(f"오류 발생: {e}")
""")
    
    @staticmethod
    def example_json_output():
        """예상 JSON 출력 예제"""
        example_output = {
            "instruction_id": "inst_20240814_001",
            "original_query": "3번 엣칭 장비 압력이 좀 이상한데, 확인해 줄 수 있나요?",
            "intent_type": "ANOMALY_CHECK",
            "priority": "HIGH",
            "target": {
                "equipment_id": "Etching_Machine_#3",
                "parameter": "Pressure",
                "process": "Etching"
            },
            "tasks": [
                {
                    "task_id": "task_001",
                    "agent": "MONITORING",
                    "action": "analyze_parameter_status",
                    "parameters": {
                        "equipment": "Etching_Machine_#3",
                        "parameter": "Pressure",
                        "time_window": "last_30_minutes",
                        "compare_with_baseline": True
                    },
                    "dependencies": [],
                    "expected_output": "anomaly_detection_report"
                }
            ],
            "context_requirements": {
                "historical_data": True,
                "real_time_data": True,
                "external_knowledge": False,
                "simulation_needed": True
            },
            "constraints": {
                "time_limit": "5_minutes",
                "safety_requirements": ["maintain_chamber_pressure_limits"],
                "regulatory_compliance": ["semiconductor_manufacturing_standards"]
            }
        }
        
        print("=== 예상 JSON 출력 예제 ===")
        print(json.dumps(example_output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    # 사용 예제 실행
    InstructionRFExample.example_usage()
    print("\n" + "="*50 + "\n")
    InstructionRFExample.example_json_output()