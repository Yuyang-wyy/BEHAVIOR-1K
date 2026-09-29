#!/usr/bin/env bash
# sup.sh SESSION CMD [args...] : run one harness command, print a one-line summary + panel path
S=$1; shift
python3 $(dirname "$0")/planner_client.py "$S" "$@" | python3 -c '
import json,sys
t=sys.stdin.read().split("\nDONE")[0]
try: r=json.loads(t)
except Exception: print(t[-800:]); sys.exit()
p=r.get("proprio",{}); m=r.get("monitor",{})
print("step",r.get("step"),"left",r.get("seconds_left"),"s | jaw L %.3f R %.3f | base %.2f | hoverL %s R %s idle %s jaw_ev %s | %s | ev %s %s" % (
 p.get("gripper_left_width",0),p.get("gripper_right_width",0),p.get("base_speed",0),m.get("left_hover_s"),m.get("right_hover_s"),m.get("base_idle_s"),m.get("since_jaw_event_s"),
 (r.get("prompt") or "")[:50], [e["event"] for e in r.get("events",[])][:4], "OVER "+json.dumps({k:r[k] for k in ("reason",) if k in r}) if r.get("episode_over") else ""))
print(r.get("images",{}).get("panel",""))
for k in ("hand","base","grip","look"):
    if k in r: print(k, json.dumps(r[k])[:300])
'
