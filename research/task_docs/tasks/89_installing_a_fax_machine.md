# 89 · Installing A Fax Machine

Task name `installing_a_fax_machine`, task index 89.

> Install the fax machine by placing it on the cubicle desk and turning it on.

## At a glance

| item | value |
| --- | --- |
| scene | `office_cubicles_right` |
| rooms in the goal | corridor, shared_office |
| rooms loaded | corridor_0, private_office_0, private_office_1, private_office_2, private_office_3, copy_room_0, shared_office_0 |
| human demo length | 135.9 s mean (4076 steps) |
| episode time limit | 203.8 s (6115 steps at 30 Hz) |
| human base travel | 10.2326 m |
| goal literals (best ground option) | 2 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 10 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://www.youtube.com/embed/v1CrUuIN0lY |

## Planner notes

**Tier:** C — lifting the fax (forced size 0.14 x 0.26 x 0.06 m, wider than the 44 mm jaws) from the floor to a cubicle desk. The `toggled_on` half is Tier A: a fingertip press, no grasp.

### Goal in plain words

The fax machine must be switched on and must rest on any of the ten cubicles in the shared office. The order is free. Nothing else is checked.

### Q traps

- Two literals, each 1/2, both false at reset (`ToggledOn` false in all 20 instances).
- The toggle is a stored bool (PREDICATES §11). Pressing it on the floor scores 0.5 and stays on while the fax is carried. A second separate 5-step press turns it back off.
- Button geometry (asset metadata, derived with the template scale 2.03 x 2.0 x 1.76): a sphere of radius about 9 mm, near the top face and about 9 cm from the centre along the long axis. Pressing elsewhere on the body does nothing.
- Carrying risk: a grasp whose finger overlaps that sphere for 5 steps flips it. Check fingers are clear of the button end.
- `ontop fax cubicle` fails if any part of the cubicle is directly above the fax's centre (PREDICATES §4). The cubicles have glass partition links; whether a cubicle has an overhead shelf is not verified. The open desk surface is the demo target.
- Both closed-loop runs on 311 scored Q = 0 (ft40k, sulab1 and local), ending at the step limit.

### Minimal plan

1. `move to the facsimile` — fax on the floor in view. ~28 s.
2. `turn on the facsimile` — fingertip on the button, then withdraw. ~12 s. Doing it on the floor first banks 0.5 before the hard lift.
3. `pick up the facsimile from the floors` — fax lifted. ~26 s.
4. `move to the chair` then `push the chair to the cubicle` — only if a swivel chair blocks the desk. ~28 s + 9 s.
5. `move to the cubicle` then `place the facsimile on the cubicle` — fax resting flat on the desk. ~28 s + 13 s.

Budget: 204 s limit vs 136 s demo mean. Tight; step 4 is the first thing to drop.

### What the demos do differently

- 70% of demos pick up the fax first and press the button while holding it, then push the chair and place the fax. Pressing on the floor first is not the demo order but gives the same literal and banks it early.
- `push the chair to the cubicle` (197 of 200 demos) moves the swivel chair out of the desk's knee space. It earns nothing.

### Hard parts and hacks

- Grasp: forced size 0.14 x 0.26 x 0.06 m; no axis fits 44 mm, and it lies flat on the floor. This is the likely point of failure.
- Any of the ten cubicles counts. Pick the nearest one to the fax; the fax moves up to 8.6 m between instances (three clusters of start positions around x 9-10.8, y -6.9, -2.6 and 1.5).
- Scripted shortcut: the press is a legal no-grasp action. A scripted fingertip press on the button end (seen from the head camera) secures Q = 0.5 without the VLA.

### Hints for the VLM

