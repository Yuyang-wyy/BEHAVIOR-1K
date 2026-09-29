"""Code skill: press the nearest ON (green) toggle marker once with a closed fingertip, then retract.

Legal inputs: head RGB + depth (via the harness `point` op), robot kinematics. The green/red marker sphere is
BEHAVIOR's visible ToggledOn indicator. One press = approach 5 cm in front, push `push` m, retract 10 cm.

    poke_marker.py SESSION [--arm right] [--max-range 1.1] [--min-z 0.3] [--push 0.065] [--pick u,v]
"""
import argparse, json, subprocess, sys
from pathlib import Path
import numpy as np
import cv2

CLIENT = Path(__file__).with_name("planner_client.py")


def send(session, cmd, timeout=900):
    out = subprocess.run([sys.executable, str(CLIENT), str(session), "raw", json.dumps(cmd), "--timeout", str(timeout)],
                         capture_output=True, text=True)
    return json.loads(out.stdout.split("\nDONE")[0])


def green_blobs(img):
    b, g, r = img[..., 0].astype(int), img[..., 1].astype(int), img[..., 2].astype(int)
    m = ((g > 140) & (g - r > 70) & (g - b > 70)).astype(np.uint8)
    n, lab, stats, cent = cv2.connectedComponentsWithStats(m)
    return [(float(cent[i][0]), float(cent[i][1]), int(stats[i][4])) for i in range(1, n) if stats[i][4] >= 4]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("session")
    ap.add_argument("--arm", default="right")
    ap.add_argument("--max-range", type=float, default=1.1)
    ap.add_argument("--min-z", type=float, default=0.3)
    ap.add_argument("--push", type=float, default=0.065)
    ap.add_argument("--pick", default=None, help="u,v native head pixel to use instead of auto-detect")
    a = ap.parse_args()
    obs = send(a.session, {"op": "observe"})
    img = cv2.imread(obs["images"]["head"])
    if a.pick:
        cands = [tuple(map(float, a.pick.split(","))) + (0,)]
    else:
        cands = green_blobs(img)
    pts = []
    for u, v, area in cands:
        p = send(a.session, {"op": "point", "cam": "head", "u": u, "v": v})
        x, y, z = p["point_base"]
        rng = float(np.hypot(x, y))
        pts.append({"uv": [round(u), round(v)], "area": area, "p": [x, y, z], "range": round(rng, 2)})
    ok = [q for q in pts if q["range"] <= a.max_range and q["p"][2] >= a.min_z]
    print(json.dumps({"candidates": pts}))
    if not ok:
        print(json.dumps({"result": "no green marker in reach"}))
        return
    t = min(ok, key=lambda q: q["range"])
    tx, ty, tz = t["p"]
    fg = send(a.session, {"op": "fingers"})
    eef = np.array(fg[a.arm]["eef"]); off = np.array(fg[a.arm]["finger_mid_minus_eef"])
    d = np.array([tx, ty, 0.0]); d /= (np.linalg.norm(d) + 1e-9)          # horizontal approach from the robot
    pre = np.array([tx, ty, tz]) - off - 0.05 * d
    send(a.session, {"op": "grip", "arm": a.arm, "close": True, "why": "poke: close fingers"})
    r1 = None
    for k in range(4):                      # long IK moves stall part-way: re-issue from the new pose until close
        fg = send(a.session, {"op": "fingers"}); eef = np.array(fg[a.arm]["eef"])
        dl = pre - eef
        if np.linalg.norm(dl) < 0.02:
            break
        r1 = send(a.session, {"op": "hand", "arm": a.arm, "forward": float(dl[0]), "left": float(dl[1]), "up": float(dl[2]),
                              "why": f"poke: 5 cm in front of marker {t['uv']} (try {k})"})
    if r1 is None or r1["hand"]["residual_m"] > 0.03:
        print(json.dumps({"result": "unreachable", "residual": None if r1 is None else r1["hand"]["residual_m"]}))
        send(a.session, {"op": "trunk", "why": "poke: upright"})
        return
    r2 = send(a.session, {"op": "hand", "arm": a.arm, "forward": float(d[0] * a.push), "left": float(d[1] * a.push), "up": 0.0,
                          "why": "poke: press"})
    r3 = send(a.session, {"op": "hand", "arm": a.arm, "forward": float(-d[0] * 0.10), "left": float(-d[1] * 0.10), "up": 0.0,
                          "why": "poke: retract (single press)"})
    send(a.session, {"op": "trunk", "why": "poke: upright"})
    print(json.dumps({"result": "pressed", "target": t, "approach_residual": r1["hand"]["residual_m"],
                      "press_residual": r2["hand"]["residual_m"], "panel": r3["images"]["panel"]}))


if __name__ == "__main__":
    main()
