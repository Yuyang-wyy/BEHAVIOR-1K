# 59 · Organizing Art Supplies

Task name `organizing_art_supplies`, task index 59.

> Put the marker, paintbrush, glue stick, and rubber eraser into the tote, then place the tote on the desk.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_upper` |
| rooms in the goal | bedroom |
| rooms loaded | bathroom_0, bedroom_0, bedroom_1, bedroom_2, living_room_0 |
| human demo length | 206.5 s mean (6194 steps) |
| episode time limit | 309.7 s (9291 steps at 30 Hz) |
| human base travel | 11.5079 m |
| goal literals (best ground option) | 5 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://www.youtube.com/embed/M1D9oCKBJZg |

## Planner notes

**Tier:** B — four small desk items into a tote, then the tote onto the desk; marker, glue stick and eraser fit the 44 mm jaw, the paintbrush and the tote handle are unverified.

### Goal in plain words

- The marker, paintbrush, glue stick and rubber eraser must all end with their centres inside the tote.
- The tote must end resting on the bedroom desk (`desk_aduafr_0`, the only desk in bedroom_0).
- One ground option, 5 literals, none true at reset, so partial Q counts each item and the tote placement at 0.2 each.
- Nothing forbids extra objects in the tote or anything else on the desk.

### Q traps

- Partial Q reads only the final state (PREDICATES §1). An item that falls out while the tote is lifted, carried or set down loses its 0.2.
- `inside` tests only the item's AABB centre against the tote's fillable volume (PREDICATES §3). A paintbrush (0.18 m long) poking out still counts if its centre is in; an item resting on the rim does not.
- The tote asset `tote/bnkjle` has an encrypted USD; its fillable volume could not be checked offline (unverified, but the task is designed around it).
- `ontop tote desk` needs the tote touching the desk with the desk under the tote's centre (PREDICATES §4). The desk top is plain (asset bbox 0.63 x 1.51 x 0.785 m, no hutch; three drawers), so any spot on the top works.
- A tote left half over the desk edge fails `ontop` and can tip items out.
- Whole-task Q was 0.00 in both closed-loop runs on 311 (page); nothing scored at all.

### Minimal plan

Demo order (80% of demos use it). Pick two items per trip, one per hand.

1. `move to the marker` — marker centred in the head camera at arm's reach; ~10 s.
2. `pick up the marker from the desk` — gripper closed but not fully shut, marker gone from the desk; ~17 s.
3. `move to the rubber eraser` — ~10 s.
4. `pick up the rubber eraser from the desk` — second gripper closed short of fully shut; ~17 s.
5. `move to the tote` — tote on the floor at close range; ~10 s.
6. `place the marker in the tote` — gripper open, marker not visible on the floor or rim; ~11 s.
7. `place the rubber eraser in the tote` — same check; ~11 s.
8. `move to the glue stick`, `pick up the glue stick from the desk` — ~27 s.
9. `move to the paintbrush`, `pick up the paintbrush from the desk` — ~27 s.
10. `move to the tote`, `place the paintbrush in the tote`, `place the glue stick in the tote` — ~32 s.
11. `pick up the tote from the floors` — tote off the floor, contents still visible inside; ~17 s.
12. `move to the desk` — desk top in view; ~10 s.
13. `place the tote on the desk` — gripper open, tote upright and fully on the desk top; ~10 s.

Demo pace is ~205 s against a 309.7 s limit, so there is ~100 s for retries.

### What the demos do differently

- All 200 demos leave the tote on the floor while filling it and carry it to the desk last. None bring the tote to the desk first.
- Item order varies (109 distinct object orders), but always two items per trip, both placed before the next trip.
- No hand-overs, no drawer use, no extra steps. The demo is already minimal.

### Hard parts and hacks

- **Grasp widths (custom_lists forced sizes).** Marker 0.14 x 0.022 x 0.022, glue stick 0.12 x 0.03 x 0.03, eraser 0.075 x 0.035 x 0.02: all straddle the 44 mm jaw top-down across the short axis.
- **Paintbrush** is forced to 0.18 x 0.05 x 0.015 m. Its widest cross-axis extent (0.05 m) exceeds 44 mm; the handle is presumably narrower, so grasp the handle, not the bristle end (handle width unverified).
- **Tote grasp.** Tote bbox is 0.34 x 0.24 x 0.47 m (asset metadata), taller than wide, so the top part is presumably the handles. A handle ≤ 44 mm is needed; unverified.
- **Items spread along the desk.** Across the 20 instances the four items span ~1.4 m along the desk's long axis (x -5.94 to -4.52). Expect one base move between items.
- **Tote 1-2.5 m from the desk**, on the floor at z 0.19; reaching into it from standing needs the trunk bent down.
- **Hack (untested, out of demo order):** carry the empty tote to the desk first, then place items into it on the desk. Nothing loaded is ever carried, so no spill risk, and every item place is at desk height. The prompts stay the trained strings (`pick up the tote from the floors`, `place the tote on the desk`, `place the X in the tote`), but Comet never saw the tote on the desk during `place in`.
- Earlier scripted attempts on instance 301 got zero confirmed grasps (radio_generalization_20260920/PICK_PLACE_STATUS.md); perception, not the jaw span, was the blocker there.

### Hints for the VLM

- Everything is in bedroom_0. The desk is the only desk in that room; other desks exist in living_room_0 and bedroom_2 and are wrong.
- Other surfaces in bedroom_0: bed, nightstand, taboret, two bookcases. Items start only on the desk.
- The tote (bbox 0.34 x 0.24 x 0.47 m) starts on the floor of bedroom_0, 1-2.5 m from the desk.
- Done for each item: it is visible inside the tote opening and absent from the desk.
- Done for the tote: it sits upright on the desk top, not overhanging, with the four items still inside.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside glue_stick.n.01_1 carryall.n.01_1)` | no | yes |
| `(inside rubber_eraser.n.01_1 carryall.n.01_1)` | no | yes |
| `(inside paintbrush.n.01_1 carryall.n.01_1)` | no | yes |
| `(inside marker.n.03_1 carryall.n.01_1)` | no | yes |
| `(ontop carryall.n.01_1 desk.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (inside glue_stick.n.01_1 carryall.n.01_1)
            (inside rubber_eraser.n.01_1 carryall.n.01_1)
            (inside paintbrush.n.01_1 carryall.n.01_1)
            (inside marker.n.03_1 carryall.n.01_1)
            (ontop carryall.n.01_1 desk.n.01_1)
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `desk.n.01_1` | desk_aduafr_0 | desk / aduafr | bedroom_0 | low (0.25-0.6 m), z 0.44 | 1.96 m (range 1.05-2.84) | no (fixed) |
| `floor.n.01_1` | floors_nlswvt_0 | floors / nlswvt | bedroom_0 | floor, z -0.15 | 0.64 m (range 0.16-1.51) | no (fixed) |
| `carryall.n.01_1` | tote_93 | tote / bnkjle | bedroom_0 | floor, z 0.19 | 1.3 m (range 0.8-2.31) | yes, spread 3.62 m |
| `glue_stick.n.01_1` | glue_stick_92 | glue_stick / sqzyci | bedroom_0 | table/counter (0.6-1.1 m), z 0.78 | 1.86 m (range 0.89-3.04) | yes, spread 1.38 m |
| `rubber_eraser.n.01_1` | rubber_eraser_91 | rubber_eraser / cungod | bedroom_0 | table/counter (0.6-1.1 m), z 0.78 | 1.88 m (range 1.03-3.16) | yes, spread 1.49 m |
| `paintbrush.n.01_1` | paintbrush_90 | paintbrush / gngyrk | bedroom_0 | table/counter (0.6-1.1 m), z 0.78 | 1.85 m (range 1.05-2.76) | yes, spread 1.24 m |
| `marker.n.03_1` | marker_89 | marker / kjxpdi | bedroom_0 | table/counter (0.6-1.1 m), z 0.78 | 2.02 m (range 0.84-3.37) | yes, spread 1.29 m |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "bedroom"
 ],
 "house_double_floor_upper": {
  "whitelist": {
   "carryall.n.01": {
    "tote": {
     "bnkjle": null
    }
   },
   "glue_stick.n.01": {
    "glue_stick": {
     "sqzyci": [
      0.12,
      0.03,
      0.03
     ]
    }
   },
   "marker.n.03": {
    "marker": {
     "kjxpdi": [
      0.14,
      0.022,
      0.022
     ]
    }
   },
   "paintbrush.n.01": {
    "paintbrush": {
     "gngyrk": [
      0.18,
      0.05,
      0.015
     ]
    }
   },
   "rubber_eraser.n.01": {
    "rubber_eraser": {
     "cungod": [
      0.075,
      0.035,
      0.02
     ]
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(inroom desk.n.01_1 bedroom)
(inroom floor.n.01_1 bedroom)
(ontop agent.n.01_1 floor.n.01_1)
(ontop carryall.n.01_1 floor.n.01_1)
(ontop glue_stick.n.01_1 desk.n.01_1)
(ontop marker.n.03_1 desk.n.01_1)
(ontop paintbrush.n.01_1 desk.n.01_1)
(ontop rubber_eraser.n.01_1 desk.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching carryall.n.01_1 floor.n.01_1)
(touching desk.n.01_1 glue_stick.n.01_1)
(touching desk.n.01_1 marker.n.03_1)
(touching desk.n.01_1 paintbrush.n.01_1)
(touching desk.n.01_1 rubber_eraser.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 carryall.n.01_1)
(touching glue_stick.n.01_1 desk.n.01_1)
(touching marker.n.03_1 desk.n.01_1)
(touching paintbrush.n.01_1 desk.n.01_1)
(touching rubber_eraser.n.01_1 desk.n.01_1)
```

