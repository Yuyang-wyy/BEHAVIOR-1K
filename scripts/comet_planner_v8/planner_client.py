"""Send one command to a planner_episode.py session and print the result.

Supervised loop (every command runs one 5 s checkpoint unless --steps is given):
    planner_client.py SESSION continue                       # keep the current prompt, keep Comet's queued actions
    planner_client.py SESSION global  --why "back to the task"
    planner_client.py SESSION skill "place the rose in the vase" --why "rose held above vase"
    planner_client.py SESSION base --forward 0.3 --left 0 --turn 45   # planner drives the base; arms held still
    planner_client.py SESSION look [--step-deg 45 --count 8 --no-return]  # turn in place, one head image per stop

Older form:

    planner_client.py SESSION run "pick up the rose from the bottom cabinet" --steps 600 --until grasp_any
    planner_client.py SESSION run --task-prompt --steps 900          # task sentence
    planner_client.py SESSION observe | status
    planner_client.py SESSION end [--stop]                           # default: run out the clock (official)
    planner_client.py SESSION raw '{"op": "status"}'
"""
import argparse
import json
import sys
import time
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("session", type=Path)
    ap.add_argument("op", choices=("continue", "global", "skill", "base", "look", "grip", "hand", "save", "load", "point", "reach", "fingers", "objinfo", "detect", "auto_grasp", "auto_place", "trunk", "container", "free_space", "config", "floor_container", "drop_in", "run", "observe", "status", "end", "raw"))
    ap.add_argument("text", nargs="?", help="prompt for run, JSON for raw")
    ap.add_argument("--steps", type=int, default=None)
    ap.add_argument("--why", default="")
    ap.add_argument("--forward", type=float, default=0.0)
    ap.add_argument("--left", type=float, default=0.0)
    ap.add_argument("--turn", type=float, default=0.0, help="degrees, counter-clockwise positive")
    ap.add_argument("--step-deg", type=float, default=45.0)
    ap.add_argument("--count", type=int, default=8)
    ap.add_argument("--no-return", action="store_true")
    ap.add_argument("--arm", choices=("left", "right"), default="right")
    ap.add_argument("--up", type=float, default=0.0)
    ap.add_argument("--cam", default="head")
    ap.add_argument("--u", type=float, default=0.0, help="pixel column in the native-resolution camera image")
    ap.add_argument("--v", type=float, default=0.0, help="pixel row")
    ap.add_argument("--above", type=float, default=0.10)
    ap.add_argument("--no-trunk", action="store_true", help="hand/reach: arm joints only (keep the other held object still)")
    ap.add_argument("--yaw", type=float, default=0.0)
    ap.add_argument("--pitch", type=float, default=0.0)
    ap.add_argument("--open", action="store_true", help="grip: open instead of close")
    ap.add_argument("--until", nargs="*", default=[])
    ap.add_argument("--task-prompt", action="store_true", help="run with the task sentence")
    ap.add_argument("--label", default="")
    ap.add_argument("--stop", action="store_true", help="end: score now instead of running out the clock")
    ap.add_argument("--timeout", type=float, default=7200)
    args = ap.parse_args()

    if args.op in ("continue", "global"):
        cmd = {"op": args.op, "until": args.until}
    elif args.op == "skill":
        if not args.text:
            sys.exit("skill needs a prompt")
        cmd = {"op": "skill", "prompt": args.text, "until": args.until}
    elif args.op == "base":
        cmd = {"op": "base", "forward": args.forward, "left": args.left, "turn_deg": args.turn}
    elif args.op == "hand":
        cmd = {"op": "hand", "arm": args.arm, "forward": args.forward, "left": args.left, "up": args.up,
               "yaw_deg": args.yaw, "pitch_deg": args.pitch, "trunk": not args.no_trunk}
    elif args.op == "point":
        cmd = {"op": "point", "cam": args.cam, "u": args.u, "v": args.v}
    elif args.op == "reach":
        cmd = {"op": "reach", "arm": args.arm, "cam": args.cam, "u": args.u, "v": args.v, "above": args.above,
               "forward_off": args.forward, "left_off": args.left, "trunk": not args.no_trunk}
    elif args.op in ("save", "load"):
        cmd = {"op": args.op, "name": args.text or "snap"}
    elif args.op == "grip":
        cmd = {"op": "grip", "arm": args.arm, "close": not args.open}
    elif args.op == "look":
        cmd = {"op": "look", "step_deg": args.step_deg, "count": args.count, "return": not args.no_return}
    elif args.op == "run":
        if not args.text and not args.task_prompt:
            sys.exit("run needs a prompt or --task-prompt")
        cmd = {"op": "run", "prompt": None if args.task_prompt else args.text, "steps": args.steps or 300,
               "until": args.until, "label": args.label}
    elif args.op == "end":
        cmd = {"op": "end", "finish": "stop" if args.stop else "run_out"}
    elif args.op == "raw":
        cmd = json.loads(args.text)
    else:
        cmd = {"op": args.op}
    if args.steps is not None and args.op in ("continue", "global", "skill"):
        cmd["steps"] = args.steps
    if args.why:
        cmd["why"] = args.why

    s = args.session
    if not (s / "READY").exists():
        sys.exit(f"session not ready: {s}")
    if (s / "DONE").exists():
        sys.exit("episode already finished: " + (s / "DONE").read_text())
    index = len(list((s / "cmd").glob("*.json")))
    tmp = s / "cmd" / f".{index:04d}.tmp"
    tmp.write_text(json.dumps(cmd))
    tmp.rename(s / "cmd" / f"{index:04d}.json")
    out = s / "out" / f"{index:04d}.json"
    deadline = time.time() + args.timeout
    while time.time() < deadline:
        if out.exists():
            time.sleep(0.1)
            print(out.read_text())
            if (s / "DONE").exists():
                print("DONE", (s / "DONE").read_text())
            return
        if (s / "DONE").exists() and not out.exists():
            time.sleep(1)
            if not out.exists():
                sys.exit("episode finished before the command ran: " + (s / "DONE").read_text())
        time.sleep(0.5)
    sys.exit("timed out")


if __name__ == "__main__":
    main()
