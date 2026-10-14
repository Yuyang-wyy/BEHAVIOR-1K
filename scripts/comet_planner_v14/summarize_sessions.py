"""Summarise planner_episode.py sessions: score, prompt segments, and when each goal literal flipped.

    summarize_sessions.py SESSION [SESSION ...]          # one block per session
    summarize_sessions.py --table SESSION [SESSION ...]  # one row per session
"""
import argparse
import json
from pathlib import Path


def load(session):
    s = Path(session)
    result = json.loads((s / "result.json").read_text())
    header = json.loads((s / "session.json").read_text())
    ticks, prompts = [], []
    for line in (s / "trace.jsonl").read_text().splitlines():
        rec = json.loads(line)
        if rec["event"] == "tick":
            ticks.append(rec)
        elif rec["event"] == "prompt":
            prompts.append(rec)
    return s, header, result, ticks, prompts


def flips(ticks):
    """Literal truth changes seen at tick resolution: (step, literal, became_true, prompt)."""
    out = []
    state = {}
    for t in ticks:
        for lit in t.get("changed", []):
            state[lit] = not state.get(lit, False)
            out.append((t["step"], lit, state[lit], t.get("prompt")))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sessions", nargs="+")
    ap.add_argument("--table", action="store_true")
    args = ap.parse_args()
    rows = []
    for sess in args.sessions:
        try:
            s, h, r, ticks, prompts = load(sess)
        except FileNotFoundError as e:
            print(f"{sess}: incomplete ({e.filename})")
            continue
        q = r.get("q_score", {}).get("final")
        hz = r["harness"]
        plan = (h.get("plan_file") or ("interactive" if h.get("plan") is None else "inline")) if h.get("plan") is not None or h.get("plan_file") else "interactive"
        lost = [f for f in flips(ticks) if not f[2]]
        rows.append((s.name, r["task"], r["instance_id"], plan, q, hz["goal_final"]["partial_q"], r["success"], r["steps"],
                     hz["step_limit"], len(hz["segments"]), len(lost)))
        if args.table:
            continue
        print(f"=== {s.name}: {r['task']} instance {r['instance_id']} seed {r['seed']} plan {plan}")
        print(f"    official Q {q} | tracker Q {hz['goal_final']['partial_q']} | success {r['success']} | "
              f"steps {r['steps']}/{hz['step_limit']} | ended by {hz['ended_by']}")
        for seg in hz["segments"]:
            print(f"    [{seg['start']:>6}-{seg['end']:>6}] {seg['reason']:<24} Q {seg['partial_q_after']:<6} "
                  f"prompt: {seg['prompt'] or '<task sentence>'}")
        for step, lit, became_true, prompt in flips(ticks):
            print(f"    step {step:>6}: {lit} -> {'TRUE' if became_true else 'false (lost)'}   under: {prompt or '<task sentence>'}")
        print("    final literals: " + ", ".join(("+" if l["now"] else "-") + l["literal"] for l in hz["goal_final"]["literals"]))
    if args.table or len(rows) > 1:
        print(f"{'session':<34} {'task':<34} {'inst':>4} {'plan':<28} {'Q':>6} {'trkQ':>6} {'succ':>5} {'steps':>12} {'segs':>4} {'lost':>4}")
        for row in rows:
            name, task, inst, plan, q, tq, succ, steps, lim, nseg, nlost = row
            print(f"{name:<34} {task:<34} {inst:>4} {str(Path(str(plan)).name):<28} {q if q is None else round(q, 3):>6} "
                  f"{round(tq, 3):>6} {str(succ):>5} {f'{steps}/{lim}':>12} {nseg:>4} {nlost:>4}")


if __name__ == "__main__":
    main()
