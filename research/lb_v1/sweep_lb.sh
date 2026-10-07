#!/usr/bin/env bash
# Leaderboard sweep: instances 0-9, videos on, resume-safe, per-task checkpoint routing.
#   env: BASE (dir with run_eval.sh/serve_comet.sh/logs), OUT (eval_out root), POLICY_FT, POLICY_ZS, ZS_LIST, TAG, PORT, SGPU
#   usage: sweep_lb.sh TASKFILE
TASKS=$1; TAG=${TAG:-lb_v1}; PORT=${PORT:-8000}; SGPU=${SGPU:-0}
cd "$BASE"; mkdir -p logs
SUMMARY=logs/${TAG}_sweep.log
while read T; do
  [ -z "$T" ] && continue
  n=$(ls "$OUT/$TAG/$T/json/"*.json 2>/dev/null | wc -l)
  [ "$n" -ge 10 ] && { echo "SKIP $T ($n done)" | tee -a $SUMMARY; continue; }
  if grep -qx "$T" "$ZS_LIST"; then PD=$POLICY_ZS; CK=zs; else PD=$POLICY_FT; CK=ft40k; fi
  echo "=== $(date '+%F %T') START $T ckpt=$CK done=$n" | tee -a $SUMMARY
  POLICY_DIR=$PD bash serve_comet.sh $T $PORT $SGPU > logs/serve_${TAG}_$PORT.log 2>&1 &
  SP=$!
  until grep -q "server listening" logs/serve_${TAG}_$PORT.log || ! kill -0 $SP 2>/dev/null; do sleep 5; done
  grep -q "server listening" logs/serve_${TAG}_$PORT.log || { echo "SERVE_FAILED $T" | tee -a $SUMMARY; tail -5 logs/serve_${TAG}_$PORT.log; sleep 60; continue; }
  WRITE_VIDEO=1 timeout 14h bash run_eval.sh $T "0 1 2 3 4 5 6 7 8 9" $TAG $PORT --resume-results > logs/eval_${TAG}_$T.log 2>&1
  pkill -P $SP; kill $SP 2>/dev/null; pkill -f "serve_b1k.py.*--port=$PORT"; sleep 5
  n2=$(ls "$OUT/$TAG/$T/json/"*.json 2>/dev/null | wc -l)
  echo "    $(date '+%F %T') END $T ckpt=$CK jsons=$n2 | $(grep -h 'Result:' logs/eval_${TAG}_$T.log | sed 's/ -> .*//' | tr '\n' ' ')" | tee -a $SUMMARY
  find "${TMP_ROOT:-$BASE/cache/tmp}" -mindepth 1 -maxdepth 1 -mmin +2 -exec rm -rf {} + 2>/dev/null
done < $TASKS
echo "SWEEP_DONE $(date '+%F %T')" | tee -a $SUMMARY
