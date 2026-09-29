# 91 · Store Produce

Task name `store_produce`, task index 91.

> Take the mangoes and pomegranates from the basket and put them into the refrigerator.

## At a glance

| item | value |
| --- | --- |
| scene | `restaurant_diner` |
| rooms in the goal | kitchen |
| rooms loaded | kitchen_0 |
| human demo length | 317.4 s mean (9522 steps) |
| episode time limit | 476.1 s (14283 steps at 30 Hz) |
| human base travel | 26.5297 m |
| goal literals (best ground option) | 4 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 2 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://www.youtube.com/embed/jppOziwq7xI |

## Planner notes

**Tier:** C. It is plain pick-and-place, but every fruit is wider than the ~44 mm jaw span: mango 0.119 x 0.100 x 0.088 m, pomegranate 0.080 x 0.080 x 0.089 m (asset bbox, scale 1). A fridge door also has to be opened.

### Goal in plain words

- All four fruits (2 mangoes and 2 pomegranates) must end inside **one** of the two kitchen fridges (`fridge_jtqazu_0` or `fridge_jtqazu_1`, the same model). Either fridge works, but all four must go in the same one.
- The goal has no `not open` literal, so the fridge door may stay open.
- The freezer in the same kitchen is not a valid target.

### Q traps

- There are 4 literals and all score (0/4 true at reset). Each fruit is worth 0.25.
- Q is the max over the 2 fridge options. Fruit split 2+2 across both fridges gives only 0.5. Pick one fridge and stay with it.
- Both fridges start closed (`joint_pos` 0 in all 20 instances), so the door must be opened.
- `inside` needs the fruit's AABB centre in the fridge volume (PREDICATES §3). Fruit left on the open door or in a door bin may not count, because door-bin volumes are unverified. Put the fruit on an interior shelf.
- Closing the door earns nothing. It can push a fruit back out, so skip it.

### Minimal plan

1. `move to the wicker basket`. Done when the basket on the floor is centred and the base has stopped. About 18 s.
2. `pick up the wicker basket from the floors`. Done when the basket is off the floor and in the gripper. About 15 s.
3. `move to the commercial kitchen table`. About 18 s.
4. `pour the mango and mango and pomegranate and pomegranate into the wicker basket`. This is the demo's wording for tipping the basket out onto the table. Done when four fruits are visible on the table top. About 19 s.
5. `place the wicker basket on the floors`. About 25 s. This frees both hands.
6. `move to the fridge`. Done when a fridge door is in front at arm's reach. About 18 s.
7. `open the door of the fridge`. Done when the door is visibly swung open and the shelves can be seen. About 32 s.
8. `move to the commercial kitchen table`. About 18 s.
9. `pick up the mango from the commercial kitchen table`. About 15 s.
10. `pick up the pomegranate from the commercial kitchen table` (other hand). About 15 s.
11. `move to the fridge`. About 18 s.
12. `place the pomegranate in the fridge`. Done when the fruit is resting on a shelf inside. About 6 s.
13. `place the mango in the fridge`. About 6 s.
14. Repeat steps 8-13 for the second mango and pomegranate. The demos use `place the pomegranate in the fridge next to the pomegranate` and `place the mango in the fridge next to the mango` here.

- Totals: about 300 s without the door close, against a 476.1 s limit.

### What the demos do differently

- 197 of 200 demos end with `close the door of the fridge` (about 19 s). The goal does not need it. Leave the door open.
- They pour the basket onto a commercial kitchen table before picking. The goal does not need this either, but it lifts the fruit from floor height (z ~0.08 m in the basket) to table height. It also matches the trained prompts: there is no demo prompt for picking fruit out of the basket.
- They carry two fruits per trip, one per hand.

### Hard parts and hacks

