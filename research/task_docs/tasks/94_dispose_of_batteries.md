# 94 · Dispose Of Batteries

Task name `dispose_of_batteries`, task index 94.

> Pick up all of the batteries and put them into the trash can.

## At a glance

| item | value |
| --- | --- |
| scene | `office_cubicles_right` |
| rooms in the goal | copy_room, private_office |
| rooms loaded | copy_room_0, corridor_0, private_office_0, private_office_1, private_office_2, private_office_3, shared_office_0 |
| human demo length | 480.9 s mean (14428 steps) |
| episode time limit | 721.4 s (21642 steps at 30 Hz) |
| human base travel | 46.6197 m |
| goal literals (best ground option) | 4 |
| literals already true at start (inferred) | 1 |
| max Q short of full success | 0.75 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://www.youtube.com/embed/TmJ7dNwDyws |

## Planner notes

**Tier:** B. Batteries are 0.034 x 0.035 x 0.061 m (asset bbox, scale 1), so they fit the 44 mm jaws. The difficulty is distance: two batteries are ~14.5 m away behind a closed door.

### Goal in plain words

- All three batteries must end inside the copy-room trash can (`trash_can_159`, model wklill).
- That trash can must also be resting on the **copy-room** floor (`floors_tkyckr_0`) at the end.
- Battery 3 starts on the copy-room bottom cabinet, near the start. Batteries 1 and 2 start on the desk in private_office_0 (`desk_mdhelw_2`).

### Q traps

- There are 4 literals. `ontop ashcan floor.n.01_1` is true at reset and never scores, so the best partial Q is 0.75.
- **The trash-can trap.** If the bin is carried to the office and left there, `ontop ashcan floor.n.01_1` becomes False and success is impossible. That floor literal names the copy-room floor. Either leave the bin in the copy room or bring it back and set it on the copy-room floor.
- A bin tipped over while dropping batteries in loses the ones already inside (§3). It also stops being `ontop` the floor if it rests on its side on something else.
- The private_office_0 door starts closed (`joint_pos` 0). The goal does not care about the door, but the robot must get through it.

### Minimal plan

Keep the bin in the copy room and carry batteries to it.

1. `move to the battery`. Go to the one on the copy-room bottom cabinet. About 44 s (demo mean; this one is ~1.5 m away).
2. `pick up the battery from the cabinet`. Done when the fingers stop short of fully closed around it. About 19 s.
3. `move to the trash can`. About 20 s.
4. `place the battery in the trash can`. Done when the gripper is open and the battery is not on the rim or the floor. About 14 s.
5. `move to the wooden door`. About 44 s.
6. `open the door of the wooden door`. Done when the doorway is visibly clear. About 17 s.
7. `move to the battery`. Go to the office desk. About 44 s.
8. `pick up the battery from the desk`, once per hand for both batteries. About 19 s each. If a chair blocks the desk, first `push the swivel chair to the desk` (about 22 s).
9. `move to the trash can`. Travel back to the copy room. The demos' mean `move to` is 44 s, and this trip is longer.
10. `place the battery in the trash can`, twice. About 14 s each.

- Totals: about 330 s against a 721.4 s limit.

### What the demos do differently

- All 200 demos pick up the trash can (`pick up the trash can from the floors`, 200 of 200) and carry it through the task. They place the batteries into the held bin, then walk back and `place the trash can on the floors`.
- That return trip averages about 136 s in the representative demo. It is required only because they moved the bin.
- If Comet insists on the bin-carry pattern, the final `move to the floors` and `place the trash can on the floors` must happen **in the copy room**.
- 110 of 200 demos push a swivel chair aside at the office desk.

### Hard parts and hacks

- **Two-handed carry.** One battery per hand saves a 29 m round trip. Check both grippers stopped short of closed before leaving the office.
- **Long navigation** (~14.5 m each way) through a corridor with many identical doors. Rotation odometry drifts, so re-identify the copy room by its trash can and cabinet rather than by dead reckoning.
- Batteries are small and can roll off the desk when a chair or arm bumps it. Re-check both on the desk before grasping.
- The trash can is 0.41 x 0.30 x 0.44 m. Drop from just above the opening.
- ft40k scored Q=0 on instance 311.

### Hints for the VLM

