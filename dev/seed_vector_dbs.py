import requests
from typing import List, Dict, Any
import os

BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")

RESEARCH_CLASS = "ResearchDocs"
MEMORY_CLASS = "AgentMemory"


def create_index(base_url: str, class_name: str, description: str, vector_dim: int, encoder_model: str) -> None:
    url = f"{base_url}/api/v1/research/vector-db/indices"
    if class_name == MEMORY_CLASS:
        url = f"{base_url}/api/v1/memory/vector-db/indices"
    payload = {
        "class_name": class_name,
        "description": description,
        "vector_dimension": vector_dim,
        "encoder_model": encoder_model,
        "properties": [
            {"name": "content", "dataType": ["text"], "description": "Document content"},
            {"name": "title", "dataType": ["string"], "description": "Title"},
            {"name": "source", "dataType": ["string"], "description": "Source"},
            {"name": "created_at", "dataType": ["date"], "description": "Creation time"}
        ],
        "vectorizer": "none",
        "distance_metric": "cosine"
    }
    r = requests.post(url, json=payload, timeout=30)
    r.raise_for_status()
    print(f"create_index {class_name}: {r.json()}")


def add_documents(base_url: str, class_name: str, docs: List[Dict[str, Any]]) -> None:
    url = f"{base_url}/api/v1/research/vector-db/documents/{class_name}/batch"
    if class_name == MEMORY_CLASS:
        url = f"{base_url}/api/v1/memory/vector-db/documents/{class_name}/batch"
    r = requests.post(url, json=docs, timeout=60)
    r.raise_for_status()
    print(f"add_documents {class_name}: {r.json()}")


def seed() -> None:
    # 1) Create indices (assume 384-dim sentence-transformers)
    create_index(BASE_URL, RESEARCH_CLASS, "External research knowledge", 384, "sentence-transformers/all-MiniLM-L6-v2")
    create_index(BASE_URL, MEMORY_CLASS, "Agent interaction memory", 384, "sentence-transformers/all-MiniLM-L6-v2")

    # 2) Insert research docs
    research_docs = [
        {
            "content": "CMP process instability root causes include pad wear, slurry flow anomalies, and temperature drift.",
            "title": "CMP Root Causes",
            "metadata": {"tags": ["cmp", "rca", "process"]},
            "source": "internal_wiki",
        },
        {
            "content": "Pressure control loop tuning improves stability; recommended PID values: P=0.8, I=0.1, D=0.05 for line A-1.",
            "title": "Pressure Loop Tuning",
            "metadata": {"line": "A-1"},
            "source": "eng_notes",
        },
        {
            "content": "Valve B-3 degradation observed after 2k cycles; monitor for leakage and hysteresis.",
            "title": "Valve B-3 Degradation",
            "metadata": {"component": "B-3", "action": "monitor"},
            "source": "maintenance_db",
        },
    ]
    add_documents(BASE_URL, RESEARCH_CLASS, research_docs)

    # 3) Insert memory docs
    memory_docs = [
        {
            "content": "2024-08-10: Investigated A-1 pressure spike. Likely caused by B-3 valve sticking.",
            "title": "Session note A-1 spike",
            "metadata": {"session": "user123_session456"},
            "source": "agent_memory",
        },
        {
            "content": "2024-08-12: After tuning, pressure variance reduced by 15% on A-1.",
            "title": "Follow-up tuning result",
            "metadata": {"line": "A-1"},
            "source": "agent_memory",
        },
    ]
    add_documents(BASE_URL, MEMORY_CLASS, memory_docs)


if __name__ == "__main__":
    seed() 