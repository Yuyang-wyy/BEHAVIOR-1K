"""sorting_vegetables v13g: Comet keeps its own strategy (global prompt: it walks 1-2 vegetables per trip from the floor
baskets to the counter, ~5 grasps / 3 scored per episode alone); one code reflex fixes the measured loss at the bowls:
when a hand has held something (EMPTY < width < 0.09) for 2 checks and a red bowl is within reach of that hand,
carry it over the bowl and release 10 cm above the rim (only if the hand gets within 6 cm; else Comet continues).
Same-bowl preference (sticky) keeps groups together."""
import argparse
import json

import cv2
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from veg_supervisor import find_bowls, scripted_place, send, OPEN, EMPTY  # noqa: E402


def wicker_frac(png):
    """Fraction of wicker-coloured pixels in a wrist image: ~0.4-0.6 when the hand holds the basket, < 0.25 for a vegetable."""
    im = cv2.imread(png) if png else None
    if im is None:
        return 1.0
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    h, s, v = (hsv[..., i].astype(int) for i in range(3))
    return float(((h >= 8) & (h <= 24) & (s >= 35) & (s <= 150) & (v >= 110) & (v <= 235)).mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("session", type=Path)
    ap.add_argument("--reach", type=float, default=0.8)
    ap.add_argument("--hold-checks", type=int, default=2)
    ap.add_argument("--home-bowl", action="store_true",
                    help="put every item in one bowl, tracked in the odometry frame (groups score only inside one bowl)")
    ap.add_argument("--drive-home", action="store_true",
                    help="when holding a vegetable and the home bowl is out of reach (< 2.5 m), drive to it (once per item)")
    ap.add_argument("--max-wicker", type=float, default=0.30, help="skip when the holding hand's wrist view is basket")
    args = ap.parse_args()
    S = args.session
    st = {"fired": 0, "placed": 0, "aborted": 0}
    held = {"left": 0, "right": 0}
    tried_at = {"left": -1, "right": -1}
    drove_for = {"left": -1, "right": -1}     # one home-bowl drive per held item
    sticky = None
    home = None             # home bowl xy in the odometry frame

    def to_odom(xy, od):
        c, s_ = math.cos(od[2]), math.sin(od[2])
        return [od[0] + c * xy[0] - s_ * xy[1], od[1] + s_ * xy[0] + c * xy[1]]

    def to_base(xy, od):
        dx, dy = xy[0] - od[0], xy[1] - od[1]
        c, s_ = math.cos(od[2]), math.sin(od[2])
        return [c * dx + s_ * dy, -s_ * dx + c * dy]
    reply = send(S, {"op": "global", "why": "veg g: Comet's own strategy"})
    while reply.get("ok") and not reply.get("episode_over"):
        w = {a: reply["proprio"][f"gripper_{a}_width"] for a in ("left", "right")}
        for a in held:
            held[a] = held[a] + 1 if EMPTY < w[a] < 0.09 else 0
            if w[a] > OPEN:
                tried_at[a] = -1
                drove_for[a] = -1
        cand = [a for a in held if held[a] >= args.hold_checks and tried_at[a] < 0]
        # v13g fired on the basket (Comet carries it under the global prompt; rim widths overlap vegetables) and
        # dumped it at the bowls: only fire when the wrist camera does not see wicker filling the view
        imgs = reply.get("images", {})
        cand = [a for a in cand if wicker_frac(imgs.get(f"{a}_wrist")) < args.max_wicker]
        if cand and reply.get("seconds_left", 0) > 20:
            bowls = find_bowls(S, reply["images"]["head"]) if reply.get("images") else []
            hands = send(S, {"op": "fingers"})
            for a in cand:
                if not bowls or not hands.get("ok"):
                    break
                hx, hy, hz = hands[a]["eef"]
                other = hands["left" if a == "right" else "right"]["eef"]
                bs = [b for b in bowls if math.hypot(b["xy"][0] - other[0], b["xy"][1] - other[1]) > 0.2]
                if not bs:
                    continue
                b = min(bs, key=lambda b: math.hypot(b["xy"][0] - hx, b["xy"][1] - hy))
                od = reply.get("odom")
                if args.home_bowl and od is not None and home is not None:
                    pred = to_base(home, od)
                    hb = min(bs, key=lambda b: math.hypot(b["xy"][0] - pred[0], b["xy"][1] - pred[1]))
                    seen = math.hypot(hb["xy"][0] - pred[0], hb["xy"][1] - pred[1]) <= 0.3
                    if seen:
                        b = hb
                        pred = hb["xy"]
                    if not seen or math.hypot(pred[0] - hx, pred[1] - hy) > args.reach:
                        r = math.hypot(*pred)
                        if args.drive_home and drove_for[a] < 0 and r < 2.5:
                            drove_for[a] = reply["step"]
                            yaw = math.degrees(math.atan2(pred[1], pred[0]))
                            send(S, {"op": "base", "turn_deg": yaw, "gentle": True, "why": "veg g: face the home bowl"})
                            reply = send(S, {"op": "base", "forward": max(0.0, r - 0.65), "gentle": True,
                                             "why": f"veg g: drive to the home bowl ({r:.2f} m)"})
                            st["drives"] = st.get("drives", 0) + 1
                            print(f"step {reply.get('step')}: drove to home bowl (was {[round(x, 2) for x in pred]}, {r:.2f} m)", flush=True)
                            break
                        print(f"step {reply['step']}: home bowl not in reach (pred {[round(x, 2) for x in pred]}); wait", flush=True)
                        continue
                elif sticky is not None:
                    b2 = min(bs, key=lambda b: math.hypot(b["xy"][0] - sticky[0], b["xy"][1] - sticky[1]))
                    if math.hypot(b2["xy"][0] - hx, b2["xy"][1] - hy) < args.reach:
                        b = b2
                d = math.hypot(b["xy"][0] - hx, b["xy"][1] - hy)
                if d > args.reach:
                    continue
                tried_at[a] = reply["step"]
                st["fired"] += 1
                try:
                    r, err, low = scripted_place(S, a, b, hands, trunk=True)
                except (KeyError, TypeError) as e:
                    r, err, low = {"ok": False}, f"error {e}", None
                if low is None:
                    st["aborted"] += 1
                    print(f"step {reply['step']}: {a} place aborted ({err}) bowl {b['xy']}", flush=True)
                else:
                    st["placed"] += 1
                    sticky = b["xy"]
                    if args.home_bowl and home is None and reply.get("odom") is not None:
                        home = to_odom(b["xy"], reply["odom"])
                        print(f"step {reply['step']}: home bowl at odom {[round(x, 2) for x in home]}", flush=True)
                    elif args.home_bowl and reply.get("odom") is not None:
                        home = [0.7 * h + 0.3 * n for h, n in zip(home, to_odom(b["xy"], reply["odom"]))]   # refine
                    print(f"step {reply['step']}: {a} item -> bowl {b['xy']} (hand {d:.2f} m, err {err}/{low})", flush=True)
                    if r.get("ok"):
                        reply = r
                break
            if reply.get("ok") and not reply.get("episode_over"):
                reply = send(S, {"op": "global", "why": "veg g: back to Comet"})
            continue
        reply = send(S, {"op": "continue"})
    send(S, {"op": "end"})
    print("done", json.dumps(st))


if __name__ == "__main__":
    main()
