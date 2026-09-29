# 31 · Clean Boxing Gloves

Task name `clean_boxing_gloves`, task index 31.

> Wash the two dusty boxing gloves from the countertop in the utility room in the washer until they are no longer covered with dust.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | utility_room |
| rooms loaded | corridor_0, dining_room_0, entryway_0, garden_0, utility_room_0 |
| human demo length | 274.5 s mean (8235 steps) |
| episode time limit | 411.8 s (12353 steps at 30 Hz) |
| human base travel | 28.582 m |
| goal literals (best ground option) | 2 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.00; ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://player.vimeo.com/video/1114060008 |

## Planner notes

**Tier:** D — two pick-and-place moves into the washer, then a washer cycle (a state transition) clears the dust.

### Goal in plain words

Both boxing gloves must end with zero dust particles on them.
The only practical route is the washer: put both gloves in, close the door, turn the washer on.
The glove itself is a particle remover, but its dust condition is `never` (PREDICATES.md §12), so rubbing gloves together does nothing.
Where the gloves end up does not matter; nothing else is scored.

### Q traps

- Two literals, both false at reset (verified: the template `system_registry` has 40 dust particles, 20 on each glove, in all 20 public instances). Max Q is 1.0.
- The washer cleans only on the step it **changes** to (toggled on AND closed) (`WasherDryerRule`, `transition_rules.py:745-757`). Pressing while the door is open does nothing lasting; ToggledOn is forced False while open (§11).
- Cleaning needs two things at that step (`WasherRule.transition`, `transition_rules.py:846-884`):
  - the washer's volume holds at least 1 dust particle (these particles sit on the gloves, so at least one glove must be well inside);
  - each glove has **any** collision point inside the washer volume. A glove only partly in still gets cleaned.
- Washer starts closed and off in all 20 instances (joint_pos ~0, `ToggledOn: False`). The door has to be opened first.
- A glove sticking out of the doorway stops the door closing within 5 % (§6). Then the washer stays off and nothing is cleaned.
- Fallback that keeps Q: washing one glove at a time works. Open the door (this forces the washer off), add glove 2, close, press again: the change condition fires again. One cleaned glove = Q 0.5.
- Success is checked every step, so the episode ends with Q 1.0 on the press step itself.

### Minimal plan

1. `move to the washer` — washer front fills the view; base stopped. ~19 s.
2. `open the door of the washer` — door visibly swung open, drum opening visible. ~46 s (slowest step).
3. `move to the boxing gloves` — gloves on the countertop in view at close range. ~19 s.
4. `pick up the boxing gloves from the countertop` — one gripper closed but stopped short of fully closed; glove gone from the counter. ~21 s.
5. `pick up the boxing gloves from the countertop` — second hand holds the second glove. ~21 s.
6. `move to the washer` — ~19 s.
7. `place the boxing gloves in the washer` — glove no longer in the gripper, not visible outside the drum. ~28 s.
8. `place the boxing gloves in the washer` — same for the second glove. ~28 s.
9. `close the door of the washer` — door flush with the washer front. ~28 s.
10. `turn on the washer` — fingertip on the control; episode ends on success. ~21 s.

Total about 250 s against a 411.8 s limit. The demo is already minimal apart from `turn to the boxing gloves` (164 of 200 demos), which can be dropped if the gloves are already in view.

### What the demos do differently

- Most demos open the washer first, then fetch both gloves in one trip (one per hand), as above. Keep that order: the hands are free for the door.
- `turn to the boxing gloves` appears in 164 demos; it is only re-aiming the head/base.
- Rare demos pick a glove back out of the washer (3) or put one on the countertop (2); these are recoveries.

### Hard parts and hacks

- Opening the washer door is the slowest demo step (46 s mean) and needs the door handle. Handle width vs the 44 mm span is unverified.
- Glove size is unknown (no custom list). Every demo picks the gloves up with the same robot, so some part registers a grasp; which part is unverified.
- The gloves sit on countertop `sjxber` (x≈23.7, y≈-2.06), about 3 m from the washer (x≈22.0, y≈0.33). Carry both at once to save a trip.
- The toggle-button location on washer `ynwamu` is unverified. A press must hold finger contact on the button sphere for 5 steps (§11).
- No scripted shortcut beyond a press routine: the planner has no object poses. A scripted "hold fingertip on button for ~0.5 s then withdraw" is legal once the arm is at the button.
- Closed-loop so far: Q 0.00 on instance 311 for all three checkpoints.

### Hints for the VLM