- **Grasp span.** No fruit dimension is under 44 mm. The demos did grasp them, but whether the assisted grasp registers them at eval is unverified. Expect slips, and check that the fingers stopped short of fully closed after each pick.
- **Round fruit rolls.** A poured mango or pomegranate can roll off the table. Re-locate all four before the fridge trips.
- **Unverified hack:** carry the whole basket (0.39 x 0.41 x 0.43 m) into the open fridge with the fruit still inside. The fruit centres would then be in the fridge volume. Whether the basket fits on a shelf, and whether it can be carried that high without tipping the robot, are both unverified.
- The basket and the fruit start anywhere in the kitchen (spread ~7.8 m). The distance to the nearer fridge also varies (1.35-7.5 m). Choose the fridge nearest the table you pour onto.
- ft40k scored Q=0 on instance 311.

### Hints for the VLM

- The scene is a restaurant kitchen. There are two identical tall fridges (model jtqazu, ~0.9 x 1.1 x 2.1 m), which have a glass link per the asset metadata. A separate freezer is a distractor.
- The wicker basket stands on the floor. The fruit inside is roughly 8-12 cm across.
- Done for each literal: the fruit is visible on a fridge shelf behind the door line, and none is left on the table, on the floor or in the basket.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside pomegranate.n.02_1 electric_refrigerator.n.01_2)` | no | yes |
| `(inside pomegranate.n.02_2 electric_refrigerator.n.01_2)` | no | yes |
| `(inside mango.n.02_2 electric_refrigerator.n.01_2)` | no | yes |
| `(inside mango.n.02_1 electric_refrigerator.n.01_2)` | no | yes |

The goal has 2 ground options (4 literals x2); Q takes the best one, so any valid choice of container or partner object counts.

BDDL goal:

```lisp
(:goal 
        (and 
            (exists
                (?electric_refrigerator.n.01 - electric_refrigerator.n.01)
                (and
                    (forall 
                        (?pomegranate.n.02 - pomegranate.n.02)
                        (inside ?pomegranate.n.02 ?electric_refrigerator.n.01) 
                    )
                    (forall 
                        (?mango.n.02 - mango.n.02)
                        (inside ?mango.n.02 ?electric_refrigerator.n.01) 
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
| `mango.n.02_1` | mango_78 | mango / nwwjbw | kitchen_0 | floor, z 0.08 | 4.38 m (range 0.97-6.39) | yes, spread 7.8 m |
| `mango.n.02_2` | mango_77 | mango / nwwjbw | kitchen_0 | floor, z 0.08 | 4.43 m (range 0.86-6.3) | yes, spread 7.64 m |
| `pomegranate.n.02_1` | pomegranate_76 | pomegranate / tldskr | kitchen_0 | floor, z 0.07 | 4.31 m (range 0.87-6.37) | yes, spread 7.86 m |
| `pomegranate.n.02_2` | pomegranate_75 | pomegranate / tldskr | kitchen_0 | floor, z 0.08 | 4.37 m (range 0.96-6.4) | yes, spread 7.89 m |
| `wicker_basket.n.01_1` | wicker_basket_74 | wicker_basket / tsjvyu | kitchen_0 | floor, z 0.19 | 4.37 m (range 0.93-6.36) | yes, spread 7.76 m |
| `floor.n.01_1` | floors_vikfyd_0 | floors / vikfyd | kitchen_0 | floor, z 0.0 | 2.67 m (range 1.56-3.42) | no (fixed) |
| `electric_refrigerator.n.01_1` | fridge_jtqazu_1 | fridge / jtqazu | kitchen_0 | table/counter (0.6-1.1 m), z 1.08 | 3.07 m (range 1.65-7.54) | no (fixed) |
| `electric_refrigerator.n.01_2` | fridge_jtqazu_0 | fridge / jtqazu | kitchen_0 | table/counter (0.6-1.1 m), z 1.08 | 2.21 m (range 1.35-7.06) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "kitchen"
 ],
 "restaurant_diner": {
  "whitelist": {
   "mango.n.02": {
    "mango": {
     "nwwjbw": null
    }
   },
   "pomegranate.n.02": {
    "pomegranate": {
     "tldskr": null
    }
   },
   "wicker_basket.n.01": {
    "wicker_basket": {
     "tsjvyu": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(inroom electric_refrigerator.n.01_1 kitchen)
(inroom electric_refrigerator.n.01_2 kitchen)
(inroom floor.n.01_1 kitchen)
(inside mango.n.02_1 wicker_basket.n.01_1)
(inside mango.n.02_2 wicker_basket.n.01_1)
(inside pomegranate.n.02_1 wicker_basket.n.01_1)
(inside pomegranate.n.02_2 wicker_basket.n.01_1)
(ontop agent.n.01_1 floor.n.01_1)
(ontop wicker_basket.n.01_1 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 wicker_basket.n.01_1)
(touching wicker_basket.n.01_1 floor.n.01_1)
```

## What the human demos did

200 annotated demos. Length 302.55 s (range 211.63-515.1). Skills per demo 20.0 (range 18-22). 10 distinct skill orders; the most common one covers 46% of demos.

Most common skill counts per demo (46% of demos): move to x7, pick up from x5, place in x2, place in next to x2, close door x1, open door x1, place on x1, pour x1.

Representative demo `episode_00911800.json` (294.7 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the wicker basket` (0.0-14.0 s)
2. `pick up the wicker basket from the floors` (14.0-31.0 s)
3. `move to the commercial kitchen table` (31.0-60.0 s)
4. `pour the mango and mango and pomegranate and pomegranate into the wicker basket` (60.0-80.2 s)
5. `place the wicker basket on the floors` (80.2-100.0 s)
6. `move to the fridge` (100.0-119.0 s)
7. `open the door of the fridge` (119.0-157.0 s)
8. `move to the commercial kitchen table` (157.0-164.0 s)
9. `pick up the mango from the commercial kitchen table` (164.0-172.0 s)
10. `pick up the pomegranate from the commercial kitchen table` (172.0-180.0 s)
11. `move to the fridge` (180.0-195.0 s)
12. `place the pomegranate in the fridge` (195.0-202.8 s)
13. `place the mango in the fridge` (202.8-210.0 s)
14. `move to the commercial kitchen table` (210.0-225.0 s)
15. `pick up the mango from the commercial kitchen table` (225.0-231.0 s)
16. `pick up the pomegranate from the commercial kitchen table` (231.0-241.0 s)
17. `move to the fridge` (241.0-254.0 s)
18. `place the pomegranate in the fridge next to the pomegranate` (254.0-262.1 s)
19. `place the mango in the fridge next to the mango` (262.1-267.0 s)
20. `close the door of the fridge` (267.0-294.7 s)

Mean duration per skill in this task: close door 19.1 s, move to 17.5 s, open door 31.8 s, pick up from 14.9 s, place in 6.3 s, place in next to 5.6 s, place on 24.9 s, pour 18.7 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the commercial kitchen table` | 600 |
| `move to the fridge` | 600 |
| `pick up the pomegranate from the commercial kitchen table` | 398 |
| `pick up the mango from the commercial kitchen table` | 397 |
| `place the mango in the fridge` | 291 |
| `place the pomegranate in the fridge` | 287 |
| `pour the mango and mango and pomegranate and pomegranate into the wicker basket` | 200 |
| `open the door of the fridge` | 200 |
| `move to the wicker basket` | 199 |
| `pick up the wicker basket from the floors` | 199 |
| `place the wicker basket on the floors` | 198 |
| `close the door of the fridge` | 197 |
| `place the pomegranate in the fridge next to the pomegranate` | 91 |
| `place the mango in the fridge next to the mango` | 84 |
| `place the pomegranate in the fridge next to the mango` | 11 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/91_store_produce.json`. Planner notes: `task_docs/notes/91_store_produce.md`.
