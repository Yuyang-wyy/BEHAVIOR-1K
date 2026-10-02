"""sorting_vegetables supervisor v13d: Claude-designed strategy, Comet skills for fetching/picking, code reflexes
for the failure points measured in v13a/b (task_docs/supervision/README.md):

  * "move to the mixing bowl" often stops ~2 m short (base idle != arrived)  -> APPROACH: find the red bowls in the
    head camera (RGB + depth) and drive the holonomic base until the nearest bowl is ~0.6 m ahead.
  * a basket held in one hand tilts while Comet picks with the other and spills (i12), and picking from the held,
    low-hanging basket stalls for minutes (i14)  -> SETDOWN: put the basket on a depth-verified free counter spot
    next to the bowls; it stays level and both hands are free.
  * the place skill drops items on the counter  -> bowl reflex: carry the picked item over the nearest bowl and
    release 10 cm above the rim (only if the hand gets within 6 cm, else the place skill).

  FETCH  : move to the wicker basket -> pick up the wicker basket from the floors   (Comet)
  CARRY  : move to the mixing bowl                                                   (Comet)
  APPROACH, SETDOWN                                                                  (code)
  SORT   : pick up the <item> from the wicker basket (Comet)  -> bowl reflex (code)
  then the next basket.
"""
import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from veg_supervisor import find_bowls, scripted_place, send, OPEN, EMPTY  # noqa: E402

import cv2  # noqa: E402


def head_points(session, head_png, stride=16, v_min=200):
    im = cv2.imread(head_png)
    H, W = im.shape[:2]
    uv = [[u, v] for v in range(v_min, H, stride) for u in range(0, W, stride)]
    pts = send(session, {"op": "points", "cam": "head", "uv": uv}).get("points", [])
    return [(np.array(p), q) for p, q in zip(pts, uv) if p]


def counter_spot(session, head_png, bowls, near_xy, clear=0.16):
    """Free flat counter spot (base frame) away from the bowls, nearest to near_xy. Legal: head depth only."""
    P = head_points(session, head_png)
    # counter height from the ring just outside each bowl (the basket and arms sit at counter height too)
    ctop = float(np.median([b["z_low"] for b in bowls])) - 0.02      # lowest red point of a bowl ~ counter + 2 cm
    try:
        json.dump({"bowls": bowls, "near": [float(x) for x in near_xy], "ctop": ctop,
                   "points": [[float(x) for x in p] + q for p, q in P]},
                  open(Path(session) / f"spot_debug_{len(list(Path(session).glob('spot_debug_*')))}.json", "w"))
    except Exception:
        pass
    flat = [p for p, _ in P if abs(p[2] - ctop) < 0.02]
    allp = [p for p, _ in P]
    best = None
    for c in flat:
        r = math.hypot(c[0], c[1])
        if not (0.4 < r < 0.85):
            continue
        if any(math.hypot(c[0] - b["xy"][0], c[1] - b["xy"][1]) < 0.30 for b in bowls):
            continue
        nb = [p for p in allp if math.hypot(p[0] - c[0], p[1] - c[1]) < clear]
        if len(nb) < 4 or any(abs(p[2] - ctop) > 0.025 for p in nb):
            continue        # something on it, or the counter edge
        d = math.hypot(c[0] - near_xy[0], c[1] - near_xy[1])
        if best is None or d < best[0]:
            best = (d, c)
    return (best[1] if best else None), ctop


