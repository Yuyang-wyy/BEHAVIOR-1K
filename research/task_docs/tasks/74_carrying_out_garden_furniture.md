# 74 · Carrying Out Garden Furniture

Task name `carrying_out_garden_furniture`, task index 74.

> Carry the garden chairs and wheelbarrow out to the lawn.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | garden, living_room |
| rooms loaded | corridor_0, dining_room_0, entryway_0, garden_0, kitchen_0, living_room_0, living_room_1 |
| human demo length | 368.6 s mean (11058 steps) |
| episode time limit | 552.9 s (16588 steps at 30 Hz) |
| human base travel | 61.164 m |
| goal literals (best ground option) | 2 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://www.youtube.com/embed/NCQc0IIRmos |

## Planner notes

**Tier:** C — two large pieces of furniture (a chair 0.74 × 1.05 × 0.81 m and a wheelbarrow 1.58 × 0.76 × 0.67 m) must be moved ~10-15 m out through a sliding door.

### Goal in plain words

- The garden chair must end resting on the garden floor object `floors_pyoemr_0`, the paved area around the pool.
- The wheelbarrow must end resting on the lawn (`lawn_wwoqjw_0`).
- Both start on the living_room_0 floor.
- The sliding door is not in the goal.

### Q traps

- 2 literals, both false at reset. Each is worth 0.5.
- Result on 311 (ft40k): Q = 0.00.
- **Surface identity matters** (PREDICATES §4): `ontop` needs contact with that exact object.
  - The chair on grass, or the wheelbarrow on paving, scores 0.
  - Both surfaces are 0.28 m slabs with their tops at the same height, and their bounding boxes overlap in plan. Tell them apart by look (paving vs grass), not by height.
- The pool (`swimming_pool_vnvmkx_0`) is sunken (root z -0.96). A chair that falls in touches the pool, not the floor, and scores 0.
- The wheelbarrow rests on its wheel and legs. All of them should touch the lawn, and its centre must be over the lawn.

### Minimal plan

1. `move to the slide door` ~28 s (trained string; the demos write "slide door").
2. `open the door of the slide door` — the 4.2 m sliding door `sliding_door_lrvyvc_0` (x 12.3, y 4.12) is visibly open. It starts closed (joint_pos 0). ~28 s.
3. `move to the garden chair`, `pick up the garden chair from the floors` ~53 + 14 s. Alternative: `push the garden chair to the floors` (51 demos).
4. `move to the pool` — carry it out to the paving beside the pool. ~53 s.
5. `place the garden chair on the floors next to the pool` — chair upright on paving, not on grass, not over the pool edge. ~7 s.
6. `move to the wheelbarrow`, `pick up the wheelbarrow from the floors` ~53 + 14 s. Alternative: `push the wheelbarrow to the floors`.
7. `move to the lawn` — the demo representative took 122 s here. ~53-120 s.
8. `place the wheelbarrow on the lawn` — all wheels/legs on grass. ~9 s.

Demo mean 369 s against a 553 s limit. Base travel in the demos is 61 m.

### What the demos do differently

- 80/200 follow the plan above as written. Others insert a `push … to the floors` before the pick (51 chair and 43 wheelbarrow push segments across the demos) or a `turn to the wheelbarrow`.
- 14/200 push the chair before opening the door.
- The demos log 184 `move to the slide door` segments; the door is usually approached separately from the chair.

### Hard parts and hacks

- **Size and weight:** both objects are far larger than the gripper. A grasp must use a thin frame member of the chair or the wheelbarrow's handle; widths are unverified. Carrying a 1.6 m wheelbarrow extended can tip the robot (robot facts).
- **Pushing is a real option:** the wheelbarrow has a wheel joint, and the demos push each object part of the way in roughly a quarter of episodes. A base push through the 4.2 m doorway is plausible, but it is not verified that pushing works over the door threshold.
- Starts: the chair and wheelbarrow each move up to ~8 m between instances, but always inside living_room_0 (x 9.7-17.1, y -0.3 to 3.3). The door is at y 4.12, the garden side.
- The lawn object spans 53 × 59 m. Where the grass is actually exposed near the house is not verified; follow the demo `move to the lawn` and check for grass under the wheels.

### Hints for the VLM

