"""Skill-prompt supervisor for container-sorting tasks (first target: sorting_vegetables), v13.

Comet alone (v2 ckpt) walks each vegetable from the floor basket to the counter one or two at a time and
scores ~3/13 by the time limit. Every demo instead carries the basket to the counter and sorts from it.
This supervisor imposes that strategy with Comet's own trained skill sentences, gated on legal signals only
(jaw widths, base idle time, time left); every 5 s checkpoint it picks the next sentence:

  no basket held        : move to the wicker basket -> pick up the wicker basket from the floors
  basket held, not moved: move to the mixing bowl (until the base stops after moving)
  basket held, free hand: pick up the <item> from the wicker basket   (item names tried in turn)
  item held             : place the <item> in the mixing bowl
  all names fail        : place the wicker basket on the floors, then the next basket
A skill over its budget falls back to the global prompt for a few checks (the recovery skill).

    veg_supervisor.py SESSION [--items "broccoli,leek,vidalia onion,bok choy,sweet corn"]
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

CLIENT = Path(__file__).with_name("planner_client.py")
try:
    import cv2
    import numpy as np
except ImportError:          # bowl reflex needs the behavior env python
    cv2 = None
OPEN = 0.095        # jaw open
EMPTY = 0.008       # closed on nothing reads 0.0-0.008


def send(session, cmd):
    out = subprocess.run([sys.executable, str(CLIENT), str(session), "raw", json.dumps(cmd), "--timeout", "3600"],
                         capture_output=True, text=True)
    text = out.stdout.split("\nDONE")[0]
    try:
        return json.loads(text)
    except Exception:
        return {"ok": False, "error": (out.stdout + out.stderr)[-1500:], "episode_over": "episode already finished" in out.stdout + out.stderr}


def find_bowls(session, head_png, max_range=1.3):
    """Red mixing bowls on the counter from the head camera (legal: RGB + depth via the `points` op).
    Red pixels are back-projected; xy cells that also hold red points above 1.25 m are the red wall, not bowls."""
    im = cv2.imread(head_png)
    if im is None:
        return []
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    m = ((hsv[..., 0] < 8) | (hsv[..., 0] > 172)) & (hsv[..., 1] > 150) & (hsv[..., 2] > 70)
    vs, us = np.nonzero(m[::10, ::10])
    if len(us) == 0:
        return []
    uv = [[int(u * 10), int(v * 10)] for u, v in zip(us, vs)]
    if len(uv) > 200:
        uv = [uv[i] for i in np.linspace(0, len(uv) - 1, 200).astype(int)]
    pts = send(session, {"op": "points", "cam": "head", "uv": uv}).get("points", [])
    P = [(tuple(p), tuple(q)) for p, q in zip(pts, uv) if p]
    wall = {(round(p[0] / 0.08), round(p[1] / 0.08)) for p, _ in P if p[2] > 1.25}
    cand = [(p, q) for p, q in P if 0.8 < p[2] < 1.25 and (p[0] ** 2 + p[1] ** 2) ** 0.5 < max_range
            and (round(p[0] / 0.08), round(p[1] / 0.08)) not in wall]
    clusters = []
    for p, q in cand:
        for c in clusters:
            if ((c["x"] - p[0]) ** 2 + (c["y"] - p[1]) ** 2) ** 0.5 < 0.15:
                c["pts"].append((p, q))
                c["x"] = float(np.mean([a[0][0] for a in c["pts"]])); c["y"] = float(np.mean([a[0][1] for a in c["pts"]]))
                break
        else:
            clusters.append({"x": p[0], "y": p[1], "pts": [(p, q)]})
    merged = True                    # one bowl often splits into fragments 0.1-0.2 m apart: merge them
    while merged:
        merged = False
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                a, b = clusters[i], clusters[j]
                if ((a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2) ** 0.5 < 0.22:
                    a["pts"] += b["pts"]
                    a["x"] = float(np.mean([q[0][0] for q in a["pts"]])); a["y"] = float(np.mean([q[0][1] for q in a["pts"]]))
                    clusters.pop(j)
                    merged = True
                    break
            if merged:
                break
    bowls = []
    for c in clusters:
        zs = [a[0][2] for a in c["pts"]]
        spread = max(((a[0][0] - c["x"]) ** 2 + (a[0][1] - c["y"]) ** 2) ** 0.5 for a in c["pts"])
        # bowl rims measured at z 1.05-1.10; the red backsplash strip at counter level reaches >= 1.16 and is wide
        if len(c["pts"]) < 6 or not (0.98 <= max(zs) <= 1.12) or spread > 0.25:     # a bowl rim stands ~0.1-0.17 m above the counter; red onions in the basket sit lower
            continue
        bowls.append({"xy": [round(c["x"], 3), round(c["y"], 3)], "z_top": round(max(zs), 3), "z_low": round(min(zs), 3),
                      "n": len(c["pts"])})
    return bowls


def scripted_place(session, arm, bowl, hands, trunk=False):
    """Carry the held item over the bowl centre and release it 10 cm above the rim (base stays put)."""
    def eef():
        return np.array(send(session, {"op": "fingers"})[arm]["eef"])

    def goto(t, why, tries=4):
        for _ in range(tries):
            d = t - eef()
            if np.linalg.norm(d) < 0.03:
                break
            send(session, {"op": "hand", "arm": arm, "forward": float(d[0]), "left": float(d[1]), "up": float(d[2]), "trunk": trunk, "why": why})
        return float(np.linalg.norm(t - eef()))
    top = bowl["z_top"] + 0.18
    e = eef()
    goto(np.array([e[0], e[1], max(e[2], top)]), "veg sup: lift above bowl height", tries=2)
    err = goto(np.array([bowl["xy"][0], bowl["xy"][1], top]), "veg sup: over the bowl", tries=3)
    if err > 0.06:
        # arm could not get over the bowl (counter/basket in the way): keep the item, let Comet's place skill try
        return {"ok": False}, round(err, 3), None
    low = goto(np.array([bowl["xy"][0], bowl["xy"][1], bowl["z_top"] + 0.10]), "veg sup: lower into bowl", tries=2)
    send(session, {"op": "grip", "arm": arm, "close": False, "why": "veg sup: release over bowl"})
    e = eef()
    r = send(session, {"op": "hand", "arm": arm, "forward": 0.0, "left": 0.0, "up": 0.12, "trunk": trunk, "why": "veg sup: clear"})
    return r, round(err, 3), round(low, 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("session", type=Path)
    ap.add_argument("--container", default="wicker basket")
    ap.add_argument("--target", default="mixing bowl")
    ap.add_argument("--items", default="broccoli,leek,vidalia onion,bok choy,sweet corn")
    ap.add_argument("--hold-checks", type=int, default=2, help="checks a hand must stay closed to count as holding the basket")
    ap.add_argument("--budget", default="cmove=8,cpick=10,tmove=6,pick=4,place=4,cdrop=5", help="checks per skill")
    ap.add_argument("--fallback-checks", type=int, default=3)
    ap.add_argument("--bowl-reflex", action="store_true", help="scripted place over the nearest red bowl after each pick")
    ap.add_argument("--reach", type=float, default=0.85, help="max hand-to-bowl distance for the scripted place")
    ap.add_argument("--fails-per-item", type=int, default=2, help="failed pick attempts before trying the next name")
    args = ap.parse_args()
    budget = {k: int(v) for k, v in (kv.split("=") for kv in args.budget.split(","))}
    items = [s.strip() for s in args.items.split(",")]
    C, T = args.container, args.target

    holder = None
    closed_n = {"left": 0, "right": 0}
    phase, n_in, moved = None, 0, False
    fallback_left = 0
    item_i, fails = 0, {}
    place_tried = False
    armed, opens = False, 0         # pick phase: free jaw seen open / scripted opens issued
    tmoved = False                  # carried the basket to the bowls already (this basket)
    counts = {"placed": 0, "picks": 0, "pick_fail": 0, "fallbacks": 0, "baskets": 0}
    reply = send(args.session, {"op": "skill", "prompt": f"move to the {C}", "why": "veg sup: start"})
    phase, n_in = "cmove", 1
    while reply.get("ok") and not reply.get("episode_over"):
        w = {a: reply["proprio"][f"gripper_{a}_width"] for a in ("left", "right")}
        mon = reply.get("monitor", {})
        step = reply.get("step")
        if mon.get("base_idle_s", 0) < 1:
            moved = True
        # basket holder bookkeeping
        if holder and w[holder] > OPEN:
            print(f"step {step}: basket released by {holder}", flush=True)
            holder, tmoved = None, False
        if holder is None and phase in ("cpick", "cmove", "fallback", "global"):
            for a in ("left", "right"):
                closed_n[a] = closed_n[a] + 1 if EMPTY < w[a] < OPEN else 0
            got = [a for a in ("left", "right") if closed_n[a] >= args.hold_checks]
            if got:
                holder = got[0] if len(got) == 1 else min(got, key=lambda a: w[a])
                counts["baskets"] += 1
                item_i, fails = 0, {}
                print(f"step {step}: basket held by {holder} (w {w[holder]:.3f})", flush=True)
        free = None if holder is None else ("left" if holder == "right" else "right")

        # wanted phase from state
        if holder is None:
            want = phase if phase in ("cmove", "cpick") else "cmove"
            if want == "cmove" and phase == "cmove" and moved and mon.get("base_idle_s", 0) >= 3:
                want = "cpick"
        elif not tmoved:
            want = "tmove"
            if phase == "tmove" and moved and mon.get("base_idle_s", 0) >= 3:
                tmoved = True
                want = "pick"
        elif phase == "pick" and not armed:
            want = "pick"           # free jaw not seen open yet in this pick: closed on the basket, not on an item
        elif w[free] < OPEN and phase in ("pick", "place"):
            if phase == "pick" and n_in >= 2 and w[free] <= EMPTY:
                want = "pick_empty"
            else:
                want = "place"
                if phase == "pick":
                    counts["picks"] += 1
                    print(f"step {step}: picked {items[item_i]} (w {w[free]:.3f})", flush=True)
        elif phase == "place" and w[free] > OPEN:
            counts["placed"] += 1
            print(f"step {step}: placed {items[item_i]} #{counts['placed']}", flush=True)
            want = "pick"
        elif phase == "cdrop":
            want = "cdrop"
        else:
            want = "pick"

        if want == "pick_empty":
            # closed on nothing: count a failure, let the jaw reopen under the next pick attempt
            fails[item_i] = fails.get(item_i, 0) + 1
            counts["pick_fail"] += 1
            want = "pick"
            n_in = 0
        if fallback_left > 0:
            fallback_left -= 1
            reply = send(args.session, {"op": "global", "why": "veg sup: fallback to global"})
            if fallback_left == 0:
                phase, n_in, moved = None, 0, False
            continue
        if want != phase:
            armed, opens = False, 0
            print(f"step {step}: {phase} -> {want}  widths {w} holder {holder} item {items[item_i] if holder else '-'}", flush=True)
            phase, n_in, moved = want, 0, False
        n_in += 1
        if phase == "pick" and n_in > budget["pick"]:
            fails[item_i] = fails.get(item_i, 0) + 1
            n_in = 1
        if phase == "pick" and fails.get(item_i, 0) >= args.fails_per_item:
            nxt = [i for i in range(len(items)) if fails.get(i, 0) < args.fails_per_item]
            if nxt:
                item_i = nxt[0]
                print(f"step {step}: next item {items[item_i]}", flush=True)
            else:
                print(f"step {step}: no item name works; put the basket down", flush=True)
                phase, n_in = "cdrop", 1
        if phase == "cmove" and n_in > budget["cmove"]:
            phase, n_in = "cpick", 1
        if phase == "tmove" and n_in > budget["tmove"]:
            tmoved, phase, n_in = True, "pick", 1
        if phase == "cdrop" and n_in > budget["cdrop"]:
            # basket did not leave the hand: treat it as dropped by opening via the global prompt
            counts["fallbacks"] += 1
            fallback_left = args.fallback_checks
            phase = "fallback"
            continue
        if phase in ("cpick", "place") and n_in > budget[phase]:
            counts["fallbacks"] += 1
            print(f"step {step}: {phase} over budget, global for {args.fallback_checks}", flush=True)
            fallback_left = args.fallback_checks
            if phase == "place":
                fails[item_i] = fails.get(item_i, 0) + 1
            phase = "fallback"
            continue
        if phase == "pick" and free and w[free] > OPEN:
            armed = True
        if phase == "pick" and free and not armed:
            if opens < 2:
                # reflex: Comet often carries the basket with both hands; open the non-holder hand so it can pick
                opens += 1
                reply = send(args.session, {"op": "grip", "arm": free, "close": False,
                                            "why": "veg sup: free hand is closed on the basket; open it to pick"})
                print(f"step {step}: opened {free} hand (was {w[free]:.3f})", flush=True)
                continue
        if phase == "place" and args.bowl_reflex and cv2 is not None and n_in == 1 and not place_tried:
            place_tried = True
            head = reply.get("images", {}).get("head")
            bowls = find_bowls(args.session, head) if head else []
            hands = send(args.session, {"op": "fingers"})
            if bowls and hands.get("ok"):
                bx_, by_, _ = hands[holder]["eef"]
                bowls = [b for b in bowls if ((b["xy"][0] - bx_) ** 2 + (b["xy"][1] - by_) ** 2) ** 0.5 > 0.25]
            if bowls and hands.get("ok"):
                hx, hy, _ = hands[free]["eef"]
                bowls.sort(key=lambda b: (b["xy"][0] - hx) ** 2 + (b["xy"][1] - hy) ** 2)
                b = bowls[0]
                dist = ((b["xy"][0] - hx) ** 2 + (b["xy"][1] - hy) ** 2) ** 0.5
                if dist < args.reach:
                    try:
                        r, err, low = scripted_place(args.session, free, b, hands)
                    except (KeyError, TypeError) as e:     # harness error reply (e.g. episode just ended)
                        r, err, low = {"ok": False}, f"error {e}", None
                    if low is None:
                        counts["scripted_abort"] = counts.get("scripted_abort", 0) + 1
                        print(f"step {step}: scripted place aborted, hand {err} m from over-bowl point; place skill", flush=True)
                    else:
                        counts["scripted"] = counts.get("scripted", 0) + 1
                        print(f"step {step}: scripted place {free} into bowl {b} (hand {dist:.2f} m away, err {err}/{low})", flush=True)
                        if r.get("ok"):
                            reply = r
                        continue
                print(f"step {step}: nearest bowl {dist:.2f} m from hand, use the place skill", flush=True)
            else:
                print(f"step {step}: no bowl seen ({len(bowls)}), use the place skill", flush=True)
        if phase != "place":
            place_tried = False
        prompt = {"cmove": f"move to the {C}", "cpick": f"pick up the {C} from the floors",
                  "tmove": f"move to the {T}", "pick": f"pick up the {items[item_i]} from the {C}",
                  "place": f"place the {items[item_i]} in the {T}", "cdrop": f"place the {C} on the floors"}[phase]
        reply = send(args.session, {"op": "skill", "prompt": prompt, "why": f"veg sup: {phase}"})
    if reply.get("ok") is False and not reply.get("episode_over"):
        print("stopped:", reply.get("error", "")[-500:])
    send(args.session, {"op": "end"})
    print("done", json.dumps(counts))


if __name__ == "__main__":
    main()
