"""Reflex supervisor v12 (held-container place): global task prompt all episode; one reflex.

When one hand holds the container (the hand that closed first) and the other hand holds an item, and both have
stayed closed for `stall_checks` consecutive 5 s checkpoints, run the scripted `auto_place` of the item into the
held container (demo release pose + mouth detection), then return to the global prompt.
Built for dispose_of_glass (Comet grabs the bin, then a glass, then wanders for minutes without releasing).

    auto_supervisor.py SESSION --place-prompt "<unused>" [--stall-checks 2] [--max-places 6]
"""
import argparse, json, subprocess, sys
from pathlib import Path
CLIENT = Path(__file__).with_name("planner_client.py")
CLOSED = 0.09


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
    a = ap.parse_args()
    first_closed = None           # hand that closed first and stayed closed = container holder
    both_n, places = 0, 0
    reply = send(a.session, {"op": "global", "why": "v12: global prompt"})
    while reply.get("ok") and not reply.get("episode_over"):
        w = {h: reply["proprio"][f"gripper_{h}_width"] for h in ("left", "right")}
        closed = {h: w[h] < CLOSED for h in w}
        if first_closed and not closed[first_closed]:
            first_closed = None
        if first_closed is None:
            c = [h for h in w if closed[h]]
            if len(c) == 1:
                first_closed = c[0]
        both_n = both_n + 1 if all(closed.values()) and first_closed else 0
        if both_n >= a.stall_checks and places < a.max_places:
            item = "left" if first_closed == "right" else "right"
            places += 1
            pl = send(a.session, {"op": "auto_place", "arm": item,
                                  "why": f"v12: {first_closed} holds the container, {item} holds an item for {both_n} checks"})
            print(f"step {reply.get('step')}: auto_place {item} -> {pl.get('auto_place', {}).get('result')} "
                  f"(widths {w})", flush=True)
            both_n = 0
            if pl.get("ok") and not pl.get("episode_over"):
                reply = send(a.session, {"op": "global", "why": "v12: back to global"})
            else:
                reply = pl
            continue
        reply = send(a.session, {"op": "continue"})
    send(a.session, {"op": "end"})
    print("done, places", places)


if __name__ == "__main__":
    main()