- Copy room: one bottom cabinet (battery on top, z ~1.05 m), one top cabinet and the trash can on the floor. The robot starts here.
- private_office_0: one desk with two batteries (z ~0.81 m), three swivel chairs, and the wooden door to the corridor.
- There are no other trash cans or batteries in these rooms.
- Done: no battery visible on the cabinet or desk, three batteries seen inside the bin, and the bin upright on the copy-room floor.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside battery.n.02_2 ashcan.n.01_1)` | no | yes |
| `(inside battery.n.02_1 ashcan.n.01_1)` | no | yes |
| `(inside battery.n.02_3 ashcan.n.01_1)` | no | yes |
| `(ontop ashcan.n.01_1 floor.n.01_1)` | yes | never (already true) |

BDDL goal:

```lisp
(:goal
        (and
            (forall
                (?battery.n.02 - battery.n.02)
                (inside ?battery.n.02 ?ashcan.n.01_1)
            )
            (ontop ?ashcan.n.01_1 ?floor.n.01_1)
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `battery.n.02_1` | battery_162 | battery / dcjyzg | private_office_0 | table/counter (0.6-1.1 m), z 0.81 | 14.54 m (range 13.96-15.04) | yes, spread 2.73 m |
| `battery.n.02_2` | battery_161 | battery / dcjyzg | private_office_0 | table/counter (0.6-1.1 m), z 0.81 | 14.49 m (range 13.69-15.08) | yes, spread 2.74 m |
| `battery.n.02_3` | battery_160 | battery / dcjyzg | copy_room_0 | table/counter (0.6-1.1 m), z 1.05 | 1.5 m (range 0.82-2.47) | yes, spread 2.92 m |
| `desk.n.01_1` | desk_mdhelw_2 | desk / mdhelw | private_office_0 | low (0.25-0.6 m), z 0.6 | 14.19 m (range 13.99-14.61) | no (fixed) |
| `cabinet.n.01_1` | bottom_cabinet_jhymlr_0 | bottom_cabinet / jhymlr | copy_room_0 | low (0.25-0.6 m), z 0.51 | 1.43 m (range 1.1-1.78) | no (fixed) |
| `ashcan.n.01_1` | trash_can_159 | trash_can / wklill | copy_room_0 | floor, z 0.22 | 0.94 m (range 0.67-2.6) | yes, spread 3.22 m |
| `floor.n.01_1` | floors_tkyckr_0 | floors / tkyckr | copy_room_0 | floor, z -0.14 | 0.7 m (range 0.34-1.08) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "copy_room",
  "corridor",
  "private_office",
  "shared_office"
 ],
 "office_cubicles_right": {
  "whitelist": {
   "ashcan.n.01": {
    "trash_can": {
     "wklill": null
    }
   },
   "battery.n.02": {
    "battery": {
     "dcjyzg": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(inroom cabinet.n.01_1 copy_room)
(inroom desk.n.01_1 private_office)
(inroom floor.n.01_1 copy_room)
(ontop agent.n.01_1 floor.n.01_1)
(ontop ashcan.n.01_1 floor.n.01_1)
(ontop battery.n.02_1 desk.n.01_1)
(ontop battery.n.02_2 desk.n.01_1)
(ontop battery.n.02_3 cabinet.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching ashcan.n.01_1 floor.n.01_1)
(touching battery.n.02_1 desk.n.01_1)
(touching battery.n.02_2 desk.n.01_1)
(touching battery.n.02_3 cabinet.n.01_1)
(touching cabinet.n.01_1 battery.n.02_3)
(touching desk.n.01_1 battery.n.02_1)
(touching desk.n.01_1 battery.n.02_2)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 ashcan.n.01_1)
```

## What the human demos did

200 annotated demos. Length 454.98 s (range 255.63-863.97). Skills per demo 17.0 (range 14-19). 27 distinct skill orders; the most common one covers 23% of demos.

Most common skill counts per demo (34% of demos): move to x7, pick up from x4, place in x3, open door x1, place on x1, push to x1.

Representative demo `episode_00940830.json` (468.7 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the trash can` (0.0-21.0 s)
2. `pick up the trash can from the floors` (21.0-47.0 s)
3. `move to the battery` (47.0-59.0 s)
4. `pick up the battery from the cabinet` (59.0-76.0 s)
5. `place the battery in the trash can` (76.0-83.0 s)
6. `move to the wooden door` (83.0-156.0 s)
7. `open the door of the wooden door` (156.0-163.0 s)
8. `move to the battery` (163.0-189.0 s)
9. `pick up the battery from the desk` (189.0-196.1 s)
10. `place the battery in the trash can` (196.1-200.0 s)
11. `move to the battery` (200.0-240.7 s)
12. `push the swivel chair to the floors` (240.7-253.1 s)
13. `move to the battery` (253.1-289.0 s)
14. `pick up the battery from the desk` (289.0-294.2 s)
15. `place the battery in the trash can` (294.2-305.0 s)
16. `move to the floors` (305.0-441.0 s)
17. `place the trash can on the floors` (441.0-460.0 s)

Mean duration per skill in this task: move to 44.1 s, open door 16.6 s, pick up from 19.0 s, place in 14.1 s, place on 21.8 s, push to 22.3 s, turn to 19.8 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the battery` | 686 |
| `place the battery in the trash can` | 600 |
| `pick up the battery from the desk` | 402 |
| `move to the wooden door` | 292 |
| `open the door of the wooden door` | 201 |
| `move to the floors` | 201 |
| `move to the trash can` | 200 |
| `pick up the trash can from the floors` | 200 |
| `pick up the battery from the cabinet` | 200 |
| `place the trash can on the floors` | 200 |
| `push the swivel chair to the desk` | 110 |
| `move to the swivel chair` | 14 |
| `push the swivel chair to the floors` | 13 |
| `turn to the trash can` | 3 |
| `push the chair to the desk` | 2 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/94_dispose_of_batteries.json`. Planner notes: `task_docs/notes/94_dispose_of_batteries.md`.
