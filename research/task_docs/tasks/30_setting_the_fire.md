# 30 · Setting The Fire

Task name `setting_the_fire`, task index 30.

> In the living room, place the newspaper from the table into the wood fireplace, then put both pieces of firewood from the floor on top of the newspaper. Use the cigar lighter to ignite any one of the items so that the whole pile catches fire, and then turn the lighter off.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | living_room |
| rooms loaded | corridor_0, garden_0, kitchen_0, living_room_0 |
| human demo length | 303.9 s mean (9118 steps) |
| episode time limit | 455.9 s (13677 steps at 30 Hz) |
| human base travel | 31.8047 m |
| goal literals (best ground option) | 8 |
| literals already true at start (inferred) | 1 |
| max Q short of full success | 0.875 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.12; ft40k@sulab1 Q=0.75; ft40k@local Q=0.75 |
| demo video | https://player.vimeo.com/video/1114059945 |

## Planner notes

**Tier:** D. Pick-and-place of a newspaper and two logs into the fireplace, then an ignition (a state transition) with a held, toggled lighter that must be switched off again.

### Goal in plain words

Both logs must rest directly on the newspaper, with their centres inside the wood fireplace, and both logs and the newspaper must be on fire. The lighter must end switched off. The newspaper itself has no `inside` literal, but it has to be under the logs in the fireplace for the log literals to hold. There is one ground option.

### Q traps

- `not toggled_on cigar_lighter` is true at reset (template `ToggledOn` value False) and never scores: 8 literals, max partial Q 0.875. Leaving the lighter on still blocks success.
- `on_fire` latches (PREDICATES §14): once a log or the paper burns, it stays burning, even if it is moved later. Igniting early costs nothing.
- `ontop log newspaper` needs direct contact and the paper under the log's AABB-centre x-y (§4). A log stacked on the other log, or resting on the fireplace floor beside the paper, fails. The paper asset is 0.29 x 0.21 m (asset metadata bbox, no custom list; unverified at runtime), a log 0.26 x 0.078 x 0.066 m; two logs side by side along the paper's long side fit.
- ft40k scored 0.75 (6/8) on instance 311. Without any `inside` literal the best is 5/8, so at least one log counted as inside: the fireplace has a working fillable volume (inferred from that result).
- Grasping the lighter can press its toggle button by accident (derived: finger contact plus overlap of the button sphere for 5 steps flips it, §11). Check the flame state after every grasp and release.
- A second press flips the lighter back. Turn it off with exactly one clean press.

### Minimal plan

1. `move to the newspaper` -> `push the newspaper to the to_the_edge_of coffee table` -> `pick up the newspaper from the coffee table`. Done: gripper closed short of full closure, paper off the table. ~85 s (push mean 38 s).
2. `move to the firewood` -> `pick up the firewood from the floors` with the free hand. Done: log lifted in the second gripper. ~33 s.
3. `move to the wood fireplace` -> `place the newspaper in the wood fireplace` -> `place the firewood in the wood fireplace`. Done: paper flat on the fireplace floor, log lying on it. ~50 s.
4. `move to the lighter` -> `pick up the lighter from the coffee table` -> `turn on the lighter`. Done: flame visible at the lighter tip. ~40 s.
5. `move to the firewood` -> `pick up the firewood from the floors` (other hand) -> `move to the wood fireplace`. ~45 s.
6. `ignite the lighter with the firewood`. Hold the flame at the log for ~3 s (lighter 23 -> 250 °C in ~2.7 s, derived). Done: fire visible on the held log. ~6 s.
7. `place the firewood in the wood fireplace`, next to the first log and on the paper. The burning log ignites the paper and the other log if they are within 0.2 m of its centre (~7 s, derived). ~16 s.
8. `turn off the lighter`. Done: flame gone. ~10 s. Then wait a few seconds and check that the paper and both logs show fire.

Total about 290 s against a 456 s limit, the same as the demo; the demo has no removable steps.

### What the demos do differently

