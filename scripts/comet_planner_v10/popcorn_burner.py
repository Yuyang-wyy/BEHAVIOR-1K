"""make_microwave_popcorn via the cooktop burner (legal inputs: RGB-D, proprioception, robot kinematics).

1. Comet skill "move to the popcorn bag" until the base stops after moving.
2. Straighten trunk, tuck arms back (driving with an arm over the counter tipped the robot).
3. Press the burner's red (OFF) marker at cooktop height with poke_marker.py (turn/back off and retry).
4. Find the flame (bright yellow blob) and the bag (largest tan blob) in the head image and push the bag
   toward the flame with push_to.py. Success (bag >= 40 C) ends the episode.

    popcorn_burner.py SESSION
"""
import json, subprocess, sys, time
from pathlib import Path
import numpy as np, cv2
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from poke_marker import send
S = sys.argv[1]; PY = sys.executable
def run(*args, timeout=400):
    out = subprocess.run([PY, *map(str, args)], capture_output=True, text=True, timeout=timeout).stdout.strip().splitlines()
    return out[-1] if out else ""
def over():
    return (Path(S) / "DONE").exists()
def blobs(img, kind):
    b, g, r = [img[..., i].astype(int) for i in range(3)]
    if kind == "flame":
        m = (r > 200) & (g > 150) & (b < 140) & (r - b > 90); minA = 40
    else:
        m = (r > 120) & (r < 230) & (g > 70) & (g < 170) & (b < 90) & (r - b > 70); minA = 300
    n, lab, st, c = cv2.connectedComponentsWithStats(m.astype(np.uint8))
    return sorted([(int(c[i][0]), int(c[i][1]), int(st[i][4])) for i in range(1, n) if st[i][4] >= minA], key=lambda x: -x[2])
t0 = time.time(); log = {}
send(S, {"op": "skill", "prompt": "move to the popcorn bag", "why": "popcorn: Comet navigates"})
moved = False
for k in range(12):
    r = send(S, {"op": "continue"})
    if r.get("episode_over"): print(json.dumps({"over": "during move"})); sys.exit()
    if r["proprio"]["base_speed"] > 0.05: moved = True
    if moved and r["monitor"]["base_idle_s"] >= 2: break
log["arrived_step"] = r["step"]
send(S, {"op": "trunk"})
for arm in ("left", "right"):
    send(S, {"op": "hand", "arm": arm, "forward": -0.25, "up": 0.1, "trunk": False, "why": "popcorn: tuck"})
on = False
for attempt, fix in enumerate([None, {"turn_deg": -35}, {"turn_deg": 70}, {"turn_deg": 35}, {"turn_deg": 35}]):
    if over(): break
    if fix: send(S, {"op": "base", "gentle": True, **fix, "why": "popcorn: find burner marker"})
    # search up to 2 m; --normal --square drives to 0.65 m in front of the cooktop face before pressing
    res = run(HERE / "poke_marker.py", S, "--arm", "right", "--horizontal", "--normal", "--square", "--color", "red",
              "--max-range", "2.0", "--min-z", "0.85", "--max-z", "0.97")
    send(S, {"op": "trunk"})
    img = cv2.imread(send(S, {"op": "observe"})["images"]["head"])
    log.setdefault("poke", []).append(res[:80])
    # ON check: a green toggle marker at cooktop height within reach (the burner's own marker turns green).
    # A second press would toggle it off again, so stop pressing as soon as this is seen.
    from poke_marker import green_blobs
    greens = []
    for u, v, area in green_blobs(img):
        p = send(S, {"op": "point", "cam": "head", "u": u, "v": v})["point_base"]
        if 0.85 <= p[2] <= 0.97 and np.hypot(p[0], p[1]) < 1.3:
            greens.append([round(u), round(v)])
    log.setdefault("green", []).append(greens)
    if greens and '"pressed"' in res:
        on = True; break
log["burner_on"] = on
for k in range(6):                       # one push per round, bag and flame re-detected by colour each time
    if over() or not on: break
    img = cv2.imread(send(S, {"op": "observe"})["images"]["head"])
    fl, bg = blobs(img, "flame"), blobs(img, "bag")
    near = lambda u, v: float(np.hypot(*send(S, {"op": "point", "cam": "head", "u": u, "v": v})["point_base"][:2]))
    bg = [b for b in bg[:4] if near(b[0], b[1]) < 1.2][:1]        # tan furniture far away also matches
    if bg:
        fl = [f for f in fl if np.hypot(f[0] - bg[0][0], f[1] - bg[0][1]) > 60]
    fl = [f for f in fl if near(f[0], f[1]) < 1.3][:1]
    if not fl or not bg:
        log.setdefault("push", []).append("lost view"); send(S, {"op": "base", "turn_deg": 15, "gentle": True}); continue
    res = run(HERE / "push_to.py", S, "--arm", "left", "--obj", f"{bg[0][0]},{bg[0][1]}", "--target", f"{fl[0][0]},{fl[0][1]}",
              "--stop", "0.12", "--rounds", "1", timeout=200)
    log.setdefault("push", []).append(res[:120])
    if '"dist"' in res and json.loads(res)[0].get("dist", 9) <= 0.12:
        break
log["done"] = (Path(S) / "DONE").read_text() if over() else None
log["wall_s"] = round(time.time() - t0)
print(json.dumps(log))