- Scene office_cubicles_right, shared_office_0: ten identical-size cubicles (two models), ten swivel chairs and sixteen bottom cabinets. None of the cabinets is a target.
- The fax is the only fax, a flat box on the floor 0.65-8.2 m from the start.
- Done: fax resting on a cubicle desk; toggled state is not verified to be visible, so press once and do not touch the button again.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(toggled_on facsimile.n.02_1)` | no | yes |
| `(ontop facsimile.n.02_1 carrel.n.02_9)` | no | yes |

The goal has 10 ground options (2 literals x10); Q takes the best one, so any valid choice of container or partner object counts.

BDDL goal:

```lisp
(:goal 
        (and 
            (toggled_on ?facsimile.n.02_1)
            (exists 
                (?carrel.n.02 - carrel.n.02)
                (ontop ?facsimile.n.02_1 ?carrel.n.02)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `facsimile.n.02_1` | facsimile_180 | facsimile / mcqqhy | shared_office_0 | floor, z 0.04 | 3.99 m (range 0.65-8.17) | yes, spread 8.57 m |
| `floor.n.01_1` | floors_ovpbsn_0 | floors / ovpbsn | shared_office_0 | floor, z -0.14 | 4.59 m (range 0.8-4.85) | no (fixed) |
| `floor.n.01_2` | floors_egqrip_0 | floors / egqrip | corridor_0 | floor, z -0.15 | 12.06 m (range 10.75-13.57) | no (fixed) |
| `carrel.n.02_1` | cubicle_deceti_0 | cubicle / deceti | shared_office_0 | low (0.25-0.6 m), z 0.6 | 2.82 m (range 1.4-5.75) | no (fixed) |
| `carrel.n.02_2` | cubicle_hzalfx_0 | cubicle / hzalfx | shared_office_0 | low (0.25-0.6 m), z 0.6 | 9.25 m (range 1.52-9.45) | no (fixed) |
| `carrel.n.02_3` | cubicle_hzalfx_1 | cubicle / hzalfx | shared_office_0 | low (0.25-0.6 m), z 0.6 | 9.28 m (range 1.4-9.57) | no (fixed) |
| `carrel.n.02_4` | cubicle_deceti_1 | cubicle / deceti | shared_office_0 | low (0.25-0.6 m), z 0.6 | 2.67 m (range 1.48-5.47) | no (fixed) |
| `carrel.n.02_5` | cubicle_hzalfx_2 | cubicle / hzalfx | shared_office_0 | low (0.25-0.6 m), z 0.6 | 5.28 m (range 1.42-5.51) | no (fixed) |
| `carrel.n.02_6` | cubicle_deceti_2 | cubicle / deceti | shared_office_0 | low (0.25-0.6 m), z 0.6 | 6.5 m (range 1.4-6.87) | no (fixed) |
| `carrel.n.02_7` | cubicle_deceti_3 | cubicle / deceti | shared_office_0 | low (0.25-0.6 m), z 0.6 | 6.47 m (range 1.55-6.69) | no (fixed) |
| `carrel.n.02_8` | cubicle_hzalfx_3 | cubicle / hzalfx | shared_office_0 | low (0.25-0.6 m), z 0.6 | 5.31 m (range 1.39-5.74) | no (fixed) |
| `carrel.n.02_9` | cubicle_hzalfx_4 | cubicle / hzalfx | shared_office_0 | low (0.25-0.6 m), z 0.6 | 1.78 m (range 1.42-6.64) | no (fixed) |
| `carrel.n.02_10` | cubicle_hzalfx_5 | cubicle / hzalfx | shared_office_0 | low (0.25-0.6 m), z 0.6 | 2.5 m (range 1.45-6.87) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "corridor",
  "shared_office"
 ],
 "office_cubicles_right": {
  "whitelist": {
   "facsimile.n.02": {
    "facsimile": {
     "mcqqhy": [
      0.14,
      0.26,
      0.06
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
(inroom carrel.n.02_1 shared_office)
(inroom carrel.n.02_10 shared_office)
(inroom carrel.n.02_2 shared_office)
(inroom carrel.n.02_3 shared_office)
(inroom carrel.n.02_4 shared_office)
(inroom carrel.n.02_5 shared_office)
(inroom carrel.n.02_6 shared_office)
(inroom carrel.n.02_7 shared_office)
(inroom carrel.n.02_8 shared_office)
(inroom carrel.n.02_9 shared_office)
(inroom floor.n.01_1 shared_office)
(inroom floor.n.01_2 corridor)
(ontop agent.n.01_1 floor.n.01_1)
(ontop facsimile.n.02_1 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching facsimile.n.02_1 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 facsimile.n.02_1)
```

## What the human demos did

200 annotated demos. Length 134.4 s (range 67.7-286.13). Skills per demo 7.0 (range 6-7). 4 distinct skill orders; the most common one covers 70% of demos.

Most common skill counts per demo (70% of demos): move to x3, pick up from x1, place on x1, push to x1, turn on switch x1.

Representative demo `episode_00892620.json` (135.0 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the facsimile` (0.0-42.0 s)
2. `pick up the facsimile from the floors` (42.0-67.3 s)
3. `turn on the facsimile` (67.3-74.8 s)
4. `move to the chair` (74.8-102.0 s)
5. `push the chair to the cubicle` (102.0-114.8 s)
6. `move to the cubicle` (114.7-122.0 s)
7. `place the facsimile on the cubicle` (122.0-135.0 s)

Mean duration per skill in this task: move to 27.5 s, pick up from 26.2 s, place on 13.4 s, push to 9.2 s, turn on switch 12.0 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the facsimile` | 200 |
| `pick up the facsimile from the floors` | 200 |
| `turn on the facsimile` | 200 |
| `place the facsimile on the cubicle` | 200 |
| `move to the chair` | 199 |
| `push the chair to the cubicle` | 197 |
| `move to the cubicle` | 145 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/89_installing_a_fax_machine.json`. Planner notes: `task_docs/notes/89_installing_a_fax_machine.md`.
