from typing import List, Dict, Any, Optional
from openai import OpenAI

from core.llm.base import BaseLLMService
from core.llm.schemas import LLMGenerationRequest
from ..core.config import settings


class OpenAIChatLLMService(BaseLLMService):
    """
    Adapter implementing prism-core BaseLLMService using OpenAI-compatible chat API.
    Works with OpenAI or vLLM OpenAI-compatible endpoint.
    """

    def __init__(self, *, base_url: Optional[str] = None, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        self.base_url = base_url or None  # Use default if None
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or "gpt-4o-mini"
        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

    def generate(self, request: LLMGenerationRequest) -> str:
        messages: List[Dict[str, Any]] = [
            {"role": "user", "content": request.prompt}
        ]
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stop=request.stop,
        )
        return resp.choices[0].message.content or "" 