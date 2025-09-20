#!/usr/bin/env bash
set -euo pipefail

### ────────────────────────── 기본 설정 ──────────────────────────
MODEL="meta-llama/Meta-Llama-3.2-3B-Instruct"
PORT=8000
BASE_URL="http://127.0.0.1:${PORT}/v1"
CSV="/home/minjoo/Github/PRISM-Orch/InstructionRF/data/Semiconductor_intent_dataset__preview_.csv"

# 사용 GPU와 텐서 병렬 크기(일치해야 함)
export CUDA_VISIBLE_DEVICES="0,1,2,3,4,5"
TP_SIZE=6

# vLLM 옵션
MAX_MODEL_LEN=65536
GPU_UTIL=0.95
DISABLE_TORCH_COMPILE="--disable-torch-compile"

# 로그/폴더
LOG_DIR="/tmp/vllm_oneclick"
SRV_LOG="${LOG_DIR}/vllm_server.log"
PID_FILE="${LOG_DIR}/vllm_server.pid"
EVAL_LOG="${LOG_DIR}/evaluate.log"
mkdir -p "$LOG_DIR"

### ─────────────────────── 멀티GPU 안정화 옵션 ───────────────────────
# 단일 노드 다중 GPU에서 NCCL/프로세스 초기화 안정화
export VLLM_WORKER_MULTIPROC=1
export NCCL_P2P_DISABLE=0
export NCCL_SHM_DISABLE=0
export NCCL_IB_DISABLE=1
export NCCL_SOCKET_IFNAME=lo
export CUDA_DEVICE_MAX_CONNECTIONS=1

### ─────────────────────── 유틸/클린업/에러처리 ───────────────────────
die() { echo "❌ $*" >&2; exit 1; }

# 라인버퍼링(실시간 출력) 보장용
stdbuf_oL() { stdbuf -oL -eL "$@"; }

# 종료 시 정리
cleanup() {
  echo "[CLEANUP] 종료 처리…"
  # tail 프로세스 종료
  [[ -n "${TAIL_PID:-}" ]] && kill "${TAIL_PID}" 2>/dev/null || true
  # vLLM 서버 종료
  if [[ -f "${PID_FILE}" ]]; then
    PID="$(cat "${PID_FILE}" || true)"
    if [[ -n "${PID}" ]] && ps -p "${PID}" >/dev/null 2>&1; then
      kill "${PID}" || true
      sleep 2
      ps -p "${PID}" >/dev/null 2>&1 && kill -9 "${PID}" || true
    fi
    rm -f "${PID_FILE}"
  fi
}
trap cleanup EXIT INT TERM

### ────────────────────────── 사전 점검 ──────────────────────────
# CUDA_VISIBLE_DEVICES 개수 ↔ TP_SIZE 일치 확인
GPU_COUNT="$(awk -F',' '{print NF}' <<< "${CUDA_VISIBLE_DEVICES}")"
if [[ "${GPU_COUNT}" -ne "${TP_SIZE}" ]]; then
  die "CUDA_VISIBLE_DEVICES(${CUDA_VISIBLE_DEVICES})의 GPU 수(${GPU_COUNT})와 TP_SIZE(${TP_SIZE})가 일치해야 합니다."
fi

# nvidia-smi 가시성 확인(선택)
if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "[WARN] nvidia-smi 를 찾을 수 없습니다. GPU 상태 스냅샷은 건너뜁니다."
fi

echo "[DBG] CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES}"
echo "[DBG] TP_SIZE=${TP_SIZE}"
echo "[DBG] MODEL=${MODEL}, PORT=${PORT}"
echo "[DBG] LOG_DIR=${LOG_DIR}"

### ────────────────────────── 서버 기동 ──────────────────────────
echo "[1/4] vLLM 서버 시작(백그라운드)…"
# 기존 로그 보존을 위해 이어쓰기
: > "${SRV_LOG}"
nohup python -m vllm.entrypoints.openai.api_server \
  --model "${MODEL}" \
  --host 0.0.0.0 \
  --port "${PORT}" \
  --tensor-parallel-size "${TP_SIZE}" \
  --max-model-len "${MAX_MODEL_LEN}" \
  --gpu-memory-utilization "${GPU_UTIL}" \
  ${DISABLE_TORCH_COMPILE} \
  >> "${SRV_LOG}" 2>&1 &

echo $! > "${PID_FILE}"
echo "  - PID: $(cat ${PID_FILE})"
echo "  - 로그: ${SRV_LOG}"

sleep 2
echo "[DBG] 현재 vLLM 관련 프로세스:"
ps -ef | grep -E "vllm|api_server" | grep -v grep || true

# 서버 로그를 실시간으로 옆에서 보여주기
echo "[LOG] vLLM 서버 로그 팔로우 시작… (Ctrl+C로 전체 작업 종료됨)"
tail -n 0 -f "${SRV_LOG}" &
TAIL_PID=$!

# GPU 메모리 스냅샷(기동 직후)
if command -v nvidia-smi >/dev/null 2>&1; then
  echo "[DBG] GPU mem after launch:"
  nvidia-smi --query-gpu=index,name,memory.total,memory.used --format=csv,noheader || true
fi

### ────────────────────────── 헬스체크 ──────────────────────────
echo "[2/4] 서버 준비 대기(/v1/models 헬스체크)…"
READY=0
for i in {1..180}; do
  if curl -sS "${BASE_URL}/models" >/dev/null 2>&1; then
    echo "  - 서버 준비 완료"
    READY=1
    break
  fi
  sleep 1
done
if [[ "${READY}" -ne 1 ]]; then
  echo "  - 서버 준비 실패. 최근 로그:"
  tail -n 100 "${SRV_LOG}" || true
  die "서버가 기동되지 않았습니다."
fi

# 로그에서 TP 초기화 확인(선택적이지만 유용)
if grep -Eiq "tensor.?parallel|world.?size|tp" "${SRV_LOG}"; then
  echo "[DBG] TP 관련 로그 감지:"
  grep -Ei "tensor.?parallel|world.?size|tp|rank" "${SRV_LOG}" | tail -n 10 || true
else
  echo "[WARN] TP 초기화 관련 로그를 찾지 못했습니다. 실제로 1GPU로 폴백했을 수 있습니다."
fi

### ────────────────────────── 평가 실행 ──────────────────────────
echo "[3/4] 성능 평가 실행(evaluate_intent_accuracy.py)… (로그: ${EVAL_LOG})"
: > "${EVAL_LOG}"
stdbuf_oL python evaluate_intent_accuracy.py \
  --base_url "${BASE_URL}" \
  --csv "${CSV}" \
  --timeout 60 2>&1 | tee -a "${EVAL_LOG}"

### ────────────────────────── 종료/정리 ──────────────────────────
echo "[4/4] 완료. 리소스 정리 중…"
# cleanup은 trap으로 자동 실행됨

# 종료 직전 GPU 메모리 스냅샷(선택)
if command -v nvidia-smi >/dev/null 2>&1; then
  echo "[DBG] GPU mem before exit:"
  nvidia-smi --query-gpu=index,name,memory.total,memory.used --format=csv,noheader || true
fi

echo "✅ 완료! 서버 로그: ${SRV_LOG}, 평가 로그: ${EVAL_LOG}"
