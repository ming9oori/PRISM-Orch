"""
Compliance Tool

안전 규정 및 법규 준수 여부를 검증하는 Tool입니다.
LLM을 통한 지능형 규정 준수 분석을 제공합니다.
"""

import requests
import json
from typing import Dict, Any, List
from core.tools import BaseTool, ToolRequest, ToolResponse
from ...core.config import settings

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  OpenAI 라이브러리가 설치되지 않았습니다. 기본 키워드 분석만 사용 가능합니다.")


class ComplianceTool(BaseTool):
    """
    안전 규정 및 법규 준수 여부를 검증하는 Tool
    
    기능:
    - 제안된 조치의 안전 규정 준수 여부 검증
    - 관련 법규 및 사내 규정 매칭
    - LLM을 통한 지능형 준수 여부 판단
    - 준수 여부에 따른 권장사항 제공
    """
    
    def __init__(self):
        super().__init__(
            name="compliance_check",
            description="제안된 조치가 안전 규정 및 사내 규정을 준수하는지 검증합니다",
            parameters_schema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "검증할 조치 내용"},
                    "context": {"type": "string", "description": "조치의 맥락 정보"},
                    "user_id": {"type": "string", "description": "사용자 ID (선택사항)"}
                },
                "required": ["action"]
            }
        )
        self._base = settings.PRISM_CORE_BASE_URL
        self._client_id = "orch"
        
        # OpenAI 클라이언트 초기화
        self._openai_client = None
        if OPENAI_AVAILABLE:
            self._initialize_openai()

    def _initialize_openai(self) -> None:
        """OpenAI 클라이언트 초기화"""
        try:
            self._openai_client = OpenAI(
                base_url=settings.OPENAI_BASE_URL or "http://localhost:8001/v1",
                api_key=settings.OPENAI_API_KEY
            )
            print("✅ OpenAI 클라이언트 초기화 완료")
        except Exception as e:
            print(f"⚠️  OpenAI 클라이언트 초기화 실패: {str(e)}")
            self._openai_client = None

    async def execute(self, request: ToolRequest) -> ToolResponse:
        """Tool 실행"""
        try:
            params = request.parameters
            action = params["action"]
            context = params.get("context", "")
            user_id = params.get("user_id", "")
            
            # 1. 관련 규정 검색
            compliance_docs = await self._search_compliance_rules(action, context)
            
            # 2. LLM을 통한 준수 여부 분석
            compliance_analysis = await self._analyze_compliance_with_llm(action, context, compliance_docs)
            
            # 3. 결과 반환
            return ToolResponse(
                success=True,
                result={
                    "action": action,
                    "compliance_checked": True,
                    "compliance_status": compliance_analysis["status"],
                    "related_rules": compliance_analysis["related_rules"],
                    "recommendations": compliance_analysis["recommendations"],
                    "risk_level": compliance_analysis["risk_level"],
                    "reasoning": compliance_analysis["reasoning"],
                    "domain": "compliance"
                }
            )
                
        except Exception as e:
            return ToolResponse(
                success=False,
                error_message=f"규정 준수 검증 중 오류: {str(e)}"
            )

    async def _search_compliance_rules(self, action: str, context: str) -> List[str]:
        """관련 규정 검색"""
        try:
            # PRISM-Core Vector DB에서 규정 검색
            response = requests.post(
                f"{self._base}/api/vector-db/search/OrchCompliance",
                json={
                    "query": f"{action} {context}",
                    "limit": 5
                },
                params={"client_id": self._client_id},
                timeout=10,
            )
            
            if response.status_code == 200:
                results = response.json()
                return [result.get("content", "") for result in results]
            else:
                return []
                
        except Exception as e:
            print(f"⚠️  규정 검색 실패: {str(e)}")
            return []

    async def _analyze_compliance_with_llm(self, action: str, context: str, compliance_docs: List[str]) -> Dict[str, Any]:
        """LLM을 사용한 규정 준수 분석"""
        try:
            if not self._openai_client:
                # Fallback: 키워드 기반 분석
                return self._analyze_compliance_fallback(action, compliance_docs)
            
            # LLM 프롬프트 구성
            system_prompt = """당신은 제조업 안전 규정 및 법규 준수 전문가입니다.

주어진 조치와 관련 규정을 분석하여 다음을 판단하세요:

1. **준수 상태**: compliant (준수), conditional (조건부 준수), requires_review (검토 필요), non_compliant (미준수)
2. **위험 수준**: low (낮음), medium (보통), high (높음)
3. **권장사항**: 구체적인 안전 조치 및 절차
4. **근거**: 판단 근거 및 관련 규정

JSON 형식으로 응답하세요:
{
    "status": "compliant",
    "risk_level": "low",
    "recommendations": ["권장사항1", "권장사항2"],
    "reasoning": "판단 근거 설명"
}"""

            user_prompt = f"""조치: {action}
맥락: {context}

관련 규정:
{chr(10).join(f"- {doc}" for doc in compliance_docs) if compliance_docs else "- 관련 규정 없음"}

위 조치의 규정 준수 여부를 분석해주세요."""

            # LLM 호출
            response = self._openai_client.chat.completions.create(
                model="gpt-4o-mini",  # 또는 설정된 모델
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            # 응답 파싱
            llm_response = response.choices[0].message.content.strip()
            
            try:
                # JSON 응답 파싱 시도
                analysis_result = json.loads(llm_response)
                
                return {
                    "status": analysis_result.get("status", "requires_review"),
                    "related_rules": compliance_docs,
                    "recommendations": analysis_result.get("recommendations", []),
                    "risk_level": analysis_result.get("risk_level", "medium"),
                    "reasoning": analysis_result.get("reasoning", "LLM 분석 완료")
                }
                
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 텍스트에서 정보 추출
                return self._extract_info_from_text(llm_response, compliance_docs)
                
        except Exception as e:
            print(f"⚠️  LLM 분석 실패: {str(e)}")
            # Fallback: 키워드 기반 분석
            return self._analyze_compliance_fallback(action, compliance_docs)

    def _extract_info_from_text(self, text: str, compliance_docs: List[str]) -> Dict[str, Any]:
        """텍스트 응답에서 정보 추출"""
        text_lower = text.lower()
        
        # 상태 추출
        status = "requires_review"
        if "준수" in text or "compliant" in text_lower:
            status = "compliant"
        elif "조건부" in text or "conditional" in text_lower:
            status = "conditional"
        elif "미준수" in text or "non_compliant" in text_lower:
            status = "non_compliant"
        
        # 위험 수준 추출
        risk_level = "medium"
        if "높음" in text or "high" in text_lower:
            risk_level = "high"
        elif "낮음" in text or "low" in text_lower:
            risk_level = "low"
        
        # 권장사항 추출 (간단한 추출)
        recommendations = []
        if "안전" in text:
            recommendations.append("안전 절차 준수")
        if "보호구" in text:
            recommendations.append("보호구 착용")
        if "승인" in text:
            recommendations.append("관리자 승인 필요")
        
        if not recommendations:
            recommendations = ["규정 준수 확인 필요"]
        
        return {
            "status": status,
            "related_rules": compliance_docs,
            "recommendations": recommendations,
            "risk_level": risk_level,
            "reasoning": text[:200] + "..." if len(text) > 200 else text
        }

    def _analyze_compliance_fallback(self, action: str, compliance_docs: List[str]) -> Dict[str, Any]:
        """키워드 기반 분석 (Fallback)"""
        action_lower = action.lower()
        
        # 위험 키워드 체크
        risk_keywords = ["위험", "폭발", "화재", "독성", "고압", "고온", "방사선"]
        high_risk_keywords = ["폭발", "화재", "독성", "방사선"]
        
        risk_level = "low"
        if any(keyword in action_lower for keyword in high_risk_keywords):
            risk_level = "high"
        elif any(keyword in action_lower for keyword in risk_keywords):
            risk_level = "medium"
        
        # 규정 준수 여부 판단
        compliance_status = "compliant"
        if risk_level == "high":
            compliance_status = "requires_review"
        elif risk_level == "medium":
            compliance_status = "conditional"
        
        # 권장사항 생성
        recommendations = []
        if risk_level == "high":
            recommendations.append("안전 관리자 승인 필요")
            recommendations.append("보호구 착용 필수")
            recommendations.append("작업 전 안전 점검 수행")
        elif risk_level == "medium":
            recommendations.append("안전 절차 준수")
            recommendations.append("작업 전 점검 권장")
        
        return {
            "status": compliance_status,
            "related_rules": compliance_docs,
            "recommendations": recommendations,
            "risk_level": risk_level,
            "reasoning": "키워드 기반 분석 (LLM 사용 불가)"
        } 