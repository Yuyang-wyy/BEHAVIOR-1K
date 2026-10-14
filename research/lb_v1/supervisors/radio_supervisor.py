"""turning_on_radio supervisor (v14): the policy approaches (and usually picks up) the radio reliably but fails the
press (5-step fingertip contact with an 11 mm sphere on the control cap). Legal inputs only.

Every 5 s checkpoint: head RGB -> largest saturated-red component = radio body (3D via the `points` op); the control
cap = small round red blob with a dark surround within 0.24 m of the body centre (heuristics from
aspire_radio/press_marker_policy.py). When the cap is within `--reach` of the base and the base is idle, press it with a
free hand: poke_marker.py --pick u,v --color red --normal (closed fingertip, approach along the face normal, push,
retract). Success ends the episode; otherwise hand back to the policy and retry up to --max-press times.
"""
import argparse, json, subprocess, sys
from pathlib import Path
import numpy as np
import cv2

HERE = Path(__file__).parent
Z_OFF = -0.004     # both dev successes came at cap - 3 mm (finger link extends below the finger-mid point)
CLIENT = HERE / "planner_client.py"


def send(session, cmd, timeout=900):
    out = subprocess.run([sys.executable, str(CLIENT), str(session), "raw", json.dumps(cmd), "--timeout", str(timeout)],
                         capture_output=True, text=True)
    try:
        return json.loads(out.stdout.split("\nDONE")[0])
    except Exception:
        return {"ok": False, "error": (out.stdout + out.stderr)[-600:], "episode_over": "episode already finished" in out.stdout + out.stderr}


def red_mask(bgr):
    b, g, r = bgr[..., 0].astype(int), bgr[..., 1].astype(int), bgr[..., 2].astype(int)
    return ((r > 145) & (r > 2 * g) & (r > 2 * b)).astype(np.uint8)


def points3d(session, uv, cam="head"):
    if not uv:
        return []
    r = send(session, {"op": "points", "cam": cam, "uv": [[int(u), int(v)] for u, v in uv]})
    return [p for p in r.get("points", []) if p]


def find_cap(session, head_png, cam="head"):
    """Returns dict(uv, p, body_range) or None."""
    img = cv2.imread(head_png)
    if img is None:
        return None
    H, W = img.shape[:2]
    m = red_mask(img)
    n, lab, stats, cent = cv2.connectedComponentsWithStats(m)
    comps = [(i, stats[i][4]) for i in range(1, n)]
    if not comps:
        return None
    big = max(comps, key=lambda c: c[1])
    if big[1] < 300:
        return None
    ys, xs = np.nonzero(lab == big[0])
    sel = np.linspace(0, len(xs) - 1, min(60, len(xs))).astype(int)
    body_pts = points3d(session, [(xs[i], ys[i]) for i in sel], cam)
    if len(body_pts) < 8:
        return None
    body = np.median(np.array(body_pts), axis=0)
    best = {"score": -1, "uv": None, "p": None, "span": None, "body_range": round(float(np.hypot(body[0], body[1])), 2),
            "body": [round(float(v), 3) for v in body], "cam": cam}
    for i, area in comps:
        if area < 10 or i == big[0] and area > 2500:
            pass
        x, y, w, h, a = stats[i]
        if a < 10 or max(w, h) > 110:
            continue
        if x < 2 or y < 2 or x + w > W - 3 or y + h > H - 3:
            continue
        aspect = min(w, h) / max(w, h); fill = a / float(w * h)
        if aspect < 0.45 or fill < 0.5:
            continue
        cy, cx = cent[i][1], cent[i][0]
        rad = float(max(w, h))
        y0, y1 = max(0, int(cy - 2.4 * rad)), min(H, int(cy + 2.4 * rad) + 1)
        x0, x1 = max(0, int(cx - 2.4 * rad)), min(W, int(cx + 2.4 * rad) + 1)
        gy, gx = np.ogrid[y0:y1, x0:x1]
        dist = np.hypot(gx - cx, gy - cy); ring = (dist >= 0.85 * rad) & (dist <= 2.2 * rad)
        dark = img[y0:y1, x0:x1].max(axis=2) < 115
        surround = float(dark[ring].mean()) if ring.any() else 0.0
        if surround < 0.12:
            continue
        ys2, xs2 = np.nonzero(lab == i)
        sel2 = np.linspace(0, len(xs2) - 1, min(12, len(xs2))).astype(int)
        pts = points3d(session, [(xs2[j], ys2[j]) for j in sel2], cam)
        if len(pts) < 4:
            continue
        P = np.array(pts); p = np.median(P, axis=0)
        if np.linalg.norm(p - body) > 0.24 or abs(p[2] - body[2]) > 0.12:
            continue
        span = float(np.max(np.percentile(P, 90, axis=0) - np.percentile(P, 10, axis=0)))
        if not 0.002 <= span <= 0.06:
            continue
        score = 2.0 * surround + fill + aspect
        if score > best["score"]:
            best = {"score": score, "uv": [int(cx), int(cy)], "p": [round(float(v), 3) for v in p], "span": round(span, 3),
                    "body_range": round(float(np.hypot(body[0], body[1])), 2), "body": [round(float(v), 3) for v in body], "cam": cam}
    return best


