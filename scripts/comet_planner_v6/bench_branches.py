"""Replay recovery branches from one saved snapshot and score them (dev only; uses privileged scoring).

    bench_branches.py SESSION SNAPSHOT.pt BRANCHES.json --repeats 3 --out results.json

BRANCHES.json: {"name": [cmd, cmd, ...], ...} where each cmd is a planner_episode command dict.
After the commands every branch runs the global prompt for --tail steps, then records the goal literals
and the height of every task object. Scoring uses simulator state and is for development only.
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

CLIENT = Path(__file__).with_name("planner_client.py")


def send(session, cmd, timeout=3600):
    out = subprocess.run([sys.executable, str(CLIENT), str(session), "raw", json.dumps(cmd), "--timeout", str(timeout)],
                         capture_output=True, text=True)
    text = out.stdout.split("\nDONE")[0]
    try:
        return json.loads(text)
    except Exception:
        return {"ok": False, "error": out.stdout[-800:] + out.stderr[-800:]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("session", type=Path)
    ap.add_argument("snapshot")
    ap.add_argument("branches", type=Path)
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--tail", type=int, default=600, help="global-prompt steps after the branch commands")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    branches = json.loads(args.branches.read_text())
    results = json.loads(args.out.read_text()) if args.out.exists() else []
    done = {(r["branch"], r["repeat"]) for r in results}
    for rep in range(args.repeats):
        for name, cmds in branches.items():
            if (name, rep) in done:
                continue
            t0 = time.time()
            load = send(args.session, {"op": "load", "name": args.snapshot})
            if not load.get("ok"):
                print("load failed", load.get("error")); return
            start_step = load["step"]
            before = send(args.session, {"op": "objinfo"})
            log = []
            for c in cmds:
                r = send(args.session, c)
                log.append({"cmd": c, "ok": r.get("ok"), "step": r.get("step"),
                            "jaws": r.get("jaws"), "err": (r.get("error") or "")[-300:]})
            mid = send(args.session, {"op": "objinfo"})
            send(args.session, {"op": "global", "steps": args.tail})
            after = send(args.session, {"op": "objinfo"})
            rec = {"branch": name, "repeat": rep, "start_step": start_step,
                   "steps_used_by_branch": (mid.get("step") or start_step) - start_step,
                   "end_step": after.get("step"), "q_before": before.get("goal", {}).get("partial_q"),
                   "q_after_branch": mid.get("goal", {}).get("partial_q"), "q_after_tail": after.get("goal", {}).get("partial_q"),
                   "objects_after_branch": mid.get("objects"), "objects_after_tail": after.get("objects"),
                   "literals_after_tail": [l["literal"] for l in after.get("goal", {}).get("literals", []) if l["now"]],
                   "log": log, "wall_s": round(time.time() - t0, 1)}
            results.append(rec)
            args.out.write_text(json.dumps(results, indent=1))
            print(f"{name:14s} rep {rep}  branch steps {rec['steps_used_by_branch']:4d}  Q {rec['q_before']} -> "
                  f"{rec['q_after_branch']} -> {rec['q_after_tail']}  wall {rec['wall_s']}s", flush=True)


if __name__ == "__main__":
    main()
