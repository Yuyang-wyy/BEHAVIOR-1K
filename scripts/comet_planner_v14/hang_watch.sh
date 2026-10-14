#!/usr/bin/env bash
# hang_watch.sh SESSION_DIR [STALL_S] : kill an episode whose trace stops advancing (hung simulator).
# Dumps Python stacks (SIGUSR1, faulthandler) into the episode log first, then kills the episode and any
# supervisor/client attached to the session, and writes SESSION/HANG. Exits when SESSION/DONE appears.
S=$1; STALL=${2:-300}
sleep 60
while [ ! -f "$S/DONE" ]; do
  if [ -f "$S/trace.jsonl" ] && [ $(( $(date +%s) - $(stat -c %Y "$S/trace.jsonl") )) -gt "$STALL" ]; then
    for p in $(pgrep -f "planner_episod[e].py.*--session $S"); do kill -USR1 "$p"; sleep 5; kill -9 "$p"; done
    for p in $(pgrep -f "superviso[r].py $S|planner_clien[t].py $S"); do kill "$p"; done
    echo "{\"hang\": true, \"stalled_s\": $STALL, \"at\": \"$(date +%T)\"}" > "$S/HANG"
    exit 0
  fi
  sleep 30
done
