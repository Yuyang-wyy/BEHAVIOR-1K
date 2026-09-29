# 07 · Picking Up Toys

Task name `picking_up_toys`, task index 7.

> Put all the toys in the child's room - the three board games (two on the bed and one on the table), the two jigsaw puzzles on the table, and the tennis ball on the table - inside the toy box on the table in the child's room.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | childs_room |
| rooms loaded | childs_room_0, childs_room_1, childs_room_2, corridor_0, dining_room_0, entryway_0, garden_0 |
| human demo length | 629.7 s mean (18890 steps) |
| episode time limit | 944.5 s (28335 steps at 30 Hz) |
| human base travel | 47.049 m |
| goal literals (best ground option) | 6 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.83; ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://player.vimeo.com/video/1114054920 |

## Planner notes

**Tier:** B, borderline C. Pure pick-and-place into an open box, but five of the six items are flat boxes that the humans push to the table or bed edge before they can grip them.

### Goal in plain words

- All six toys must end with their AABB centre inside the toy box: 3 board games, 2 jigsaw puzzles, 1 tennis ball.
- There is only one toy box, so there is no container choice.
- The toy box has no lid or joints (no `joint_pos` in the template registry), so nothing needs opening or closing.
- Nothing must be left out; there are no `not` literals.

### Q traps

- 6 literals, none true at reset. Each item placed is worth 1/6.
- Zero-shot `zs_pt50` reached Q=0.83 (5/6) on instance 311, so the toy box's `inside` volume works in practice.
- Partial Q reads only the final state. Bumping or dragging the toy box can spill items already inside (PREDICATES.md §3, knock-on displacement).
- A flat box leaning on the rim with its centre outside the box scores nothing. Check it dropped in.
- The toy box itself must stay on the desk. 55/200 demos lifted it and set it back `on the to_the_edge_of desk`; not needed.

### Minimal plan

Order: desk items first (toy box is on the same desk), then the two bed items.

1. `pick up the tennis ball from the desk`. Done: gripper closed, fingers short of fully closed, ball gone from desk. ~25 s.
2. `place the tennis ball in the toy box`. Done: gripper open, ball visible inside the box in RGB. ~17 s.
3. `push the jigsaw puzzle to the to_the_edge_of desk`. Done: puzzle overhangs the desk edge nearest the robot. ~46 s.
4. `pick up the jigsaw puzzle from the desk`. Done: puzzle lifted clear of desk. ~25 s.
5. `place the jigsaw puzzle in the toy box`. ~17 s.
6. Repeat 3-5 for the second jigsaw puzzle.
7. `push the board game to the to_the_edge_of desk`, `pick up the board game from the desk`, `place the board game in the toy box`. ~90 s.
8. `move to the board game` (the ones on the bed). ~15 s.
9. `push the board game to the to_the_edge_of bed`. ~46 s (demo segments on the bed run up to ~130 s).
10. `pick up the board game from the bed`. ~25 s.
11. `move to the toy box`. Done: base stopped facing the desk with the box in view. ~15 s.
12. `place the board game in the toy box`. ~17 s.
13. Repeat 8-12 for the second board game on the bed.

Budget: human mean 630 s, limit 944.5 s. Push steps dominate (mean 46 s each, 5 per demo).

### What the demos do differently

- The representative demo does bed games first, then desk items. Order does not matter for the goal.
- 55/200 demos pick up the toy box and re-place it at the desk edge. Skip it: it risks spilling items.
- 74 hand-over segments across 200 demos (`hand over the board game with the left` is the common one) appear. Not needed if one arm can place.
- Humans push every flat item (board games, puzzles) to an edge before picking; only the tennis ball is picked directly.

### Hard parts and hacks

- Board game and puzzle sizes are unknown (no custom list). The consistent push-to-edge in 200/200 demos suggests their top faces are too wide for the 44 mm jaws, so the grip goes on the overhanging thin edge.
- The jigsaw puzzle asset (antykn) is scaled 7.6x in z and ~1x in x-y, so it is a thicker slab than the native model. Its real thickness is unknown.
- The bed items sit low (z ~0.5 m) on a soft-looking bed; pushing them to the edge is the slowest demo step.
- Pushing too far drops the item on the floor. Then `pick up the board game from the floors` is not a trained prompt for this task (unverified whether Comet generalises).
- The bed and desk are ~2.5 m apart (template poses), so each bed item needs a carry.
- No scripted shortcut beyond the pushes: every literal needs a grasp or a drop into the box.

