"""Reflex trigger: run Comet checkpoints until a green (ON) toggle marker is within reach, then stop.

    green_watch.py SESSION [--n 10] [--reach 1.2] [--min-z 0.3]
Prints one line per checkpoint; exits with the in-reach marker list (for poke_marker.py --pick u,v).
"""
import argparse, json, subprocess, sys
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).parent))
from poke_marker import send, green_blobs

ap = argparse.ArgumentParser()
ap.add_argument("session"); ap.add_argument("--n", type=int, default=10)
ap.add_argument("--reach", type=float, default=1.2); ap.add_argument("--min-z", type=float, default=0.3)
a = ap.parse_args()
for k in range(a.n):
    r = send(a.session, {"op": "continue"})
    if r.get("episode_over"):
        print("episode over"); break
    img = cv2.imread(r["images"]["head"])
    hits = []
    for u, v, area in green_blobs(img):
        p = send(a.session, {"op": "point", "cam": "head", "u": u, "v": v})["point_base"]
        rng = float(np.hypot(p[0], p[1]))
        if rng <= a.reach and p[2] >= a.min_z:
            hits.append({"uv": [round(u), round(v)], "p": p, "range": round(rng, 2)})
    print(json.dumps({"step": r["step"], "left_s": r.get("seconds_left"), "prompt": (r.get("prompt") or "")[:30],
                      "in_reach": hits}), flush=True)
    if hits:
        break
