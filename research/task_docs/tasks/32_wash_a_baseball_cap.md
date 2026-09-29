# 32 · Wash A Baseball Cap

Task name `wash_a_baseball_cap`, task index 32.

> Wash the two baseball caps on the countertop in the utility room using the washer until they are no longer dirty.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | utility_room |
| rooms loaded | corridor_0, dining_room_0, entryway_0, garden_0, utility_room_0 |
| human demo length | 278.3 s mean (8349 steps) |
| episode time limit | 417.5 s (12524 steps at 30 Hz) |
| human base travel | 28.9362 m |
| goal literals (best ground option) | 2 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.00; ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://player.vimeo.com/video/1114060147 |

## Planner notes

**Tier:** D — two pick-and-place moves into the washer, then a washer cycle (a state transition) clears the dirt.

### Goal in plain words

Both baseball caps must end with zero dirt particles on them.
The route is the washer: put both caps in, close the door, turn it on.
Where the caps end up does not matter; nothing else is scored.

### Q traps

- Two literals, both false at reset (verified: 40 dirt particles, 20 per cap, in all 20 public instances). Max Q is 1.0.
- The washer cleans only on the step it **changes** to (toggled on AND closed) (`transition_rules.py:745-757`). A press with the door open does nothing lasting (§11).
- At that step (`WasherRule.transition`, `transition_rules.py:846-884`):
  - the washer volume must hold at least 1 dirt particle (the particles are on the caps, so at least one cap must be well inside);
  - each cap with **any** collision point inside the washer volume is cleaned, even if partly out.
- Washer starts closed and off in all 20 instances (joint_pos ~0, `ToggledOn: False`).
- A cap brim caught in the doorway keeps the door more than 5 % open (§6), so the washer never turns on.
- Fallback: wash one cap per cycle. Opening the door forces the washer off; closing and pressing again fires a new cycle. One clean cap = Q 0.5.
- Success ends the episode on the press step.

### Minimal plan

1. `move to the washer` — washer front in view; base stopped. ~18 s.
2. `open the door of the washer` — door swung open, drum visible. ~47 s.
3. `move to the baseball cap` — cap on the long countertop in view. ~18 s.
4. `turn to the baseball cap` — optional; only if the cap is off-centre. ~23 s.
5. `pick up the baseball cap from the countertop` — gripper closed short of fully closed; cap gone from the counter. ~15 s.
6. `move to the baseball cap` — only if the second cap is out of reach (caps can be up to ~2 m apart). ~18 s.
7. `pick up the baseball cap from the countertop` — second hand holds the second cap. ~15 s.
8. `move to the washer` — ~18 s.
9. `place the baseball cap in the washer` — cap released, not visible outside the drum. ~28 s.
10. `place the baseball cap in the washer` — second cap. ~28 s.
11. `close the door of the washer` — door flush. ~24 s.
12. `turn on the washer` — fingertip on the control; episode ends on success. ~25 s.

About 260-280 s against a 417.5 s limit. This matches the representative demo; drop steps 4 and 6 when not needed.

### What the demos do differently

- All demos open the washer before picking up the caps, and carry both caps in one trip (one per hand).
- `turn to the baseball cap` in 211 segments and a second `move to the baseball cap` in many demos: the caps are often far apart.
- Two demos pick a cap back out of the washer (recovery).

### Hard parts and hacks

- Caps start anywhere along countertop `ikwqer`, a ~4 m counter on the wall opposite the washer (cap y from -2.14 to 2.03 across instances; washer at x≈22.0, counter at x≈24.5). The page's "spread 4.1 m" is this, not a different surface.
- Cap size is unknown (no custom list). Demos grasp them, so some part (probably the brim) registers; unverified.
- Opening the washer door is the slowest step (47 s mean). Handle width vs 44 mm is unverified.
- Button location on washer `ynwamu` is unverified. The press needs 5 steps of finger contact on the button sphere (§11).
- A scripted press routine (hold fingertip ~0.5 s, withdraw) is legal once the hand is at the button.
- Closed-loop so far: Q 0.00 on instance 311 for all three checkpoints.

### Hints for the VLM

