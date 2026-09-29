# 83 · Store Honey

Task name `store_honey`, task index 83.

> Put the jar of honey into the cabinet drawer, then close the drawer.

## At a glance

| item | value |
| --- | --- |
| scene | `Rs_int` |
| rooms in the goal | entryway, kitchen, living_room |
| rooms loaded | bedroom_0, entryway_0, kitchen_0, living_room_0 |
| human demo length | 225.6 s mean (6766 steps) |
| episode time limit | 338.3 s (10150 steps at 30 Hz) |
| human base travel | 12.0735 m |
| goal literals (best ground option) | 1 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | not evaluated yet |
| demo video | https://www.youtube.com/embed/oFu38YPgVEU |

## Planner notes

**Tier:** C — one pick and one drawer place, but the jar (forced size 75 x 85 x 150 mm) is wider than the 44 mm jaw span on both short axes, and it sits on a high counter behind bar chairs.

### Goal in plain words

The jar of honey must be inside the entryway bottom cabinet (`bottom_cabinet_slgzfc_0`). The goal has **no** `not open` literal, so the drawer may stay open. Nothing else is checked.

### Q traps

- One literal: Q is 0 or 1.
- The task sentence says "then close the drawer", but that is not a goal literal.
- `inside` tests the jar's AABB centre against the cabinet's fillable volume (PREDICATES §3). Whether an open drawer carries its own volume is not verified; if only the carcass has one, the jar counts only once the drawer is shut. Close it anyway (~10 s).
- The jar is 0.15 m tall. A drawer too shallow for it will jam on closing and can push the jar's centre out. Pick the drawer by eye; drawer depths are not verified.
- All four openable links of the cabinet start closed (joint_pos 0 in all 20 instances).

### Minimal plan

1. `move to the chair` / `pick up the chair from the floors` / `move to the floors` / `place the chair on the floors` — only if a bar chair blocks the counter in front of the jar. ~55 s.
2. `move to the jar of honey` — jar on the counter in view. ~14 s.
3. `pick up the jar of honey from the countertop` — jar lifted, gripper stopped short of closed. ~14 s.
4. `move to the cabinet` — entryway cabinet front in view. ~14 s.
5. `open the drawer of the cabinet` — drawer visibly out. ~12 s.
6. `place the jar of honey in the cabinet` — jar standing in the drawer. ~7 s.
7. `close the drawer of the cabinet` — drawer flush, jar not visible. ~10 s.

Budget: 338 s limit vs 226 s demo mean. Without the chair detour the plan is about 70 s of skills plus walking.

### What the demos do differently

- All 200 demos follow one order. They move a chair away, carry the jar to the breakfast table, put the chair back, pick the jar up again, and only then go to the cabinet. The breakfast-table stop and the chair return are not needed.
- A few demos (2) say `move to the storage container` for the cabinet. Stick with `move to the cabinet`.

### Hard parts and hacks

- Grasp: the task forces the jar to 0.075 x 0.085 x 0.15 m. Neither short axis fits 44 mm, and the jar has no handle. Grasp may fail outright; the lid rim is not a separate part (single link, not verified to be narrower).
- Height: the jar stands on the counter top at about 1.08 m (jar centre z 1.16), behind two straight chairs at (-0.4, 1.1) and (-1.26, 1.1).
- The cabinet is in entryway_0 at (1.67, 2.2), facing -x; 2.5-3.5 m from the start.
- Opening the drawer needs its handle; handle width is not verified.

### Hints for the VLM