### Hints for the VLM

- Everything is in `childs_room_0`. The other two child's rooms have no toys or toy box (template init_info).
- The "table" in the BDDL is a desk (`desk_xhjsub_0`). The toy box sits on it at z ~0.83 m.
- Two board games start on the bed, one on the desk; both puzzles and the ball start on the desk. Positions shift up to ~1.8 m between instances, so look, do not assume.
- There are no other board games, puzzles or balls in the loaded scene to confuse with.
- Done looks like: desk and bed empty of toys; all six visible inside the open toy box.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside jigsaw_puzzle.n.01_2 toy_box.n.01_1)` | no | yes |
| `(inside jigsaw_puzzle.n.01_1 toy_box.n.01_1)` | no | yes |
| `(inside board_game.n.01_1 toy_box.n.01_1)` | no | yes |
| `(inside board_game.n.01_3 toy_box.n.01_1)` | no | yes |
| `(inside board_game.n.01_2 toy_box.n.01_1)` | no | yes |
| `(inside tennis_ball.n.01_1 toy_box.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (exists
                (?toy_box.n.01 - toy_box.n.01)
                (forall 
                    (?jigsaw_puzzle.n.01 - jigsaw_puzzle.n.01) 
                    (inside ?jigsaw_puzzle.n.01 ?toy_box.n.01)
                ) 
            )
            (exists
                (?toy_box.n.01 - toy_box.n.01)
                (forall 
                    (?board_game.n.01 - board_game.n.01) 
                    (inside ?board_game.n.01 ?toy_box.n.01)
                ) 
            )
            (exists
                (?toy_box.n.01 - toy_box.n.01)
                (forall
                    (?tennis_ball.n.01 - tennis_ball.n.01)
                    (inside ?tennis_ball.n.01 ?toy_box.n.01)
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
| `floor.n.01_1` | floors_vcsslq_0 | floors / vcsslq | childs_room_0 | floor, z -0.14 | 0.97 m (range 0.52-1.63) | no (fixed) |
| `board_game.n.01_1` | board_game_230 | board_game / ovttum | childs_room_0 | low (0.25-0.6 m), z 0.5 | 1.61 m (range 0.99-2.52) | yes, spread 1.69 m |
| `board_game.n.01_2` | board_game_229 | board_game / rgvkmy | childs_room_0 | low (0.25-0.6 m), z 0.51 | 1.95 m (range 0.84-2.55) | yes, spread 1.83 m |
| `board_game.n.01_3` | board_game_228 | board_game / vbamua | childs_room_0 | table/counter (0.6-1.1 m), z 0.8 | 1.15 m (range 0.81-2.02) | yes, spread 1.36 m |
| `jigsaw_puzzle.n.01_1` | jigsaw_puzzle_227 | jigsaw_puzzle / antykn | childs_room_0 | table/counter (0.6-1.1 m), z 0.77 | 1.57 m (range 0.85-1.83) | yes, spread 1.64 m |
| `jigsaw_puzzle.n.01_2` | jigsaw_puzzle_226 | jigsaw_puzzle / antykn | childs_room_0 | table/counter (0.6-1.1 m), z 0.8 | 1.27 m (range 0.84-1.96) | yes, spread 1.54 m |
| `tennis_ball.n.01_1` | tennis_ball_225 | tennis_ball / rgekxe | childs_room_0 | table/counter (0.6-1.1 m), z 0.81 | 1.38 m (range 0.83-2.03) | yes, spread 1.76 m |
| `bed.n.01_1` | bed_rrcvaq_0 | bed / rrcvaq | childs_room_0 | low (0.25-0.6 m), z 0.4 | 1.77 m (range 1.5-2.46) | no (fixed) |
| `table.n.02_1` | desk_xhjsub_0 | desk / xhjsub | childs_room_0 | low (0.25-0.6 m), z 0.43 | 1.41 m (range 0.95-1.67) | no (fixed) |
| `toy_box.n.01_1` | toy_box_224 | toy_box / aviadj | childs_room_0 | table/counter (0.6-1.1 m), z 0.83 | 1.52 m (range 1.08-1.85) | yes, spread 0.45 m |

Initial conditions from `:init`:

```lisp
(inroom bed.n.01_1 childs_room)
(inroom floor.n.01_1 childs_room)
(inroom table.n.02_1 childs_room)
(ontop agent.n.01_1 floor.n.01_1)
(ontop board_game.n.01_1 bed.n.01_1)
(ontop board_game.n.01_2 bed.n.01_1)
(ontop board_game.n.01_3 table.n.02_1)
(ontop jigsaw_puzzle.n.01_1 table.n.02_1)
(ontop jigsaw_puzzle.n.01_2 table.n.02_1)
(ontop tennis_ball.n.01_1 table.n.02_1)
(ontop toy_box.n.01_1 table.n.02_1)
(touching agent.n.01_1 floor.n.01_1)
(touching bed.n.01_1 board_game.n.01_1)
(touching bed.n.01_1 board_game.n.01_2)
(touching board_game.n.01_1 bed.n.01_1)
(touching board_game.n.01_2 bed.n.01_1)
(touching board_game.n.01_3 table.n.02_1)
(touching floor.n.01_1 agent.n.01_1)
(touching jigsaw_puzzle.n.01_1 table.n.02_1)
(touching jigsaw_puzzle.n.01_2 table.n.02_1)
(touching table.n.02_1 board_game.n.01_3)
(touching table.n.02_1 jigsaw_puzzle.n.01_1)
(touching table.n.02_1 jigsaw_puzzle.n.01_2)
(touching table.n.02_1 tennis_ball.n.01_1)
(touching table.n.02_1 toy_box.n.01_1)
(touching tennis_ball.n.01_1 table.n.02_1)
(touching toy_box.n.01_1 table.n.02_1)
```

## What the human demos did

200 annotated demos. Length 618.83 s (range 257.07-1070.13). Skills per demo 26.0 (range 21-33). 147 distinct skill orders; the most common one covers 5% of demos.

Most common skill counts per demo (14% of demos): move to x8, pick up from x6, place in x6, push to x5.

Representative demo `episode_00071610.json` (752.3 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the board game` (0.0-32.3 s)
2. `push the board game to the to_the_edge_of bed` (32.3-119.7 s)
3. `pick up the board game from the bed` (119.7-140.5 s)
4. `move to the toy box` (140.5-149.6 s)
5. `place the board game in the toy box` (149.6-169.9 s)
6. `move to the board game` (169.9-226.7 s)
7. `push the board game to the to_the_edge_of bed` (226.7-359.3 s)
8. `pick up the board game from the bed` (359.3-391.6 s)
9. `move to the toy box` (391.6-408.1 s)
10. `place the board game in the toy box` (408.1-434.5 s)
11. `move to the board game` (434.5-445.5 s)
12. `push the board game to the to_the_edge_of desk` (445.5-465.4 s)
13. `pick up the board game from the desk` (465.4-485.3 s)
14. `move to the toy box` (485.3-490.7 s)
15. `place the board game in the toy box` (490.7-514.9 s)
16. `push the jigsaw puzzle to the to_the_edge_of desk` (514.9-552.5 s)
17. `pick up the jigsaw puzzle from the desk` (552.5-584.1 s)
18. `move to the toy box` (584.1-586.9 s)
19. `place the jigsaw puzzle in the toy box` (586.9-609.2 s)
20. `push the jigsaw puzzle to the to_the_edge_of desk` (609.2-647.4 s)
21. `pick up the jigsaw puzzle from the desk` (647.4-679.6 s)
22. `move to the toy box` (679.6-690.7 s)
23. `place the jigsaw puzzle in the toy box` (690.8-706.8 s)
24. `pick up the tennis ball from the desk` (706.8-722.6 s)
25. `place the tennis ball in the toy box` (722.6-752.3 s)

Mean duration per skill in this task: hand over 11.8 s, move to 15.3 s, pick up from 24.6 s, place in 17.2 s, place on 9.9 s, push to 46.4 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the toy box` | 958 |
| `place the board game in the toy box` | 598 |
| `move to the board game` | 493 |
| `pick up the board game from the bed` | 400 |
| `pick up the jigsaw puzzle from the desk` | 400 |
| `place the jigsaw puzzle in the toy box` | 399 |
| `push the jigsaw puzzle to the to_the_edge_of desk` | 398 |
| `push the board game to the to_the_edge_of bed` | 393 |
| `pick up the tennis ball from the desk` | 201 |
| `place the tennis ball in the toy box` | 201 |
| `push the board game to the to_the_edge_of desk` | 200 |
| `pick up the board game from the desk` | 199 |
| `move to the jigsaw puzzle` | 175 |
| `move to the tennis ball` | 82 |
| `pick up the toy box from the desk` | 55 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/07_picking_up_toys.json`. Planner notes: `task_docs/notes/07_picking_up_toys.md`.
