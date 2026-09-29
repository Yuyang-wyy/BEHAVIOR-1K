# 10 · Set Up A Coffee Station In Your Kitchen

Task name `set_up_a_coffee_station_in_your_kitchen`, task index 10.

> Set up a coffee station on the kitchen countertop: keep the coffee maker on the countertop, move the bottle of coffee from the kitchen shelf to the counter next to the coffee maker, place a paper coffee filter on top of the coffee maker, put the saucer next to the coffee maker with the coffee cup on the saucer, and place the electric kettle next to the coffee maker.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | kitchen |
| rooms loaded | corridor_0, dining_room_0, entryway_0, garden_0, kitchen_0, living_room_0, living_room_1 |
| human demo length | 208.9 s mean (6266 steps) |
| episode time limit | 313.3 s (9399 steps at 30 Hz) |
| human base travel | 17.3596 m |
| goal literals (best ground option) | 6 |
| literals already true at start (inferred) | 1 |
| max Q short of full success | 0.833 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.00; ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://player.vimeo.com/video/1114056931 |

## Planner notes

**Tier:** B — five small pick-and-place moves around a fixed coffee maker; the high shelf bottle and tight `nextto` gaps are the hard parts.

### Goal in plain words

The coffee maker stays on the countertop. The bottle of coffee, the saucer and the electric kettle each end next to the coffee maker. The coffee cup ends on the saucer. The paper coffee filter ends on top of the coffee maker. Sides (left/right/front) are free, and `nextto` does not require the countertop. Do not knock the coffee maker off the counter.

### Q traps

- `ontop coffee_maker countertop` is true at reset: it never scores but must stay true. Max partial Q is 5/6 = 0.833.
- The page's "true at start" column is incomplete. The five movable items spawn at random along the counter. An AABB estimate from the 20 instance poses (asset bboxes, `nextto` gap limit ~0.08-0.12 m) says:
  - kettle already within the gap in 303, 305, 309, 315, 316 (and near in 313, 320);
  - saucer already within the gap in 311 and 315.
  - The ray half of `nextto` is unverified, so treat these as "probably true at reset, will not score". If so, leave the item where it is: moving it earns nothing and risks losing success.
- `ontop paper_coffee_filter coffee_maker` fails if any part of the coffee maker is directly above the filter's centre (PREDICATES §4). The demos say `place the paper coffee filter in the coffee maker`; if that slot sits under a lid or hood of the maker, the literal is False. Maker geometry is unverified; resting the filter on the maker's topmost surface is the safe choice.
- The coffee maker asset has no fillable meta link, so "in" is not a checked relation anyway; only `ontop` counts.
- Cup on saucer: the cup must touch the saucer and its centre must be over the saucer (14.4 cm disc). Place the saucer first, cup last, or the cup rides along and may slide off.
- Gap limits are tight (derived, §5): saucer ~7.4 cm, bottle ~7.5 cm, kettle ~9.4 cm from the maker's AABB. "Next to" means almost touching.
- Saucer is 11 mm tall: its horizontal rays sit ~5 mm above the counter and must hit the maker's base. Unverified that the base is solid there.

### Minimal plan

1. `move to the paper coffee filter` ~9 s; `pick up the paper coffee filter from the countertop` ~15 s — filter off the counter.
2. `move to the coffee maker` ~9 s; `place the paper coffee filter in the coffee maker` ~19 s — filter visible on the maker's top, no maker part above it.
3. `move to the bottle of coffee`; `pick up the bottle of coffee from the shelf` ~15 s — bottle lifted off the wall shelf at ~1.6 m.
4. `move to the coffee maker`; `place the bottle of coffee on the countertop next to the left coffee maker` ~12 s — bottle upright, gap to maker a few cm.
5. Skip if the saucer already touches the maker. `move to the saucer`; `pick up the saucer from the countertop`; `move to the coffee maker`; `place the saucer on the countertop next to the right coffee maker` ~12 s.
6. Skip if the kettle already touches the maker. `move to the electric kettle`; `pick up the electric kettle from the countertop`; `move to the coffee maker`; `place the electric kettle on the countertop next to the right coffee maker` ~12 s. Use the side the saucer did not take.
7. `move to the coffee cup`; `pick up the coffee cup from the countertop`; `move to the saucer`; `place the coffee cup on the saucer` ~12 s — cup resting centred on the saucer.
- Total ~170 s against a 313 s limit (demo mean 209 s).

### What the demos do differently

- Order varies a lot (84 distinct orders, the modal one 11%); the modal one is the order above.
- Humans always carry the saucer and kettle, even when they start next to the maker (175/200 demos pick up each). Skipping these is safe only if the item already touches the maker.
- A few demos push the saucer along the counter (`push the saucer to the to_the_edge_of countertop`, 7); not needed.
- Left/right choice is split; any side works for the goal.