- Scene Rs_int. The jar is the only jar on the high counter between the kitchen and the living room.
- `the cabinet` in the demo prompts is the single bottom cabinet in the entryway. Five other bottom cabinets exist (two in the kitchen, two in the living room, one in the bedroom); they are not in scope.
- Done: jar inside the entryway cabinet, drawer closed.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside jar__of__honey.n.01_1 cabinet.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (inside ?jar__of__honey.n.01_1 ?cabinet.n.01_1)
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `jar__of__honey.n.01_1` | jar_of_honey_72 | jar_of_honey / wdxfaq | kitchen_0, living_room_0 | high (1.1-1.6 m), z 1.16 | 2.24 m (range 1.33-3.41) | yes, spread 1.56 m |
| `countertop.n.01_1` | countertop_tpuwys_0 | countertop / tpuwys | kitchen_0, living_room_0 | table/counter (0.6-1.1 m), z 1.06 | 2.2 m (range 1.22-2.87) | no (fixed) |
| `cabinet.n.01_1` | bottom_cabinet_slgzfc_0 | bottom_cabinet / slgzfc | entryway_0 | low (0.25-0.6 m), z 0.42 | 2.94 m (range 2.46-3.47) | no (fixed) |
| `floor.n.01_1` | floors_ptwlei_0 | floors / ptwlei | living_room_0 | floor, z -0.15 | 1.07 m (range 0.56-1.79) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "bedroom",
  "entryway",
  "kitchen",
  "living_room"
 ],
 "Rs_int": {
  "whitelist": {
   "jar__of__honey.n.01": {
    "jar_of_honey": {
     "wdxfaq": [
      0.075,
      0.085,
      0.15
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
(inroom cabinet.n.01_1 entryway)
(inroom countertop.n.01_1 kitchen)
(inroom floor.n.01_1 living_room)
(ontop agent.n.01_1 floor.n.01_1)
(ontop jar__of__honey.n.01_1 countertop.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching countertop.n.01_1 jar__of__honey.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching jar__of__honey.n.01_1 countertop.n.01_1)
```

## What the human demos did

200 annotated demos. Length 240.87 s (range 95.37-336.57). Skills per demo 18.0 (range 6-18). 2 distinct skill orders; the most common one covers 100% of demos.

Most common skill counts per demo (100% of demos): move to x8, pick up from x4, place on x3, close drawer x1, open drawer x1, place in x1.

Representative demo `episode_00831080.json` (241.2 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the chair` (0.0-11.0 s)
2. `pick up the chair from the floors` (11.0-28.0 s)
3. `move to the floors` (28.0-40.3 s)
4. `place the chair on the floors` (40.3-48.0 s)
5. `move to the jar of honey` (48.0-65.0 s)
6. `pick up the jar of honey from the countertop` (65.0-74.0 s)
7. `move to the breakfast table` (74.0-91.0 s)
8. `place the jar of honey on the breakfast table` (91.0-107.8 s)
9. `move to the chair` (107.8-126.0 s)
10. `pick up the chair from the floors` (126.0-143.0 s)
11. `move to the countertop` (143.0-154.0 s)
12. `place the chair on the floors` (154.0-162.0 s)
13. `move to the jar of honey` (162.0-177.0 s)
14. `pick up the jar of honey from the breakfast table` (177.0-190.0 s)
15. `move to the cabinet` (190.0-208.0 s)
16. `open the drawer of the cabinet` (208.0-218.0 s)
17. `place the jar of honey in the cabinet` (218.0-228.6 s)
18. `close the drawer of the cabinet` (228.6-237.0 s)

Mean duration per skill in this task: close drawer 10.0 s, move to 13.7 s, open drawer 11.6 s, pick up from 14.1 s, place in 7.0 s, place on 10.3 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the chair` | 401 |
| `pick up the chair from the floors` | 398 |
| `place the chair on the floors` | 398 |
| `move to the jar of honey` | 395 |
| `move to the cabinet` | 201 |
| `pick up the jar of honey from the countertop` | 200 |
| `move to the breakfast table` | 200 |
| `open the drawer of the cabinet` | 200 |
| `place the jar of honey in the cabinet` | 200 |
| `close the drawer of the cabinet` | 200 |
| `place the jar of honey on the breakfast table` | 199 |
| `pick up the jar of honey from the breakfast table` | 199 |
| `move to the countertop` | 198 |
| `move to the floors` | 197 |
| `move to the storage container` | 2 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/83_store_honey.json`. Planner notes: `task_docs/notes/83_store_honey.md`.