- 94 % of demos follow exactly the order above. The demos carry the lit lighter to the second log and ignite it while holding it, so the robot holds lighter and log in two hands at once.
- 11 demos use `ignite the firewood with the lighter` and 2 ignite the newspaper; the in-distribution wording is `ignite the lighter with the firewood` (187 demos).
- A simpler variant, not in the demos: put both logs on the paper first, then light the paper or a log in place with the lighter. It avoids the two-handed carry but needs the lighter to reach into the firebox; no trained prompt for "ignite in place" other than `ignite the lighter with the firewood`.

### Hard parts and hacks

- Grasp widths (asset metadata bbox, no custom list; unverified at runtime): newspaper 46 mm thick (at or over the 44 mm limit, hence the push-to-edge), log 66-78 mm across its cross-section (above the limit unless grasped at an end or tapered part; unverified how the demos' grasp registers), lighter 18 mm thick.
- Log placement is the precision step: both log centres over the 0.29 x 0.21 m paper, in contact with it, inside the firebox. Dropping from height can roll a log off the paper.
- Keep the two logs close (centres within 0.2 m of each other and of the paper centre) so one ignition spreads to all three.
- The lighter heats anything within 0.2 m of its tip while on (§2). Switch it off before putting it down.
- Log start positions vary by up to 4.7 m between instances; the paper and lighter are always on the coffee table.

### Hints for the VLM

- living_room_0 has one wood fireplace, one coffee table, one lighter, one newspaper and two logs; no same-category distractors.
- The logs start on the floor; the newspaper and lighter start on the low coffee table (~0.4 m).
- The fireplace is a large fixed unit (0.74 x 1.75 x 1.31 m asset bbox, unverified at runtime) against a wall; the firebox opening faces the room.
- Fire should show as a flame effect on the object (rendering unverified). Done means flame on both logs and the paper, logs lying on the paper, lighter with no flame.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(on_fire firewood.n.01_1)` | no | yes |
| `(ontop firewood.n.01_1 newspaper.n.03_1)` | no | yes |
| `(inside firewood.n.01_1 wood_fireplace.n.01_1)` | no | yes |
| `(on_fire firewood.n.01_2)` | no | yes |
| `(ontop firewood.n.01_2 newspaper.n.03_1)` | no | yes |
| `(inside firewood.n.01_2 wood_fireplace.n.01_1)` | no | yes |
| `(on_fire newspaper.n.03_1)` | no | yes |
| `(not toggled_on cigar_lighter.n.01_1))` | yes | never (already true) |

BDDL goal:

```lisp
(:goal 
        (and 
            (forall 
                (?firewood.n.01 - firewood.n.01) 
                (and
                    (on_fire ?firewood.n.01)
                    (ontop ?firewood.n.01 ?newspaper.n.03_1)
                    (inside ?firewood.n.01 ?wood_fireplace.n.01_1)
                )
            )
            (on_fire ?newspaper.n.03_1)
            (not
                (toggled_on cigar_lighter.n.01_1)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `firewood.n.01_1` | firewood_76 | firewood / agntyc | living_room_0 | floor, z 0.03 | 1.65 m (range 0.58-3.39) | yes, spread 4.67 m |
| `firewood.n.01_2` | firewood_75 | firewood / agntyc | living_room_0 | floor, z 0.03 | 1.47 m (range 0.62-3.31) | yes, spread 4.52 m |
| `floor.n.01_1` | floors_ulujpr_0 | floors / ulujpr | living_room_0 | floor, z -0.15 | 1.45 m (range 0.84-2.14) | no (fixed) |
| `newspaper.n.03_1` | newspaper_74 | newspaper / omsont | living_room_0 | low (0.25-0.6 m), z 0.45 | 1.86 m (range 1.05-2.35) | yes, spread 1.41 m |
| `table.n.02_1` | coffee_table_koagbh_0 | coffee_table / koagbh | living_room_0 | low (0.25-0.6 m), z 0.36 | 1.67 m (range 1.26-2.15) | no |
| `cigar_lighter.n.01_1` | lighter_73 | lighter / zsxfjz | living_room_0 | low (0.25-0.6 m), z 0.43 | 1.82 m (range 0.96-2.59) | yes, spread 1.45 m |
| `wood_fireplace.n.01_1` | wood_fireplace_gpnsij_0 | wood_fireplace / gpnsij | living_room_0 | table/counter (0.6-1.1 m), z 0.65 | 2.11 m (range 1.31-3.05) | no (fixed) |

Initial conditions from `:init`:

```lisp
(inroom floor.n.01_1 living_room)
(inroom table.n.02_1 living_room)
(inroom wood_fireplace.n.01_1 living_room)
(ontop agent.n.01_1 floor.n.01_1)
(ontop cigar_lighter.n.01_1 table.n.02_1)
(ontop firewood.n.01_1 floor.n.01_1)
(ontop firewood.n.01_2 floor.n.01_1)
(ontop newspaper.n.03_1 table.n.02_1)
(touching agent.n.01_1 floor.n.01_1)
(touching cigar_lighter.n.01_1 table.n.02_1)
(touching firewood.n.01_1 floor.n.01_1)
(touching firewood.n.01_2 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 firewood.n.01_1)
(touching floor.n.01_1 firewood.n.01_2)
(touching newspaper.n.03_1 table.n.02_1)
(touching table.n.02_1 cigar_lighter.n.01_1)
(touching table.n.02_1 newspaper.n.03_1)
```

## What the human demos did

200 annotated demos. Length 290.23 s (range 189.0-477.77). Skills per demo 17.0 (range 16-17). 6 distinct skill orders; the most common one covers 94% of demos.

Most common skill counts per demo (98% of demos): move to x6, pick up from x4, place in x3, ignite x1, push to x1, turn off switch x1, turn on switch x1.

Representative demo `episode_00301020.json` (290.9 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the newspaper` (0.0-31.4 s)
2. `push the newspaper to the to_the_edge_of coffee table` (37.4-70.3 s)
3. `pick up the newspaper from the coffee table` (72.6-86.5 s)
4. `move to the firewood` (86.5-111.1 s)
5. `pick up the firewood from the floors` (116.7-128.3 s)
6. `move to the wood fireplace` (128.4-145.9 s)
7. `place the newspaper in the wood fireplace` (149.1-161.2 s)
8. `place the firewood in the wood fireplace` (162.4-171.8 s)
9. `move to the lighter` (172.4-184.2 s)
10. `pick up the lighter from the coffee table` (185.0-200.3 s)
11. `turn on the lighter` (215.2-223.6 s)
12. `move to the firewood` (224.9-230.6 s)
13. `pick up the firewood from the floors` (231.2-242.1 s)
14. `move to the wood fireplace` (242.6-257.1 s)
15. `ignite the lighter with the firewood` (257.2-262.0 s)
16. `place the firewood in the wood fireplace` (263.0-278.4 s)
17. `turn off the lighter` (279.6-290.9 s)

Mean duration per skill in this task: ignite 5.3 s, move to 16.2 s, pick up from 16.6 s, place in 15.7 s, push to 38.3 s, turn off switch 9.8 s, turn on switch 10.1 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the firewood` | 399 |
| `pick up the firewood from the floors` | 399 |
| `place the firewood in the wood fireplace` | 398 |
| `move to the wood fireplace` | 396 |
| `place the newspaper in the wood fireplace` | 201 |
| `move to the newspaper` | 200 |
| `pick up the newspaper from the coffee table` | 200 |
| `move to the lighter` | 200 |
| `turn on the lighter` | 200 |
| `turn off the lighter` | 200 |
| `push the newspaper to the to_the_edge_of coffee table` | 196 |
| `pick up the lighter from the coffee table` | 196 |
| `ignite the lighter with the firewood` | 187 |
| `ignite the firewood with the lighter` | 11 |
| `pick up the lighter from the floors` | 4 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/30_setting_the_fire.json`. Planner notes: `task_docs/notes/30_setting_the_fire.md`.
