#!/usr/bin/env bash
# chop_an_onion recipe (live, legal): Comet picks the cutting board, carries it to the sink, supervisor releases it
# over the basin. Worth 0.25 (board-in-sink literal); the rest of the episode runs on the global prompt.
#   onion_board.sh SESSION
S=$1; D=$(dirname "$0"); C="python3 $D/planner_client.py $S"
w() { $C raw "{\"op\":\"$1\"}" | python3 -c "import json,sys; r=json.loads(sys.stdin.read().split('\nDONE')[0]); p=r.get('proprio',{}); print(r.get('step'), p.get('gripper_left_width'), p.get('gripper_right_width'), r.get('images',{}).get('head',''))"; }
$C global --why "start" >/dev/null
$C skill "move to the cutting board" --why "recipe: Comet picks the board" >/dev/null
for i in $(seq 1 24); do
  read st wl wr img < <(w continue)
  echo "step $st L $wl R $wr"
  held=$(python3 -c "print(1 if (0.004<$wl<0.06) or (0.004<$wr<0.06) else 0)")
  [ "$held" = 1 ] && break
done
[ "$held" != 1 ] && { echo "board not picked"; exit 1; }
$C skill "move to the drop in sink" --why "recipe: carry board to sink" >/dev/null
for i in 1 2 3 4 5 6; do read st wl wr img < <(w continue); echo "step $st carry $img"; done
echo "CHECK_IMAGE $img"
