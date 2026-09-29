# 33 · Wash Dog Toys

Task name `wash_dog_toys`, task index 33.

> In the utility room, take the two teddy toys, the tennis ball, and the softball out of the cabinet and wash them in the washer so that both teddies are free of dirt and dust, the tennis ball has no debris, and the softball has no dirt.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | utility_room |
| rooms loaded | corridor_0, dining_room_0, entryway_0, garden_0, utility_room_0 |
| human demo length | 374.1 s mean (11222 steps) |
| episode time limit | 561.1 s (16834 steps at 30 Hz) |
| human base travel | 46.5824 m |
| goal literals (best ground option) | 6 |
| literals already true at start (inferred) | 2 |
| max Q short of full success | 0.667 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.00; ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://player.vimeo.com/video/1114060219 |

## Planner notes

**Tier:** D — four items out of a closed two-door cabinet into the washer, then a washer cycle (a state transition) clears three particle systems.

### Goal in plain words

Both teddy bears must be free of dirt and dust, the tennis ball free of debris, the softball free of dirt.
The route is one washer cycle with all four toys inside: open washer, open cabinet, move the four toys into the washer, close the washer door, turn it on.
The cabinet may be left open: the goal has no `not open` literal.

### Q traps

- 6 literals, 2 already true at reset, so max partial Q is 0.667 (4 scoring literals). Verified from the template `system_registry` in all 20 instances:
  - dirt: 40 particles, 20 on `teddy_bear_191` (teddy_1) and 20 on the softball;
  - dust: 20 particles, only on `teddy_bear_190` (teddy_2);
  - debris: 20 on the tennis ball (19 or 13 in instances 309, 314, 315).
  - So `not covered teddy_2 dirt` and `not covered teddy_1 dust` are true at reset and never score. The page is right.
- The washer cleans only on the step it **changes** to (toggled on AND closed) (`transition_rules.py:745-757`). Per system, it clears `covered` only if the washer volume holds at least 1 particle of that system at that step (`transition_rules.py:846-884`). Then every object with any collision point in the volume is cleaned of it.
  - dust lives only on teddy_2, and debris only on the tennis ball. If either of them is missing or only grazing the rim, that literal stays false even though the others clean.
- Washer starts closed and off in all 20 instances; the cabinet (`gjrero_0`, 2 doors) starts closed in all 20 (joint_pos ~0).
- Four toys in one drum: a teddy leg or ball in the doorway keeps the door >5 % open (§6), so nothing fires. Check the door is flush before pressing.
- Fallback: several cycles work. Opening the washer forces it off; close and press again to fire a new cycle. Each toy scores 1 literal (Q 0.167 each).
- Success ends the episode on the press step.

### Minimal plan

1. `move to the washer` — washer front in view. ~14 s.
2. `open the door of the washer` — door open, drum visible. ~34 s.
3. `move to the bottom cabinet no top` — cabinet doors in view at close range. ~14 s.
4. `open the door of the left_door bottom cabinet no top` — left door swung open. ~34 s.
5. `open the door of the right_door bottom cabinet no top` — right door open; both shelves visible. ~34 s.
6. `pick up the teddy bear from the high_level bottom cabinet no top` (or `..._middle_level ...`, and the softball / tennis ball variants, matching the shelf the item is on) — gripper closed short of fully closed; item gone from the shelf. ~13 s each. Carry two items per trip, one per hand.
7. If an item faces the wrong way: `push the teddy bear to the reorient bottom cabinet no top` (same for softball / tennis ball). ~12 s.
8. `move to the washer` — ~14 s.
9. `place the teddy bear in the washer` / `place the softball in the washer` / `place the tennis ball in the washer` — item released, not visible outside the drum. ~21 s each.
10. Repeat 3, 6, 8, 9 for the second pair (`move to the teddy bear` etc. also works as the move prompt).
11. `close the door of the washer` — door flush. ~21 s.
12. `turn on the washer` — fingertip on the control; episode ends on success. ~22 s.

About 350 s against a 561.1 s limit; the representative demo is already this plan (350.8 s). Prioritise teddy_2 (dust) and the tennis ball (debris) if time is short: they are the only carriers of those systems.

