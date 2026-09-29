# 65 · Unloading The Car

Task name `unloading_the_car`, task index 65.

> Open the car, take out the briefcase and satchel, and place them on the floor outside the car.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | garage, living_room |
| rooms loaded | garage_0, corridor_0, living_room_0, kitchen_0, garden_0 |
| human demo length | 377.4 s mean (11323 steps) |
| episode time limit | 566.2 s (16985 steps at 30 Hz) |
| human base travel | 33.706 m |
| goal literals (best ground option) | 2 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@local Q=0.00 |
| demo video | https://www.youtube.com/embed/IBV8nn39hTM |

## Planner notes

**Tier:** C — the car's articulated trunk lid has to be opened, and two bags have to be carried ~10 m through a doorway.

### Goal in plain words

The briefcase and the satchel must both end `nextto` the sofa in living_room_0. They start in the car's trunk in the garage. The instruction says "on the floor outside the car", but the BDDL only checks nearness to the sofa. The car lid, the garage door and the garage/corridor door are not in the goal, so leaving them open costs nothing.

### Q traps

- 2 literals, both false at reset. Each bag is worth 0.5.
- `nextto` (PREDICATES §5): the AABB gap must be at most L/6. Here that allows about **0.35 m** (briefcase) and **0.38 m** (satchel) to the sofa's AABB. The sofa is 1.79 × 3.29 × 0.67 m (x 1.0-2.8, y 4.4-7.7). In addition, a horizontal ray from one AABB centre must hit the other object.
  - A bag on the floor has its centre ~5-11 cm above the floor. Whether those rays hit the sofa body or pass under it is unverified. Put the bag right against the sofa's side or front, not 30 cm away.
- A bag dropped on the sofa seat also passes the distance test, because the gap is 0. It is not the demo behaviour and is untested.
- Only the final state counts. A bag left by the car scores 0.

### Minimal plan

1. `move to the door` — facing the garage→corridor door `door_bexenl_0` (x -3.89, y 2.38). ~28 s.
2. `open the door of the door` — it starts closed (joint_pos 0), and all 200 demos open it. ~18 s.
3. `move to the car` — at the car's rear. The car is 5 m long, centred at x -4.43, and its rear is at x ≈ -6.96. The bags sit ~0.5 m inside the rear. ~28 s.
4. `open the lid of the car` — the trunk lid is visibly raised. ~49 s, the slowest skill in the demos.
5. `pick up the briefcase from the car` — gripper closed on the handle, briefcase lifted clear. ~28 s.
6. `pick up the satchel from the car` — other hand. ~28 s.
7. `move to the sofa` — carrying both bags. ~45 s. Route: garage → door → corridor → living_room_0. The template has no door object between the corridor and living_room_0.
8. `place the satchel on the floors` — against the sofa. ~20 s.
9. `place the briefcase on the floors` — against the sofa. ~20 s.

About 290 s against a 566 s limit. There is no trained "place … next to the sofa" sentence; the demos use `place the <bag> on the floors` after `move to the sofa`.

### What the demos do differently

- 138/200 pick both bags, put the satchel down on the garage floor, `close the lid of the car`, then `pick up the satchel from the floors` again. The lid close is not in the goal; skipping it saves ~40 s and one regrasp.
- 26/200 pick the satchel first. 20/200 add `push … to the car` or `turn to` to reach a bag deeper in the trunk.
- All 200 open the interior door first. All 200 also end with both bags placed on the floor after `move to the sofa`.

### Hard parts and hacks

- **Trunk lid:** a heavy articulated link (the car has one joint, link `trunk`). Opening it is the longest demo skill. Nothing verifies that a closed-gripper push can lift it.
- **Bag sizes:** briefcase 0.26 × 0.30 × 0.09 m, satchel 0.41 × 0.49 × 0.22 m. Neither body fits the 44 mm span, so the grasp must be on a handle or strap. Handle widths are not in the metadata (unverified).
- The bag poses vary slightly (spread 0.6-0.8 m, random yaw), so the handle direction changes per instance.
- Carrying two bags at arm's length over ~10 m risks tipping (robot facts). Keep the loads low while driving.
- Possible cheap shortcut: one bag per trip. It is slower, but a drop only costs that bag.

### Hints for the VLM

