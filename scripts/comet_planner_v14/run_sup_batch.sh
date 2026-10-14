#!/usr/bin/env bash
# Supervised episodes with any supervisor script in this dir:
#   run_sup_batch.sh TASK "IDX IDX ..." OUT_DIR TAG PORT SUPERVISOR.py [supervisor args...]
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
TASK=$1; IDXS=$2; OUT=$3; TAG=$4; PORT=$5; SUP=$6; shift 6
mkdir -p "$OUT/logs"
CONDA_SH=${CONDA_SH:-$HOME/miniconda3/etc/profile.d/conda.sh}
PY=$(dirname "$CONDA_SH")/../../envs/behavior/bin/python; [ -x "$PY" ] || PY=python3
TMP_ROOT=${TMP_ROOT:-${LOCAL_EVAL:-$HOME/Behavior/local_eval}/cache/tmp}
for IDX in $IDXS; do
  S="$OUT/${TAG}__${TASK}__i${IDX}"
  [ -f "$S/DONE" ] && { echo "SKIP $S"; continue; }
  bash "$HERE/wait_gpu.sh"
  rm -rf "$S"
  echo "=== $(date +%T) $TAG $TASK i$IDX"
  bash "$HERE/planner_session.sh" start "$TASK" "$IDX" "$S" "$PORT" ${EPISODE_ARGS:-} > "$OUT/logs/${TAG}__i${IDX}_launch.log" 2>&1
  bash "$HERE/hang_watch.sh" "$S" & WATCH=$!
  "$PY" "$HERE/$SUP" "$S" "$@" > "$OUT/logs/${TAG}__i${IDX}_sup.log" 2>&1
  kill $WATCH 2>/dev/null
  for _ in $(seq 1 120); do [ -f "$S/DONE" ] && break; sleep 5; done
  echo "    $(cat "$S/DONE" 2>/dev/null || echo FAILED) | $(tail -1 "$OUT/logs/${TAG}__i${IDX}_sup.log")"
  find "$TMP_ROOT" -mindepth 1 -maxdepth 1 -mmin +1 -exec rm -rf {} + 2>/dev/null
done
echo AUTO_BATCH_DONE
