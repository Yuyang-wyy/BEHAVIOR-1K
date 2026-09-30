"""Rule-based supervisor for a planner_episode.py session (legal inputs only: RGB-D, proprio, time).

Global task prompt by default, one decision every 5 s (the sim is paused while deciding).
If a small floor object stays within reach of an open, free hand for `stall_checks` consecutive
checkpoints, take over that arm with auto_grasp, then prompt the place skill until the jaw
reopens (or `place_checks` checkpoints), then return to the global prompt.

    auto_supervisor.py SESSION --place-prompt "place the can of soda in the trash can"
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

CLIENT = Path(__file__).with_name("planner_client.py")


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
    ap.add_argument("--reach-m", type=float, default=0.45)
    ap.add_argument("--stall-checks", type=int, default=2)
    ap.add_argument("--place-checks", type=int, default=3)
    ap.add_argument("--max-grasps", type=int, default=6)
    ap.add_argument("--max-size", type=float, default=0.16, help="largest horizontal extent of a graspable object (m)")
    ap.add_argument("--min-seconds-left", type=float, default=15.0)
    ap.add_argument("--scripted-place", action="store_true",
                    help="after a held grasp, put the object into the container held by the other hand by micro-control")
    args = ap.parse_args()

    near_count = {"left": 0, "right": 0}
    grasps = 0
    unstucks = 0
    reply = send(args.session, {"op": "global", "why": "auto: start with the global prompt"})
    while reply.get("ok") and not reply.get("episode_over"):
        widths = {a: reply["proprio"][f"gripper_{a}_width"] for a in ("left", "right")}
        # v11: only grasp a can with a free hand while the OTHER hand holds the bin (closed on the thin rim);
        # grasping cans before the bin is held left both hands full and nothing could be placed (lb 303/307).
        other = {"left": "right", "right": "left"}
        free = [a for a in ("left", "right") if widths[a] > 0.095 and widths[other[a]] < 0.045]
        target, arm = None, None
        if free and grasps < args.max_grasps and reply.get("seconds_left", 0) > args.min_seconds_left:
            det = send(args.session, {"op": "detect"})
            hands = send(args.session, {"op": "fingers"})
            if det.get("tilt_deg") is not None and det["tilt_deg"] > 30:
                print(f"step {det.get('step')}: robot tilted {det['tilt_deg']} deg, no takeover", flush=True)
                det = {"objects": []}
            objs = [o for o in det.get("objects", []) if o.get("graspable")]
            for a in ("left", "right"):
                if a not in free or not hands.get("ok"):
                    near_count[a] = 0
                    continue
                hx, hy, _ = hands[a]["eef"]
                close = [o for o in objs if ((o["center"][0] - hx) ** 2 + (o["center"][1] - hy) ** 2) ** 0.5 < args.reach_m]
                near_count[a] = near_count[a] + 1 if close else 0
                if close and near_count[a] >= args.stall_checks and target is None:
                    close.sort(key=lambda o: (o["center"][0] - hx) ** 2 + (o["center"][1] - hy) ** 2)
                    target, arm = close[0], a
        if target is not None:
            grasps += 1
            near_count = {"left": 0, "right": 0}
            g = send(args.session, {"op": "auto_grasp", "arm": arm, "target": target,
                                    "why": f"auto: {arm} hand near a floor object for {args.stall_checks} checks without a grasp"})
            if not g.get("ok"):
                reply = g
                break
            result = g["auto_grasp"].get("result")
            print(f"step {g['step']}: auto_grasp {arm} -> {result}", flush=True)
            reply = g
            placed = False
            if result == "held" and args.scripted_place:
                other = "right" if arm == "left" else "left"
                if g["proprio"][f"gripper_{other}_width"] < 0.045:     # other jaw closed on a thin rim (the bin), not a can (0.06-0.085)
                    pl = send(args.session, {"op": "auto_place", "arm": arm,
                                             "why": "auto: place into the container held by the other hand"})
                    if pl.get("ok"):
                        reply = pl
                        placed = pl["auto_place"].get("result") == "released"
                        print(f"step {pl['step']}: auto_place {arm} -> {pl['auto_place'].get('result')}", flush=True)
                if placed and reply.get("ok") and not reply.get("episode_over"):
                    reply = send(args.session, {"op": "global", "why": "auto: back to the global prompt"})
            if result == "held" and not placed and reply.get("ok") and not reply.get("episode_over"):
                for _ in range(args.place_checks):
                    reply = send(args.session, {"op": "skill", "prompt": args.place_prompt,
                                                "why": "auto: place the object just grasped"})
                    if not reply.get("ok") or reply.get("episode_over"):
                        break
                    if reply["proprio"][f"gripper_{arm}_width"] > 0.095:
                        break
                if reply.get("ok") and not reply.get("episode_over"):
                    reply = send(args.session, {"op": "global", "why": "auto: back to the global prompt"})
            if result != "held" and reply.get("ok") and not reply.get("episode_over"):
                reply = send(args.session, {"op": "global", "why": f"auto: grasp {result}; back to global"})
            continue
        mon = reply.get("monitor", {})
        if unstucks < 2 and mon.get("since_jaw_event_s", 0) > 40 and reply.get("seconds_left", 0) > 40:
            fs = send(args.session, {"op": "free_space"}).get("head_depth_median", {})
            if fs.get("center") is not None and fs["center"] < 0.6:
                unstucks += 1
                turn = 90 if (fs.get("left") or 0) >= (fs.get("right") or 0) else -90
                holding = False
                send(args.session, {"op": "base", "forward": -0.4, "gentle": holding,
                                    "why": f"auto: stuck facing a wall ({fs}); back off"})
                reply = send(args.session, {"op": "base", "turn_deg": turn, "gentle": holding, "why": "auto: turn toward open space"})
                print(f"step {reply.get('step')}: unstuck (head depth {fs}), turned {turn}", flush=True)
                if reply.get("ok") and not reply.get("episode_over"):
                    reply = send(args.session, {"op": "global", "why": "auto: resume after unstuck"})
                continue
        reply = send(args.session, {"op": "continue"})
    if reply.get("ok") is False and not reply.get("episode_over"):
        print("stopped:", reply.get("error", "")[-500:])
    send(args.session, {"op": "end"})
    print("done, grasps", grasps)


if __name__ == "__main__":
    main()