def basket_contents(session, head_png, holder_eef, radius=0.35):
    """Count onion-pink and corn-yellow pixels whose 3D point is within `radius` of the basket hand (legal: RGB-D).
    Onion: red hue at moderate saturation (bowls are > 200); corn: hue 18-32 with saturation > 140 (leek/bok choy < 70)."""
    im = cv2.imread(head_png)
    if im is None:
        return {}
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    h, s_, v = hsv[..., 0].astype(int), hsv[..., 1].astype(int), hsv[..., 2].astype(int)
    masks = {"onion": ((h <= 5) | (h >= 170)) & (s_ > 60) & (s_ < 170) & (v > 150),
             "corn": (h >= 18) & (h <= 32) & (s_ > 140) & (v > 180)}
    out = {}
    for k, m in masks.items():
        vs, us = np.nonzero(m[::4, ::4])
        uv = [[int(u * 4), int(vv * 4)] for u, vv in zip(us, vs)]
        if len(uv) > 60:
            uv = [uv[i] for i in np.linspace(0, len(uv) - 1, 60).astype(int)]
        if not uv:
            out[k] = 0
            continue
        pts = send(session, {"op": "points", "cam": "head", "uv": uv}).get("points", [])
        out[k] = sum(1 for p in pts if p and math.dist(p, holder_eef) < radius)
    return out


def hand_goto(session, arm, t, why, tries=3):
    e = None
    for _ in range(tries):
        e = np.array(send(session, {"op": "fingers"})[arm]["eef"])
        d = t - e
        if np.linalg.norm(d) < 0.03:
            break
        send(session, {"op": "hand", "arm": arm, "forward": float(d[0]), "left": float(d[1]), "up": float(d[2]),
                       "trunk": False, "why": why})
    e = np.array(send(session, {"op": "fingers"})[arm]["eef"])
    return float(np.linalg.norm(t - e))


