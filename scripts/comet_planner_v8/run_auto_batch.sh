#!/usr/bin/env bash
# Auto-supervised episodes: run_auto_batch.sh TASK "IDX IDX ..." OUT_DIR TAG PLACE_PROMPT [PORT] [extra auto_supervisor args]
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
TASK=$1; IDXS=$2; OUT=$3; TAG=$4; PLACE=$5; PORT=${6:-8000}; shift 6 || shift $#
mkdir -p "$OUT/logs"
TMP_ROOT=${TMP_ROOT:-${LOCAL_EVAL:-$HOME/Behavior/local_eval}/cache/tmp}
for IDX in $IDXS; do
  S="$OUT/${TAG}__${TASK}__i${IDX}"
  [ -f "$S/DONE" ] && { echo "SKIP $S"; continue; }
  rm -rf "$S"
  echo "=== $(date +%T) $TAG $TASK i$IDX"
  bash "$HERE/planner_session.sh" start "$TASK" "$IDX" "$S" "$PORT" ${EPISODE_ARGS:-} > "$OUT/logs/${TAG}__i${IDX}_launch.log" 2>&1
  timeout ${EPISODE_TIMEOUT:-3000} python3 "$HERE/auto_supervisor.py" "$S" --place-prompt "$PLACE" "$@" > "$OUT/logs/${TAG}__i${IDX}_sup.log" 2>&1
  if [ ! -f "$S/DONE" ]; then     # hung simulator: dump stacks, then kill, and record the failure
    for p in $(pgrep -f "planner_episod[e].py.*--session $S"); do kill -USR1 $p; sleep 3; kill -9 $p; done
    echo '{"hang": true}' > "$S/HANG"
  fi
  for _ in $(seq 1 120); do [ -f "$S/DONE" ] && break; sleep 5; done
  echo "    $(cat "$S/DONE" 2>/dev/null || echo FAILED) | $(grep -c auto_grasp "$OUT/logs/${TAG}__i${IDX}_sup.log") grasps: $(grep 'auto_grasp' "$OUT/logs/${TAG}__i${IDX}_sup.log" | sed 's/.*-> //' | tr '\n' ' ')"
  find "$TMP_ROOT" -mindepth 1 -maxdepth 1 -mmin +1 -exec rm -rf {} + 2>/dev/null
done
echo AUTO_BATCH_DONE
