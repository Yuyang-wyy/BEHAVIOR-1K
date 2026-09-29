"""Skill-first supervisor (v9): drives Comet with the task's trained skill sentences, no scripted takeovers.

Every 5 s checkpoint (sim paused) it reads legal signals only (jaw widths, base idle time, floor-object
detection from RGB-D) and picks the next skill sentence in the demo order:

  no bin held      : move to the trash can -> pick up the trash can from the floors
  bin held, hand free: move to the can of soda -> pick up the can of soda from the floors
  can held         : place the can of soda in the trash can
A skill that exceeds its time budget hands control to the global prompt for `fallback_checks`, then resumes.

    auto_supervisor.py SESSION --place-prompt "place the can of soda in the trash can"
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

CLIENT = Path(__file__).with_name("planner_client.py")
OPEN, RIM, CAN_LO = 0.095, 0.045, 0.05     # open > 0.095 ; bin rim / empty < 0.045 ; can 0.05-0.095
BIN_RIM = 0.02    # a hand on the bin rim reads ~0.005; a fridge/door handle reads ~0.04


def send(session, cmd):
    out = subprocess.run([sys.executable, str(CLIENT), str(session), "raw", json.dumps(cmd), "--timeout", "3600"],
                         capture_output=True, text=True)
    text = out.stdout.split("\nDONE")[0]
    try:
        return json.loads(text)
    except Exception:
        return {"ok": False, "error": (out.stdout + out.stderr)[-1500:], "episode_over": "episode already finished" in out.stdout + out.stderr}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("session", type=Path)
    ap.add_argument("--place-prompt", required=True)
    ap.add_argument("--obj", default="can of soda")
    ap.add_argument("--container", default="trash can")
    ap.add_argument("--reach-m", type=float, default=0.45)
    ap.add_argument("--budget", default="move=8,pick=6,place=5,binmove=10,binpick=8", help="checks per skill before fallback")
    ap.add_argument("--fallback-checks", type=int, default=3)
    ap.add_argument("--global-first", type=int, default=0, help="checkpoints of global prompt before the skill loop")
    ap.add_argument("--bin-global", action="store_true", help="leave bin pickup to the global prompt")
    ap.add_argument("--bin-width", type=float, default=BIN_RIM, help="jaw width below which a hand may be on the bin rim")
    ap.add_argument("--bin-hold-checks", type=int, default=1, help="consecutive closed checks before the hand counts as holding the bin")
    ap.add_argument("--scripted-place", action="store_true", help="when a can is held, use v5's scripted auto_place instead of the place skill")
    ap.add_argument("--grasp-fallback", action="store_true", help="when the pick skill times out, try v5's scripted auto_grasp first")
    ap.add_argument("--max-size", type=float, default=0.16)
    args = ap.parse_args()
    budget = {k: int(v) for k, v in (kv.split("=") for kv in args.budget.split(","))}
    S = {"binmove": f"move to the {args.container}",
         "binpick": f"pick up the {args.container} from the floors",
         "move": f"move to the {args.obj}",
         "pick": f"pick up the {args.obj} from the floors",
         "place": args.place_prompt}

    holder = None          # arm holding the bin
    unstucks = 0
    scripted_tried = False
    closed_n = {"left": 0, "right": 0}
    phase, n_in_phase, fallback_left, moved = None, 0, 0, False
    counts = {"placed": 0, "fallbacks": 0, "switches": 0}
    reply = send(args.session, {"op": "global", "why": "skill sup: start"})
    for _ in range(args.global_first):
        if not reply.get("ok") or reply.get("episode_over"):
            break
        reply = send(args.session, {"op": "continue"})

    while reply.get("ok") and not reply.get("episode_over"):
        w = {a: reply["proprio"][f"gripper_{a}_width"] for a in ("left", "right")}
        mon = reply.get("monitor", {})
        step = reply.get("step")
        # bin holder bookkeeping: a hand that closes onto a thin rim becomes the holder until it opens
        if holder and w[holder] > OPEN:
            print(f"step {step}: bin released/dropped by {holder}", flush=True)
            holder = None
        if holder is None:
            for a in ("left", "right"):
                closed_n[a] = closed_n[a] + 1 if w[a] < args.bin_width else 0
            rims = [a for a in ("left", "right") if closed_n[a] >= args.bin_hold_checks]
            if len(rims) == 1:
                holder = rims[0]
                print(f"step {step}: bin held by {holder}", flush=True)
        free = None if holder is None else ("left" if holder == "right" else "right")
        can_held = free is not None and CAN_LO < w[free] < OPEN

        # decide the wanted phase from state
        if holder is None:
            want = "global" if args.bin_global else ("binpick" if phase == "binpick" else "binmove")
            if want == "binmove" and phase == "binmove" and moved and mon.get("base_idle_s", 0) >= 3:
                want = "binpick"
        elif can_held:
            want = "place"
        else:
            want = "move" if phase not in ("move", "pick") else phase
            if phase == "place":
                if w[free] > OPEN:
                    counts["placed"] += 1
                print(f"step {step}: place ended, jaw {w[free]:.3f} (placed #{counts['placed']})", flush=True)
                want = "move"
            if want == "move":
                det = send(args.session, {"op": "detect"})
                hands = send(args.session, {"op": "fingers"})
                objs = [o for o in det.get("objects", []) if o.get("graspable")]
                if hands.get("ok") and w[free] > OPEN:
                    hx, hy, _ = hands[free]["eef"]
                    if any(((o["center"][0] - hx) ** 2 + (o["center"][1] - hy) ** 2) ** 0.5 < args.reach_m for o in objs):
                        want = "pick"
            if want == "pick" and phase == "pick" and w[free] < RIM and n_in_phase >= 3:
                want = "move"      # closed on nothing for a while: go find the can again

        # same stuck recovery as v5 (legal: head depth only), so v9 differs from v5 only in prompts vs takeovers
        if unstucks < 2 and mon.get("since_jaw_event_s", 0) > 40 and reply.get("seconds_left", 0) > 40:
            fs = send(args.session, {"op": "free_space"}).get("head_depth_median", {})
            if fs.get("center") is not None and fs["center"] < 0.6:
                unstucks += 1
                turn = 90 if (fs.get("left") or 0) >= (fs.get("right") or 0) else -90
                send(args.session, {"op": "base", "forward": -0.4, "why": f"skill sup: stuck facing a wall ({fs}); back off"})
                reply = send(args.session, {"op": "base", "turn_deg": turn, "why": "skill sup: turn toward open space"})
                print(f"step {reply.get('step')}: unstuck (head depth {fs}), turned {turn}", flush=True)
                phase, n_in_phase, moved, fallback_left = None, 0, False, 0
                continue
        if fallback_left > 0:
            fallback_left -= 1
            reply = send(args.session, {"op": "global", "why": "skill sup: fallback to global"})
            if fallback_left == 0:
                phase, n_in_phase, moved = None, 0, False
            continue
        if want != phase:
            counts["switches"] += 1
            print(f"step {step}: {phase} -> {want}  widths {w} holder {holder}", flush=True)
            phase, n_in_phase, moved = want, 0, False
        n_in_phase += 1
        if mon.get("base_idle_s", 0) < 1:
            moved = True
        if phase == "binmove" and n_in_phase > budget["binmove"]:
            print(f"step {step}: binmove over budget, try binpick", flush=True)
            phase, n_in_phase = "binpick", 1
        if phase == "pick" and args.grasp_fallback and n_in_phase > budget["pick"] and free and w[free] > OPEN:
            det = send(args.session, {"op": "detect"})
            hands = send(args.session, {"op": "fingers"})
            objs = [o for o in det.get("objects", []) if o.get("graspable")]
            if hands.get("ok") and objs and not (det.get("tilt_deg") or 0) > 30:
                hx, hy, _ = hands[free]["eef"]
                objs.sort(key=lambda o: (o["center"][0] - hx) ** 2 + (o["center"][1] - hy) ** 2)
                if ((objs[0]["center"][0] - hx) ** 2 + (objs[0]["center"][1] - hy) ** 2) ** 0.5 < args.reach_m:
                    counts["grasp_fallbacks"] = counts.get("grasp_fallbacks", 0) + 1
                    g = send(args.session, {"op": "auto_grasp", "arm": free, "target": objs[0],
                                            "why": "skill sup: pick skill timed out; scripted grasp"})
                    if g.get("ok"):
                        reply = g
                        print(f"step {g['step']}: auto_grasp {free} -> {g['auto_grasp'].get('result')}", flush=True)
                        phase, n_in_phase = None, 0
                        continue
        if phase != "global" and n_in_phase > budget.get(phase, 99):
            counts["fallbacks"] += 1
            print(f"step {step}: {phase} over budget, global for {args.fallback_checks}", flush=True)
            fallback_left = args.fallback_checks
            phase = "fallback"
            continue
        if phase == "place" and args.scripted_place and not scripted_tried:
            scripted_tried = True
            pl = send(args.session, {"op": "auto_place", "arm": free, "why": "skill sup: scripted place into the held bin"})
            if pl.get("ok"):
                reply = pl
                print(f"step {pl['step']}: auto_place {free} -> {pl['auto_place'].get('result')}", flush=True)
                continue
        if phase != "place":
            scripted_tried = False
        if phase == "global":
            reply = send(args.session, {"op": "global"})
        else:
            reply = send(args.session, {"op": "skill", "prompt": S[phase], "why": f"skill sup: {phase}"})
    if reply.get("ok") is False and not reply.get("episode_over"):
        print("stopped:", reply.get("error", "")[-500:])
    send(args.session, {"op": "end"})
    print("done", json.dumps(counts))


if __name__ == "__main__":
    main()
