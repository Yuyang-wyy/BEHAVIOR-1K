"""Demo-plan skill supervisor (v13): Comet executes a skill-sentence plan, legal signals gate each step.

The plan is the representative human demo's skill sentences for the task (task_docs/facts/NN_task.json,
demos.representative_episode), or a hand-written JSON list of {"prompt", "s"} (s = demo seconds).
Every 5 s checkpoint the supervisor checks the current step's completion signal (legal inputs only):
  move ...     : base moved and has been idle >= 3 s
  pick up ...  : number of hands holding something (EMPTY < width < OPEN) went up and stayed up 2 checks
  place ...    : a holding hand opened
  other        : after the demo duration, base idle >= 2 s and both arms still
A step over its budget gets the global prompt for a few checks (recovery skill), then one retry, then is skipped.
A place step with nothing held is skipped. After the plan, the global prompt runs to the time limit.

    plan_supervisor.py SESSION --task-facts task_docs/facts/25_clearing_food_from_table_into_fridge.json
    plan_supervisor.py SESSION --plan plan.json
"""
import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

CLIENT = Path(__file__).with_name("planner_client.py")
OPEN = 0.095        # jaw open
EMPTY = 0.008       # closed on nothing reads 0.0-0.008
CHECK_S = 5.0


def send(session, cmd):
    out = subprocess.run([sys.executable, str(CLIENT), str(session), "raw", json.dumps(cmd), "--timeout", "3600"],
                         capture_output=True, text=True)
    text = out.stdout.split("\nDONE")[0]
    try:
        return json.loads(text)
    except Exception:
        return {"ok": False, "error": (out.stdout + out.stderr)[-1500:], "episode_over": "episode already finished" in out.stdout + out.stderr}


def kind(prompt):
    p = prompt.lower()
    for k in ("move", "pick", "place"):
        if p.startswith(k):
            return k
    return "other"


def load_plan(args):
    if args.plan:
        steps = json.load(open(args.plan))
    else:
        d = json.load(open(args.task_facts))
        steps = [{"prompt": s["prompt"], "s": s["end_s"] - s["start_s"]} for s in d["demos"]["representative_episode"]["steps"]]
    # merge immediate repeats of a move (demos re-issue "move to X" for tiny adjustments)
    out = []
    for s in steps:
        if out and kind(s["prompt"]) == "move" and out[-1]["prompt"] == s["prompt"]:
            out[-1]["s"] += s["s"]
            continue
        out.append(dict(s))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("session", type=Path)
    ap.add_argument("--task-facts")
    ap.add_argument("--plan")
    ap.add_argument("--slack", type=float, default=2.5, help="budget = slack x demo seconds (+ 2 checks)")
    ap.add_argument("--fallback-checks", type=int, default=3)
    ap.add_argument("--retries", type=int, default=1)
    args = ap.parse_args()
    plan = load_plan(args)
    print(f"plan: {len(plan)} steps", flush=True)

    def holding(w):
        return sum(EMPTY < w[a] < OPEN for a in ("left", "right"))

    i, n_in, tries, moved, up_n = 0, 0, 0, False, 0
    fallback_left = 0
    stats = {"done": 0, "skipped": 0, "fallbacks": 0}
    reply = send(args.session, {"op": "global", "steps": 30, "why": "plan sup: warm up"})
    h0 = holding({a: reply["proprio"][f"gripper_{a}_width"] for a in ("left", "right")}) if reply.get("ok") else 0
    while reply.get("ok") and not reply.get("episode_over"):
        w = {a: reply["proprio"][f"gripper_{a}_width"] for a in ("left", "right")}
        mon = reply.get("monitor", {})
        step = reply.get("step")
        h = holding(w)
        if fallback_left > 0:
            fallback_left -= 1
            reply = send(args.session, {"op": "global", "why": "plan sup: recovery with the global prompt"})
            if fallback_left == 0:
                n_in, moved, up_n, h0 = 0, False, 0, holding({a: reply["proprio"][f"gripper_{a}_width"] for a in ("left", "right")}) if reply.get("ok") else h
            continue
        if i >= len(plan):
            reply = send(args.session, {"op": "global", "why": "plan sup: plan finished, global to the end"})
            continue
        st = plan[i]
        k = kind(st["prompt"])
        if n_in == 0:
            if k == "place" and h == 0:
                print(f"step {step}: skip [{i}] {st['prompt']} (nothing held)", flush=True)
                stats["skipped"] += 1
                i += 1
                continue
            h0, moved, up_n = h, False, 0
            print(f"step {step}: [{i}] {st['prompt']}  (try {tries + 1}, holding {h}, w {w['left']:.3f}/{w['right']:.3f})", flush=True)
        if mon.get("base_idle_s", 0) < 1:
            moved = True
        done = False
        if n_in > 0:
            if k == "move":
                done = moved and mon.get("base_idle_s", 0) >= 3
            elif k == "pick":
                up_n = up_n + 1 if h > h0 else 0
                done = up_n >= 2
            elif k == "place":
                done = h < h0
            else:
                done = (n_in * CHECK_S >= st["s"] and mon.get("base_idle_s", 0) >= 2
                        and max(reply["proprio"]["arm_left_speed"], reply["proprio"]["arm_right_speed"]) < 0.05)
        budget = math.ceil(args.slack * st["s"] / CHECK_S) + 2
        if done:
            print(f"step {step}: done [{i}] after {n_in} checks", flush=True)
            stats["done"] += 1
            i, n_in, tries = i + 1, 0, 0
            continue
        if n_in >= budget:
            if tries < args.retries:
                tries += 1
                stats["fallbacks"] += 1
                print(f"step {step}: [{i}] over budget ({budget}), global for {args.fallback_checks} then retry", flush=True)
                fallback_left = args.fallback_checks
                n_in = 0
                continue
            print(f"step {step}: skip [{i}] {st['prompt']} (over budget twice)", flush=True)
            stats["skipped"] += 1
            i, n_in, tries = i + 1, 0, 0
            continue
        n_in += 1
        reply = send(args.session, {"op": "skill", "prompt": st["prompt"], "why": f"plan sup: [{i}] {k}"})
    if reply.get("ok") is False and not reply.get("episode_over"):
        print("stopped:", reply.get("error", "")[-500:])
    send(args.session, {"op": "end"})
    print("done", json.dumps({**stats, "reached": i, "of": len(plan)}))


if __name__ == "__main__":
    main()
