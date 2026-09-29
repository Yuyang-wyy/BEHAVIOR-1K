# 85 · Putting Dirty Dishes In Sink

Task name `putting_dirty_dishes_in_sink`, task index 85.

> Put all of the dirty bowls and plates into the kitchen sink.

## At a glance

| item | value |
| --- | --- |
| scene | `restaurant_diner` |
| rooms in the goal | dining_room, kitchen |
| rooms loaded | kitchen_0, bar_0, dining_room_0, corridor_0 |
| human demo length | 405.0 s mean (12148 steps) |
| episode time limit | 607.4 s (18222 steps at 30 Hz) |
| human base travel | 57.395 m |
| goal literals (best ground option) | 4 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | not evaluated yet |
| demo video | https://www.youtube.com/embed/SCX0NPFlMhI |

## Planner notes

**Tier:** C — four dishes carried about 13 m through a bar flip-up and a closed kitchen door. The plates are flat (28 mm thick, lying on a table), and no dish has a bbox axis of 44 mm or less except the plate thickness.

### Goal in plain words

Both bowls and both plates must be inside the commercial kitchen sink. Stacking is fine: only each dish's AABB centre has to be inside the sink volume. The dirt and stain on the dishes are not in the goal; no cleaning is needed. Nothing else is checked, and the doors may stay open.

### Q traps

- Four literals, each 1/4, all false at reset.
- `inside` tests only the dish's AABB centre (PREDICATES §3). A dish perched on the sink rim or on the faucet deck does not count; a bowl stacked on a bowl inside the basin does.
- The sink `commercial_kitchen_sink_xecfyh_0` has fluid and toggle meta links; its fillable volume is not readable from metadata and is not verified here.
- The bar flip-up lid (`bar_xxftww_0`) and the kitchen door (`door_mkcndz_0`) start closed (joint_pos 0). Closing them again, as the demos do, is not a goal literal.

### Minimal plan

1. `move to the booth` — dishes on the booth table in view. ~34 s.
2. `pick up the bowl from the booth` twice, one per hand — both grippers stopped short of closed. ~8 s each.
3. `move to the flipup countertop` then `open the lid of the flipup countertop` — bar flap raised. ~34 s + 7 s.
4. `move to the kitchen door` then `open the door of the kitchen door` — door swung open. ~34 s + 10 s.
5. `move to the commercial kitchen sink` — basin in view. ~34 s.
6. `place the bowl in the commercial kitchen sink`, then `place the bowl on the bowl` — both bowls in the basin. ~15 s + 12 s.
7. `move to the booth`, `pick up the plate from the booth` twice, `move to the commercial kitchen sink`, `place the plate in the commercial kitchen sink`, `place the plate on the plate` — both plates in the basin. ~140 s.

Budget: 607 s limit vs 405 s demo mean. Skipping the demos' close-lid and close-door steps saves about 30 s plus two detours.

### What the demos do differently

- 98% of demos use one order: bowls first (both hands), open lid and door, sink; back for the plates; close lid and door on the second trip; sink.
- The closing steps (`close the lid of the flipup countertop`, `close the door of the kitchen door`) are housekeeping. Skip them.

### Hard parts and hacks

- Grasp widths (asset bboxes): bowl 0.117 x 0.105 x 0.060 m; plate 0.169 x 0.176 x 0.028 m. The bowl can only be held across its rim wall. The plate's 28 mm axis is vertical, so the jaws must get under its edge on the table. Expect plate grasps to fail.
- Distance: the dishes are on `booth_xzrpar_2` at (0.12, -9.11) in the far end of the dining room; the sink is in kitchen_0 at (-10.78, 0.92). Human base travel averaged 57 m per demo.
- Route: every demo passes the bar flip-up and the kitchen door, so treat both as on the path. Opening them needs graspable handles; widths not verified.
- Four booths are in the dining room; only `booth_xzrpar_2` holds dishes.

### Hints for the VLM