- house_single_floor living_room_0 has a 4.2 m sliding door to the garden. The pool lies ~5 m beyond it (pool AABB starts at y ≈ 9.6).
- The garden chair is the outdoor chair standing on the living-room floor. The wheelbarrow is the barrow with a wheel, also on the living-room floor.
- Done: the chair standing on paving near the pool, and the wheelbarrow standing on grass.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(ontop lawn_chair.n.01_1 floor.n.01_2)` | no | yes |
| `(ontop barrow.n.03_1 lawn.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal
        (and
            (ontop ?lawn_chair.n.01_1 ?floor.n.01_2)
            (exists
                (?lawn.n.01 - lawn.n.01)
                (ontop ?barrow.n.03_1 ?lawn.n.01)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `lawn_chair.n.01_1` | garden_chair_454 | garden_chair / cottya | living_room_0 | low (0.25-0.6 m), z 0.44 | 2.72 m (range 1.68-4.35) | yes, spread 8.26 m |
| `floor.n.01_1` | floors_uzsntg_0 | floors / uzsntg | living_room_0 | floor, z -0.14 | 2.05 m (range 1.02-3.63) | no (fixed) |
| `floor.n.01_2` | floors_pyoemr_0 | floors / pyoemr | garden_0 | floor, z -0.16 | 15.2 m (range 13.71-17.96) | no (fixed) |
| `barrow.n.03_1` | wheelbarrow_453 | wheelbarrow / msaevo | living_room_0 | low (0.25-0.6 m), z 0.44 | 3.08 m (range 1.23-6.67) | yes, spread 8.21 m |
| `lawn.n.01_1` | lawn_wwoqjw_0 | lawn / wwoqjw | garden_0 | floor, z -0.16 | 15.33 m (range 13.91-18.09) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "corridor",
  "dining_room",
  "entryway",
  "garden",
  "kitchen",
  "living_room"
 ],
 "house_single_floor": {
  "whitelist": {
   "barrow.n.03": {
    "wheelbarrow": {
     "msaevo": null
    }
   },
   "lawn_chair.n.01": {
    "garden_chair": {
     "cottya": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(inroom floor.n.01_1 living_room)
(inroom floor.n.01_2 garden)
(inroom lawn.n.01_1 garden)
(ontop agent.n.01_1 floor.n.01_1)
(ontop barrow.n.03_1 floor.n.01_1)
(ontop lawn_chair.n.01_1 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching barrow.n.03_1 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 barrow.n.03_1)
(touching floor.n.01_1 lawn_chair.n.01_1)
(touching lawn_chair.n.01_1 floor.n.01_1)
```

## What the human demos did

200 annotated demos. Length 364.98 s (range 282.97-464.87). Skills per demo 11.0 (range 10-15). 26 distinct skill orders; the most common one covers 40% of demos.

Most common skill counts per demo (40% of demos): move to x5, pick up from x2, open door x1, place on x1, place on next to x1.

Representative demo `episode_00740460.json` (356.3 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the garden chair` (0.0-25.0 s)
2. `open the door of the slide door` (25.0-58.0 s)
3. `move to the garden chair` (58.0-89.0 s)
4. `pick up the garden chair from the floors` (89.0-112.0 s)
5. `move to the pool` (112.0-146.0 s)
6. `place the garden chair on the floors next to the pool` (146.0-154.0 s)
7. `move to the wheelbarrow` (154.0-208.0 s)
8. `pick up the wheelbarrow from the floors` (208.0-224.0 s)
9. `move to the lawn` (224.0-346.0 s)
10. `place the wheelbarrow on the lawn` (346.0-356.0 s)

Mean duration per skill in this task: move to 53.1 s, open door 27.6 s, pick up from 13.8 s, place on 8.9 s, place on next to 7.0 s, push to 19.3 s, turn to 15.9 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the garden chair` | 249 |
| `move to the wheelbarrow` | 231 |
| `open the door of the slide door` | 200 |
| `pick up the garden chair from the floors` | 200 |
| `move to the pool` | 200 |
| `pick up the wheelbarrow from the floors` | 200 |
| `move to the lawn` | 200 |
| `place the wheelbarrow on the lawn` | 200 |
| `place the garden chair on the floors next to the pool` | 199 |
| `move to the slide door` | 184 |
| `push the garden chair to the floors` | 51 |
| `push the wheelbarrow to the floors` | 43 |
| `turn to the wheelbarrow` | 18 |
| `push the garden chair to the slide door` | 16 |
| `push the wheelbarrow to the slide door` | 8 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/74_carrying_out_garden_furniture.json`. Planner notes: `task_docs/notes/74_carrying_out_garden_furniture.md`.