def face_normal(session, uv, tz):
    """Horizontal outward normal of the face around pixel uv, fitted from 8 depth neighbours (poke_marker's method)."""
    u0, v0 = uv; P = []
    for du in (-24, 0, 24):
        for dv in (-24, 0, 24):
            if du == 0 and dv == 0:
                continue
            q = send(session, {"op": "point", "cam": "head", "u": u0 + du, "v": v0 + dv}).get("point_base")
            if q:
                P.append(q)
    P = np.array(P) if P else np.zeros((0, 3))
    P = P[np.abs(P[:, 2] - tz) < 0.2] if len(P) else P
    if len(P) < 4:
        return None
    c = P.mean(0); n = np.linalg.svd(P - c)[2][-1]; n[2] = 0.0; n /= (np.linalg.norm(n) + 1e-9)
    return n


def fingertip(session, arm):
    fg = send(session, {"op": "fingers"})[arm]
    return np.array(fg["eef"]) + np.array(fg["finger_mid_minus_eef"])


def goto_tip(session, arm, target, why, tries=5, tol=0.012):
    """Move until the FINGER MID (not the wrist) is at target; re-read the finger offset after every move because
    the wrist orientation changes over long reaches."""
    err = None
    for k in range(tries):
        tip = fingertip(session, arm); d = target - tip; err = float(np.linalg.norm(d))
        if err < tol:
            break
        r = send(session, {"op": "hand", "arm": arm, "forward": float(d[0]), "left": float(d[1]), "up": float(d[2]), "why": f"{why} (try {k}, err {err:.3f})"})
        if r.get("episode_over"):
            return r, err
    return None, float(np.linalg.norm(target - fingertip(session, arm)))


