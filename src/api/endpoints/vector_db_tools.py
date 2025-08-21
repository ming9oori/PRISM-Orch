from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

from ...core.config import settings
from .vector_db import _research_api, _memory_api
from core.vector_db.schemas import SearchQuery, SearchResult

router = APIRouter()

class ToolSearchRequest(BaseModel):
    class_name: str = Field(...)
    query: str = Field(...)
    limit: int = Field(10, ge=1, le=100)
    threshold: float = Field(0.7, ge=0.0, le=1.0)
    filters: Dict[str, Any] = Field(default_factory=dict)
    include_metadata: bool = Field(True)
    include_vector: bool = Field(False)
    client_id: str = Field("default")
    encoder_model: Optional[str] = Field(None)

@router.post("/research/search", response_model=List[SearchResult])
async def research_search(req: ToolSearchRequest) -> List[SearchResult]:
    client = _research_api.get_client(req.client_id)
    if not client.is_connected():
        client.connect()
    if req.encoder_model:
        encoder = _research_api.get_encoder(req.encoder_model)
        client.encoder = encoder
    q = SearchQuery(
        query=req.query,
        limit=req.limit,
        threshold=req.threshold,
        filters=req.filters,
        include_metadata=req.include_metadata,
        include_vector=req.include_vector,
    )
    return client.search(req.class_name, q)

@router.post("/memory/search", response_model=List[SearchResult])
async def memory_search(req: ToolSearchRequest) -> List[SearchResult]:
    client = _memory_api.get_client(req.client_id)
    if not client.is_connected():
        client.connect()
    if req.encoder_model:
        encoder = _memory_api.get_encoder(req.encoder_model)
        client.encoder = encoder
    q = SearchQuery(
        query=req.query,
        limit=req.limit,
        threshold=req.threshold,
        filters=req.filters,
        include_metadata=req.include_metadata,
        include_vector=req.include_vector,
    )
    return client.search(req.class_name, q) 