### Hard parts and hacks

- Bottle of coffee: 0.078 x 0.078 x 0.168 m after scale 0.62, so its body exceeds the 44 mm span; the cap or neck may be narrower (unverified). It sits on wall shelf `shelf_pfusrd_1` at ~1.6 m; reaching needs the trunk raised, and tipping risk grows with the arm extended high.
- Coffee maker is 0.30 x 0.30 x 0.43 m, top at ~1.3 m. In instances 301, 305, 309, 313 it stands almost directly under the bottle's shelf, so the filter placement has little headroom.
- Filter 0.14 x 0.13 x 0.10 m; grasp the paper rim. Cup 0.10 x 0.09 x 0.07 m; use the handle. Saucer 0.144 m disc, 11 mm thick; grasp the rim edge. Kettle 0.23 x 0.17 x 0.27 m; use the handle.
- Pushing the saucer or kettle the last few cm against the maker (`push the saucer to the to_the_edge_of coffee maker`, 1 demo) is a cheap way to close the gap.
- A bump can shove the maker toward the counter edge; `ontop` then fails if it falls.

### Hints for the VLM

- All items are on the kitchen_0 countertop except the bottle, which is on the wall shelf above it. The kitchen has two countertops and two wall shelves; the items are on `countertop_kelzer_0`.
- Coffee maker: the only one, ~43 cm tall box. Kettle: the only kettle. The water glass in the kitchen is a distractor for the cup.
- Done for each `nextto`: the item stands on the counter with no visible gap (a few cm at most) beside the maker.
- Done for the filter: it rests on the maker's top, visible from the side, not hidden inside.
- Done for the cup: cup centred on the saucer, and the saucer next to the maker.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(ontop coffee_maker.n.01_1 countertop.n.01_1)` | yes | never (already true) |
| `(nextto bottle__of__coffee.n.01_1 coffee_maker.n.01_1)` | no | yes |
| `(ontop paper_coffee_filter.n.01_1 coffee_maker.n.01_1)` | no | yes |
| `(nextto saucer.n.02_1 coffee_maker.n.01_1)` | no | yes |
| `(ontop coffee_cup.n.01_1 saucer.n.02_1)` | no | yes |
| `(nextto electric_kettle.n.01_1 coffee_maker.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (ontop ?coffee_maker.n.01_1 ?countertop.n.01_1) 
            (nextto ?bottle__of__coffee.n.01_1 ?coffee_maker.n.01_1) 
            (ontop ?paper_coffee_filter.n.01_1 ?coffee_maker.n.01_1) 
            (nextto ?saucer.n.02_1 ?coffee_maker.n.01_1) 
            (ontop ?coffee_cup.n.01_1 ?saucer.n.02_1) 
            (nextto ?electric_kettle.n.01_1 ?coffee_maker.n.01_1)
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `coffee_maker.n.01_1` | coffee_maker_212 | coffee_maker / fwlabx | kitchen_0 | table/counter (0.6-1.1 m), z 1.08 | 3.21 m (range 0.91-3.82) | yes, spread 2.08 m |
| `countertop.n.01_1` | countertop_kelzer_0 | countertop / kelzer | kitchen_0 | table/counter (0.6-1.1 m), z 0.87 | 3.21 m (range 1.14-3.65) | no (fixed) |
| `bottle__of__coffee.n.01_1` | bottle_of_coffee_211 | bottle_of_coffee / zywanc | kitchen_0 | very high (>1.6 m), z 1.61 | 3.56 m (range 1.18-4.1) | yes, spread 0.67 m |
| `shelf.n.01_1` | shelf_pfusrd_1 | shelf / pfusrd | kitchen_0 | high (1.1-1.6 m), z 1.5 | 3.69 m (range 1.14-4.13) | no (fixed) |
| `paper_coffee_filter.n.01_1` | paper_coffee_filter_210 | paper_coffee_filter / kizndy | kitchen_0 | table/counter (0.6-1.1 m), z 0.92 | 3.12 m (range 0.75-4.39) | yes, spread 2.74 m |
| `coffee_cup.n.01_1` | coffee_cup_209 | coffee_cup / nbhcgu | kitchen_0 | table/counter (0.6-1.1 m), z 0.92 | 3.17 m (range 1.16-4.2) | yes, spread 2.93 m |
| `dishwasher.n.01_1` | dishwasher_ynrhuk_0 | dishwasher / ynrhuk | kitchen_0 | low (0.25-0.6 m), z 0.41 | 3.68 m (range 1.11-4.11) | no (fixed) |
| `saucer.n.02_1` | saucer_208 | saucer / vghfkh | kitchen_0 | table/counter (0.6-1.1 m), z 0.89 | 3.14 m (range 0.91-4.16) | yes, spread 2.73 m |
| `electric_kettle.n.01_1` | electric_kettle_207 | electric_kettle / hkdsla | kitchen_0 | table/counter (0.6-1.1 m), z 0.96 | 3.15 m (range 1.06-3.89) | yes, spread 2.48 m |
| `floor.n.01_1` | floors_kxcpgy_0 | floors / kxcpgy | kitchen_0 | floor, z -0.14 | 2.0 m (range 0.73-2.38) | no (fixed) |

Initial conditions from `:init`:

```lisp
(inroom countertop.n.01_1 kitchen)
(inroom dishwasher.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(inroom shelf.n.01_1 kitchen)
(ontop agent.n.01_1 floor.n.01_1)
(ontop bottle__of__coffee.n.01_1 shelf.n.01_1)
(ontop coffee_cup.n.01_1 countertop.n.01_1)
(ontop coffee_maker.n.01_1 countertop.n.01_1)
(ontop electric_kettle.n.01_1 countertop.n.01_1)
(ontop paper_coffee_filter.n.01_1 countertop.n.01_1)
(ontop saucer.n.02_1 countertop.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching bottle__of__coffee.n.01_1 shelf.n.01_1)
(touching coffee_cup.n.01_1 countertop.n.01_1)
(touching coffee_maker.n.01_1 countertop.n.01_1)
(touching countertop.n.01_1 coffee_cup.n.01_1)
(touching countertop.n.01_1 coffee_maker.n.01_1)
(touching countertop.n.01_1 electric_kettle.n.01_1)
(touching countertop.n.01_1 paper_coffee_filter.n.01_1)
(touching countertop.n.01_1 saucer.n.02_1)
(touching electric_kettle.n.01_1 countertop.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching paper_coffee_filter.n.01_1 countertop.n.01_1)
(touching saucer.n.02_1 countertop.n.01_1)
(touching shelf.n.01_1 bottle__of__coffee.n.01_1)
```

## What the human demos did

200 annotated demos. Length 202.08 s (range 91.3-344.5). Skills per demo 18.0 (range 10-21). 84 distinct skill orders; the most common one covers 11% of demos.

Most common skill counts per demo (24% of demos): move to x9, pick up from x5, place on next to x3, place in x1, place on x1.

Representative demo `episode_00102110.json` (234.2 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the paper coffee filter` (0.0-22.6 s)
2. `pick up the paper coffee filter from the countertop` (22.6-40.4 s)
3. `move to the coffee maker` (40.4-52.4 s)
4. `place the paper coffee filter in the coffee maker` (52.4-70.0 s)
5. `move to the bottle of coffee` (70.0-74.0 s)
6. `pick up the bottle of coffee from the shelf` (74.0-90.1 s)
7. `move to the coffee maker` (90.1-91.6 s)
8. `place the bottle of coffee on the countertop next to the right coffee maker` (91.6-100.2 s)
9. `move to the saucer` (100.2-117.1 s)
10. `pick up the saucer from the countertop` (117.1-134.7 s)
11. `move to the coffee maker` (134.7-144.5 s)
12. `place the saucer on the countertop next to the left coffee maker` (144.5-154.7 s)
13. `move to the electric kettle` (154.7-171.0 s)
14. `pick up the electric kettle from the countertop` (171.0-186.3 s)
15. `move to the coffee maker` (186.3-193.2 s)
16. `place the electric kettle on the countertop next to the right coffee maker` (193.2-204.4 s)
17. `move to the coffee cup` (204.4-210.4 s)
18. `pick up the coffee cup from the countertop` (210.4-224.0 s)
19. `move to the saucer` (224.0-225.4 s)
20. `place the coffee cup on the saucer` (225.4-234.2 s)

Mean duration per skill in this task: move to 9.4 s, pick up from 14.8 s, place in 18.6 s, place on 12.1 s, place on next to 11.5 s, push to 22.6 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the coffee maker` | 545 |
| `move to the saucer` | 329 |
| `pick up the coffee cup from the countertop` | 200 |
| `place the coffee cup on the saucer` | 200 |
| `pick up the paper coffee filter from the countertop` | 200 |
| `place the paper coffee filter in the coffee maker` | 200 |
| `move to the paper coffee filter` | 199 |
| `pick up the bottle of coffee from the shelf` | 199 |
| `pick up the electric kettle from the countertop` | 175 |
| `pick up the saucer from the countertop` | 175 |
| `move to the coffee cup` | 173 |
| `move to the bottle of coffee` | 172 |
| `move to the electric kettle` | 164 |
| `place the bottle of coffee on the countertop next to the left coffee maker` | 151 |
| `place the electric kettle on the countertop next to the right coffee maker` | 143 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/10_set_up_a_coffee_station_in_your_kitchen.json`. Planner notes: `task_docs/notes/10_set_up_a_coffee_station_in_your_kitchen.md`.
