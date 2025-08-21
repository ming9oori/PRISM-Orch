from typing import Dict, Any, List
from pydantic import BaseModel

from core.llm.tools import Tool, HttpEndpoint, ToolRegistry as HttpToolRegistry
from core.llm.openai_compat_service import OpenAICompatService


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
        # Register tools
        registry = HttpToolRegistry()
        for tool in self._build_tools():
            registry.register_tool(self.client_id, tool)

        # Build OpenAI tool specs
        tools_for_openai: List[Dict[str, Any]] = []
        for t in registry.list_tools(self.client_id):
            tools_for_openai.append({
                "name": t.name,
                "description": t.description,
                "parameters": t.input_schema,
            })

        # OpenAI-compatible chat loop with tool execution
        oa = OpenAICompatService(base_url=self.openai_base_url, api_key=self.api_key, model_name=self.model_name)
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": "You are a helpful manufacturing assistant. Use tools when helpful."},
            {"role": "user", "content": prompt},
        ]

        while True:
            text = oa.chat_complete_with_tools(
                messages=messages,
                tools=tools_for_openai,
                temperature=0.3,
                max_tokens=512,
                tool_choice="auto",
            )

            if text != "__TOOL_CALLS__":
                return text

            # The last assistant message contains tool_calls; extract and execute
            last = messages[-1]
            # We need to call OpenAI API again to get actual tool_calls structure; to avoid modifying the
            # prism-core service, fetch tool_calls from last assistant step via a direct minimal call.
            # As a workaround, simply break to return current content if tool_calls aren't accessible.
            # In production, extend OpenAICompatService to return both text and tool_calls.
            return text 