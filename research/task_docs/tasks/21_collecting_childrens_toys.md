# 21 · Collecting Children's Toys

Task name `collecting_childrens_toys`, task index 21.

> Pick up the two dice from the bed, the two teddy bears from the floor, and the two board games (one from the desk and one from the bed), and place them all inside the same bookcase in the child's room.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | childs_room |
| rooms loaded | childs_room_0, childs_room_1, childs_room_2, corridor_0, dining_room_0, entryway_0, garden_0 |
| human demo length | 639.5 s mean (19186 steps) |
| episode time limit | 959.3 s (28779 steps at 30 Hz) |
| human base travel | 58.4048 m |
| goal literals (best ground option) | 7 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 2 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.29; ft40k@sulab1 Q=0.57; ft40k@local Q=0.57 |
| demo video | https://player.vimeo.com/video/1114058872 |

## Planner notes

**Tier:** B — seven small toys go into a bookcase in one room, with short moves. The dice (0.04 m) fit the 44 mm span. The board games (0.044 m thick, lying flat) need a push to the edge first, as in the demos. The teddies (0.11 m smallest side) and the train (0.052 m wide) are wider than the span.

### Goal in plain words

Both dice, both teddy bears, both board games and the toy train must all be inside the same bookcase.
Either of the two identical bookcases works (2 ground options), but all seven toys must share it.
Shelf choice inside the bookcase is free.

### Q traps

- 7 literals, all False at reset. Each toy is worth 1/7. ft40k reached 4/7 on instance 311.
- All toys must go in ONE bookcase. Toys split across the two bookcases score only the larger group. The demos use `bookcase_zfpyqe_1` (the one at y 6.93, nearer the start in most instances); stick to it.
- `inside` needs each toy's AABB centre in a shelf volume (PREDICATES §3). A toy on top of the bookcase (1.64 m tall) is not inside. A board game stacked on the other board game still counts if its centre is within the shelf volume.
- Instance 313: `dice_269` starts at z 1.0 m, not 0.44 m like the other 19 instances, at x 21.36, just past the bed's x-extent. It is not on the bed mattress there; look for it higher up (headboard or elsewhere). Unverified what it rests on.

### Minimal plan

Everything is in childs_room_2, 0.3-3.5 m from the start. The teddies are on the floor, the dice and one board game on the bed, the train and the other board game on the desk.

1. `move to the teddy bear`, `pick up the teddy bear from the floors` twice (one per hand). ~15 s + 27 s each.
2. `move to the bookcase`, `place the teddy bear in the layer_3 bookcase` twice. ~15 s + 18 s each.
3. `move to the dice`, `pick up the dice from the bed` twice. ~15 s + 27 s each.
4. `move to the bookcase`, `place the dice in the layer_2 bookcase` twice.
5. `move to the board game`, `push the board game to the to_the_edge_of bed`, `pick up the board game from the bed`. ~15 + 53 + 27 s.
6. `move to the bookcase`, `place the board game in the layer_2 bookcase`.
7. `move to the toy train`, `push the toy train to the to_the_edge_of desk`, `pick up the toy train from the desk`, `move to the bookcase`, `place the toy train in the layer_4 bookcase`.
8. `move to the board game`, `push the board game to the to_the_edge_of desk`, `pick up the board game from the desk`, `move to the bookcase`, `place the board game on the board game` (on the first board game, inside the shelf).

Done-check each time: toy visible between shelf boards, gripper withdrawn, toy not visible at its source.
Budget: about 600 s against a 959 s limit. Do the dice first if Q must be banked fast: they are the most graspable.

### What the demos do differently

- 200/200 demos push the board games and ~196 push the train to the furniture edge before picking; that is the trained route for flat objects.
- All but one demo use `bookcase_zfpyqe_1`. Shelf words (`layer_2`, `layer_3`, `layer_4`) vary by toy.
- ~194 demos stack the second board game on the first (`place the board game on the board game`). This scores only because the stack is inside the shelf.
- A few demos push a chair out of the way at the desk.

### Hard parts and hacks

- Dice: 0.04 m cubes, the easiest grasp. Two dice = 2/7 quickly.
- Teddy bears: 0.24 x 0.16 x 0.11 m, rigid in sim; the span only fits a limb or ear, unverified.
- Toy train: 0.55 x 0.052 x 0.066 m, just wider than the span; placing a 0.55 m object needs the shelf opening wide enough (bookcase 0.85 m wide, fine).
- Board games: 0.13 x 0.20 x 0.044 m. The 0.044 m thickness is at the limit; grasp only after the push overhangs the edge.

### Hints for the VLM

