# 63 · Installing Smoke Detectors

Task name `installing_smoke_detectors`, task index 63.

> Attach the two smoke detectors to the wall nails.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | living_room |
| rooms loaded | corridor_0, kitchen_0, living_room_0, garden_0 |
| human demo length | 85.6 s mean (2568 steps) |
| episode time limit | 128.4 s (3853 steps at 30 Hz) |
| human base travel | 8.6081 m |
| goal literals (best ground option) | 1 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://www.youtube.com/embed/gRtLcTllXqQ |

## Planner notes

**Tier:** C — one pick-and-place, but the alarm is a 100 x 100 x 38 mm disc lying flat, and it must be mounted on a wall nail 1.71 m up within 5 cm and 15°.

### Goal in plain words

One literal: `attached fire_alarm_102 wall_nail_wlnail_1`. The task sentence says "two smoke detectors"; the BDDL has only one fire alarm and one nail, so one attach is full success. The attach happens by itself the moment the alarm's back mount touches the nail in the right pose; no release is needed, and success ends the episode on that step.

### Q traps

- Single literal, so Q is 0 or 1. There is no partial credit for carrying the alarm near the nail.
- Page error: the BDDL puts the nail `inroom living_room`, but the sampled scene object `wall_nail_wlnail_1` is listed `in_rooms ['kitchen_0']` in the template and sits at (8.40, 2.87, 1.71) in all 20 instances. The alarm starts on the living-room coffee table around (3.2-3.9, 4.6-5.9). Expect ~5.5 m of travel.
- Time limit is only 128 s (demo mean 86 s). Every re-grasp costs ~20 s; two failed grasps use up the budget.
- The other two `wall_nail` objects in the scene are in `garage_0`, which is not loaded. There is no distractor nail.
- The alarm's toggle button (`togglebutton` on the front face) is irrelevant; pressing it does not matter.

### Minimal plan

1. `move to the fire alarm` — the white disc on the coffee table is centred in the head camera. ~22 s demo mean; the table is 1.1-2.0 m away, so less.
2. `pick up the fire alarm from the coffee table` — gripper closed but not fully, disc lifted clear of the table. ~21 s.
3. `move to the wall nail` — base stopped facing the wall with the nail at the top of the image. ~22 s (longest leg).
4. `attach the fire alarm to the wall nail` — disc stays on the wall after the gripper opens; episode ends with success if attached. ~11 s.

This is exactly the demo plan (156/200 demos). Nothing can be dropped.

### What the demos do differently

- 44 of 200 demos put the alarm back on the coffee table and re-grasp it (`place the fire alarm on the coffee table`), presumably to fix the grip orientation for wall mounting. A planner should allow one such re-grasp if the disc is held face-down.
- No demo uses a hand-over or second arm.

### Hard parts and hacks

- Grasp: the disc is 100 mm across and 38 mm thick (asset bbox, scale 1.0). Only the 38 mm thickness fits the 44 mm jaw span, and while it lies flat that needs a finger under it (same problem as the books). Pinching it at the table edge, or tipping it up against something first, are the realistic options. Unverified whether assisted grasp registers at all.
- Mount geometry: the male link `displaywallM` is at the disc's back centre (z -15 mm) with a 90° pitched frame; the nail's `displaywallF` is 15 mm behind the nail tip. The disc must be held upright, back face to the wall, centred on the nail, within 5 cm and 15° (PREDICATES §10). A top-down grasp that leaves the disc horizontal will never attach.
- Height: the nail is at z 1.71 m. The trunk must be extended and the arm raised; carrying the load high risks tipping the base. Approach close to the wall before raising the arm.
- The nail is tiny (about 19 x 19 x 29 mm after the 2.44 scale), so it is hard to see at range. Localise it from the wall first, then servo the alarm onto it.
- Contact with the nail is required (any substep since the last step). Pushing the disc flat against the wall slightly beside the nail will not attach.
- No legal scripted shortcut: attach needs real contact and alignment.

### Hints for the VLM

- The coffee table is the large low table (0.8 x 1.66 m, top ~0.4 m) in `living_room_0`; the alarm is a white round disc, the only small object on it.
- The nail is in `kitchen_0`, on a wall at about 1.7 m, alone on bare wall. It is a small dark peg; look for it at head height, not near the floor.
- Done looks like: the white disc flat against the wall at head height, not in the gripper and not falling. If it drops after release, it did not attach.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(attached fire_alarm.n.02_1 wall_nail.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (attached fire_alarm.n.02_1 wall_nail.n.01_1)
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `wall_nail.n.01_1` | wall_nail_wlnail_1 | wall_nail / wlnail | kitchen_0 | very high (>1.6 m), z 1.71 | 4.48 m (range 3.94-5.72) | no (fixed) |
| `floor.n.01_1` | floors_ulujpr_0 | floors / ulujpr | living_room_0 | floor, z -0.15 | 1.19 m (range 0.73-1.46) | no (fixed) |
| `table.n.02_1` | coffee_table_koagbh_0 | coffee_table / koagbh | living_room_0 | low (0.25-0.6 m), z 0.36 | 1.56 m (range 1.08-1.96) | no |
| `fire_alarm.n.02_1` | fire_alarm_102 | fire_alarm / dkwmmf | living_room_0 | low (0.25-0.6 m), z 0.44 | 1.63 m (range 1.11-2.42) | yes, spread 1.45 m |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "living_room",
  "kitchen",
  "garden"
 ],
 "house_double_floor_lower": {
  "whitelist": {
   "fire_alarm.n.02": {
    "fire_alarm": {
     "dkwmmf": null
    }
   },
   "wall_nail.n.01": {
    "wall_nail": {
     "wlnail": null
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
(inroom table.n.02_1 living_room)
(inroom wall_nail.n.01_1 living_room)
(ontop agent.n.01_1 floor.n.01_1)
(ontop fire_alarm.n.02_1 table.n.02_1)
(touching agent.n.01_1 floor.n.01_1)
(touching fire_alarm.n.02_1 table.n.02_1)
(touching floor.n.01_1 agent.n.01_1)
(touching table.n.02_1 fire_alarm.n.02_1)
```

## What the human demos did

200 annotated demos. Length 81.0 s (range 53.4-155.1). Skills per demo 4.0 (range 4-8). 5 distinct skill orders; the most common one covers 78% of demos.

Most common skill counts per demo (78% of demos): move to x2, attach x1, pick up from x1.

Representative demo `episode_00630980.json` (77.3 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the fire alarm` (0.0-14.0 s)
2. `pick up the fire alarm from the coffee table` (14.0-36.0 s)
3. `move to the wall nail` (36.0-70.7 s)
4. `attach the fire alarm to the wall nail` (70.7-77.0 s)

Mean duration per skill in this task: attach 11.1 s, move to 21.9 s, pick up from 21.0 s, place on 7.0 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `pick up the fire alarm from the coffee table` | 244 |
| `move to the fire alarm` | 221 |
| `move to the wall nail` | 200 |
| `attach the fire alarm to the wall nail` | 200 |
| `place the fire alarm on the coffee table` | 44 |
| `move to the coffee table` | 2 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/63_installing_smoke_detectors.json`. Planner notes: `task_docs/notes/63_installing_smoke_detectors.md`.
