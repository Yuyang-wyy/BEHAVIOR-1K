# 78 · Make Cabinet Doors

Task name `make_cabinet_doors`, task index 78.

> Attach the cabinet door to the cabinet base.

## At a glance

| item | value |
| --- | --- |
| scene | `Rs_int` |
| rooms in the goal | living_room |
| rooms loaded | bedroom_0, entryway_0, kitchen_0, living_room_0 |
| human demo length | 114.8 s mean (3442 steps) |
| episode time limit | 172.1 s (5163 steps at 30 Hz) |
| human base travel | 4.4664 m |
| goal literals (best ground option) | 1 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | not evaluated yet |
| demo video | https://www.youtube.com/embed/rqqgwEPTLwk |

## Planner notes

**Tier:** C — a floor pick of a door panel plus an `attached` alignment (5 cm, 15°) on a free-standing cabinet base that the demos first tip over. Single literal, so Q is 0 or 1.

### Goal in plain words

The cabinet door must be attached to the cabinet base. There is exactly one of each, both standing upright on the living-room floor. Nothing else is checked: where the base ends up, and whether it lies on its back, do not matter.

### Q traps

- One literal: Q is 0 or 1. Success ends the episode at once, with no release needed (PREDICATES §10).
- Attachment fires automatically while the door touches the base and the door's `doorcabinetM` link is within 5 cm and 15° of the base's `doorcabinetF` link.
- Meta links verified in asset metadata (both scale 1.0 in the template):
  - base `dcmhhh` (0.253 x 0.264 x 0.457 m): `doorcabinetF` at local (+0.149, +0.128, 0), identity orientation. That is just outside the +x face (half-depth 0.126), at the +y edge, mid-height.
  - door `ertkre` (0.024 x 0.263 x 0.457 m): `doorcabinetM` at local (-0.005, -0.129, 0), rotated 180° about x.
- Derived from those links: the door must lie flush over the base's +x face, covering it edge to edge (the door face 0.263 x 0.457 matches the base face 0.264 x 0.457). Its local "up" must point opposite to the base's "up". With both objects upright, as at reset, that means standing the door on its other end. After tipping the base onto its back, any in-plane rotation is a yaw of the flat door, which is why the demos tip first (derived).
- Tipping the base onto its front or side buries or tilts the +x face. Only "on its back, +x face up" leaves a horizontal mounting face (derived).
- Both objects start upright (tilt 0°) in all 20 instances, 0.3-3.8 m apart.

### Minimal plan

1. `move to the cabinet door` — the door panel fills the view. ~16 s.
2. `pick up the cabinet door from the floors` — gripper closed across the 24 mm edge, door off the floor. ~17 s.
3. `move to the cabinet base` — base in front of the robot. ~16 s.
4. `tip over the cabinet base` — base lying on its back, open face up. ~14 s.
5. `place the cabinet door on the cabinet base` — door lying flat on the base, edges aligned. ~30 s.
6. `attach the cabinet door to the cabinet base` — done when the episode ends (success). If not, nudge the door so its edges line up with the base within a few cm. ~14 s.

Budget: 172 s limit vs 115 s demo mean. Little room for retries. Doing step 4 with the door already in one hand follows the demo order; tipping first with both hands free is an untested alternative.

### What the demos do differently

- 60% of demos follow the plan above exactly.
- 24 demos add `turn to the cabinet door` and 14 add `turn to the cabinet base` (reorientation).
- 49 extra `move to the cabinet base` over 200 demos: some humans re-approach after tipping.

### Hard parts and hacks

- The door is 24 mm thick, so the jaws fit across it (asset bbox). It stands on edge on the floor, so the grasp is low on the top edge.
- The base (0.25 x 0.26 x 0.46 m) is too wide to grasp; tipping is a push.
- The alignment is the hard step: 5 cm on the link position and 15° on the full orientation. A door placed rotated by 180° in plane (hinge edge on the wrong side) never latches (derived from the link orientations).
- Scripted shortcut (unverified): with the door resting flat on the base, a slow in-plane wrist rotation sweep plus small translations while in contact passes through the window. Attachment is checked every step.

### Hints for the VLM

- Both objects are in living_room_0 of Rs_int, on the floor, 0.7-3.3 m from the start. No distractors of either category.
- The base is a small open box about knee height (0.46 m); the door is a flat panel of the same height standing on edge.
- Done: the door lies flush on the tipped base, covering its open face, and the episode ends.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(attached cabinet_door.n.01_1 cabinet_base.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (attached ?cabinet_door.n.01_1 ?cabinet_base.n.01_1)
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `cabinet_base.n.01_1` | cabinet_base_72 | cabinet_base / dcmhhh | living_room_0 | floor, z 0.23 | 1.59 m (range 0.96-3.3) | yes, spread 4.81 m |
| `cabinet_door.n.01_1` | cabinet_door_73 | cabinet_door / ertkre | living_room_0 | floor, z 0.23 | 1.31 m (range 0.72-3.03) | yes, spread 4.74 m |
| `floor.n.01_1` | floors_ptwlei_0 | floors / ptwlei | living_room_0 | floor, z -0.15 | 1.0 m (range 0.57-2.03) | no (fixed) |

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
   "cabinet_base.n.01": {
    "cabinet_base": {
     "dcmhhh": null
    }
   },
   "cabinet_door.n.01": {
    "cabinet_door": {
     "ertkre": null
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
(ontop agent.n.01_1 floor.n.01_1)
(ontop cabinet_base.n.01_1 floor.n.01_1)
(ontop cabinet_door.n.01_1 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching cabinet_base.n.01_1 floor.n.01_1)
(touching cabinet_door.n.01_1 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 cabinet_base.n.01_1)
(touching floor.n.01_1 cabinet_door.n.01_1)
```

## What the human demos did

200 annotated demos. Length 112.07 s (range 64.6-222.27). Skills per demo 6.0 (range 5-9). 12 distinct skill orders; the most common one covers 60% of demos.

Most common skill counts per demo (60% of demos): move to x2, attach x1, pick up from x1, place on x1, tip over x1.

Representative demo `episode_00782310.json` (110.1 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the cabinet door` (0.0-38.0 s)
2. `pick up the cabinet door from the floors` (38.0-52.0 s)
3. `move to the cabinet base` (52.0-70.5 s)
4. `tip over the cabinet base` (70.5-77.8 s)
5. `place the cabinet door on the cabinet base` (77.8-98.3 s)
6. `attach the cabinet door to the cabinet base` (98.3-106.2 s)

Mean duration per skill in this task: attach 14.2 s, lift 9.8 s, move to 15.9 s, pick up from 16.8 s, place on 30.1 s, tip over 13.8 s, turn to 13.9 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the cabinet base` | 249 |
| `move to the cabinet door` | 200 |
| `pick up the cabinet door from the floors` | 200 |
| `place the cabinet door on the cabinet base` | 200 |
| `attach the cabinet door to the cabinet base` | 200 |
| `tip over the cabinet base` | 199 |
| `turn to the cabinet door` | 24 |
| `turn to the cabinet base` | 14 |
| `tip over the cabinet door` | 1 |
| `lift the cabinet door` | 1 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/78_make_cabinet_doors.json`. Planner notes: `task_docs/notes/78_make_cabinet_doors.md`.