def holding(w):
    return [a for a in ("left", "right") if EMPTY < w[a] < OPEN]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("session", type=Path)
    ap.add_argument("--items", default="broccoli,leek,vidalia onion,bok choy,sweet corn")
    ap.add_argument("--reach", type=float, default=0.85)
    ap.add_argument("--setdown", choices=["none", "floor"], default="none",
                    help="floor: put the basket down at the counter first (v13e; slower picks, bowls out of view)")
    args = ap.parse_args()
    S = args.session
    items = [s.strip() for s in args.items.split(",")]
    C, T = "wicker basket", "mixing bowl"
    st = {"placed": 0, "scripted": 0, "aborted": 0, "picks": 0, "approach": 0, "setdown": 0, "setdown_fail": 0, "baskets": 0}

    def skill(prompt, why):
        return send(S, {"op": "skill", "prompt": prompt, "why": f"veg d: {why}"})

    def alive(r):
        return r.get("ok") and not r.get("episode_over")

    def widths(r):
        return {a: r["proprio"][f"gripper_{a}_width"] for a in ("left", "right")}

    reply = {"ok": True}
    while alive(reply):
        # ---------- FETCH: Comet picks up a basket ----------
        holder, closed, n, moved = None, {"left": 0, "right": 0}, 0, False
        reply = skill(f"move to the {C}", "fetch")
        while alive(reply) and holder is None and n < 30:
            n += 1
            w, mon = widths(reply), reply.get("monitor", {})
            for a in ("left", "right"):
                closed[a] = closed[a] + 1 if EMPTY < w[a] < OPEN else 0
            got = [a for a in ("left", "right") if closed[a] >= 2]
            if got:
                holder = got[0]
                break
            moved = moved or mon.get("base_idle_s", 0) < 1
            prompt = f"pick up the {C} from the floors" if (n > 8 or (moved and mon.get("base_idle_s", 0) >= 3)) else f"move to the {C}"
            reply = skill(prompt, "fetch")
        if not alive(reply):
            break
        if holder is None:
            reply = send(S, {"op": "global", "why": "veg d: basket fetch failed; global"})
            continue
        st["baskets"] += 1
        print(f"step {reply['step']}: basket held by {holder}", flush=True)
        # ---------- CARRY: Comet walks to the bowls ----------
        n, moved = 0, False
        reply = skill(f"move to the {T}", "carry")
        while alive(reply) and n < 8:
            n += 1
            mon = reply.get("monitor", {})
            moved = moved or mon.get("base_idle_s", 0) < 1
            if moved and mon.get("base_idle_s", 0) >= 3:
                break
            reply = skill(f"move to the {T}", "carry")
        # ---------- APPROACH (code): drive until the nearest bowl is ~0.6 m ahead ----------
        bowls = []
        for k in range(3):
            if not alive(reply):
                break
            bowls = find_bowls(S, reply["images"]["head"], max_range=4.0)
            if not bowls:
                reply = send(S, {"op": "base", "turn_deg": 45, "gentle": True, "why": "veg d: look for the bowls"})
                continue
            b = min(bowls, key=lambda b: math.hypot(*b["xy"]))
            r = math.hypot(*b["xy"])
            print(f"step {reply['step']}: nearest bowl {b['xy']} ({r:.2f} m)", flush=True)
            if r < 0.85:
                break
            yaw = math.degrees(math.atan2(b["xy"][1], b["xy"][0]))
            if abs(yaw) > 8:
                send(S, {"op": "base", "turn_deg": yaw, "gentle": True, "why": "veg d: face the bowl"})
            reply = send(S, {"op": "base", "forward": r - 0.65, "gentle": True,
                             "why": f"veg d: drive to the bowl ({r:.2f} m away)"})
            st["approach"] += 1
        if not alive(reply):
            break
        # ---------- SETDOWN (code): basket onto a free counter spot ----------
        w = widths(reply)
        free = "left" if holder == "right" else "right"
        basket_down = False
        if args.setdown == "floor" and w[holder] < OPEN:
            # no free counter space within reach (bowls fill it, i11 depth dump), so put the basket on the floor right
            # here at the counter with Comet's own demo skill: it cannot tilt/spill in the hand and both hands are free
            if w[free] < OPEN:
                send(S, {"op": "grip", "arm": free, "close": False, "why": "veg d: free the second hand"})
            for k in range(8):
                reply = skill(f"place the {C} on the floors", "set the basket down at the counter")
                if not alive(reply) or widths(reply)[holder] > OPEN:
                    break
            if alive(reply) and widths(reply)[holder] < OPEN:
                # skill did not let go: lower the hand toward the floor and open (code)
                e = np.array(send(S, {"op": "fingers"})[holder]["eef"])
                hand_goto(S, holder, np.array([e[0], e[1], 0.35]), "veg d: lower basket to the floor", tries=2)
                reply = send(S, {"op": "grip", "arm": holder, "close": False, "why": "veg d: release basket on the floor"})
            if alive(reply):
                basket_down = widths(reply)[holder] > OPEN
                st["setdown" if basket_down else "setdown_fail"] += 1
                print(f"step {reply['step']}: basket down={basket_down}", flush=True)
        # ---------- SORT ----------
        fails, item_i, idle_picks = {}, 0, 0
        sticky = None                   # bowl xy used for this basket: keep its items together (groups score per bowl)
        if not basket_down and alive(reply):
            hands = send(S, {"op": "fingers"})
            obs = send(S, {"op": "observe"})
            cnt = basket_contents(S, obs["images"]["head"], hands[holder]["eef"]) if hands.get("ok") else {}
            names = list(items)
            if cnt.get("onion", 0) >= 2:
                names = ["vidalia onion", "broccoli", "leek"]
            elif cnt.get("corn", 0) >= 2:
                names = ["sweet corn", "bok choy"]
            items = names + [x for x in items if x not in names]
            for i in range(len(names), len(items)):
                fails[i] = 1            # other basket's names: one try only
            print(f"step {obs.get('step')}: basket contents {cnt} -> names {names}", flush=True)
        while alive(reply):
            w = widths(reply)
            hands_free = [a for a in ("left", "right") if (basket_down or a != holder)]
            if not hands_free:
                break
            # one pick attempt: up to 4 checks of the pick skill until a free hand closes on something
            got, armed = None, {a: w[a] > OPEN for a in hands_free}
            for _ in range(4):
                reply = skill(f"pick up the {items[item_i]} from the {C}", f"pick {items[item_i]}")
                if not alive(reply):
                    break
                w = widths(reply)
                for a in hands_free:
                    armed[a] = armed[a] or w[a] > OPEN
                closed = [a for a in hands_free if armed[a] and EMPTY < w[a] < OPEN]
                if not basket_down and w[holder] > OPEN:
                    break               # basket dropped
                if closed:
                    got = closed[0]
                    break
                for a in hands_free:    # Comet sometimes keeps the second hand on the basket rim
                    if not armed[a] and w[a] < OPEN:
                        send(S, {"op": "grip", "arm": a, "close": False, "why": "veg d: open the hand for picking"})
            if not alive(reply):
                break
            if not basket_down and w[holder] > OPEN:
                print(f"step {reply['step']}: basket dropped", flush=True)
                break
            if got is None:
                fails[item_i] = fails.get(item_i, 0) + 1
                nxt = [i for i in range(len(items)) if fails.get(i, 0) < 2]
                if not nxt:
                    print(f"step {reply['step']}: no item name picks any more; next basket", flush=True)
                    break
                item_i = nxt[0]
                continue
            st["picks"] += 1
            print(f"step {reply['step']}: picked {items[item_i]} with {got} (w {w[got]:.3f})", flush=True)
            # bowl reflex
            done = False
            obs = send(S, {"op": "observe"})
            hands = send(S, {"op": "fingers"})
            bowls = find_bowls(S, obs["images"]["head"]) if obs.get("images") else []
            if not bowls:
                # picking from the floor basket leaves the head looking down; straighten up to see the counter
                tr = send(S, {"op": "trunk", "why": "veg d: look up for the bowls"})
                if tr.get("images"):
                    bowls = find_bowls(S, tr["images"]["head"])
                    reply = tr if tr.get("ok") else reply
                hands = send(S, {"op": "fingers"})
                print(f"step {tr.get('step')}: trunk up, bowls {[b['xy'] for b in bowls]}", flush=True)
            if bowls and hands.get("ok"):
                hx, hy, _ = hands[got]["eef"]
                b = min(bowls, key=lambda b: math.hypot(b["xy"][0] - hx, b["xy"][1] - hy))
                if sticky is not None:
                    bs = min(bowls, key=lambda b: math.hypot(b["xy"][0] - sticky[0], b["xy"][1] - sticky[1]))
                    if math.hypot(bs["xy"][0] - sticky[0], bs["xy"][1] - sticky[1]) < 0.25 and \
                            math.hypot(bs["xy"][0] - hx, bs["xy"][1] - hy) < args.reach:
                        b = bs
                if math.hypot(b["xy"][0] - hx, b["xy"][1] - hy) < args.reach:
                    try:
                        r, err, low = scripted_place(S, got, b, hands, trunk=basket_down)
                    except (KeyError, TypeError) as e:
                        r, err, low = {"ok": False}, f"error {e}", None
                    if low is not None:
                        sticky = b["xy"]
                        st["scripted"] += 1
                        done = True
                        reply = r if r.get("ok") else reply
                        print(f"step {reply.get('step')}: scripted place {got} -> bowl {b['xy']} (err {err}/{low})", flush=True)
                    else:
                        st["aborted"] += 1
                        print(f"step {obs.get('step')}: scripted place aborted ({err}), bowl {b['xy']}, hand {[round(x, 2) for x in hands[got]['eef']]}", flush=True)
            if not done:
                print(f"step {reply.get('step')}: place skill (bowls {[b['xy'] for b in bowls]}, hand "
                      f"{[round(x, 2) for x in hands[got]['eef']] if hands.get('ok') else '?'})", flush=True)
                for _ in range(4):
                    reply = skill(f"place the {items[item_i]} in the {T}", "place skill")
                    if not alive(reply) or widths(reply)[got] > OPEN:
                        break
            if alive(reply) and widths(reply)[got] > OPEN:
                st["placed"] += 1
        if not alive(reply):
            break
        if not basket_down and widths(reply)[holder] < OPEN:
            reply = skill(f"place the {C} on the floors", "basket done")
    send(S, {"op": "end"})
    print("done", json.dumps(st))


if __name__ == "__main__":
    main()