### What the demos do differently

- All demos open the washer before the cabinet, then do two trips of two items each.
- 253 segments reorient a teddy inside the cabinet with `push ... to the reorient ...` before grasping it. Balls are reoriented less often.
- Humans never close the cabinet; do not spend time on it.
- The shelf words `high_level` / `middle_level` in the prompts track which shelf the item is on (items sit at z≈0.71 or z≈0.45 in the instances; the mapping of words to shelves is unverified).

### Hard parts and hacks

- Grasping inside a cabinet shelf with doors half in the way; the low shelf is at ~0.45 m.
- Item sizes are unknown (no custom list). Demos grasp all four, so some part registers within 44 mm; which part is unverified (teddy limbs likely).
- Cabinet and washer door handles: width vs 44 mm unverified. The washer door is the slow step.
- The cabinet row (x≈24.58) faces the washer (x≈22.0) across the room, ~2.6 m apart.
- Button location on washer `ynwamu` unverified; the press needs 5 steps of finger contact on the button sphere (§11). A scripted press routine is legal once the hand is there.
- Closed-loop so far: Q 0.00 on instance 311 for all three checkpoints.

### Hints for the VLM

- Utility room. The toys are always in `bottom_cabinet_no_top_gjrero_0`, the end cabinet (y≈1.68) of a row of four identical two-door cabinets under the long counter. The other three (and a fifth under the far counter) are distractors.
- Washer and clothes dryer stand side by side on the opposite wall (washer y≈0.33, dryer y≈0.95). Use the washer.
- Two teddy bears (slightly different scale, 0.8 vs 0.9), one tennis ball, one softball. Dirt, dust and debris show as small specks on them; they vanish on the press step.
- Done = all four toys out of the cabinet and inside the washer drum, washer door flush, washer pressed.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(not covered teddy.n.01_2 dirt.n.02_1))` | yes | never (already true) |
| `(not covered teddy.n.01_2 dust.n.01_1))` | no | yes |
| `(not covered teddy.n.01_1 dirt.n.02_1))` | no | yes |
| `(not covered teddy.n.01_1 dust.n.01_1))` | yes | never (already true) |
| `(not covered tennis_ball.n.01_1 debris.n.01_1))` | no | yes |
| `(not covered softball.n.01_1 dirt.n.02_1))` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (forall 
                (?teddy.n.01 - teddy.n.01)
                (and
                    (not 
                        (covered ?teddy.n.01 ?dirt.n.02_1)
                    )
                    (not 
                        (covered ?teddy.n.01 ?dust.n.01_1)
                    )
                )
            )
            (not 
                (covered ?tennis_ball.n.01_1 ?debris.n.01_1)
            ) 
            (not 
                (covered ?softball.n.01_1 ?dirt.n.02_1)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `teddy.n.01_1` | teddy_bear_191 | teddy_bear / mvwvlv | utility_room_0 | table/counter (0.6-1.1 m), z 0.71 | 1.95 m (range 1.04-3.39) | yes, spread 0.66 m |
| `teddy.n.01_2` | teddy_bear_190 | teddy_bear / mvwvlv | utility_room_0 | table/counter (0.6-1.1 m), z 0.72 | 2.08 m (range 1.02-3.48) | yes, spread 0.63 m |
| `washer.n.03_1` | washer_ynwamu_0 | washer / ynwamu | utility_room_0 | low (0.25-0.6 m), z 0.47 | 1.54 m (range 1.05-2.02) | no (fixed) |
| `dirt.n.02_1` | particle system | dirt | - | - | - | - |
| `dust.n.01_1` | particle system | dust | - | - | - | - |
| `tennis_ball.n.01_1` | tennis_ball_189 | tennis_ball / rgekxe | utility_room_0 | table/counter (0.6-1.1 m), z 0.68 | 1.96 m (range 1.28-3.42) | yes, spread 0.86 m |
| `debris.n.01_1` | particle system | debris | - | - | - | - |
| `softball.n.01_1` | softball_188 | softball / erhbze | utility_room_0 | low (0.25-0.6 m), z 0.45 | 2.13 m (range 1.34-3.21) | yes, spread 0.9 m |
| `cabinet.n.01_1` | bottom_cabinet_no_top_gjrero_0 | bottom_cabinet_no_top / gjrero | utility_room_0 | low (0.25-0.6 m), z 0.47 | 2.08 m (range 1.17-3.27) | no (fixed) |
| `floor.n.01_1` | floors_glwobe_0 | floors / glwobe | utility_room_0 | floor, z -0.14 | 0.88 m (range 0.04-1.65) | no (fixed) |

Initial conditions from `:init`:

```lisp
(covered softball.n.01_1 dirt.n.02_1)
(covered teddy.n.01_1 dirt.n.02_1)
(covered teddy.n.01_2 dust.n.01_1)
(covered tennis_ball.n.01_1 debris.n.01_1)
(inroom cabinet.n.01_1 utility_room)
(inroom floor.n.01_1 utility_room)
(inroom washer.n.03_1 utility_room)
(inside softball.n.01_1 cabinet.n.01_1)
(inside teddy.n.01_1 cabinet.n.01_1)
(inside teddy.n.01_2 cabinet.n.01_1)
(inside tennis_ball.n.01_1 cabinet.n.01_1)
(ontop agent.n.01_1 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
```

## What the human demos did

200 annotated demos. Length 359.95 s (range 278.0-819.3). Skills per demo 20.0 (range 18-22). 24 distinct skill orders; the most common one covers 13% of demos.

Most common skill counts per demo (43% of demos): move to x5, pick up from x4, place in x4, open door x3, push to x2, close door x1, turn on switch x1.

Representative demo `episode_00331620.json` (350.8 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the washer` (0.0-20.2 s)
2. `open the door of the washer` (20.2-57.8 s)
3. `move to the bottom cabinet no top` (57.8-76.5 s)
4. `open the door of the left_door bottom cabinet no top` (76.5-103.5 s)
5. `open the door of the right_door bottom cabinet no top` (103.5-137.3 s)
6. `pick up the softball from the high_level bottom cabinet no top` (137.3-148.1 s)
7. `pick up the teddy bear from the high_level bottom cabinet no top` (148.1-157.4 s)
8. `move to the washer` (157.4-165.7 s)
9. `place the teddy bear in the washer` (165.7-184.9 s)
10. `place the softball in the washer` (184.9-210.3 s)
11. `move to the teddy bear` (210.3-226.2 s)
12. `pick up the teddy bear from the middle_level bottom cabinet no top` (226.2-245.5 s)
13. `pick up the tennis ball from the middle_level bottom cabinet no top` (245.5-260.2 s)
14. `move to the washer` (260.2-270.8 s)
15. `place the teddy bear in the washer` (270.8-286.5 s)
16. `place the tennis ball in the washer` (286.5-307.2 s)
17. `close the door of the washer` (307.2-333.5 s)
18. `turn on the washer` (333.5-350.8 s)

Mean duration per skill in this task: close door 20.6 s, move to 13.8 s, open door 33.6 s, pick up from 12.5 s, place in 20.8 s, push to 12.1 s, turn on switch 21.9 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the washer` | 596 |
| `place the teddy bear in the washer` | 398 |
| `push the teddy bear to the reorient bottom cabinet no top` | 253 |
| `pick up the teddy bear from the high_level bottom cabinet no top` | 213 |
| `move to the bottom cabinet no top` | 200 |
| `close the door of the washer` | 200 |
| `turn on the washer` | 200 |
| `open the door of the washer` | 199 |
| `open the door of the left_door bottom cabinet no top` | 199 |
| `open the door of the right_door bottom cabinet no top` | 199 |
| `place the tennis ball in the washer` | 199 |
| `place the softball in the washer` | 197 |
| `pick up the teddy bear from the middle_level bottom cabinet no top` | 185 |
| `pick up the softball from the middle_level bottom cabinet no top` | 137 |
| `pick up the tennis ball from the middle_level bottom cabinet no top` | 136 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/33_wash_dog_toys.json`. Planner notes: `task_docs/notes/33_wash_dog_toys.md`.
