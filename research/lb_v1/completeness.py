"""List missing (task, instance) pairs for lb_v1 across local + pulled roots; print per-machine video sizes if given."""
import glob, json, os, sys
facts = sorted(json.load(open(f))['name'] for f in glob.glob('/home/ywang/Behavior/task_docs/facts/[0-9]*_*.json'))
have = {}
for root in sys.argv[1:]:
    for f in glob.glob(os.path.join(root, '*', 'json', '*.json')):
        r = json.load(open(f)); have.setdefault((r['task'], r['instance_id']), []).append(root)
missing = [(t, i) for t in facts for i in range(301, 311) if (t, i) not in have]
dups = {k: v for k, v in have.items() if len(v) > 1}
print(f"have {len(have)}/1000; missing {len(missing)}; duplicated across machines {len(dups)}")
bytask = {}
for t, i in missing: bytask.setdefault(t, []).append(i)
for t, ii in bytask.items(): print(f"  {t:42s} missing {ii}")
if dups: print("duplicates:", list(dups.items())[:5])
