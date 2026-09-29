#!/usr/bin/env bash
# Run planner episodes back to back from a job file (one per line: TASK INSTANCE_INDEX PLAN_JSON TAG).
#   run_batch.sh JOBFILE OUT_DIR [PORT]
# Sessions go to OUT_DIR/<TAG>__<TASK>__i<INDEX>; finished sessions are skipped, so it can be re-run.
# The Comet server is restarted whenever the task changes (its default prompt is the task sentence).
# Same env vars as planner_session.sh (POLICY_DIR, SIM_GPU, POLICY_GPU, LOCAL_EVAL, CONDA_SH).
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
JOBS=$1; OUT=$2; PORT=${3:-8000}
mkdir -p "$OUT/logs"
TMP_ROOT=${TMP_ROOT:-${LOCAL_EVAL:-$HOME/Behavior/local_eval}/cache/tmp}
current_task=""
stop_server() { for p in $(pgrep -f "serve_b1k.py.*--port=$PORT"); do kill "$p" 2>/dev/null; done; sleep 5; }
while read -r TASK IDX PLAN TAG; do
  [ -z "${TASK:-}" ] && continue
  case "$TASK" in \#*) continue ;; esac
  S="$OUT/${TAG}__${TASK}__i${IDX}"
  if [ -f "$S/DONE" ]; then echo "SKIP $S"; continue; fi
  if [ -e "$S" ]; then echo "removing incomplete $S"; rm -rf "$S"; fi
  if [ "$TASK" != "$current_task" ]; then stop_server; current_task=$TASK; fi
  bash "$HERE/wait_gpu.sh"
  echo "=== $(date +%T) $TAG $TASK i$IDX"
  bash "$HERE/planner_session.sh" start "$TASK" "$IDX" "$S" "$PORT" --plan "$PLAN" ${EPISODE_ARGS:-} > "$OUT/logs/${TAG}__${TASK}__i${IDX}_launch.log" 2>&1
  bash "$HERE/hang_watch.sh" "$S" & WATCH=$!
  # wait for the episode to finish (hard cap 3 h), then clean simulator temp files
  for _ in $(seq 1 2160); do [ -f "$S/DONE" ] && break; pgrep -f "planner_episode.py.*--session $S" >/dev/null || break; sleep 5; done
  if [ -f "$S/DONE" ]; then echo "    $(cat "$S/DONE")"; else echo "    FAILED (see $OUT/logs)"; for p in $(pgrep -f "planner_episode.py.*--session $S"); do kill "$p"; done; fi
  kill $WATCH 2>/dev/null
  find "$TMP_ROOT" -mindepth 1 -maxdepth 1 -mmin +1 -exec rm -rf {} + 2>/dev/null
done < "$JOBS"
stop_server
echo BATCH_DONE
