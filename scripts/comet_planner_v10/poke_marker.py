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
    ap.add_argument("--horizontal", action="store_true",
                    help="point the gripper at the marker (approach axis horizontal) - needed for high wall switches")
    ap.add_argument("--normal", action="store_true", help="approach along the wall normal fitted from depth around the marker")
    ap.add_argument("--square", action="store_true", help="with --normal: drive the base to 0.65 m in front of the wall, facing it")
    ap.add_argument("--standoff", type=float, default=0.05, help="approach this far in front of the marker")
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
    if a.normal:
        u0, v0 = t["uv"]; P = []
        for du in (-28, 0, 28):
            for dv in (-28, 0, 28):
                if du == 0 and dv == 0:
                    continue
                q = send(a.session, {"op": "point", "cam": "head", "u": u0 + du, "v": v0 + dv})["point_base"]
                P.append(q)
        P = np.array(P); P = P[np.abs(P[:, 2] - tz) < 0.2]          # drop floor/ceiling hits
        if len(P) >= 4:
            c = P.mean(0); n = np.linalg.svd(P - c)[2][-1]
            n[2] = 0.0; n /= (np.linalg.norm(n) + 1e-9)
            if n @ np.array([tx, ty, 0.0]) < 0:
                n = -n
            print(json.dumps({"wall_normal": n.round(3).tolist(), "n_pts": int(len(P))}))
            d = n                                                      # push into the wall
            if a.square:
                st = np.array([tx, ty]) - 0.65 * n[:2]
                yaw = float(np.arctan2(n[1], n[0]))
                send(a.session, {"op": "base", "forward": float(st[0]), "left": float(st[1]), "gentle": True,
                                 "why": "poke: stand 0.65 m in front of the switch"})
                send(a.session, {"op": "base", "turn_deg": float(np.degrees(yaw)), "gentle": True, "why": "poke: face the wall"})
                q = np.array([tx, ty]) - st
                c_, s_ = np.cos(-yaw), np.sin(-yaw)
                tx, ty = float(c_ * q[0] - s_ * q[1]), float(s_ * q[0] + c_ * q[1])
                d = np.array([1.0, 0.0, 0.0])
                print(json.dumps({"squared": True, "target_new_frame": [round(tx, 3), round(ty, 3), round(tz, 3)]}))
    standoff = a.standoff if not a.horizontal else max(a.standoff, 0.15)
    pre = np.array([tx, ty, tz]) - off - standoff * d
    send(a.session, {"op": "grip", "arm": a.arm, "close": True, "why": "poke: close fingers"})
    if a.horizontal:
        yaw = float(np.arctan2(d[1], d[0]))             # base-frame quat: yaw toward target, then pitch 90 deg (approach axis -> forward)
        qz = np.array([0, 0, np.sin(yaw / 2), np.cos(yaw / 2)]); qy = np.array([0, np.sin(np.pi / 4), 0, np.cos(np.pi / 4)])
        x1, y1, z1, w1 = qz; x2, y2, z2, w2 = qy
        q = [w1*x2 + x1*w2 + y1*z2 - z1*y2, w1*y2 - x1*z2 + y1*w2 + z1*x2, w1*z2 + x1*y2 - y1*x2 + z1*w2, w1*w2 - x1*x2 - y1*y2 - z1*z2]
        send(a.session, {"op": "hand", "arm": a.arm, "quat": [float(v) for v in q], "why": "poke: gripper points at the marker"})
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
    push = a.push if not a.horizontal else standoff + 0.03
    r2 = send(a.session, {"op": "hand", "arm": a.arm, "forward": float(d[0] * push), "left": float(d[1] * push), "up": 0.0,
                          "max_steps": 90, "why": "poke: press (stops when blocked)"})
    r3 = send(a.session, {"op": "hand", "arm": a.arm, "forward": float(-d[0] * 0.10), "left": float(-d[1] * 0.10), "up": 0.0,
                          "why": "poke: retract (single press)"})
    send(a.session, {"op": "trunk", "why": "poke: upright"})
    print(json.dumps({"result": "pressed", "target": t, "approach_residual": r1["hand"]["residual_m"],
                      "press_residual": r2["hand"]["residual_m"], "panel": r3["images"]["panel"]}))


if __name__ == "__main__":
    main()
