# 90 · Composting Waste

Task name `composting_waste`, task index 90.

> Put the food waste into the compost bin.

## At a glance

| item | value |
| --- | --- |
| scene | `Rs_int` |
| rooms in the goal | entryway, kitchen, living_room |
| rooms loaded | entryway_0, kitchen_0, bedroom_0, living_room_0 |
| human demo length | 121.3 s mean (3638 steps) |
| episode time limit | 181.9 s (5457 steps at 30 Hz) |
| human base travel | 6.4352 m |
| goal literals (best ground option) | 2 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| starts open (joint_pos > 0.02) | `ashcan.n.01_1` in 20/20 instances |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://www.youtube.com/embed/RR3PLEFcdYg |

## Planner notes

**Tier:** B. This is two small pick-and-place moves into a floor bin. The half banana is 42 mm thick, just inside the ~44 mm jaw span. The half pomegranate is 76-93 mm on every axis, so a registered assisted grasp on it is doubtful.

### Goal in plain words

- Both food halves must end inside the kitchen trash can (`trash_can_66`, model ifzxzj), which stands on the kitchen floor.
- There are no other goal literals. Nothing needs closing, and the bin may stay where it is.
- The kitchen also has a `public_trash_can`. Food put in it earns nothing.

### Q traps

- There are 2 literals and both score (0/2 true at reset). Each one is worth 0.5.
- `inside` tests only the food's AABB centre against the bin's volume (PREDICATES §3). A half that lands on the rim or the lid does not count.
- The bin is 0.31 x 0.40 x 0.80 m (asset bbox, scale 1). A tipped bin loses anything already in it, so do not bump it while placing the second item.
- The bin's lid joint starts at 0.63-0.66 in all 20 instances (template and instance `joint_pos`). The joint limits are in the encrypted USD, so whether the lid is open or ajar is unverified. The demos never open it.

### Minimal plan

1. `move to the half pomegranate`. Done when the counter and the fruit are centred in the head camera and the base has stopped. About 10 s.
2. `pick up the half pomegranate from the countertop`. Done when the gripper is closed but not fully (the fingers stopped short) and the fruit is gone from the counter. About 10 s.
3. `move to the trash can`. Done when the bin is in front at arm's reach and the base has stopped. About 10 s.
4. `place the half pomegranate in the trash can`. Done when the gripper is open and the fruit is not visible on the rim or the floor. About 9 s.
5. `move to the half banana`. About 10 s.
6. `pick up the half banana from the countertop`. About 10 s.
7. `move to the trash can`. About 10 s.
8. `place the half banana in the trash can`. About 9 s.

- The plan totals about 80 s against a 181.9 s limit.
- To save one trip, pick both halves first, one per hand (two `pick up ... from the countertop` calls), then do one `move to the trash can` and two places. This is unverified: the modal demo order (88% of demos) carries one item per trip.

### What the demos do differently

- 100% of demos first carry the trash can to the furniture sink (`pick up the trash can from the floors`, `place the trash can on the floors next to the furniture sink`). The goal does not need this. Skip it and save about 35 s.
- Carrying the 0.8 m bin also risks tipping the robot. The bin stays a valid target wherever it ends up.
- The demos go pomegranate first, then banana. The order does not matter for the goal.

### Hard parts and hacks

- The pomegranate half has no dimension under 44 mm, so a VLA grasp may slip. If the grasp fails twice, try pushing the half off the counter edge into the bin. This only works if the bin sits next to the counter, which is unverified.
- The bin is 0.80 m tall. Release above the opening, not beside it. The fruit's centre has to end up in the cavity.
- The food and the bin move between instances (the food spreads about 1.5 m and the bin about 1.3 m). Do not reuse a fixed route.
- ft40k scored Q=0 on instance 311, so the task sentence alone does not work. Use skill sentences.

### Hints for the VLM

