"""Code skill: carry the object held in ARM over a target seen in the head camera and release it.

Legal inputs: head depth (harness `point`), robot kinematics. Steps: point at the target pixel -> if farther than
~0.75 m, drive the base so the target sits 0.6 m ahead -> raise the hand to target_z + `above` -> move over the
target (re-issued until within 3 cm) -> lower to target_z + `drop` -> open -> lift and straighten the trunk.

    place_at.py SESSION --arm left --u 490 --v 505 [--above 0.25] [--drop 0.12] [--no-drive]
"""
import argparse, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
from poke_marker import send

ap = argparse.ArgumentParser()
ap.add_argument("session"); ap.add_argument("--arm", default="right")
ap.add_argument("--u", type=float, required=True); ap.add_argument("--v", type=float, required=True)
ap.add_argument("--above", type=float, default=0.25); ap.add_argument("--drop", type=float, default=0.12)
ap.add_argument("--no-drive", action="store_true")
a = ap.parse_args()
S = a.session
p = np.array(send(S, {"op": "point", "cam": "head", "u": a.u, "v": a.v})["point_base"])
log = {"target0": p.round(3).tolist()}
rng = float(np.hypot(p[0], p[1]))
if not a.no_drive and rng > 0.75:
    # drive most of the way, then re-point the target from the new pose (odometry drifts on turns)
    yaw = float(np.degrees(np.arctan2(p[1], p[0])))
    send(S, {"op": "base", "turn_deg": yaw, "gentle": True, "why": "place_at: face target"})
    send(S, {"op": "base", "forward": rng - 0.62, "gentle": True, "why": "place_at: target to ~0.6 m"})
    log["drove"] = [round(yaw, 1), round(rng - 0.62, 2)]
    print(json.dumps({"need_repoint": True, **log}))
    sys.exit(0)
def eef():
    return np.array(send(S, {"op": "fingers"})[a.arm]["eef"])
def goto(t, why, tries=4):
    r = None
    for _ in range(tries):
        d = t - eef()
        if np.linalg.norm(d) < 0.03:
            break
        r = send(S, {"op": "hand", "arm": a.arm, "forward": float(d[0]), "left": float(d[1]), "up": float(d[2]), "why": why})
    return float(np.linalg.norm(t - eef()))
e = eef()
log["lift_res"] = goto(np.array([e[0], e[1], p[2] + a.above]), "place_at: lift")
log["over_res"] = goto(np.array([p[0], p[1], p[2] + a.above]), "place_at: over target")
log["low_res"] = goto(np.array([p[0], p[1], p[2] + a.drop]), "place_at: lower")
send(S, {"op": "grip", "arm": a.arm, "close": False, "why": "place_at: release"})
e = eef(); goto(e + np.array([0, 0, 0.15]), "place_at: clear", tries=1)
r = send(S, {"op": "trunk", "why": "place_at: upright"})
log["panel"] = r["images"]["panel"]
print(json.dumps(log))
