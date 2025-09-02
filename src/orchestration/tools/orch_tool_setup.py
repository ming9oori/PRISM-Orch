"""
PRISM-Orch Tool Setup

PRISM-Core의 도구들을 사용하여 Orch 전용 도구들을 설정합니다.
"""

from typing import Optional
from prism_core.core.tools import (
    create_rag_search_tool,
    create_compliance_tool,
    create_memory_search_tool,
    ToolRegistry
)
from ...core.config import settings
from .agent_interaction_summary_tool import AgentInteractionSummaryTool


class OrchToolSetup:
    """
    PRISM-Orch 전용 도구 설정 클래스
    
    PRISM-Core의 도구들을 Orch 환경에 맞게 설정하여 제공합니다.
    """
    
    def __init__(self):
        # Orch 전용 설정
        self.weaviate_url = settings.WEAVIATE_URL
        self.openai_base_url = settings.OPENAI_BASE_URL
        self.openai_api_key = settings.OPENAI_API_KEY
        self.encoder_model = settings.VECTOR_ENCODER_MODEL
        self.vector_dim = settings.VECTOR_DIM
        self.client_id = "orch"
        self.class_prefix = "Orch"
        
        # 도구 레지스트리
        self.tool_registry = ToolRegistry()
        
        # 도구들
        self.rag_tool = None
        self.compliance_tool = None
        self.memory_tool = None
        self.interaction_summary_tool = None
        
    def setup_tools(self) -> ToolRegistry:
        """Orch 전용 도구들을 설정하고 등록합니다."""
        import sys
        try:
            # RAG Search Tool 설정
            print("🔧 [TOOL] Creating RAG search tool...", file=sys.stderr, flush=True)
            self.rag_tool = create_rag_search_tool(
                weaviate_url=self.weaviate_url,
                encoder_model=self.encoder_model,
                vector_dim=self.vector_dim,
                client_id=self.client_id,
                class_prefix=self.class_prefix
            )
            print("🔧 [TOOL] RAG search tool created, registering...", file=sys.stderr, flush=True)
            self.tool_registry.register_tool(self.rag_tool)
            print(f"✅ Orch RAG Search Tool 등록 완료 (클래스: {self.class_prefix}Research)", file=sys.stderr, flush=True)
            
            # Compliance Tool 설정
            print("🔧 [TOOL] Creating compliance tool...", file=sys.stderr, flush=True)
            self.compliance_tool = create_compliance_tool(
                weaviate_url=self.weaviate_url,
                openai_base_url=self.openai_base_url,
                openai_api_key=self.openai_api_key,
                model_name=settings.VLLM_MODEL,
                client_id=self.client_id,
                class_prefix=self.class_prefix
            )
            print("🔧 [TOOL] Compliance tool created, registering...", file=sys.stderr, flush=True)
            self.tool_registry.register_tool(self.compliance_tool)
            print(f"✅ Orch Compliance Tool 등록 완료 (클래스: {self.class_prefix}Compliance)", file=sys.stderr, flush=True)
            
            # Memory Search Tool 설정
            self.memory_tool = create_memory_search_tool(
                weaviate_url=self.weaviate_url,
                openai_base_url=self.openai_base_url,
                openai_api_key=self.openai_api_key,
                model_name=settings.VLLM_MODEL,
                embedder_model_name=settings.VECTOR_ENCODER_MODEL,
                client_id=self.client_id,
                class_prefix=self.class_prefix
            )
            self.tool_registry.register_tool(self.memory_tool)
            print(f"✅ Orch Memory Search Tool 등록 완료 (클래스: {self.class_prefix}History)")
            
            # Agent Interaction Summary Tool 설정
            self.interaction_summary_tool = AgentInteractionSummaryTool(
                weaviate_url=self.weaviate_url,
                openai_base_url=self.openai_base_url,
                openai_api_key=self.openai_api_key,
                model_name=settings.VLLM_MODEL,
                client_id=self.client_id,
                class_prefix=self.class_prefix
            )
            self.tool_registry.register_tool(self.interaction_summary_tool)
            print(f"✅ Orch Agent Interaction Summary Tool 등록 완료")
            
            return self.tool_registry
            
        except Exception as e:
            print(f"❌ Orch 도구 설정 실패: {str(e)}")
            raise
    
    def get_tool_registry(self) -> ToolRegistry:
        """설정된 도구 레지스트리를 반환합니다."""
        return self.tool_registry
    
    def get_rag_tool(self):
        """RAG Search Tool을 반환합니다."""
        return self.rag_tool
    
    def get_compliance_tool(self):
        """Compliance Tool을 반환합니다."""
        return self.compliance_tool
    
    def get_memory_tool(self):
        """Memory Search Tool을 반환합니다."""
        return self.memory_tool
    
    def get_interaction_summary_tool(self):
        """Agent Interaction Summary Tool을 반환합니다."""
        return self.interaction_summary_tool
    
    def print_tool_info(self):
        """등록된 도구들의 정보를 출력합니다."""
        print("\n" + "="*60)
        print("🔧 PRISM-Orch 도구 설정 정보")
        print("="*60)
        print(f"Weaviate URL: {self.weaviate_url}")
        print(f"OpenAI Base URL: {self.openai_base_url}")
        print(f"Encoder Model: {self.encoder_model}")
        print(f"Vector Dimension: {self.vector_dim}")
        print(f"Client ID: {self.client_id}")
        print(f"Class Prefix: {self.class_prefix}")
        print("\n등록된 도구들:")
        for tool_name, tool in self.tool_registry._tools.items():
            print(f"  - {tool_name}: {tool.__class__.__name__}")
        print("="*60) 