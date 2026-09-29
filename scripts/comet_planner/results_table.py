"""Collect result.json from local and remote planner_runs dirs and print a per-version x instance Q table.

    results_table.py [--fetch]      # --fetch pulls remote result.json files first (cse110 4090)
"""
import argparse, glob, json, os, subprocess, collections
from pathlib import Path

LOCAL = Path("/home/ywang/Behavior/planner_runs")
MIRROR = LOCAL / "remote_mirror"
REMOTE = os.environ.get("PLANNER_REMOTE", "")          # user@host of the second GPU box
REMOTE_PORT = os.environ.get("PLANNER_REMOTE_PORT", "22")


def fetch():
    MIRROR.mkdir(exist_ok=True)
    cmd = (f"cd /home/ywang/Behavior/planner_runs && find trash_auto trash_ab tasks_auto tasks_ab -maxdepth 2 -name result.json 2>/dev/null | "
           f"tar -czf - -T -")
    tar = subprocess.run(["ssh", "-p", REMOTE_PORT, "-o", "BatchMode=yes", REMOTE, cmd], capture_output=True)
    subprocess.run(["tar", "-xzf", "-", "-C", str(MIRROR)], input=tar.stdout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--task", default=None, help="only this task")
    args = ap.parse_args()
    if args.fetch:
        fetch()
    rows = collections.defaultdict(dict)
    for root in (LOCAL, MIRROR):
        for f in glob.glob(str(root / "*_a*" / "*" / "result.json")):
            name = Path(f).parent.name
            if "__" not in name:
                continue
            tag, task, inst = name.split("__")
            if args.task and task != args.task:
                continue
            try:
                r = json.load(open(f))
            except Exception:
                continue          # empty/partial file (e.g. written while a disk was full)
            key = f"{task[:18]}:{tag}{'' if r.get('seed', 0) == 0 else '_s' + str(r['seed'])}"
            rows[key][r["instance_id"]] = (r["q_score"]["final"], r["success"])
    insts = sorted({i for v in rows.values() for i in v})
    print("task:version".ljust(30) + "".join(f"{i:>7}" for i in insts) + "   mean   succ  n")
    for k in sorted(rows):
        v = rows[k]
        qs = [v[i][0] for i in insts if i in v]
        cells = "".join(f"{v[i][0]:>7.2f}" if i in v else "      -" for i in insts)
        print(k.ljust(30) + cells + f"  {sum(qs)/len(qs):5.2f}  {sum(v[i][1] for i in v):4d}  {len(qs)}")


if __name__ == "__main__":
    main()
