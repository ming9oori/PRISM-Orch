from typing import Dict, Any, List
from pydantic import BaseModel

from core.llm.tools import Tool, HttpEndpoint, ToolRegistry as HttpToolRegistry
from core.llm.tool_orchestrator import ToolOrchestrator
from .openai_llm_service import OpenAIChatLLMService


class FunctionCallingSearch(BaseModel):
    base_url: str = "http://localhost:8000"
    client_id: str = "orch"
    model_name: str = "gpt-4o-mini"  # or vLLM served model id
    openai_base_url: str | None = None  # if using vLLM openai-compatible server
    api_key: str | None = None

    def _build_tools(self) -> List[Tool]:
        common_schema = {
            "type": "object",
            "properties": {
                "class_name": {"type": "string"},
                "query": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                "threshold": {"type": "number", "minimum": 0, "maximum": 1},
                "filters": {"type": "object"},
                "include_metadata": {"type": "boolean"},
                "include_vector": {"type": "boolean"},
                "client_id": {"type": "string"},
                "encoder_model": {"type": ["string", "null"]},
            },
            "required": ["class_name", "query"]
        }
        return [
            Tool(
                name="research_search",
                description="Searches the research vector DB for relevant external knowledge.",
                input_schema=common_schema,
                endpoint=HttpEndpoint(
                    url=f"{self.base_url}/api/v1/tools/research/search",
                    method="POST",
                ),
            ),
            Tool(
                name="memory_search",
                description="Searches the agent memory vector DB for past interactions.",
                input_schema=common_schema,
                endpoint=HttpEndpoint(
                    url=f"{self.base_url}/api/v1/tools/memory/search",
                    method="POST",
                ),
            ),
        ]

    def run(self, prompt: str) -> str:
        # Prepare LLM and tool orchestrator
        llm = OpenAIChatLLMService(base_url=self.openai_base_url, api_key=self.api_key, model=self.model_name)
        tools_registry = HttpToolRegistry()
        tools = self._build_tools()
        for tool in tools:
            tools_registry.register_tool(self.client_id, tool)

        orchestrator = ToolOrchestrator(llm_service=llm, tool_registry=tools_registry)
        text = orchestrator.generate_with_tools(
            base_prompt=prompt,
            client_id=self.client_id,
            tools=tools,
            max_tool_calls=3,
            max_tokens=512,
            temperature=0.3,
            stop=None,
        )
        return text 