- Utility room. The washer and a clothes dryer stand side by side on one wall (washer at y≈0.33, dryer at y≈0.95, 0.6 m apart). Do not load the dryer: it has no cleaning rule for dust.
- The gloves are on the countertop over the cabinet at the far end of the room (countertop `sjxber`, above cabinet `gjrero_4`), not on the long counter opposite the washer.
- Dust is drawn as small visual specks on the gloves. After the press the specks vanish; that is the done signal.
- "Door closed" = washer door flush, no gap at the hinge side.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(not covered boxing_glove.n.01_1 dust.n.01_1))` | no | yes |
| `(not covered boxing_glove.n.01_2 dust.n.01_1))` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (forall 
                (?boxing_glove.n.01 - boxing_glove.n.01)
                (not 
                    (covered ?boxing_glove.n.01 ?dust.n.01_1)
                )
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `boxing_glove.n.01_1` | boxing_gloves_189 | boxing_gloves / jlfuaf | utility_room_0 | table/counter (0.6-1.1 m), z 0.99 | 2.22 m (range 1.04-3.6) | yes, spread 0.37 m |
| `boxing_glove.n.01_2` | boxing_gloves_188 | boxing_gloves / jlfuaf | utility_room_0 | table/counter (0.6-1.1 m), z 0.99 | 2.14 m (range 0.85-3.76) | yes, spread 0.78 m |
| `dust.n.01_1` | particle system | dust | - | - | - | - |
| `washer.n.03_1` | washer_ynwamu_0 | washer / ynwamu | utility_room_0 | low (0.25-0.6 m), z 0.47 | 1.57 m (range 0.93-2.03) | no (fixed) |
| `countertop.n.01_1` | countertop_sjxber_0 | countertop / sjxber | utility_room_0 | table/counter (0.6-1.1 m), z 0.91 | 2.17 m (range 1.02-3.68) | no (fixed) |
| `floor.n.01_1` | floors_glwobe_0 | floors / glwobe | utility_room_0 | floor, z -0.14 | 0.88 m (range 0.14-1.77) | no (fixed) |

Initial conditions from `:init`:

```lisp
(covered boxing_glove.n.01_1 dust.n.01_1)
(covered boxing_glove.n.01_2 dust.n.01_1)
(inroom countertop.n.01_1 utility_room)
(inroom floor.n.01_1 utility_room)
(inroom washer.n.03_1 utility_room)
(ontop agent.n.01_1 floor.n.01_1)
(ontop boxing_glove.n.01_1 countertop.n.01_1)
(ontop boxing_glove.n.01_2 countertop.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching boxing_glove.n.01_1 countertop.n.01_1)
(touching boxing_glove.n.01_2 countertop.n.01_1)
(touching countertop.n.01_1 boxing_glove.n.01_1)
(touching countertop.n.01_1 boxing_glove.n.01_2)
(touching floor.n.01_1 agent.n.01_1)
```

## What the human demos did

200 annotated demos. Length 251.98 s (range 139.43-503.4). Skills per demo 11.0 (range 9-14). 15 distinct skill orders; the most common one covers 38% of demos.

Most common skill counts per demo (38% of demos): move to x3, pick up from x2, place in x2, close door x1, open door x1, turn on switch x1.

Representative demo `episode_00311080.json` (236.1 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the washer` (0.0-17.4 s)
2. `open the door of the washer` (17.4-59.6 s)
3. `move to the boxing gloves` (59.6-76.9 s)
4. `pick up the boxing gloves from the countertop` (76.9-98.0 s)
5. `pick up the boxing gloves from the countertop` (98.0-113.4 s)
6. `move to the washer` (113.4-141.8 s)
7. `place the boxing gloves in the washer` (142.4-162.6 s)
8. `place the boxing gloves in the washer` (162.6-195.9 s)
9. `close the door of the washer` (195.9-225.1 s)
10. `turn on the washer` (225.1-236.1 s)

Mean duration per skill in this task: close door 27.8 s, move to 18.7 s, open door 46.0 s, pick up from 21.0 s, place in 28.1 s, turn on switch 20.5 s, turn to 29.2 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `place the boxing gloves in the washer` | 398 |
| `pick up the boxing gloves from the countertop` | 396 |
| `move to the washer` | 382 |
| `move to the boxing gloves` | 217 |
| `open the door of the washer` | 200 |
| `close the door of the washer` | 200 |
| `turn on the washer` | 200 |
| `turn to the boxing gloves` | 164 |
| `pick up the boxing gloves from the washer` | 3 |
| `place the boxing gloves in the countertop` | 2 |
| `pick up the boxing gloves from the robot` | 1 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/31_clean_boxing_gloves.json`. Planner notes: `task_docs/notes/31_clean_boxing_gloves.md`.