- The two bookcases are identical tall (1.64 m) shelves standing side by side (0.87 m apart, same wall). Use the one the demos use, `bookcase_zfpyqe_1`, which is nearer the robot start in most instances (median 1.23 m vs 1.8 m), and remember it.
- The room also has one bed, one desk, three straight chairs and a floor lamp. Two other children's rooms are loaded; the toys are all in childs_room_2.
- Done: nothing left on the bed, the desk or the floor; all seven toys visible on the shelves of one bookcase.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside die.n.01_2 bookcase.n.01_2)` | no | yes |
| `(inside die.n.01_1 bookcase.n.01_2)` | no | yes |
| `(inside teddy.n.01_1 bookcase.n.01_2)` | no | yes |
| `(inside teddy.n.01_2 bookcase.n.01_2)` | no | yes |
| `(inside board_game.n.01_1 bookcase.n.01_2)` | no | yes |
| `(inside board_game.n.01_2 bookcase.n.01_2)` | no | yes |
| `(inside train_set.n.01_1 bookcase.n.01_2)` | no | yes |

The goal has 2 ground options (7 literals x2); Q takes the best one, so any valid choice of container or partner object counts.

BDDL goal:

```lisp
(:goal 
        (and 
            (exists
                (?bookcase.n.01 - bookcase.n.01)
                (and 
                    (forall
                        (?die.n.01 - die.n.01)
                        (inside ?die.n.01 ?bookcase.n.01)
                    )
                    (forall
                        (?teddy.n.01 - teddy.n.01)
                        (inside ?teddy.n.01 ?bookcase.n.01)         
                    )
                    (forall
                        (?board_game.n.01 - board_game.n.01)
                        (inside ?board_game.n.01 ?bookcase.n.01)
                    )
                    (forall
                        (?train_set.n.01 - train_set.n.01)
                        (inside ?train_set.n.01 ?bookcase.n.01)
                    )
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
| `die.n.01_1` | dice_269 | dice / jommvx | childs_room_2 | low (0.25-0.6 m), z 0.44 | 1.39 m (range 0.76-2.29) | yes, spread 1.74 m |
| `die.n.01_2` | dice_268 | dice / iswudu | childs_room_2 | low (0.25-0.6 m), z 0.44 | 1.35 m (range 0.73-2.77) | yes, spread 1.61 m |
| `floor.n.01_1` | floors_vmamhf_0 | floors / vmamhf | childs_room_2 | floor, z -0.14 | 0.92 m (range 0.3-1.45) | no (fixed) |
| `teddy.n.01_1` | teddy_bear_267 | teddy_bear / dgagea | childs_room_2 | floor, z 0.05 | 1.22 m (range 0.67-2.29) | yes, spread 3.4 m |
| `teddy.n.01_2` | teddy_bear_266 | teddy_bear / dgagea | childs_room_2 | floor, z 0.05 | 1.9 m (range 0.65-2.93) | yes, spread 3.44 m |
| `train_set.n.01_1` | toy_train_265 | toy_train / zdfhbw | childs_room_2 | low (0.25-0.6 m), z 0.58 | 2.53 m (range 1.11-2.96) | yes, spread 0.56 m |
| `board_game.n.01_1` | board_game_264 | board_game / gcfkqa | childs_room_2 | low (0.25-0.6 m), z 0.57 | 2.51 m (range 1.44-3.14) | yes, spread 0.97 m |
| `board_game.n.01_2` | board_game_263 | board_game / gcfkqa | childs_room_2 | low (0.25-0.6 m), z 0.45 | 1.44 m (range 1.0-2.56) | yes, spread 1.42 m |
| `desk.n.01_1` | desk_nbpuns_0 | desk / nbpuns | childs_room_2 | low (0.25-0.6 m), z 0.43 | 2.59 m (range 1.59-3.16) | no (fixed) |
| `bed.n.01_1` | bed_ivdnny_0 | bed / ivdnny | childs_room_2 | low (0.25-0.6 m), z 0.34 | 1.5 m (range 1.13-2.08) | no (fixed) |
| `bookcase.n.01_1` | bookcase_zfpyqe_1 | bookcase / zfpyqe | childs_room_2 | table/counter (0.6-1.1 m), z 0.78 | 1.23 m (range 0.81-3.2) | no (fixed) |
| `bookcase.n.01_2` | bookcase_zfpyqe_0 | bookcase / zfpyqe | childs_room_2 | table/counter (0.6-1.1 m), z 0.78 | 1.8 m (range 1.35-3.51) | no (fixed) |

Initial conditions from `:init`:

```lisp
(inroom bed.n.01_1 childs_room)
(inroom bookcase.n.01_1 childs_room)
(inroom bookcase.n.01_2 childs_room)
(inroom desk.n.01_1 childs_room)
(inroom floor.n.01_1 childs_room)
(ontop agent.n.01_1 floor.n.01_1)
(ontop board_game.n.01_1 desk.n.01_1)
(ontop board_game.n.01_2 bed.n.01_1)
(ontop die.n.01_1 bed.n.01_1)
(ontop die.n.01_2 bed.n.01_1)
(ontop teddy.n.01_1 floor.n.01_1)
(ontop teddy.n.01_2 floor.n.01_1)
(ontop train_set.n.01_1 desk.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching bed.n.01_1 board_game.n.01_2)
(touching bed.n.01_1 die.n.01_1)
(touching bed.n.01_1 die.n.01_2)
(touching board_game.n.01_1 desk.n.01_1)
(touching board_game.n.01_2 bed.n.01_1)
(touching desk.n.01_1 board_game.n.01_1)
(touching desk.n.01_1 train_set.n.01_1)
(touching die.n.01_1 bed.n.01_1)
(touching die.n.01_2 bed.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 teddy.n.01_1)
(touching floor.n.01_1 teddy.n.01_2)
(touching teddy.n.01_1 floor.n.01_1)
(touching teddy.n.01_2 floor.n.01_1)
(touching train_set.n.01_1 desk.n.01_1)
```

## What the human demos did

200 annotated demos. Length 629.83 s (range 420.17-1208.5). Skills per demo 28.0 (range 26-31). 29 distinct skill orders; the most common one covers 36% of demos.

Most common skill counts per demo (69% of demos): move to x11, pick up from x7, place in x6, push to x3, place on x1.

Representative demo `episode_00211780.json` (625.7 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the teddy bear` (3.3-6.3 s)
2. `pick up the teddy bear from the floors` (7.3-32.8 s)
3. `move to the teddy bear` (32.8-35.8 s)
4. `pick up the teddy bear from the floors` (35.8-45.0 s)
5. `move to the bookcase` (45.0-69.6 s)
6. `place the teddy bear in the layer_3 bookcase` (69.6-83.2 s)
7. `place the teddy bear in the layer_3 bookcase` (83.2-92.0 s)
8. `move to the dice` (92.0-107.9 s)
9. `pick up the dice from the bed` (107.9-154.8 s)
10. `pick up the dice from the bed` (154.8-170.4 s)
11. `move to the bookcase` (170.4-183.7 s)
12. `place the dice in the layer_2 bookcase` (183.7-200.6 s)
13. `place the dice in the layer_2 bookcase` (200.6-212.0 s)
14. `move to the board game` (212.0-223.4 s)
15. `push the board game to the to_the_edge_of bed` (223.4-246.3 s)
16. `pick up the board game from the bed` (246.3-259.6 s)
17. `move to the bookcase` (259.6-264.6 s)
18. `place the board game in the layer_2 bookcase` (264.6-279.3 s)
19. `move to the toy train` (279.3-298.9 s)
20. `push the toy train to the to_the_edge_of desk` (298.9-355.3 s)
21. `pick up the toy train from the desk` (355.3-384.4 s)
22. `move to the bookcase` (384.4-405.6 s)
23. `place the toy train in the layer_4 bookcase` (405.6-429.2 s)
24. `move to the board game` (429.2-455.2 s)
25. `push the board game to the to_the_edge_of desk` (455.2-574.5 s)
26. `pick up the board game from the desk` (574.5-596.3 s)
27. `move to the bookcase` (596.3-608.7 s)
28. `place the board game on the board game` (608.7-629.0 s)

Mean duration per skill in this task: hand over 11.4 s, move to 14.7 s, pick up from 26.7 s, place in 18.0 s, place on 20.5 s, place on next to 10.0 s, push to 53.1 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the bookcase` | 997 |
| `move to the board game` | 402 |
| `pick up the teddy bear from the floors` | 400 |
| `place the dice in the layer_2 bookcase` | 400 |
| `pick up the dice from the bed` | 398 |
| `place the teddy bear in the layer_3 bookcase` | 396 |
| `move to the teddy bear` | 373 |
| `move to the dice` | 226 |
| `pick up the toy train from the desk` | 201 |
| `push the board game to the to_the_edge_of bed` | 200 |
| `pick up the board game from the bed` | 200 |
| `move to the toy train` | 200 |
| `pick up the board game from the desk` | 200 |
| `place the toy train in the layer_4 bookcase` | 199 |
| `place the board game in the layer_2 bookcase` | 198 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/21_collecting_childrens_toys.json`. Planner notes: `task_docs/notes/21_collecting_childrens_toys.md`.
