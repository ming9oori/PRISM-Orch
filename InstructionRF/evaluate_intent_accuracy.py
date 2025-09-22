import json
import argparse
import time
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from instruction_rf_client import InstructionRefinementClient

VALID_INTENTS = ["ANOMALY_CHECK","PREDICTION","CONTROL","INFORMATION","OPTIMIZATION"]

DEFAULT_CSV = "/home/minjoo/Github/PRISM-Orch/InstructionRF/data/Semiconductor_intent_dataset__preview_.csv"
DEFAULT_BASE_URL = "http://127.0.0.1:8000/v1"
DEFAULT_MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct"  # 기본값(옵션으로 변경 가능) # 예: unsloth/Qwen3-4B-Instruct-2507-bnb-4bit

def safe_intent(x):
    return x if isinstance(x, str) and x in VALID_INTENTS else None

def main():
    ap = argparse.ArgumentParser(description="Evaluate intent classification accuracy using vLLM backend")
    ap.add_argument("--base_url", default=DEFAULT_BASE_URL, help="Base URL of vLLM OpenAI-compatible server (must end with /v1)")
    ap.add_argument("--csv", default=DEFAULT_CSV, help="Path to CSV dataset (id,intent,query)")
    ap.add_argument("--timeout", type=int, default=60, help="HTTP timeout seconds")
    ap.add_argument("--sleep", type=float, default=0.0, help="Optional delay between requests")
    ap.add_argument("--limit", type=int, default=0, help="Evaluate only the first N rows (0 = all)")
    ap.add_argument("--out", default="predictions.jsonl", help="Where to save detailed predictions")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="Model ID served by vLLM (e.g., unsloth/Qwen3-4B-Instruct-2507-bnb-4bit)")
    args = ap.parse_args()

    print(f"[info] Using dataset: {args.csv}")
    print(f"[info] Using base_url: {args.base_url}")
    print(f"[info] Using model:    {args.model}")

    # 모델명을 클라이언트에 전달
    client = InstructionRefinementClient(server_url=args.base_url, timeout=args.timeout, model=args.model)
    health = client.test_api_connection()
    if health.get("status") != "success":
        raise RuntimeError(f"Server not healthy: {health}")

    df = pd.read_csv(args.csv)
    if args.limit > 0:
        df = df.head(args.limit)

    gold, pred, lines = [], [], []
    errors = 0

    for _, row in df.iterrows():
        qid, query, true_intent = row["id"], row["query"], row["intent"]
        try:
            out = client.refine_instruction(query)
            model_intent = safe_intent(out.get("intent_type"))
            gold.append(true_intent)
            pred.append(model_intent if model_intent else "INFORMATION")
            lines.append(json.dumps({
                "id": qid,
                "query": query,
                "gold_intent": true_intent,
                "pred_intent": model_intent,
                "model_output": out
            }, ensure_ascii=False))
        except Exception as e:
            errors += 1
            gold.append(true_intent)
            pred.append("INFORMATION")
            lines.append(json.dumps({
                "id": qid,
                "query": query,
                "gold_intent": true_intent,
                "pred_intent": None,
                "error": str(e)
            }, ensure_ascii=False))

        if args.sleep > 0:
            time.sleep(args.sleep)

    with open(args.out, "w", encoding="utf-8") as f:
        for ln in lines:
            f.write(ln + "\n")

    acc = accuracy_score(gold, pred)
    print(f"\nAccuracy: {acc*100:.2f}%  (errors: {errors})\n")
    # zero_division=0 으로 정답/예측이 없는 클래스의 경고 억제
    print(classification_report(gold, pred, labels=VALID_INTENTS, digits=3, zero_division=0))
    print("Confusion Matrix (labels in order):", VALID_INTENTS)
    print(confusion_matrix(gold, pred, labels=VALID_INTENTS))

if __name__ == "__main__":
    main()