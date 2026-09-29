# 56 · Make Rose Centerpieces

Task name `make_rose_centerpieces`, task index 56.

> Place all four roses into the vase and leave the vase on the coffee table.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | living_room |
| rooms loaded | bathroom_0, corridor_0, garage_0, garden_0, kitchen_0, living_room_0 |
| human demo length | 151.1 s mean (4532 steps) |
| episode time limit | 226.6 s (6798 steps at 30 Hz) |
| human base travel | 9.0471 m |
| goal literals (best ground option) | 4 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.00; ft24k@sulab1 Q=0.00; ft40k@sulab1 Q=0.75; ft40k@local Q=0.75; ft10k@sulab1 Q=0.00 |
| demo video | https://www.youtube.com/embed/Nb8kdrf7c_M |

## Planner notes

**Tier:** C — roses are thin-stemmed and should fit the jaw, but the vase (forced size 0.32 x 0.32 x 0.35 m) must also be carried, and nothing on it is verified to be <= 44 mm.

### Goal in plain words

- All three roses must end with their AABB centre inside the vase's volume, and the vase must rest on the coffee table.
- The task sentence says "four roses"; the BDDL and all 20 instances have **three** (`rose_78/79/80`). Do not search for a fourth.
- There is exactly one vase, one coffee table and one bottom cabinet in living_room_0 (template `init_info`), so there are no choices and no same-category distractors.
- Nothing must be closed or turned off. No literal is true at reset, so max partial Q is 1.0 (each literal = 0.25).

### Q traps

- `ontop vase coffee_table` needs the vase's centre x-y over the table top and the vase touching it; an edge overhang fails (PREDICATES §4).
- Carrying a filled vase can spill roses. A rose that falls out loses its `inside` literal; only the final state counts (§1).
- A rose lying across the rim scores nothing: `inside` tests only the rose's AABB centre (§3). The rose is 0.27 m long, so it must go in stem-down, not lie on top.
- **Measured 2026-09-23 (instance 311, `BEHAVIOR-1K/scripts/aspire_radio/rose_inside_probe.py`): the vase's fill volume is small and deep.** It spans only z 0.56-0.69 m with the vase on the table, which is 8 cm below the rim, and about 0.19 m across. A rose is about 0.25 m long. A rose standing upright on the cavity floor has its AABB centre only 7 mm under the volume top, so it passes by a hair. A rose that lands on another rose's stem sits higher and fails. Dropping three roses in from above failed at least one rose in 6 of 6 trials. Placing each rose so its lower end reaches the cavity floor, leaning 20-40 deg against a different side, passed all three in 3 of 3 trials. The opposite end-down orientation failed the third rose every time (which end is the bloom is unverified).
- The ft40k rollout on 311 (Q 0.75) fits this exactly. The video shows the vase on the table and all three roses visibly in it, and the episode then idled until the time limit. So one rose's centre sat above the volume.
- Planner consequence: after each `place the rose in the vase`, the rose must go down to the bottom, not rest on the others. Spread the roses to different sides of the vase, and push a high-standing rose down before moving on.

### Minimal plan

All demos (199/200) fill the vase on the cabinet first, then carry it. Follow that order; it keeps prompts in distribution.

1. `move to the rose` — done: roses and vase on the low cabinet centred in the head camera, base stopped. ~10 s.
2. `pick up the rose from the bottom cabinet` — done: gripper closed short of fully closed, one rose gone from the cabinet top. ~14 s.
3. `move to the vase` — ~10 s (often not needed: vase is on the same cabinet).
4. `place the rose in the vase` — done: gripper open, rose visible standing in the vase, stem hidden. ~11 s.
5. Repeat 1-4 for the other two roses. Demos often pick two roses (one per hand) before placing both.
6. `pick up the vase from the bottom cabinet` — done: vase lifted clear of the cabinet top, roses still in it. ~8 s.
7. `move to the coffee table` — ~14 s.
8. `place the vase on the coffee table` — done: vase upright on the table, gripper open, three roses still visible in it. ~10 s.

Total demo mean 151 s vs a 226.6 s limit: about 75 s of slack for retries.

### What the demos do differently

- 45% of demos use exactly 6 moves, 4 picks, 3 place-ins, 1 place-on. Only 18 distinct orders exist.
- 198 of 200 demos pick two roses (one per hand) before placing both in succession.
- `hand over the rose` appears 3 times in 200 demos; not needed.
- No demo moves the empty vase to the coffee table first (0/200). That alternative avoids carrying a full vase but has no in-distribution precedent for placing roses into a vase on the coffee table.

### Hard parts and hacks

- Vase pick-up: all 200 demo vase picks are single-arm (`uncoordinated`, mean 7.9 s), but the vase is 0.32 m across. Whether the jaw registers on its rim/neck under the 44 mm rule is unverified; this is the most likely failure.
- If the vase grasp fails, securing the three roses still gives Q = 0.75. Put the roses in first so a failed vase move costs only 0.25.
- Do not tilt the vase in transit; roses can slide out. Keep the carry low and slow.
- Rose insertion: lower the rose head-up, stem into the opening. A rose dropped from above may land on the rim.
- Cheap check: after step 8, count three rose heads above the vase opening in RGB.

### Hints for the VLM