def press(session, arm, cap, n, standoff, push, hold_steps, lateral):
    """Closed fingertip: pre-pose standoff in front of the cap (+lateral offset in the face plane), push in 3 small
    steps re-aimed at the cap, hold, retract."""
    t = np.array(cap["p"], dtype=float)
    side = np.array([-n[1], n[0], 0.0])
    t = t + lateral[0] * side + np.array([0, 0, lateral[1] + Z_OFF])   # toggle sphere sits ~11 mm below the red cap centre (calibrated 2026-10-13)
    if n @ np.array([t[0], t[1], 0.0]) < 0:
        n = -n
    send(session, {"op": "grip", "arm": arm, "close": True, "why": "radio: close fingers"})
    r, err = goto_tip(session, arm, t - 0.10 * n, "radio: waypoint 10 cm out", tries=3, tol=0.03)   # keep the arm off the radio on the way in
    if r is not None:
        return r, "over"
    r, err = goto_tip(session, arm, t - standoff * n, "radio: pre-press")
    if r is not None:
        return r, "over"
    if err > 0.025:
        return None, f"unreachable ({err:.3f})"
    last = None
    for k in range(4):                                   # push past the cap surface in 1 cm steps; contact persists while the radio slides
        r = send(session, {"op": "hand", "arm": arm, "forward": float(n[0] * push), "left": float(n[1] * push), "up": 0.0, "max_steps": 40, "why": f"radio: press step {k}"})
        if r.get("episode_over"):
            return r, "over"
        last = r
    r3 = send(session, {"op": "grip", "arm": arm, "close": True, "steps": hold_steps, "why": "radio: hold the contact"})
    if r3.get("episode_over"):
        return r3, "over"
    tip = fingertip(session, arm)
    print(f"   tip after press {tip.round(3).tolist()} vs cap {t.round(3).tolist()} (dist {np.linalg.norm(tip - t):.3f})", flush=True)
    r4 = send(session, {"op": "hand", "arm": arm, "forward": float(-n[0] * 0.08), "left": float(-n[1] * 0.08), "up": 0.0, "why": "radio: retract"})
    return r4, "pressed"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("session", type=Path)
    ap.add_argument("--reach", type=float, default=1.0, help="press when the radio body is within this range")
    ap.add_argument("--drive-reach", type=float, default=1.4, help="drive toward the radio when it is within this range but beyond --reach")
    ap.add_argument("--max-press", type=int, default=8)
    ap.add_argument("--push", type=float, default=0.01)
    ap.add_argument("--standoff", type=float, default=0.04)
    ap.add_argument("--hold-steps", type=int, default=25)
    ap.add_argument("--min-seconds-left", type=float, default=6.0)
    a = ap.parse_args()
    S = a.session
    offsets = [(0.0, 0.0), (0.0, -0.007), (0.0, 0.007), (0.007, 0.0), (-0.007, 0.0), (0.0, -0.014), (0.0, 0.014), (0.0, 0.0)]
    presses, drives, blind, putdowns = 0, 0, 0, 0
    reply = send(S, {"op": "global", "why": "radio sup: policy approaches the radio"})
    while reply.get("ok") and not reply.get("episode_over"):
        imgs = reply.get("images", {})
        det = None
        for cam in ("head", "left_wrist", "right_wrist"):
            if imgs.get(cam):
                d = find_cap(S, imgs[cam], cam)
                if d and d["uv"] is not None:
                    det = d; break
                if d and det is None:
                    det = d                     # body only; keep looking for a cap in the other cameras
        w = {h: reply["proprio"][f"gripper_{h}_width"] for h in ("left", "right")}
        left = reply.get("seconds_left", 0)
        if det:
            print(f"step {reply['step']}: {'cap ' + str(det['uv']) if det['uv'] else 'body only'} ({det['cam']}) at {det['p']} body range {det['body_range']}", flush=True)
        if det and det["uv"] is not None and det["body_range"] <= a.reach and presses < a.max_press and left > a.min_seconds_left:
            free = [h for h in ("left", "right") if w[h] > 0.095] or sorted(w, key=lambda h: -w[h])
            hands = send(S, {"op": "fingers"})
            if hands.get("ok") and len(free) > 1:
                free.sort(key=lambda h: np.linalg.norm(np.array(hands[h]["eef"]) - np.array(det["p"])))
            arm = free[0]
            n = np.array([det["p"][0], det["p"][1], 0.0]); n /= (np.linalg.norm(n) + 1e-9)
            r, res = press(S, arm, det, n, a.standoff, a.push, a.hold_steps, offsets[presses % len(offsets)])
            presses += 1
            print(f"step {reply['step']}: press #{presses} {arm} offset {offsets[(presses - 1) % len(offsets)]} -> {res}", flush=True)
            if r is not None and r.get("episode_over"):
                reply = r; break
            # stay in control: re-observe and press again while the cap is visible (handing back lets the policy wander)
            reply = send(S, {"op": "observe"})
            reply.update({"ok": True, "seconds_left": left - 12, "proprio": reply.get("proprio") or {"gripper_left_width": w["left"], "gripper_right_width": w["right"]}})
            if res.startswith("unreachable"):
                send(S, {"op": "trunk", "why": "radio: upright"})
                reply = send(S, {"op": "global", "steps": 60, "why": "radio sup: policy re-approaches"})
            continue
        if det and det["body_range"] > 0.45 and (det["uv"] is None or det["body_range"] > a.reach) and det["body_range"] <= a.drive_reach and drives < 4 and left > a.min_seconds_left + 6:
            drives += 1
            yaw = float(np.degrees(np.arctan2(det["body"][1], det["body"][0])))
            if abs(yaw) > 8:
                send(S, {"op": "base", "turn_deg": yaw, "gentle": True, "why": "radio sup: face the radio"})
            fwd = max(0.0, det["body_range"] - 0.65)
            reply = send(S, {"op": "base", "forward": fwd, "gentle": True, "why": f"radio sup: close in ({det['body_range']} m)"}) if fwd > 0.05 else send(S, {"op": "observe"})
            if "proprio" not in reply:
                reply.update({"ok": True, "seconds_left": left - 3, "proprio": {"gripper_left_width": w["left"], "gripper_right_width": w["right"]}})
            print(f"step {reply.get('step')}: faced/drove toward the radio (yaw {yaw:.0f})", flush=True)
            continue
        hidden = det is not None and det["uv"] is None and det["body_range"] < 0.7
        held = any(w[h] < 0.09 for h in w)
        blind = blind + 1 if hidden else 0
        if hidden and held and blind >= 2 and putdowns < 2 and left > 20:
            putdowns += 1
            print(f"step {reply['step']}: radio close but cap hidden and a hand closed -> ask the policy to put it down", flush=True)
            reply = send(S, {"op": "skill", "prompt": "place the radio on the coffee table", "steps": 240, "why": "radio sup: put the radio down so the control is visible"})
            blind = 0
            continue
        reply = send(S, {"op": "continue"})
    send(S, {"op": "end"})
    print("done", json.dumps({"presses": presses, "drives": drives}))


if __name__ == "__main__":
    main()