- Scene restaurant_diner. Two bowls and two plates sit together on one booth table. The robot starts about 2.2-11 m from them.
- The sink is the large commercial kitchen sink in kitchen_0; the bathroom's five furniture sinks are not the target.
- Done per literal: dish visible down in the basin, not on the rim.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside bowl.n.01_2 sink.n.01_1)` | no | yes |
| `(inside bowl.n.01_1 sink.n.01_1)` | no | yes |
| `(inside plate.n.04_1 sink.n.01_1)` | no | yes |
| `(inside plate.n.04_2 sink.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal
        (and
            (forall
                (?bowl.n.01 - bowl.n.01)
                (inside ?bowl.n.01 ?sink.n.01_1)
            )
            (forall
                (?plate.n.04 - plate.n.04)
                (inside ?plate.n.04 ?sink.n.01_1)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `stain.n.01_1` | particle system | stain | - | - | - | - |
| `dirt.n.02_1` | particle system | dirt | - | - | - | - |
| `bowl.n.01_1` | bowl_136 | bowl / fiarri | dining_room_0 | table/counter (0.6-1.1 m), z 0.78 | 3.78 m (range 2.12-11.11) | yes, spread 0.68 m |
| `bowl.n.01_2` | bowl_135 | bowl / fiarri | dining_room_0 | table/counter (0.6-1.1 m), z 0.78 | 3.9 m (range 1.91-10.7) | yes, spread 0.66 m |
| `plate.n.04_1` | plate_134 | plate / lkomhp | dining_room_0 | table/counter (0.6-1.1 m), z 0.77 | 3.82 m (range 2.16-10.9) | yes, spread 0.65 m |
| `plate.n.04_2` | plate_133 | plate / lkomhp | dining_room_0 | table/counter (0.6-1.1 m), z 0.77 | 3.93 m (range 2.16-11.03) | yes, spread 0.49 m |
| `booth.n.01_1` | booth_xzrpar_2 | booth / xzrpar | dining_room_0 | table/counter (0.6-1.1 m), z 0.62 | 4.12 m (range 2.44-11.26) | no (fixed) |
| `sink.n.01_1` | commercial_kitchen_sink_xecfyh_0 | commercial_kitchen_sink / xecfyh | kitchen_0 | table/counter (0.6-1.1 m), z 0.62 | 10.96 m (range 8.55-12.52) | no (fixed) |
| `floor.n.01_1` | floors_cxcxqq_0 | floors / cxcxqq | dining_room_0 | floor, z -0.0 | 3.12 m (range 1.1-5.21) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "kitchen",
  "dining_room"
 ],
 "restaurant_diner": {
  "whitelist": {
   "bowl.n.01": {
    "bowl": {
     "fiarri": null
    }
   },
   "plate.n.04": {
    "plate": {
     "lkomhp": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(covered bowl.n.01_1 dirt.n.02_1)
(covered bowl.n.01_2 dirt.n.02_1)
(covered plate.n.04_1 stain.n.01_1)
(covered plate.n.04_2 stain.n.01_1)
(inroom booth.n.01_1 dining_room)
(inroom floor.n.01_1 dining_room)
(inroom sink.n.01_1 kitchen)
(ontop agent.n.01_1 floor.n.01_1)
(ontop bowl.n.01_1 booth.n.01_1)
(ontop bowl.n.01_2 booth.n.01_1)
(ontop plate.n.04_1 booth.n.01_1)
(ontop plate.n.04_2 booth.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching booth.n.01_1 bowl.n.01_1)
(touching booth.n.01_1 bowl.n.01_2)
(touching booth.n.01_1 plate.n.04_1)
(touching booth.n.01_1 plate.n.04_2)
(touching bowl.n.01_1 booth.n.01_1)
(touching bowl.n.01_2 booth.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching plate.n.04_1 booth.n.01_1)
(touching plate.n.04_2 booth.n.01_1)
```

## What the human demos did

200 annotated demos. Length 395.53 s (range 308.27-518.47). Skills per demo 20.0 (range 18-20). 3 distinct skill orders; the most common one covers 98% of demos.

Most common skill counts per demo (98% of demos): move to x8, pick up from x4, place in x2, place on x2, close door x1, close lid x1, open door x1, open lid x1.

Representative demo `episode_00850650.json` (396.0 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the booth` (0.0-23.0 s)
2. `pick up the bowl from the booth` (23.0-33.3 s)
3. `pick up the bowl from the booth` (33.3-43.1 s)
4. `move to the flipup countertop` (43.1-62.4 s)
5. `open the lid of the flipup countertop` (62.4-69.4 s)
6. `move to the kitchen door` (69.4-79.0 s)
7. `open the door of the kitchen door` (79.0-87.6 s)
8. `move to the commercial kitchen sink` (87.6-130.0 s)
9. `place the bowl in the commercial kitchen sink` (130.0-143.4 s)
10. `place the bowl on the bowl` (143.4-154.7 s)
11. `move to the booth` (154.7-230.0 s)
12. `pick up the plate from the booth` (230.0-239.5 s)
13. `pick up the plate from the booth` (239.5-246.0 s)
14. `move to the bar` (246.0-278.0 s)
15. `close the lid of the flipup countertop` (278.0-287.0 s)
16. `move to the kitchen door` (287.0-331.9 s)
17. `close the door of the kitchen door` (331.9-347.6 s)
18. `move to the commercial kitchen sink` (347.6-370.0 s)
19. `place the plate in the commercial kitchen sink` (370.0-386.2 s)
20. `place the plate on the plate` (386.2-396.0 s)

Mean duration per skill in this task: close door 19.2 s, close lid 11.0 s, move to 33.6 s, open door 9.8 s, open lid 6.7 s, pick up from 8.4 s, place in 14.5 s, place on 12.2 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the booth` | 400 |
| `pick up the bowl from the booth` | 400 |
| `move to the commercial kitchen sink` | 400 |
| `pick up the plate from the booth` | 400 |
| `move to the kitchen door` | 398 |
| `move to the flipup countertop` | 200 |
| `open the lid of the flipup countertop` | 200 |
| `open the door of the kitchen door` | 200 |
| `place the bowl in the commercial kitchen sink` | 200 |
| `place the bowl on the bowl` | 200 |
| `place the plate in the commercial kitchen sink` | 200 |
| `place the plate on the plate` | 200 |
| `move to the bar` | 199 |
| `close the lid of the flipup countertop` | 199 |
| `close the door of the kitchen door` | 198 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/85_putting_dirty_dishes_in_sink.json`. Planner notes: `task_docs/notes/85_putting_dirty_dishes_in_sink.md`.
