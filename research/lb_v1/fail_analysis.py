"""Failure-mode analysis of lb_v1 episodes from goal_history ([satisfied, total] per step) + task facts.
Per episode: success | never (no literal ever gained) | undo (gained then lost, ends below max) | stall (last gain
before 60% of the episode, ends below total) | slow (still gaining in the last 40%, timed out).
Per task: mode counts, mean Q, time to first gain (s), ceiling (max satisfied fraction ever reached), goal predicates."""
import glob, json, os, sys, statistics as st, collections
facts = {}
for f in glob.glob('/home/ywang/Behavior/task_docs/facts/[0-9]*_*.json'):
    d = json.load(open(f)); facts[d['name']] = d
eps = collections.defaultdict(list)
for root in sys.argv[1:]:
    for f in glob.glob(os.path.join(root, '*', 'json', '*.json')):
        r = json.load(open(f)); gh = r.get('goal_history') or []
        if not gh: continue
        sat = [g[0] for g in gh]; tot = gh[-1][1]; n = len(sat)
        gains = [i for i in range(1, n) if sat[i] > sat[i-1]]
        losses = [i for i in range(1, n) if sat[i] < sat[i-1]]
        if r.get('success'): mode = 'success'
        elif not gains: mode = 'never'
        elif losses and sat[-1] < max(sat): mode = 'undo'
        elif gains[-1] < 0.6 * n: mode = 'stall'
        else: mode = 'slow'
        eps[r['task']].append(dict(q=r['q_score']['final'], mode=mode, first=gains[0]/30 if gains else None,
                                   ceil=max(sat)/tot if tot else 0, end=sat[-1]/tot if tot else 0, steps=n, losses=len(losses)))
rows = []
for t, E in eps.items():
    if len(E) < 5: continue
    modes = collections.Counter(e['mode'] for e in E)
    firsts = [e['first'] for e in E if e['first'] is not None]
    gp = facts[t].get('goal_predicates', [])
    preds = collections.Counter((p[0] if isinstance(p, list) else str(p).split()[0].strip('(')) for p in gp) if isinstance(gp, list) else collections.Counter(gp.keys() if isinstance(gp, dict) else [])
    rows.append((t, len(E), st.mean(e['q'] for e in E), modes, st.median(firsts) if firsts else None, st.mean(e['ceil'] for e in E),
                 st.mean(e['end'] for e in E), facts[t]['human']['mean_steps']/30, dict(preds)))
rows.sort(key=lambda r: -r[2])
print(f"{'task':40s} n  meanQ  succ never undo stall slow | 1st gain s / human s | ceil  end")
for t, n, q, m, first, ceil, end, hum, preds in rows:
    print(f"{t:40s} {n:2d} {q:.2f}   {m['success']:2d}   {m['never']:2d}   {m['undo']:2d}   {m['stall']:2d}   {m['slow']:2d} | "
          f"{(f'{first:5.0f}' if first else '    -')} / {hum:4.0f} | {ceil:.2f} {end:.2f}")
tot = collections.Counter()
for t, n, q, m, *_ in rows: tot.update(m)
N = sum(tot.values()); print('\nALL episodes:', {k: f"{v} ({v/N:.0%})" for k, v in tot.items()})
# predicate-level: which goal predicate types dominate the never-tasks vs the partial tasks
never_tasks = [r for r in rows if r[3]['never'] >= 0.8*r[1]]
print(f"\n'never' tasks ({len(never_tasks)}):", [r[0] for r in never_tasks])
pc = collections.Counter()
for r in never_tasks: pc.update(r[8].keys())
print('goal predicate types among never-tasks:', pc.most_common(12))
undo_heavy = [(r[0], r[3]['undo'], round(r[5]-r[6],2)) for r in rows if r[3]['undo'] >= 3]
print(f"\nundo-heavy tasks (>=3 eps gained then lost; (task, n_undo, ceil-end)):", undo_heavy)