- All objects are in living_room_0. Roses (0.27 x 0.13 x 0.08 m) and the vase start together on the low bottom cabinet (roses at z ~0.46 m).
- The coffee table is the low table ~1.2-1.9 m from the start pose; it is the only coffee table.
- The bottom cabinet in the living room is the only one there; a second bottom cabinet is in bathroom_0, a different room.
- Done for each rose: the rose stands in the vase opening, not resting on the rim or the cabinet.
- Done for the vase: upright on the coffee table top, fully on the surface, gripper released.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside rose.n.01_1 vase.n.01_1)` | no | yes |
| `(inside rose.n.01_2 vase.n.01_1)` | no | yes |
| `(inside rose.n.01_3 vase.n.01_1)` | no | yes |
| `(ontop vase.n.01_1 coffee_table.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (inside ?rose.n.01_1 ?vase.n.01_1) 
            (inside ?rose.n.01_2 ?vase.n.01_1) 
            (inside ?rose.n.01_3 ?vase.n.01_1) 
            (ontop ?vase.n.01_1 ?coffee_table.n.01_1)
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `vase.n.01_1` | vase_81 | vase / jpwsrp | living_room_0 | low (0.25-0.6 m), z 0.59 | 1.99 m (range 1.17-3.71) | yes, spread 1.97 m |
| `cabinet.n.01_1` | bottom_cabinet_rhdbzv_0 | bottom_cabinet / rhdbzv | living_room_0 | floor, z 0.21 | 2.23 m (range 1.08-3.12) | no (fixed) |
| `coffee_table.n.01_1` | coffee_table_koagbh_0 | coffee_table / koagbh | living_room_0 | low (0.25-0.6 m), z 0.36 | 1.51 m (range 1.21-1.92) | no |
| `rose.n.01_1` | rose_80 | rose / hrwson | living_room_0 | low (0.25-0.6 m), z 0.46 | 2.23 m (range 0.91-3.66) | yes, spread 1.76 m |
| `rose.n.01_2` | rose_79 | rose / hrwson | living_room_0 | low (0.25-0.6 m), z 0.46 | 1.95 m (range 1.05-3.71) | yes, spread 1.76 m |
| `rose.n.01_3` | rose_78 | rose / hrwson | living_room_0 | low (0.25-0.6 m), z 0.46 | 1.96 m (range 1.16-3.64) | yes, spread 2.19 m |
| `floor.n.01_1` | floors_ulujpr_0 | floors / ulujpr | living_room_0 | floor, z -0.15 | 1.26 m (range 0.84-1.79) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "living_room"
 ],
 "house_double_floor_lower": {
  "whitelist": {
   "rose.n.01": {
    "rose": {
     "hrwson": [
      0.27,
      0.13,
      0.08
     ]
    }
   },
   "vase.n.01": {
    "vase": {
     "jpwsrp": [
      0.32,
      0.32,
      0.35
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
(inroom cabinet.n.01_1 living_room)
(inroom coffee_table.n.01_1 living_room)
(inroom floor.n.01_1 living_room)
(ontop agent.n.01_1 floor.n.01_1)
(ontop rose.n.01_1 cabinet.n.01_1)
(ontop rose.n.01_2 cabinet.n.01_1)
(ontop rose.n.01_3 cabinet.n.01_1)
(ontop vase.n.01_1 cabinet.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching cabinet.n.01_1 rose.n.01_1)
(touching cabinet.n.01_1 rose.n.01_2)
(touching cabinet.n.01_1 rose.n.01_3)
(touching cabinet.n.01_1 vase.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching rose.n.01_1 cabinet.n.01_1)
(touching rose.n.01_2 cabinet.n.01_1)
(touching rose.n.01_3 cabinet.n.01_1)
(touching vase.n.01_1 cabinet.n.01_1)
```

## What the human demos did

200 annotated demos. Length 144.2 s (range 102.93-268.8). Skills per demo 14.0 (range 11-16). 18 distinct skill orders; the most common one covers 44% of demos.

Most common skill counts per demo (45% of demos): move to x6, pick up from x4, place in x3, place on x1.

Representative demo `episode_00562440.json` (146.3 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the rose` (0.0-13.0 s)
2. `pick up the rose from the bottom cabinet` (13.0-25.0 s)
3. `move to the rose` (25.0-34.0 s)
4. `pick up the rose from the bottom cabinet` (34.0-46.0 s)
5. `move to the vase` (46.0-53.0 s)
6. `place the rose in the vase` (53.0-63.0 s)
7. `place the rose in the vase` (63.0-73.0 s)
8. `move to the rose` (73.0-80.1 s)
9. `pick up the rose from the bottom cabinet` (80.1-97.0 s)
10. `move to the vase` (97.0-103.0 s)
11. `place the rose in the vase` (103.0-110.8 s)
12. `pick up the vase from the bottom cabinet` (110.8-120.9 s)
13. `move to the coffee table` (120.9-136.7 s)
14. `place the vase on the coffee table` (136.7-146.0 s)

Mean duration per skill in this task: hand over 7.8 s, move to 10.4 s, pick up from 12.8 s, place in 10.7 s, place on 10.0 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `pick up the rose from the bottom cabinet` | 600 |
| `place the rose in the vase` | 599 |
| `move to the rose` | 567 |
| `move to the vase` | 325 |
| `pick up the vase from the bottom cabinet` | 200 |
| `move to the coffee table` | 200 |
| `place the vase on the coffee table` | 200 |
| `hand over the rose` | 3 |
| `move to the bottom cabinet` | 1 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/56_make_rose_centerpieces.json`. Planner notes: `task_docs/notes/56_make_rose_centerpieces.md`.
