import os
import time
import subprocess
import requests

BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8100")


def up_weaviate():
    print("[e2e] Starting Weaviate via docker-compose (if not up)...")
    subprocess.run(["bash", "-lc", "cd db && docker compose up -d weaviate"], check=False)


def wait_for(url: str, timeout_s: int = 60):
    print(f"[e2e] Waiting for {url} ...")
    start = time.time()
    while time.time() - start < timeout_s:
        try:
            r = requests.get(url, timeout=3)
            if r.status_code < 500:
                return True
        except Exception:
            pass
        time.sleep(2)
    raise RuntimeError(f"Timeout waiting for {url}")


def seed():
    print("[e2e] Seeding vector DBs...")
    subprocess.run(["bash", "-lc", "python dev/seed_vector_dbs.py"], check=True)


def run_orchestration(prompt: str):
    print("[e2e] Running orchestration invoke...")
    payload = {
        "query": prompt,
        "session_id": "e2e_session",
        "user_id": "e2e_user",
    }
    r = requests.post(f"{BASE_URL}/api/v1/orchestrate/", json=payload, timeout=180)
    r.raise_for_status()
    data = r.json()
    print("[e2e] Orchestration final_answer:\n", data.get("final_answer", "<no text>"))


def main():
    up_weaviate()
    wait_for("http://localhost:18080/v1/.well-known/ready")
    wait_for(f"{BASE_URL}/")
    seed()
    run_orchestration("A-1 라인 압력 불안정 원인을 자료와 과거 기록에서 찾아 요약해줘")


if __name__ == "__main__":
    main() 