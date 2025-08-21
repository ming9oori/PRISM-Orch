from fastapi import APIRouter
from ...core.config import settings

# Import VectorDBAPI from prism-core
from core.vector_db.api import VectorDBAPI

# Research Vector DB
_research_api = VectorDBAPI(
    weaviate_url=settings.RESEARCH_WEAVIATE_URL,
    api_key=settings.RESEARCH_WEAVIATE_API_KEY or None,
)
research_router: APIRouter = _research_api.create_router()

# Memory Vector DB
_memory_api = VectorDBAPI(
    weaviate_url=settings.MEMORY_WEAVIATE_URL,
    api_key=settings.MEMORY_WEAVIATE_API_KEY or None,
)
memory_router: APIRouter = _memory_api.create_router() 