"""Code skill: push an object across a surface toward a target, both seen in the head camera.

Each round: back-project object and target pixels (the object pixel is re-found by colour-tracking a patch
around the previous pixel), put the closed hand 8 cm behind the object on the far side from the target at the
object's mid height, then push along the object->target direction by min(remaining - stop, 0.15 m).
Stops when the object is within `stop` of the target or after `rounds`.

    push_to.py SESSION --arm left --obj u,v --target u,v [--stop 0.12] [--rounds 4]
"""
import argparse, json, sys
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).parent))
from poke_marker import send

ap = argparse.ArgumentParser()
ap.add_argument("session"); ap.add_argument("--arm", default="left")
ap.add_argument("--obj", required=True); ap.add_argument("--target", required=True)
ap.add_argument("--stop", type=float, default=0.12); ap.add_argument("--rounds", type=int, default=4)
a = ap.parse_args(); S = a.session
ou, ov = map(float, a.obj.split(",")); tu, tv = map(float, a.target.split(","))
img = cv2.imread(send(S, {"op": "observe"})["images"]["head"]); patch = img[int(ov) - 12:int(ov) + 12, int(ou) - 12:int(ou) + 12].copy()
pt = lambda u, v: np.array(send(S, {"op": "point", "cam": "head", "u": u, "v": v})["point_base"])
T = pt(tu, tv); log = []
send(S, {"op": "grip", "arm": a.arm, "close": True, "why": "push_to: fist"})
def eef():
    return np.array(send(S, {"op": "fingers"})[a.arm]["eef"])
def goto(t, why):
    for _ in range(3):
        d = t - eef()
        if np.linalg.norm(d) < 0.03:
            break
        send(S, {"op": "hand", "arm": a.arm, "forward": float(d[0]), "left": float(d[1]), "up": float(d[2]), "why": why})
    return float(np.linalg.norm(t - eef()))
for k in range(a.rounds):
    O = pt(ou, ov); v = (T - O)[:2]; dist = float(np.linalg.norm(v))
    log.append({"round": k, "obj": O.round(3).tolist(), "dist": round(dist, 3)})
    if dist <= a.stop:
        break
    u = v / dist
    behind = np.array([O[0] - 0.08 * u[0], O[1] - 0.08 * u[1], O[2]])
    goto(behind + np.array([0, 0, 0.12]), "push_to: above behind")
    log[-1]["behind_res"] = goto(behind, "push_to: behind object")
    step = min(dist - a.stop + 0.02, 0.15)
    send(S, {"op": "hand", "arm": a.arm, "forward": float(u[0] * step), "left": float(u[1] * step), "up": 0.0, "why": "push_to: push"})
    goto(eef() + np.array([0, 0, 0.12]), "push_to: lift")
    img = cv2.imread(send(S, {"op": "observe"})["images"]["head"])
    r = cv2.matchTemplate(img, patch, cv2.TM_SQDIFF_NORMED); _, _, mn, _ = cv2.minMaxLoc(r)
    ou, ov = mn[0] + 12, mn[1] + 12
log.append({"final_obj": pt(ou, ov).round(3).tolist()})
send(S, {"op": "trunk", "why": "push_to: upright"})
print(json.dumps(log))