- Both halves start on the kitchen countertop (z ~1.06-1.12 m). The robot starts in the living room, 1.2-4.8 m away.
- The target bin is a 0.8 m tall kitchen trash can with a hinged lid. Do not use the public trash can, which is a different category.
- Done for each literal: the fruit is not visible on the counter or the floor, and looking down into the bin shows it inside.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside half__banana.n.01_1 ashcan.n.01_1)` | no | yes |
| `(inside half__pomegranate.n.01_1 ashcan.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (inside ?half__banana.n.01_1 ?ashcan.n.01_1) 
            (inside ?half__pomegranate.n.01_1 ?ashcan.n.01_1) 
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `countertop.n.01_1` | countertop_tpuwys_0 | countertop / tpuwys | kitchen_0, living_room_0 | table/counter (0.6-1.1 m), z 1.06 | 1.5 m (range 1.21-4.79) | no (fixed) |
| `half__banana.n.01_1` | half_banana_68 | half_banana / xytkre | kitchen_0, living_room_0 | table/counter (0.6-1.1 m), z 1.1 | 1.56 m (range 1.21-4.55) | yes, spread 1.55 m |
| `half__pomegranate.n.01_1` | half_pomegranate_67 | half_pomegranate / vqybii | kitchen_0, living_room_0 | high (1.1-1.6 m), z 1.12 | 1.7 m (range 1.3-4.85) | yes, spread 1.44 m |
| `ashcan.n.01_1` | trash_can_66 | trash_can / ifzxzj | kitchen_0 | low (0.25-0.6 m), z 0.33 | 2.27 m (range 1.8-5.7) | yes, spread 1.33 m |
| `floor.n.01_1` | floors_ifmioj_0 | floors / ifmioj | kitchen_0 | floor, z -0.15 | 2.5 m (range 2.19-5.73) | no (fixed) |
| `floor.n.01_2` | floors_ptwlei_0 | floors / ptwlei | living_room_0 | floor, z -0.15 | 1.55 m (range 0.61-1.92) | no (fixed) |
| `floor.n.01_3` | floors_gjemfr_0 | floors / gjemfr | entryway_0 | floor, z -0.15 | 2.98 m (range 2.31-5.45) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "entryway",
  "kitchen",
  "living_room"
 ],
 "Rs_int": {
  "whitelist": {
   "ashcan.n.01": {
    "trash_can": {
     "ifzxzj": null
    }
   },
   "half__banana.n.01": {
    "half_banana": {
     "xytkre": null
    }
   },
   "half__pomegranate.n.01": {
    "half_pomegranate": {
     "vqybii": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(inroom countertop.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(inroom floor.n.01_2 living_room)
(inroom floor.n.01_3 entryway)
(ontop agent.n.01_1 floor.n.01_2)
(ontop ashcan.n.01_1 floor.n.01_1)
(ontop half__banana.n.01_1 countertop.n.01_1)
(ontop half__pomegranate.n.01_1 countertop.n.01_1)
(open ashcan.n.01_1)
(touching agent.n.01_1 floor.n.01_2)
(touching ashcan.n.01_1 floor.n.01_1)
(touching countertop.n.01_1 half__banana.n.01_1)
(touching countertop.n.01_1 half__pomegranate.n.01_1)
(touching floor.n.01_1 ashcan.n.01_1)
(touching floor.n.01_2 agent.n.01_1)
(touching half__banana.n.01_1 countertop.n.01_1)
(touching half__pomegranate.n.01_1 countertop.n.01_1)
```

## What the human demos did

200 annotated demos. Length 119.17 s (range 89.1-181.33). Skills per demo 12.0 (range 10-12). 5 distinct skill orders; the most common one covers 88% of demos.

Most common skill counts per demo (88% of demos): move to x6, pick up from x3, place in x2, place on next to x1.

Representative demo `episode_00901200.json` (119.3 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the trash can` (0.0-13.0 s)
2. `pick up the trash can from the floors` (13.0-20.0 s)
3. `move to the furniture sink` (20.0-32.0 s)
4. `place the trash can on the floors next to the furniture sink` (32.0-47.0 s)
5. `move to the half pomegranate` (47.0-55.8 s)
6. `pick up the half pomegranate from the countertop` (55.8-66.3 s)
7. `move to the trash can` (66.3-75.0 s)
8. `place the half pomegranate in the trash can` (75.0-81.0 s)
9. `move to the half banana` (81.0-86.0 s)
10. `pick up the half banana from the countertop` (86.0-98.0 s)
11. `move to the trash can` (98.0-110.0 s)
12. `place the half banana in the trash can` (110.0-119.3 s)

Mean duration per skill in this task: move to 10.2 s, pick up from 9.8 s, place in 8.9 s, place on next to 12.8 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the trash can` | 562 |
| `pick up the half pomegranate from the countertop` | 201 |
| `place the half banana in the trash can` | 201 |
| `pick up the trash can from the floors` | 200 |
| `place the trash can on the floors next to the furniture sink` | 200 |
| `move to the half banana` | 200 |
| `move to the half pomegranate` | 199 |
| `place the half pomegranate in the trash can` | 199 |
| `pick up the half banana from the countertop` | 199 |
| `move to the furniture sink` | 195 |
| `move to the sink` | 3 |
| `move to the countertop` | 1 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/90_composting_waste.json`. Planner notes: `task_docs/notes/90_composting_waste.md`.
