import requests
from typing import List, Dict, Any
import os
import time

CORE_BASE_URL = os.getenv("PRISM_CORE_BASE_URL", "http://localhost:8000")

RESEARCH_CLASS = "OrchResearch"
HISTORY_CLASS = "OrchHistory"
COMPLIANCE_CLASS = "OrchCompliance"


def wait_for(url: str, timeout_s: int = 90) -> None:
    start = time.time()
    while time.time() - start < timeout_s:
        try:
            r = requests.get(url, timeout=3)
            if r.status_code < 500:
                return
        except Exception:
            pass
        time.sleep(2)
    raise RuntimeError(f"Timeout waiting for {url}")


def create_index(class_name: str, description: str) -> None:
    url = f"{CORE_BASE_URL}/api/vector-db/indices"
    payload = {
        "class_name": class_name,
        "description": description,
        "properties": {"text": {"type": "text"}},
        "encoder_model": None,
    }
    r = requests.post(url, json=payload, params={"client_id": "orch", "encoder_model": None}, timeout=30)
    r.raise_for_status()
    print(f"create_index {class_name}: {r.status_code}")


def add_documents(class_name: str, docs: List[Dict[str, Any]]) -> None:
    url = f"{CORE_BASE_URL}/api/vector-db/documents/{class_name}/batch"
    r = requests.post(url, json=docs, params={"client_id": "orch", "encoder_model": None}, timeout=60)
    r.raise_for_status()
    print(f"add_documents {class_name}: {len(docs)} docs -> {r.status_code}")


def seed() -> None:
    # Wait for core API
    wait_for(f"{CORE_BASE_URL}/")

    # 1) Create indices
    create_index(RESEARCH_CLASS, "Papers/technical docs knowledge base")
    create_index(HISTORY_CLASS, "All users' past execution logs")
    create_index(COMPLIANCE_CLASS, "Safety/legal/company compliance rules")

    # 2) Insert research docs
    research_docs = [
        {"title": f"Paper {i+1}", "text": f"제조 공정 최적화 기술 문서 {i+1}: 공정 제어, 안전 규정, 예지 정비, 데이터 기반 분석."}
        for i in range(10)
    ]
    add_documents(RESEARCH_CLASS, research_docs)

    # 3) Insert history docs
    history_docs = [
        {"title": f"History {i+1}", "text": f"사용자 수행 내역 {i+1}: 압력 이상 대응, 점검 절차 수행, 원인 분석 리포트, 후속 조치 완료."}
        for i in range(10)
    ]
    add_documents(HISTORY_CLASS, history_docs)

    # 4) Insert compliance docs
    compliance_docs = [
        {"title": f"Rule {i+1}", "text": f"안전 법규 및 사내 규정 {i+1}: 잠금/표시 절차(LOTO), 보호구 착용, 위험물 취급, 점검 기록 보관, 승인 절차 준수."}
        for i in range(10)
    ]
    add_documents(COMPLIANCE_CLASS, compliance_docs)


if __name__ == "__main__":
    seed() 