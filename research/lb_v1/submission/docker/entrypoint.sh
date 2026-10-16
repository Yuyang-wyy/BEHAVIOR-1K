#!/usr/bin/env bash
# Policy server entrypoint. The evaluator (OmniGibson, outside the container) connects via websocket on $PORT.
#   TASK_NAME  (required) BEHAVIOR task name, e.g. picking_up_trash  - selects the prompt and the checkpoint
#   PORT       (default 8000)
#   CKPT_ROOT  (default /ckpt) with subdirs ft40k/ and zs-pt50/ (downloaded at build time from HuggingFace)
set -euo pipefail
TASK_NAME=${TASK_NAME:-${TASK:-${B1K_TASK:-${BEHAVIOR_TASK:-}}}}
[ -z "$TASK_NAME" ] && [ -f /task.txt ] && TASK_NAME=$(head -1 /task.txt)
: "${TASK_NAME:?set TASK_NAME (or TASK / B1K_TASK / BEHAVIOR_TASK, or mount /task.txt) to the BEHAVIOR task name}"
PORT=${PORT:-8000}; CKPT_ROOT=${CKPT_ROOT:-/ckpt}
if grep -qx "$TASK_NAME" /app/routing_zero_shot_tasks.txt; then CK=$CKPT_ROOT/zs-pt50; else CK=$CKPT_ROOT/ft40k; fi
echo "[entrypoint] task=$TASK_NAME checkpoint=$CK port=$PORT"
cd /app/openpi-comet
export OPENPI_DISABLE_TORCH_COMPILE=1 XLA_PYTHON_CLIENT_MEM_FRACTION=0.35 HF_HUB_OFFLINE=1
exec /app/openpi-comet/.venv/bin/python scripts/serve_b1k.py --task_name="$TASK_NAME" --port="$PORT" --control_mode=receeding_horizon --max_len=32 \
  policy:checkpoint --policy.config=pi05_b1k-base --policy.dir="$CK"
