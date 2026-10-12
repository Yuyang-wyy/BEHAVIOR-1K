#!/usr/bin/env bash
# Run specific missing instances: run_missing.sh "TASK:idx,idx,...;TASK2:idx,..."   (env as sweep_lb.sh: BASE OUT POLICY_FT POLICY_ZS ZS_LIST TAG PORT SGPU RESUME_ARGS)
SPEC=$1; TAG=${TAG:-lb_v1}; PORT=${PORT:-8000}; SGPU=${SGPU:-0}
cd "$BASE"; mkdir -p logs; SUMMARY=logs/${TAG}_sweep.log
IFS=';' read -ra ITEMS <<< "$SPEC"
for IT in "${ITEMS[@]}"; do
  T=${IT%%:*}; IDX=$(echo "${IT#*:}" | tr ',' ' ')
  if grep -qx "$T" "$ZS_LIST"; then PD=$POLICY_ZS; CK=zs; else PD=$POLICY_FT; CK=ft40k; fi
  echo "=== $(date '+%F %T') START $T ckpt=$CK missing-only idx=[$IDX]" | tee -a $SUMMARY
  POLICY_DIR=$PD bash serve_comet.sh $T $PORT $SGPU > logs/serve_${TAG}_$PORT.log 2>&1 &
  SP=$!
  until grep -q "server listening" logs/serve_${TAG}_$PORT.log || ! kill -0 $SP 2>/dev/null; do sleep 5; done
  grep -q "server listening" logs/serve_${TAG}_$PORT.log || { echo "SERVE_FAILED $T" | tee -a $SUMMARY; sleep 60; continue; }
  WRITE_VIDEO=1 timeout 10h bash run_eval.sh $T "$IDX" $TAG $PORT ${RESUME_ARGS---resume-results} > logs/eval_${TAG}_${T}_missing.log 2>&1
  pkill -P $SP; kill $SP 2>/dev/null; pkill -f "serve_b1k.py.*--port=$PORT"; sleep 5
  echo "    $(date '+%F %T') END $T missing-only jsons=$(ls "$OUT/$TAG/$T/json/"*.json 2>/dev/null | wc -l) | $(grep -h 'Result:' logs/eval_${TAG}_${T}_missing.log | sed 's/ -> .*//' | tr '\n' ' ')" | tee -a $SUMMARY
done
echo "MISSING_DONE $(date '+%F %T')" | tee -a $SUMMARY
