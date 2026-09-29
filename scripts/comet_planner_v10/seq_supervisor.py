"""Generic skill sequencer (v10): walk the task's representative demo skill list with Comet skill prompts.

Every 5 s checkpoint (sim paused) the current skill is kept or advanced from legal signals only:
  move to ...  : done when the base moved and then stayed idle >= 2 s
  pick up ...  : done when a hand that was open at the start of the skill is closed for 2 checks
  place ...    : done when a hand that was closed at the start of the skill opens
  other verbs  : done after their demo duration x budget factor, or when a hand opens / closes
A skill that exceeds its budget (demo mean duration x factor) gets `fallback_checks` of the global prompt and one
retry, then it is skipped. Places with no closed hand and picks with no free hand are skipped.
After the last skill: the global prompt until the end. Stuck recovery identical to v5/v9.

    seq_supervisor.py SESSION --task setting_mousetraps
"""
import argparse
import glob
import json
import subprocess
import sys
from pathlib import Path

CLIENT = Path(__file__).with_name("planner_client.py")
FACTS = Path(__file__).resolve().parents[3] / "task_docs" / "facts"
OPEN = 0.095


def send(session, cmd):
    out = subprocess.run([sys.executable, str(CLIENT), str(session), "raw", json.dumps(cmd), "--timeout", "3600"],
                         capture_output=True, text=True)
    text = out.stdout.split("\nDONE")[0]
    try:
        return json.loads(text)
    except Exception:
        return {"ok": False, "error": (out.stdout + out.stderr)[-1500:], "episode_over": "episode already finished" in out.stdout + out.stderr}


def verb(p):
    for v in ("move to", "pick up", "place", "open", "close", "turn on", "turn off", "push", "pour", "wipe", "put"):
        if p.startswith(v):
            return v
    return "other"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("session", type=Path)
    ap.add_argument("--task", required=True)
    ap.add_argument("--place-prompt", default=None, help="ignored (batch-script compatibility)")
    ap.add_argument("--factor", type=float, default=2.0, help="skill budget = demo mean seconds x factor")
    ap.add_argument("--min-checks", type=int, default=3)
    ap.add_argument("--fallback-checks", type=int, default=3)
    ap.add_argument("--global-first", type=int, default=0)
    args = ap.parse_args()

    f = glob.glob(str(FACTS / f"*_{args.task}.json"))
    facts = json.load(open(f[0]))
    demos = facts["demos"]
    skills = [s["prompt"] for s in demos["representative_episode"]["steps"]]
    rep = {s["prompt"]: s["end_s"] - s["start_s"] for s in demos["representative_episode"]["steps"]}
    vmean = demos.get("verb_mean_seconds", {})

    def budget(p):
        secs = next((v for k, v in vmean.items() if p.startswith(k.split()[0])), None) or rep.get(p, 20)
        return max(args.min_checks, int(round(secs * args.factor / 5)))

    print("skills:", json.dumps(skills), flush=True)
    k, n, tries, moved, fallback_left, unstucks = 0, 0, 0, False, 0, 0
    start_w = None
    counts = {"done": 0, "timeouts": 0, "skipped": 0}
    reply = send(args.session, {"op": "global", "why": "seq: start"})
    for _ in range(args.global_first):
        if reply.get("ok") and not reply.get("episode_over"):
            reply = send(args.session, {"op": "continue"})
    closed_n = {"left": 0, "right": 0}
    while reply.get("ok") and not reply.get("episode_over"):
        w = {a: reply["proprio"][f"gripper_{a}_width"] for a in ("left", "right")}
        for a in w:
            closed_n[a] = closed_n[a] + 1 if w[a] < OPEN else 0
        mon = reply.get("monitor", {})
        step = reply.get("step")

        if unstucks < 2 and mon.get("since_jaw_event_s", 0) > 40 and reply.get("seconds_left", 0) > 40:
            fs = send(args.session, {"op": "free_space"}).get("head_depth_median", {})
            if fs.get("center") is not None and fs["center"] < 0.6:
                unstucks += 1
                turn = 90 if (fs.get("left") or 0) >= (fs.get("right") or 0) else -90
                send(args.session, {"op": "base", "forward": -0.4, "why": f"seq: stuck facing a wall ({fs}); back off"})
                reply = send(args.session, {"op": "base", "turn_deg": turn, "why": "seq: turn toward open space"})
                print(f"step {reply.get('step')}: unstuck, turned {turn}", flush=True)
                n, moved = 0, False
                continue
        if fallback_left > 0:
            fallback_left -= 1
            reply = send(args.session, {"op": "global", "why": "seq: fallback"})
            if fallback_left == 0:
                n, moved, start_w = 0, False, None
            continue
        if k >= len(skills):
            reply = send(args.session, {"op": "global", "why": "seq: skill list finished"})
            continue

        p = skills[k]
        v = verb(p)
        if start_w is None:                     # entering skill k
            start_w = dict(w)
            if v == "place" and not any(x < OPEN for x in w.values()):
                print(f"step {step}: skip '{p}' (nothing held)", flush=True)
                counts["skipped"] += 1
                k, start_w, tries = k + 1, None, 0
                continue
            if v == "pick up" and not any(x > OPEN for x in w.values()):
                print(f"step {step}: skip '{p}' (both hands full)", flush=True)
                counts["skipped"] += 1
                k, start_w, tries = k + 1, None, 0
                continue
            print(f"step {step}: [{k}] {p}  (budget {budget(p)} checks, widths {w})", flush=True)
        done = False
        if n > 0:
            if v == "move to":
                done = moved and mon.get("base_idle_s", 0) >= 2
            elif v == "pick up":
                done = any(start_w[a] > OPEN and closed_n[a] >= 2 for a in w)
            elif v == "place":
                done = any(start_w[a] < OPEN and w[a] > OPEN for a in w)
            else:
                done = any((start_w[a] < OPEN) != (w[a] < OPEN) for a in w) and n >= 2
        if done:
            counts["done"] += 1
            print(f"step {step}: done [{k}] after {n} checks", flush=True)
            k, n, tries, moved, start_w = k + 1, 0, 0, False, None
            continue
        if n >= budget(p):
            counts["timeouts"] += 1
            tries += 1
            if tries >= 2 or v not in ("move to", "pick up", "place"):
                print(f"step {step}: timeout [{k}] -> advance", flush=True)
                k, tries = k + 1, 0
            else:
                print(f"step {step}: timeout [{k}] -> global {args.fallback_checks}, then retry", flush=True)
            fallback_left, n, start_w = args.fallback_checks, 0, None
            continue
        n += 1
        if mon.get("base_idle_s", 0) < 1:
            moved = True
        reply = send(args.session, {"op": "skill", "prompt": p, "why": f"seq: [{k}] {v}"})
    if reply.get("ok") is False and not reply.get("episode_over"):
        print("stopped:", reply.get("error", "")[-500:])
    send(args.session, {"op": "end"})
    print("done", json.dumps(counts))


if __name__ == "__main__":
    main()
