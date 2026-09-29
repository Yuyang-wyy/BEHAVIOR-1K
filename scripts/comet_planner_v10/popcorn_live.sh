#!/usr/bin/env bash
# live popcorn burner pipeline over instances; tag v2burner
B=/home/ywang/Behavior; T=make_microwave_popcorn; C="python3 $B/BEHAVIOR-1K/scripts/comet_planner_v10/planner_client.py"
cd $B
for I in "$@"; do
  S=$B/planner_runs/claude_sup/${TAG:-burner2}__${T}__i$I; rm -rf $S
  B1K_MAX_TOKEN_LEN=256 POLICY_DIR=$B/local_eval/exports/v2-step-00040000 bash BEHAVIOR-1K/scripts/comet_planner_v10/planner_session.sh start $T $I $S 8100 ${EXTRA:-} >/dev/null 2>&1
  until [ -f $S/READY ]; do sleep 5; done
  echo "=== i$I $(date +%T)"
  timeout 1500 ~/miniconda3/envs/behavior/bin/python BEHAVIOR-1K/scripts/comet_planner_v10/popcorn_burner.py $S | cut -c1-400
  [ -f $S/DONE ] || $C $S end --timeout 400 >/dev/null 2>&1
  cat $S/DONE; echo
done