- The garage holds one car (`car_ssxsje`); a second car stands outside in the garden (`car_xxsgpq`). Use the one in the garage.
- The bags are in the rear trunk at ~0.8-0.86 m height.
- living_room_0 has exactly one sofa. It is a large 3.3 m sofa and the only upholstered seat there.
- Done looks like: both bags resting on the floor touching or almost touching the sofa, with no gap wider than a hand.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(nextto briefcase.n.01_1 sofa.n.01_1)` | no | yes |
| `(nextto satchel.n.01_1 sofa.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (forall 
                (?briefcase.n.01 - briefcase.n.01)
                (nextto ?briefcase.n.01 ?sofa.n.01_1)
            )
            (forall
                (?satchel.n.01 - satchel.n.01)
                (nextto ?satchel.n.01 ?sofa.n.01_1)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `car.n.01_1` | car_ssxsje_0 | car / ssxsje | garage_0 | table/counter (0.6-1.1 m), z 0.67 | 3.14 m (range 1.89-4.24) | no (fixed) |
| `floor.n.01_1` | floors_nbxnpk_0 | floors / nbxnpk | garage_0 | floor, z -0.15 | 2.06 m (range 0.38-3.21) | no (fixed) |
| `briefcase.n.01_1` | briefcase_84 | briefcase / psvdau | garage_0 | table/counter (0.6-1.1 m), z 0.8 | 3.19 m (range 1.63-4.94) | yes, spread 0.84 m |
| `satchel.n.01_1` | satchel_83 | satchel / ppzjuj | garage_0 | table/counter (0.6-1.1 m), z 0.86 | 3.16 m (range 1.58-4.63) | yes, spread 0.61 m |
| `sofa.n.01_1` | sofa_frlxgz_0 | sofa / frlxgz | living_room_0 | low (0.25-0.6 m), z 0.28 | 7.06 m (range 4.14-10.17) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "garage",
  "living_room"
 ],
 "house_double_floor_lower": {
  "whitelist": {
   "briefcase.n.01": {
    "briefcase": {
     "psvdau": null
    }
   },
   "satchel.n.01": {
    "satchel": {
     "ppzjuj": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(inroom car.n.01_1 garage)
(inroom floor.n.01_1 garage)
(inroom sofa.n.01_1 living_room)
(inside briefcase.n.01_1 car.n.01_1)
(inside satchel.n.01_1 car.n.01_1)
(ontop agent.n.01_1 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
```

## What the human demos did

200 annotated demos. Length 361.32 s (range 263.27-611.7). Skills per demo 15.0 (range 12-20). 22 distinct skill orders; the most common one covers 38% of demos.

Most common skill counts per demo (38% of demos): move to x6, pick up from x3, place on x3, close lid x1, open door x1, open lid x1.

Representative demo `episode_00651090.json` (362.3 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the door` (0.0-16.0 s)
2. `open the door of the door` (16.0-35.0 s)
3. `move to the car` (35.0-70.2 s)
4. `open the lid of the car` (70.2-115.5 s)
5. `pick up the briefcase from the car` (115.5-146.5 s)
6. `pick up the satchel from the car` (146.5-181.1 s)
7. `move to the floors` (181.1-203.3 s)
8. `place the satchel on the floors` (203.3-232.4 s)
9. `move to the car` (232.4-237.9 s)
10. `close the lid of the car` (237.9-249.0 s)
11. `move to the floors` (249.0-255.8 s)
12. `pick up the satchel from the floors` (255.8-273.4 s)
13. `move to the sofa` (273.4-318.7 s)
14. `place the satchel on the floors` (318.7-334.7 s)
15. `place the briefcase on the floors` (334.7-362.0 s)

Mean duration per skill in this task: close lid 11.3 s, move to 27.8 s, open door 17.6 s, open lid 48.9 s, pick up from 28.2 s, place on 19.5 s, push to 25.7 s, turn to 10.4 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `place the satchel on the floors` | 390 |
| `move to the car` | 367 |
| `move to the floors` | 250 |
| `place the briefcase on the floors` | 212 |
| `pick up the briefcase from the car` | 201 |
| `move to the sofa` | 201 |
| `move to the door` | 200 |
| `open the door of the door` | 200 |
| `open the lid of the car` | 200 |
| `close the lid of the car` | 200 |
| `pick up the satchel from the car` | 199 |
| `pick up the satchel from the floors` | 187 |
| `move to the satchel` | 73 |
| `pick up the briefcase from the floors` | 13 |
| `push the satchel to the car` | 12 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/65_unloading_the_car.json`. Planner notes: `task_docs/notes/65_unloading_the_car.md`.
