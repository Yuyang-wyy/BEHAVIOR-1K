#!/usr/bin/env bash
# Start a Comet policy server plus one planner episode.
#   planner_session.sh start TASK INSTANCE_INDEX SESSION_DIR [PORT] [extra planner_episode.py args...]
#   planner_session.sh stop PORT
# Env: POLICY_DIR (default ft40k export), SIM_GPU / POLICY_GPU (default 0 / same as SIM_GPU),
#      LOCAL_EVAL (dir with serve_comet.sh + openpi-comet; default ~/Behavior/local_eval),
#      CONDA_SH (default ~/miniconda3/etc/profile.d/conda.sh). On sulab1:
#      LOCAL_EVAL=/data/ywang CONDA_SH=/data/ywang/miniconda3/etc/profile.d/conda.sh SIM_GPU=0 POLICY_GPU=1
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
B1K=$(cd "$HERE/../.." && pwd)
LOCAL_EVAL=${LOCAL_EVAL:-$HOME/Behavior/local_eval}
CONDA_SH=${CONDA_SH:-$HOME/miniconda3/etc/profile.d/conda.sh}
if [ -z "${POLICY_DIR:-}" ]; then
  for d in "$LOCAL_EVAL/exports/step-00040000" "$LOCAL_EVAL/ckpt/exports/step-00040000"; do [ -d "$d" ] && POLICY_DIR=$d && break; done
fi
export POLICY_DIR
SIM_GPU=${SIM_GPU:-${GPU:-0}}
POLICY_GPU=${POLICY_GPU:-$SIM_GPU}
TMP_ROOT=${TMP_ROOT:-$LOCAL_EVAL/cache/tmp}
case "${1:-}" in
  start)
    TASK=$2; IDX=$3; SESSION=$4; PORT=${5:-8000}; shift 5 || shift $#
    mkdir -p "$(dirname "$SESSION")"
    [ -e "$SESSION" ] && { echo "session exists: $SESSION" >&2; exit 1; }
    LOG_DIR=$(dirname "$SESSION")/logs; mkdir -p "$LOG_DIR"; NAME=$(basename "$SESSION")
    if ! curl -fsS "http://127.0.0.1:$PORT/healthz" >/dev/null 2>&1; then
      nohup setsid bash "$LOCAL_EVAL/serve_comet.sh" "$TASK" "$PORT" "$POLICY_GPU" > "$LOG_DIR/${NAME}_server.log" 2>&1 &
      echo "server starting (pid $!) for $TASK on :$PORT, ckpt $POLICY_DIR"
      for _ in $(seq 1 180); do
        grep -q "server listening" "$LOG_DIR/${NAME}_server.log" 2>/dev/null && break
        sleep 2
      done
      grep -q "server listening" "$LOG_DIR/${NAME}_server.log" || { echo "server failed"; tail -20 "$LOG_DIR/${NAME}_server.log"; exit 1; }
    else
      echo "WARNING: a server is already on :$PORT; its task sentence must be $TASK" >&2
    fi
    set +u; source "$CONDA_SH"; conda activate behavior; set -u
    cd "$B1K/OmniGibson"
    mkdir -p "$TMP_ROOT"
    export CUDA_VISIBLE_DEVICES=$SIM_GPU OMNIGIBSON_GPU_ID=0 OMNI_KIT_ACCEPT_EULA=YES OMNIGIBSON_HEADLESS=1 \
           TMPDIR=$TMP_ROOT
    nohup setsid python "$HERE/planner_episode.py" --task "$TASK" --instance-index "$IDX" --session "$SESSION" \
          --port "$PORT" "$@" > "$LOG_DIR/${NAME}_episode.log" 2>&1 &
    echo "episode starting (pid $!), log $LOG_DIR/${NAME}_episode.log"
    for _ in $(seq 1 600); do
      [ -f "$SESSION/READY" ] && { echo "READY: $(cat "$SESSION/READY")"; exit 0; }
      [ -f "$SESSION/DONE" ] && { echo "DONE: $(cat "$SESSION/DONE")"; exit 0; }
      sleep 2
    done
    echo "episode not ready after 20 min"; tail -30 "$LOG_DIR/${NAME}_episode.log"; exit 1 ;;
  stop)
    PORT=${2:-8000}
    for p in $(pgrep -f "serve_b1k.py.*--port=$PORT"); do kill "$p"; done
    echo "stopped server on :$PORT" ;;
  *) sed -n 2,6p "$0"; exit 2 ;;
esac