- Utility room. Washer and clothes dryer stand side by side (washer y≈0.33, dryer y≈0.95). Use the washer; the dryer does not clean.
- The target counter is the long one over the row of four identical cabinets opposite the washer. The two caps may be at opposite ends of it.
- Dirt shows as brown specks on the caps. They vanish on the press step; that is the done signal.
- "Door closed" = washer door flush with the front.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(not covered baseball_cap.n.01_2 dirt.n.02_1))` | no | yes |
| `(not covered baseball_cap.n.01_1 dirt.n.02_1))` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (forall
                (?baseball_cap.n.01 - baseball_cap.n.01)
                (not 
                    (covered ?baseball_cap.n.01 ?dirt.n.02_1)
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
| `baseball_cap.n.01_1` | baseball_cap_189 | baseball_cap / ogptul | utility_room_0 | table/counter (0.6-1.1 m), z 0.98 | 1.7 m (range 1.12-3.57) | yes, spread 4.11 m |
| `baseball_cap.n.01_2` | baseball_cap_188 | baseball_cap / ogptul | utility_room_0 | table/counter (0.6-1.1 m), z 0.98 | 1.78 m (range 1.02-3.32) | yes, spread 4.09 m |
| `dirt.n.02_1` | particle system | dirt | - | - | - | - |
| `floor.n.01_1` | floors_glwobe_0 | floors / glwobe | utility_room_0 | floor, z -0.14 | 0.76 m (range 0.13-1.5) | no (fixed) |
| `washer.n.03_1` | washer_ynwamu_0 | washer / ynwamu | utility_room_0 | low (0.25-0.6 m), z 0.47 | 1.47 m (range 1.04-2.15) | no (fixed) |
| `countertop.n.01_1` | countertop_ikwqer_0 | countertop / ikwqer | utility_room_0 | table/counter (0.6-1.1 m), z 0.91 | 1.48 m (range 1.13-1.95) | no (fixed) |

Initial conditions from `:init`:

```lisp
(covered baseball_cap.n.01_1 dirt.n.02_1)
(covered baseball_cap.n.01_2 dirt.n.02_1)
(inroom countertop.n.01_1 utility_room)
(inroom floor.n.01_1 utility_room)
(inroom washer.n.03_1 utility_room)
(ontop agent.n.01_1 floor.n.01_1)
(ontop baseball_cap.n.01_1 countertop.n.01_1)
(ontop baseball_cap.n.01_2 countertop.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching baseball_cap.n.01_1 countertop.n.01_1)
(touching baseball_cap.n.01_2 countertop.n.01_1)
(touching countertop.n.01_1 baseball_cap.n.01_1)
(touching countertop.n.01_1 baseball_cap.n.01_2)
(touching floor.n.01_1 agent.n.01_1)
```

## What the human demos did

200 annotated demos. Length 269.28 s (range 190.57-379.0). Skills per demo 12.0 (range 10-13). 10 distinct skill orders; the most common one covers 20% of demos.

Most common skill counts per demo (36% of demos): move to x4, pick up from x2, place in x2, close door x1, open door x1, turn on switch x1, turn to x1.

Representative demo `episode_00320240.json` (284.7 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the washer` (0.0-10.4 s)
2. `open the door of the washer` (10.4-59.8 s)
3. `move to the baseball cap` (59.8-88.3 s)
4. `turn to the baseball cap` (88.3-108.3 s)
5. `pick up the baseball cap from the countertop` (108.3-117.2 s)
6. `move to the baseball cap` (117.2-135.2 s)
7. `pick up the baseball cap from the countertop` (135.2-149.1 s)
8. `move to the washer` (149.1-168.0 s)
9. `place the baseball cap in the washer` (168.0-198.2 s)
10. `place the baseball cap in the washer` (198.2-226.9 s)
11. `close the door of the washer` (226.9-252.8 s)
12. `turn on the washer` (252.8-284.7 s)

Mean duration per skill in this task: close door 23.9 s, move to 18.2 s, open door 46.7 s, pick up from 15.4 s, place in 27.6 s, turn on switch 24.6 s, turn to 22.7 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `place the baseball cap in the washer` | 400 |
| `move to the washer` | 399 |
| `pick up the baseball cap from the countertop` | 398 |
| `move to the baseball cap` | 327 |
| `turn to the baseball cap` | 211 |
| `open the door of the washer` | 200 |
| `close the door of the washer` | 200 |
| `turn on the washer` | 200 |
| `pick up the baseball cap from the washer` | 2 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/32_wash_a_baseball_cap.json`. Planner notes: `task_docs/notes/32_wash_a_baseball_cap.md`.
