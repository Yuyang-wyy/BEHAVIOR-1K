# 42 · Chop an Onion

Task name `chop_an_onion`, task index 42.

> In the kitchen, take the Vidalia onion out of the sink, dice it on the chopping board with the paring knife, put the diced onion into the bowl on the countertop, then place both the paring knife and the chopping board into the sink.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | kitchen |
| rooms loaded | corridor_0, garden_0, kitchen_0, living_room_0 |
| human demo length | 213.3 s mean (6399 steps) |
| episode time limit | 320.0 s (9599 steps at 30 Hz) |
| human base travel | 16.9982 m |
| goal literals (best ground option) | 4 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.50; ft40k@local Q=0.50 |
| demo video | https://player.vimeo.com/video/1114061062 |

## Planner notes

**Tier:** D — one slice-then-dice transition plus a particle transfer into a bowl and two place-in-sink moves.

### Goal in plain words

The onion must be diced: `diced__vidalia_onion` must exist. At least one diced particle must sit inside the bowl `bowl_73`. The paring knife `parer_74` and the cutting board `cutting_board_76` must both end with their AABB centres inside the drop-in sink `drop_in_sink_lkklqs_0`. **Tool:** the parer, the only slicer. The board is just a surface; the goal does not care where the cut happens.

### Q traps

- Four literals, all false at start, so max Q is 1.0.
- `real diced__vidalia_onion` needs two contacts: first the whole onion (becomes halves), then, after the 2 s re-arm, one half (§7). Dicing one half is enough; the second half is optional.
- `contains bowl diced` needs just **1 particle** in the bowl's volume (§13). A pour that drops even a few pieces in scores.
- **Sink drain.** The sink's `particleSink` is set to `default_non_fluid_conditions: []` (KB), which means it always removes physical particles, diced onion included, that reach its drain volume. Do not dice over the drain if you still need the pieces for the bowl. Losing particles probably does not undo `real`: the slot empties only on `system.clear()` (`behavior_task.py:672`). Whether the system clears when the count hits zero is not verified.
- Put the knife and the board in the sink **after** the pour. A board already in the sink cannot be used to pour.
- `inside` tests only the AABB centre (§3). A board leaning on the rim with its centre above the basin does not count.

### Minimal plan

1. `move to the cutting board`, then `pick up the cutting board from the bar`, then `place the cutting board on the bar next to the left drop in sink` — board beside the sink. ~5 s + ~19 s + ~14 s. This step is optional when the board already lies near the sink.
2. `move to the vidalia onion`, then `pick up the vidalia onion from the drop in sink` — onion lifted out of the basin. ~5 s + ~19 s.
3. `move to the cutting board`, then `place the vidalia onion on the cutting board` — ~5 s + ~13 s.
4. `pick up the parer from the bar` — ~19 s.
5. `chop the parer with the vidalia onion` — two halves visible. Lift the knife and hold it clear for more than 2 s. ~6 s.
6. `chop the parer with the half vidalia onion 75` — the half turns into small pieces. ~6 s. Skip the second half.
7. `place the parer in the drop in sink` — knife out of hand, in the basin. ~12 s. **This scores 0.25.**
8. `pick up the cutting board from the bar`, `move to the bowl`, then `pour the diced  vidalia onion into the cutting board` (sic, double space; it means pour from the board into the bowl) — pieces visible in the bowl. ~19 s + ~5 s + ~11 s.
9. `move to the drop in sink`, then `place the cutting board in the drop in sink` — board lying in the basin. ~5 s + ~12 s.

The plan takes about 210 s against a 320 s limit.

Grasp-free partial route (derived, untested; worth 0.75 at most):
- Chop the onion **where it lies in the sink**: `chop the parer with the vidalia onion`, then a half.
- Drop the parer in the sink.
- Push the board off the bar edge into the adjacent basin. No trained prompt; closest: `push the cutting board to the to_the_edge_of countertop` (seen in cook_cabbage).
- The bowl literal is lost.

### What the demos do differently

- They dice **both** halves (only one is needed).
- 173 of 200 demos first move the board next to the sink, and about 64 also move the bowl next to the board. These moves just shorten the reach for the pour and the final place.
- They hold the knife until both halves are diced, then drop it in the sink before picking up the board.

### Hard parts and hacks

- **Onion size.** The onion is 100 x 70 x 71 mm and its halves are about 97 x 68 x 41 mm. Neither fits the 44 mm span by bbox. The ft40k checkpoint still scored 0.5 on instance 311 (which two literals is not recorded). Chopping it in the sink avoids the onion grasp entirely.
- **Parer.** `lwpdhi` is 268 x 31 x 14 mm and fits the jaws.
- **Board.** It is 300 x 200 x 20 mm and lies flat, so its 20 mm edge is reachable only if it overhangs the bar edge. The pour needs a real grasp and a tilt.
- **Bowl.** `aspeds` is 225 mm across and 75 mm deep, a shallow target for the pour. Tilt slowly at close range.

### Hints for the VLM

