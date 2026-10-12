#!/usr/bin/env bash
# Kill the running lb_v1 evaluator if its task log has not changed for STALE_MIN minutes (hung episode); the sweep
# then moves on and the task can be re-queued. env: LOGDIR, STALE_MIN (default 200), TAG (lb_v1)
LOGDIR=${LOGDIR:?}; STALE_MIN=${STALE_MIN:-200}; TAG=${TAG:-lb_v1}
while true; do
  sleep 600
  P=$(pgrep -f "omnigibson.eval.eval --task-nam[e]" | head -1); [ -z "$P" ] && continue
  T=$(ps -o args= -p $P | sed 's/.*--task-name \([^ ]*\).*/\1/')
  L=$LOGDIR/eval_${TAG}_$T.log; [ -f "$L" ] || continue
  age=$(( ( $(date +%s) - $(stat -c %Y "$L") ) / 60 ))
  if [ "$age" -ge "$STALE_MIN" ]; then
    echo "$(date '+%F %T') HANG $T pid $P log idle ${age} min -> kill" >> $LOGDIR/${TAG}_hangs.log
    kill $P; sleep 30; kill -9 $P 2>/dev/null
  fi
done
