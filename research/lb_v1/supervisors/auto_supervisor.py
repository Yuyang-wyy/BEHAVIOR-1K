"""v14 reflex supervisor: global task prompt all episode; ONE reflex for the "both hands full" stall.

Built for dispose_of_glass / dispose_of_batteries: the policy grabs the bin with one hand, an item with the other,
then carries both for minutes without releasing. Trigger (legal: jaw widths only, 2 consecutive 5 s checks):
  holder hand closed on a thin rim (width < RIM) and the other hand closed on an item (ITEM_LO < width < OPEN).
v12 fired on EMPTY jaws (closed-on-nothing reads ~0.008 < 0.09) and hurt; the item band excludes that.
Action: scripted `auto_place` of the item into the held container (demo release pose + mouth detection from head
depth), then back to the global prompt. `--grasp` adds v11's near-floor-object grasp reflex (trash structure).

    auto_supervisor.py SESSION --place-prompt "<unused>" [--stall-checks 2] [--max-places 6] [--grasp]
"""
import argparse, json, subprocess, sys
from pathlib import Path
CLIENT = Path(__file__).with_name("planner_client.py")
OPEN, RIM, ITEM_LO = 0.095, 0.045, 0.02


def send(session, cmd):
    out = subprocess.run([sys.executable, str(CLIENT), str(session), "raw", json.dumps(cmd), "--timeout", "3600"],
                         capture_output=True, text=True)
    try:
        return json.loads(out.stdout.split("\nDONE")[0])
    except Exception:
        return {"ok": False, "error": (out.stdout + out.stderr)[-800:], "episode_over": "episode already finished" in out.stdout + out.stderr}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("session", type=Path)
    ap.add_argument("--place-prompt", default="")
    ap.add_argument("--stall-checks", type=int, default=2)
    ap.add_argument("--max-places", type=int, default=6)
    ap.add_argument("--min-seconds-left", type=float, default=30.0)
    ap.add_argument("--grasp", action="store_true", help="also run v11's grasp reflex (free hand near a floor object while the other holds the rim)")
    ap.add_argument("--reach-m", type=float, default=0.45)
    a = ap.parse_args()
    S = a.session
    both_n, places, grasps = 0, 0, 0
    near = {"left": 0, "right": 0}
    reply = send(S, {"op": "global", "why": "v14: global prompt"})
    while reply.get("ok") and not reply.get("episode_over"):
        w = {h: reply["proprio"][f"gripper_{h}_width"] for h in ("left", "right")}
        rim = [h for h in w if w[h] < RIM]
        other = {"left": "right", "right": "left"}
        pair = [(h, other[h]) for h in rim if ITEM_LO < w[other[h]] < OPEN]
        both_n = both_n + 1 if pair else 0
        if pair and both_n >= a.stall_checks and places < a.max_places and reply.get("seconds_left", 0) > a.min_seconds_left:
            holder, item = pair[0]
            places += 1
            pl = send(S, {"op": "auto_place", "arm": item, "why": f"v14: {holder} holds the rim ({w[holder]:.3f}), {item} holds an item ({w[item]:.3f}) for {both_n} checks"})
            print(f"step {reply.get('step')}: auto_place {item} -> {pl.get('auto_place', {}).get('result')} widths {w}", flush=True)
            both_n = 0
            reply = pl if pl.get("ok") else reply
            if reply.get("ok") and not reply.get("episode_over"):
                reply = send(S, {"op": "global", "why": "v14: back to the global prompt"})
            continue
        if a.grasp and rim and grasps < 6 and reply.get("seconds_left", 0) > a.min_seconds_left:
            free = [other[h] for h in rim if w[other[h]] > OPEN]
            if free:
                det = send(S, {"op": "detect"}); hands = send(S, {"op": "fingers"})
                objs = [o for o in det.get("objects", []) if o.get("graspable")] if (det.get("tilt_deg") or 0) <= 30 else []
                f = free[0]; target = None
                if hands.get("ok") and objs:
                    hx, hy, _ = hands[f]["eef"]
                    close = sorted(objs, key=lambda o: (o["center"][0] - hx) ** 2 + (o["center"][1] - hy) ** 2)
                    if ((close[0]["center"][0] - hx) ** 2 + (close[0]["center"][1] - hy) ** 2) ** 0.5 < a.reach_m:
                        near[f] += 1
                        if near[f] >= a.stall_checks:
                            target = close[0]
                    else:
                        near[f] = 0
                if target is not None:
                    grasps += 1; near[f] = 0
                    g = send(S, {"op": "auto_grasp", "arm": f, "target": target, "why": "v14: free hand near a floor object while the other holds the rim"})
                    print(f"step {g.get('step')}: auto_grasp {f} -> {g.get('auto_grasp', {}).get('result')}", flush=True)
                    reply = g if g.get("ok") else reply
                    if reply.get("ok") and not reply.get("episode_over"):
                        reply = send(S, {"op": "global", "why": "v14: back to global"})
                    continue
        reply = send(S, {"op": "continue"})
    send(S, {"op": "end"})
    print("done", json.dumps({"places": places, "grasps": grasps}))


if __name__ == "__main__":
    main()