- Kitchen of `house_double_floor_lower`. `bar_egwapq_0` is the counter along the x ≈ 8.2 wall. It has the drop-in sink at y ≈ 0.23 and top cabinets above.
- The onion starts **in the sink basin** (z 0.81), not on the counter. The board, parer and bowl are on the same bar, and their positions vary by up to about 2 m between instances.
- There is only one sink, one bowl, one knife and one board in the kitchen.
- Done: pieces in the bowl, knife and board lying in the sink. The episode ends by itself on success.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(real diced__vidalia_onion.n.01_1)` | no | yes |
| `(inside parer.n.02_1 sink.n.01_1)` | no | yes |
| `(inside chopping_board.n.01_1 sink.n.01_1)` | no | yes |
| `(contains bowl.n.01_1 diced__vidalia_onion.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (real ?diced__vidalia_onion.n.01_1)
            (inside ?parer.n.02_1 ?sink.n.01_1)
            (inside ?chopping_board.n.01_1 ?sink.n.01_1)
            (contains ?bowl.n.01_1 ?diced__vidalia_onion.n.01_1)
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `chopping_board.n.01_1` | cutting_board_76 | cutting_board / aibvew | kitchen_0 | table/counter (0.6-1.1 m), z 0.9 | 1.97 m (range 1.06-6.7) | yes, spread 2.09 m |
| `sink.n.01_1` | drop_in_sink_lkklqs_0 | drop_in_sink / lkklqs | kitchen_0 | table/counter (0.6-1.1 m), z 0.86 | 2.5 m (range 1.37-6.51) | no (fixed) |
| `vidalia_onion.n.01_1` | vidalia_onion_75 | vidalia_onion / buyxll | kitchen_0 | table/counter (0.6-1.1 m), z 0.81 | 2.41 m (range 1.26-6.43) | yes, spread 0.41 m |
| `diced__vidalia_onion.n.01_1` | particle system | diced__vidalia_onion | - | - | - | - |
| `parer.n.02_1` | parer_74 | parer / lwpdhi | kitchen_0 | table/counter (0.6-1.1 m), z 0.89 | 2.6 m (range 1.1-6.91) | yes, spread 2.11 m |
| `countertop.n.01_1` | bar_egwapq_0 | bar / egwapq | kitchen_0 | low (0.25-0.6 m), z 0.45 | 2.58 m (range 1.43-6.58) | no (fixed) |
| `bowl.n.01_1` | bowl_73 | bowl / aspeds | kitchen_0 | table/counter (0.6-1.1 m), z 0.93 | 2.6 m (range 1.26-6.18) | yes, spread 2.1 m |
| `floor.n.01_1` | floors_zqjkvm_0 | floors / zqjkvm | kitchen_0 | floor, z -0.15 | 2.04 m (range 0.83-3.22) | no (fixed) |

Initial conditions from `:init`:

```lisp
(future diced__vidalia_onion.n.01_1)
(inroom countertop.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(inroom sink.n.01_1 kitchen)
(inside vidalia_onion.n.01_1 sink.n.01_1)
(ontop agent.n.01_1 floor.n.01_1)
(ontop bowl.n.01_1 countertop.n.01_1)
(ontop chopping_board.n.01_1 countertop.n.01_1)
(ontop parer.n.02_1 countertop.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching bowl.n.01_1 countertop.n.01_1)
(touching chopping_board.n.01_1 countertop.n.01_1)
(touching countertop.n.01_1 bowl.n.01_1)
(touching countertop.n.01_1 chopping_board.n.01_1)
(touching countertop.n.01_1 parer.n.02_1)
(touching floor.n.01_1 agent.n.01_1)
(touching parer.n.02_1 countertop.n.01_1)
```

## What the human demos did

200 annotated demos. Length 206.35 s (range 123.57-394.2). Skills per demo 19.5 (range 14-28). 158 distinct skill orders; the most common one covers 3% of demos.

Most common skill counts per demo (16% of demos): move to x6, pick up from x4, chop x3, place in x2, place on x1, place on next to x1, pour x1.

Representative demo `episode_00420160.json` (201.9 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the cutting board` (1.4-16.7 s)
2. `pick up the cutting board from the bar` (16.7-43.5 s)
3. `place the cutting board on the bar next to the left drop in sink` (43.5-64.7 s)
4. `move to the vidalia onion` (64.7-67.7 s)
5. `pick up the vidalia onion from the drop in sink` (67.7-84.3 s)
6. `move to the cutting board` (84.3-86.1 s)
7. `place the vidalia onion on the cutting board` (86.1-104.4 s)
8. `pick up the parer from the bar` (104.4-132.1 s)
9. `move to the vidalia onion` (132.1-139.6 s)
10. `chop the parer with the vidalia onion` (139.6-148.2 s)
11. `chop the parer with the half vidalia onion 75` (148.2-149.1 s)
12. `chop the parer with the half vidalia onion 75` (149.1-152.4 s)
13. `place the parer in the drop in sink` (152.4-157.3 s)
14. `pick up the cutting board from the bar` (157.3-171.9 s)
15. `move to the bowl` (171.9-175.8 s)
16. `pour the diced  vidalia onion into the cutting board` (175.8-183.3 s)
17. `move to the drop in sink` (183.3-185.4 s)
18. `place the cutting board in the drop in sink` (185.4-203.3 s)

Mean duration per skill in this task: chop 6.1 s, move to 5.4 s, pick up from 18.8 s, place in 11.6 s, place on 12.8 s, place on next to 14.1 s, pour 11.0 s, push to 22.8 s, turn to 25.3 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the cutting board` | 531 |
| `pick up the cutting board from the bar` | 389 |
| `chop the parer with the half vidalia onion 75` | 376 |
| `move to the vidalia onion` | 282 |
| `move to the drop in sink` | 242 |
| `pick up the parer from the bar` | 205 |
| `place the parer in the drop in sink` | 202 |
| `pick up the vidalia onion from the drop in sink` | 200 |
| `place the vidalia onion on the cutting board` | 200 |
| `chop the parer with the vidalia onion` | 200 |
| `pour the diced  vidalia onion into the cutting board` | 200 |
| `move to the bowl` | 199 |
| `place the cutting board in the drop in sink` | 198 |
| `place the cutting board on the bar next to the left drop in sink` | 173 |
| `move to the parer` | 169 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/42_chop_an_onion.json`. Planner notes: `task_docs/notes/42_chop_an_onion.md`.
