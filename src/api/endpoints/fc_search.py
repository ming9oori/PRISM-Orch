from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from ...modules.fc_search import FunctionCallingSearch

router = APIRouter()

class FCSearchRequest(BaseModel):
    prompt: str = Field(...)
    base_url: str = Field("http://localhost:8000")
    model_name: str = Field("gpt-4o-mini")
    openai_base_url: Optional[str] = Field(None)
    api_key: Optional[str] = Field(None)

class FCSearchResponse(BaseModel):
    text: str

@router.post("/fc/search", response_model=FCSearchResponse)
async def fc_search(req: FCSearchRequest) -> FCSearchResponse:
    fc = FunctionCallingSearch(
        base_url=req.base_url,
        model_name=req.model_name,
        openai_base_url=req.openai_base_url,
        api_key=req.api_key,
    )
    text = fc.run(req.prompt)
    return FCSearchResponse(text=text) 