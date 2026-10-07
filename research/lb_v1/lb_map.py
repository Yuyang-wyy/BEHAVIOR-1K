"""Collect lb_v1 result JSONs (local + pulled remote/sulab1 copies) into one table.
Usage: lb_map.py ROOT [ROOT ...]  (each ROOT = an eval_out/lb_v1 dir)  -> prints mean Q, per-task table, and
supervision candidates: (a) partial-progress-then-stall tasks (goal_history rises early, flat for the last 40% of the
episode), (b) near-zero tasks, (c) high-variance tasks (instance Q spread >= 0.5)."""
import glob, json, os, sys, statistics as st

rows = {}
for root in sys.argv[1:]:
    for f in glob.glob(os.path.join(root, "*", "json", "*.json")):
        try:
            r = json.load(open(f))
        except Exception:
            continue
        t = r["task"]; i = r["instance_id"]
        gh = r.get("goal_history") or []
        stall = None
        if gh and len(gh) > 50:
            sat = [g[0] for g in gh]; n = len(sat)
            first_gain = next((k for k, s in enumerate(sat) if s > sat[0]), None)
            stall = first_gain is not None and sat[-1] == sat[int(n * 0.6)] and sat[-1] < gh[-1][1]
        rows[(t, i)] = dict(q=r["q_score"]["final"], success=r.get("success"), steps=r.get("steps"),
                           tnorm=(r.get("time") or {}).get("normalized_time"), stall=stall, src=root)
tasks = sorted({t for t, _ in rows})
print(f"episodes {len(rows)}  tasks {len(tasks)}  mean Q {st.mean(v['q'] for v in rows.values()):.4f}  "
      f"full success {sum(bool(v['success']) for v in rows.values())}/{len(rows)}")
print(f"{'task':42s} n  meanQ  succ  Q per instance")
cands = {"stall": [], "zero": [], "spread": []}
for t in tasks:
    qs = [rows[(t, i)]["q"] for i in range(301, 311) if (t, i) in rows]
    succ = sum(bool(rows[(t, i)]["success"]) for i in range(301, 311) if (t, i) in rows)
    stalls = sum(bool(rows[(t, i)]["stall"]) for i in range(301, 311) if (t, i) in rows)
    print(f"{t:42s} {len(qs):2d} {st.mean(qs):.3f}  {succ:2d}   " + " ".join(f"{q:.2f}" for q in qs) + (f"  stalls={stalls}" if stalls else ""))
    if len(qs) >= 3:
        if st.mean(qs) < 0.05: cands["zero"].append(t)
        if max(qs) - min(qs) >= 0.5: cands["spread"].append((t, round(st.mean(qs), 2)))
        if stalls >= len(qs) / 2: cands["stall"].append((t, round(st.mean(qs), 2), stalls))
print("\nSupervision candidates")
print(" partial progress then stall (>=half the instances):", cands["stall"])
print(" high instance spread (>=0.5):", cands["spread"])
print(" near zero:", len(cands["zero"]), cands["zero"][:30])
