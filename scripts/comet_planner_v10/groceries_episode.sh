#!/usr/bin/env bash
# Supervised carrying_in_groceries episode: skill "close the lid of the car" until the trunk literal is true
# (max 90 s), then the global prompt; re-issue the close skill if the literal is lost. Prints a summary.
I=$1; B=/home/ywang/Behavior; T=carrying_in_groceries; S=$B/planner_runs/claude_sup/claude__${T}__i$I
C="python3 $B/BEHAVIOR-1K/scripts/comet_planner_v10/planner_client.py $S"
cd $B; B1K_MAX_TOKEN_LEN=256 POLICY_DIR=$B/local_eval/exports/v2-step-00040000 bash BEHAVIOR-1K/scripts/comet_planner_v10/planner_session.sh start $T $I $S 8100 >/dev/null 2>&1
until [ -f $S/READY ]; do sleep 5; done
q() { grep -o '"partial_q": [0-9.]*' $S/trace.jsonl | tail -1 | cut -d' ' -f2; }
mode=close; $C skill "close the lid of the car" --why "bank the trunk" >/dev/null; n=0; closes=1
while :; do
  over=$($C continue | python3 -c "import json,sys; r=json.loads(sys.stdin.read().split('\nDONE')[0]); print(r.get('episode_over'), r.get('step'))")
  set -- $over; [ "$1" = "True" ] && break
  n=$((n+1)); cur=$(q)
  if [ "$mode" = close ] && [ "$cur" = "0.25" ]; then echo "trunk closed at step $2"; mode=global; $C global --why "trunk banked" >/dev/null
  elif [ "$mode" = close ] && [ $n -ge 18 ]; then echo "close skill timed out at step $2"; mode=global; $C global >/dev/null
  elif [ "$mode" = global ] && [ "$cur" = "0.0" ] && [ $closes -lt 3 ]; then echo "trunk reopened at step $2"; mode=close; n=0; closes=$((closes+1)); $C skill "close the lid of the car" --why "re-bank" >/dev/null
  fi
done
cat $S/DONE; echo
