# 27 · Sorting Household Items

Task name `sorting_household_items`, task index 27.

> From the two baskets on the bedroom floor, take out the items and organize them in the bathroom: place both detergent bottles under the bathroom sink next to each other; put the box of sanitary napkins on the bathroom shelf; set the soap dispenser on the sink; make sure the cup remains on the sink; put both the toothpaste tube and the toothbrush inside the cup.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | bathroom, bedroom |
| rooms loaded | bathroom_0, bathroom_1, bedroom_0, corridor_0, dining_room_0, entryway_0, garden_0 |
| human demo length | 526.9 s mean (15807 steps) |
| episode time limit | 790.4 s (23711 steps at 30 Hz) |
| human base travel | 50.9062 m |
| goal literals (best ground option) | 8 |
| literals already true at start (inferred) | 1 |
| max Q short of full success | 0.875 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.50; ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://player.vimeo.com/video/1114059574 |

## Planner notes

**Tier:** B — six small items move from two floor hampers to a bathroom vanity and shelf, but the bathroom sliding door must be opened first and two placements (`under`, `inside` a coffee cup) are geometrically tight. Item widths vs 44 mm are unknown (no custom list).

### Goal in plain words

Both detergent bottles end up on the floor under the multi-station furniture sink and next to each other. The box of sanitary napkins sits on the bathroom shelf. The soap dispenser sits on the sink. The coffee cup stays on the sink, the toothbrush is inside the cup and the toothpaste tube is next to the cup. There is exactly one ground option: no free choice of furniture. No door or hamper state is checked.

### Q traps

- `ontop cup sink` is true at reset and never scores. Max partial Q is 7/8 = 0.875. Knocking the cup off still blocks full success.
- The cup is the anchor for two literals. Tipping it while inserting the toothbrush can lose `ontop cup sink` (blocks success) and the toothbrush literal.
- `inside toothbrush cup` tests the toothbrush's AABB centre (PREDICATES §3). A long brush leaning out of a small cup may have its centre above the rim. Push it down as far as it goes. Unverified whether the cup is deep enough.
- `nextto toothpaste cup` is a small–small pair: the gap must be about L/6, a few cm (§5). Demos drop the tube into the cup instead. Derived: inside the cup the AABBs overlap (gap 0) and the tube's horizontal rays hit the cup wall, so `nextto` holds.
- `under detergent sink` needs sink geometry directly above each bottle's centre (§9). Push each bottle fully under the basin or counter overhang. Whether the vanity has open space below is unverified.
- `nextto detergent_1 detergent_2`: bottles side by side, nearly touching. Place the second one right against the first.
- `ontop soap_dispenser sink`: keep it clear of the faucet. Any part of the sink above the dispenser's centre fails the literal (§4).
- Closed-loop on 311: zero-shot Q 0.50, fine-tuned 40k Q 0.00.

### Minimal plan

1. `move to the sliding door` — the bedroom–bathroom sliding door (closed at reset per template joint_pos). ~23 s.
2. `open the door of the sliding door` — doorway clear in RGB-D. ~49 s. Nothing requires closing it again.
3. `move to the bottle of detergent` — hamper with bottles in view. ~23 s.
4. `pick up the bottle of detergent from the hamper` (x2, one per hand) — both grippers closed short of full. ~21 s each.
5. `move to the multi station furniture sink`. ~23 s.
6. `place the bottle of detergent under the multi station furniture sink` (x2) — bottles on the floor below the vanity, touching each other. ~18 s each.
7. `move to the soap dispenser`; `pick up the soap dispenser from the hamper`. ~44 s.
8. `move to the box of sanitary napkins`; `pick up the box of sanitary napkins from the hamper`. ~44 s.
9. `move to the multi station furniture sink`. ~23 s.
10. `place the soap dispenser on the multi station furniture sink` — resting on the counter, away from the faucet. ~15 s.
11. `place the box of sanitary napkins on the shelf` — box resting on the bathroom shelf. ~15 s. The shelf is reachable from the sink spot in most demos.
12. `move to the toothbrush`; `pick up the toothbrush from the hamper`. ~44 s.
13. `move to the tube of toothpaste`; `pick up the tube of toothpaste from the hamper`. ~44 s.
14. `move to the coffee cup`. ~23 s.
15. `place the toothbrush in the coffee cup` — brush standing in the cup, cup still upright. ~18 s.
16. `place the tube of toothpaste in the coffee cup` — or, if the cup is full, no trained prompt; closest: `place the tube of toothpaste in the coffee cup`, released touching the cup's side. ~18 s.

Budget: ~515 s demo mean vs a 790 s limit.

### What the demos do differently

- All 200 demos open the sliding door first.
- 193 demos `push the hamper to the away robot` (and 48 `... near robot`) to get a better reach at the items. Not in the goal; use only if an item is out of reach.
- 7 demos pick up and re-place a hamper. Not needed.
- Some demos stand at `the shelf` for the box (12 uses of `move to the shelf`); most place it from the sink position.
- Order is always: detergents, then soap and box, then toothbrush and toothpaste.