## What the human demos did

200 annotated demos. Length 201.42 s (range 134.33-332.17). Skills per demo 17.0 (range 15-19). 15 distinct skill orders; the most common one covers 80% of demos.

Most common skill counts per demo (82% of demos): move to x7, pick up from x5, place in x4, place on x1.

Representative demo `episode_00591790.json` (202.3 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the marker` (0.0-7.9 s)
2. `pick up the marker from the desk` (7.9-29.0 s)
3. `move to the rubber eraser` (29.0-34.0 s)
4. `pick up the rubber eraser from the desk` (34.0-56.0 s)
5. `move to the tote` (56.0-66.0 s)
6. `place the marker in the tote` (66.0-79.0 s)
7. `place the rubber eraser in the tote` (79.0-104.0 s)
8. `move to the glue stick` (104.0-109.9 s)
9. `pick up the glue stick from the desk` (109.9-123.0 s)
10. `move to the paintbrush` (123.0-128.2 s)
11. `pick up the paintbrush from the desk` (128.2-142.0 s)
12. `move to the tote` (142.0-159.0 s)
13. `place the paintbrush in the tote` (159.0-172.0 s)
14. `place the glue stick in the tote` (172.0-182.1 s)
15. `pick up the tote from the floors` (182.1-189.6 s)
16. `move to the desk` (189.6-196.2 s)
17. `place the tote on the desk` (196.2-202.0 s)

Mean duration per skill in this task: move to 9.8 s, pick up from 16.7 s, place in 11.1 s, place on 10.0 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the tote` | 418 |
| `pick up the marker from the desk` | 201 |
| `move to the paintbrush` | 200 |
| `place the marker in the tote` | 200 |
| `place the paintbrush in the tote` | 200 |
| `pick up the glue stick from the desk` | 200 |
| `pick up the rubber eraser from the desk` | 200 |
| `place the rubber eraser in the tote` | 200 |
| `place the glue stick in the tote` | 200 |
| `pick up the tote from the floors` | 200 |
| `place the tote on the desk` | 200 |
| `pick up the paintbrush from the desk` | 199 |
| `move to the marker` | 197 |
| `move to the rubber eraser` | 197 |
| `move to the desk` | 194 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/59_organizing_art_supplies.json`. Planner notes: `task_docs/notes/59_organizing_art_supplies.md`.