### Hard parts and hacks

- Opening a sliding door is slow (49 s mean) and the handle width is unverified.
- Picking items out of a hamper on the floor: low reach, walls of the hamper, items can be stacked.
- Placing a bottle `under` a vanity from standing height: the arm must reach low and far forward.
- The toothbrush-in-cup step is the most likely to fail and can knock the cup off the counter. Do it last so earlier literals are safe.
- If the cup falls, `ontop cup sink` fails and success is lost, but partial Q keeps the other literals.

### Hints for the VLM

- Items start in two hampers on the bedroom_0 floor. Hamper 1 holds both detergents and the napkin box; hamper 2 holds soap, toothbrush and toothpaste.
- The bathroom is bathroom_1, behind sliding door `sliding_door_tprpvb_10` from bedroom_0. The house has many identical sliding doors; the right one leads from the bedroom into the room with the sink, toilet and bathtub.
- bathroom_1 has one multi-station furniture sink (the vanity), one shelf (z ~1.05 m, next to the sink), one coffee cup (z ~0.79 m, on the sink counter).
- Done: two bottles side by side on the floor below the vanity, box on the shelf, dispenser on the counter, brush sticking out of the upright cup, tube in or touching the cup.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(under bottle__of__detergent.n.01_2 sink.n.01_1)` | no | yes |
| `(under bottle__of__detergent.n.01_1 sink.n.01_1)` | no | yes |
| `(nextto bottle__of__detergent.n.01_1 bottle__of__detergent.n.01_2)` | no | yes |
| `(ontop box__of__sanitary_napkin.n.01_1 shelf.n.01_1)` | no | yes |
| `(ontop soap_dispenser.n.01_1 sink.n.01_1)` | no | yes |
| `(ontop cup.n.01_1 sink.n.01_1)` | yes | never (already true) |
| `(nextto tube__of__toothpaste.n.01_1 cup.n.01_1)` | no | yes |
| `(inside toothbrush.n.01_1 cup.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (forall 
                (?bottle__of__detergent.n.01 - bottle__of__detergent.n.01)
                (under ?bottle__of__detergent.n.01 ?sink.n.01_1)
            )
            (nextto ?bottle__of__detergent.n.01_1 ?bottle__of__detergent.n.01_2)
            (ontop ?box__of__sanitary_napkin.n.01_1 ?shelf.n.01_1)
            (ontop ?soap_dispenser.n.01_1 ?sink.n.01_1)
            (ontop cup.n.01_1 sink.n.01_1)
            (nextto ?tube__of__toothpaste.n.01_1 cup.n.01_1)
            (inside ?toothbrush.n.01_1 cup.n.01_1)
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `bottle__of__detergent.n.01_1` | bottle_of_detergent_228 | bottle_of_detergent / qjkmhq | bedroom_0 | floor, z 0.13 | 2.14 m (range 0.88-3.23) | yes, spread 3.75 m |
| `bottle__of__detergent.n.01_2` | bottle_of_detergent_227 | bottle_of_detergent / gkpmii | bedroom_0 | floor, z 0.13 | 2.2 m (range 0.89-3.34) | yes, spread 3.58 m |
| `basket.n.01_1` | hamper_226 | hamper / drgdfh | bedroom_0 | floor, z 0.07 | 2.16 m (range 0.88-3.22) | yes, spread 3.56 m |
| `basket.n.01_2` | hamper_225 | hamper / drgdfh | bedroom_0 | floor, z 0.07 | 2.48 m (range 0.98-3.34) | yes, spread 4.92 m |
| `floor.n.01_1` | floors_htolat_0 | floors / htolat | bedroom_0 | floor, z -0.14 | 1.25 m (range 0.75-2.39) | no (fixed) |
| `box__of__sanitary_napkin.n.01_1` | box_of_sanitary_napkins_224 | box_of_sanitary_napkins / zqinib | bedroom_0 | floor, z 0.06 | 2.12 m (range 0.77-3.31) | yes, spread 3.7 m |
| `soap_dispenser.n.01_1` | soap_dispenser_223 | soap_dispenser / jmulpc | bedroom_0 | floor, z 0.07 | 2.53 m (range 0.97-3.26) | yes, spread 4.96 m |
| `tube__of__toothpaste.n.01_1` | tube_of_toothpaste_222 | tube_of_toothpaste / vsclsj | bedroom_0 | floor, z 0.02 | 2.54 m (range 1.0-3.53) | yes, spread 4.84 m |
| `toothbrush.n.01_1` | toothbrush_221 | toothbrush / vkrjps | bedroom_0 | floor, z 0.02 | 2.46 m (range 0.98-3.23) | yes, spread 4.81 m |
| `cup.n.01_1` | coffee_cup_220 | coffee_cup / ykuftq | bathroom_1 | table/counter (0.6-1.1 m), z 0.79 | 3.72 m (range 2.42-5.61) | yes, spread 1.01 m |
| `shelf.n.01_1` | shelf_fjozhc_0 | shelf / fjozhc | bathroom_1 | table/counter (0.6-1.1 m), z 1.05 | 3.59 m (range 2.72-5.52) | no (fixed) |
| `sink.n.01_1` | multi_station_furniture_sink_upwldu_0 | multi_station_furniture_sink / upwldu | bathroom_1 | low (0.25-0.6 m), z 0.59 | 3.77 m (range 2.55-5.49) | no (fixed) |

Initial conditions from `:init`:

```lisp
(inroom floor.n.01_1 bedroom)
(inroom shelf.n.01_1 bathroom)
(inroom sink.n.01_1 bathroom)
(inside bottle__of__detergent.n.01_1 basket.n.01_1)
(inside bottle__of__detergent.n.01_2 basket.n.01_1)
(inside box__of__sanitary_napkin.n.01_1 basket.n.01_1)
(inside soap_dispenser.n.01_1 basket.n.01_2)
(inside toothbrush.n.01_1 basket.n.01_2)
(inside tube__of__toothpaste.n.01_1 basket.n.01_2)
(ontop agent.n.01_1 floor.n.01_1)
(ontop basket.n.01_1 floor.n.01_1)
(ontop basket.n.01_2 floor.n.01_1)
(ontop cup.n.01_1 sink.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching basket.n.01_1 floor.n.01_1)
(touching basket.n.01_2 floor.n.01_1)
(touching cup.n.01_1 sink.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 basket.n.01_1)
(touching floor.n.01_1 basket.n.01_2)
(touching sink.n.01_1 cup.n.01_1)
```

## What the human demos did

200 annotated demos. Length 515.43 s (range 375.0-1036.13). Skills per demo 24.0 (range 20-29). 86 distinct skill orders; the most common one covers 10% of demos.

Most common skill counts per demo (13% of demos): move to x10, pick up from x6, place in x2, place on x2, place under x2, open door x1, push to x1.

Representative demo `episode_00270260.json` (508.9 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the sliding door` (0.0-23.4 s)
2. `open the door of the sliding door` (23.4-76.3 s)
3. `move to the bottle of detergent` (76.3-90.9 s)
4. `pick up the bottle of detergent from the hamper` (90.9-114.1 s)
5. `move to the bottle of detergent` (114.1-120.1 s)
6. `pick up the bottle of detergent from the hamper` (120.1-132.6 s)
7. `move to the multi station furniture sink` (132.6-155.2 s)
8. `place the bottle of detergent under the multi station furniture sink` (155.2-169.7 s)
9. `place the bottle of detergent under the multi station furniture sink` (169.7-181.2 s)
10. `move to the box of sanitary napkins` (181.2-208.9 s)
11. `pick up the box of sanitary napkins from the hamper` (208.9-234.8 s)
12. `move to the soap dispenser` (234.8-245.0 s)
13. `pick up the soap dispenser from the hamper` (245.0-264.6 s)
14. `move to the shelf` (264.6-286.4 s)
15. `place the box of sanitary napkins on the shelf` (286.4-306.6 s)
16. `place the soap dispenser on the multi station furniture sink` (306.6-319.3 s)
17. `move to the tube of toothpaste` (319.3-356.8 s)
18. `pick up the tube of toothpaste from the hamper` (356.8-376.3 s)
19. `move to the toothbrush` (376.3-387.0 s)
20. `pick up the toothbrush from the hamper` (387.0-417.5 s)
21. `move to the coffee cup` (417.5-440.2 s)
22. `place the toothbrush in the coffee cup` (440.3-479.0 s)
23. `place the tube of toothpaste in the coffee cup` (479.0-508.9 s)

Mean duration per skill in this task: move to 23.3 s, open door 48.8 s, pick up from 20.5 s, place in 17.9 s, place on 15.1 s, place under 17.7 s, push to 21.1 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `pick up the bottle of detergent from the hamper` | 400 |
| `place the bottle of detergent under the multi station furniture sink` | 400 |
| `move to the multi station furniture sink` | 389 |
| `move to the bottle of detergent` | 280 |
| `move to the coffee cup` | 201 |
| `move to the sliding door` | 200 |
| `open the door of the sliding door` | 200 |
| `pick up the soap dispenser from the hamper` | 200 |
| `pick up the box of sanitary napkins from the hamper` | 200 |
| `place the soap dispenser on the multi station furniture sink` | 200 |
| `place the box of sanitary napkins on the shelf` | 200 |
| `pick up the tube of toothpaste from the hamper` | 200 |
| `place the toothbrush in the coffee cup` | 200 |
| `place the tube of toothpaste in the coffee cup` | 200 |
| `pick up the toothbrush from the hamper` | 199 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/27_sorting_household_items.json`. Planner notes: `task_docs/notes/27_sorting_household_items.md`.
