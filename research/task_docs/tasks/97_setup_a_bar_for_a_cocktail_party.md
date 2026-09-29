# 97 · Setup A Bar For A Cocktail Party

Task name `setup_a_bar_for_a_cocktail_party`, task index 97.

> Set up the bar for a cocktail party by placing the wineglasses, wine bottle, corkscrew, soda cans, and ice bucket on the bar.

## At a glance

| item | value |
| --- | --- |
| scene | `restaurant_diner` |
| rooms in the goal | bar |
| rooms loaded | bar_0, corridor_0, kitchen_0, dining_room_0 |
| human demo length | 447.3 s mean (13418 steps) |
| episode time limit | 670.9 s (20128 steps at 30 Hz) |
| human base travel | 22.8071 m |
| goal literals (best ground option) | 20 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 54 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.50; ft40k@local Q=0.50 |
| demo video | https://www.youtube.com/embed/3V0ySKyGKRw |

## Planner notes

**Tier:** C. It moves 12 objects from the bottom cabinet to the bar and has 20 literals, including exact `nextto` pairings and a tray-to-bucket pour. Cans (0.081 m) and wineglasses (0.117 m bowls) are wider than the 44 mm jaws, so the grasp is unverified. Partial Q is easy to collect, though: ft40k already got 0.50 on instance 311.

### Goal in plain words

- **On the bar** (`bar_xxftww_0`): the wine bottle, all 3 soda cans, both wineglasses, the corkscrew, and the ice bucket.
- **Pairings:**
  - every can is next to some other can;
  - wineglass 1 is next to wineglass 2;
  - at least one wineglass is next to the bottle;
  - the corkscrew is next to the bottle.
- **All 6 ice cubes inside the ice bucket.**
- The tray and the fridge are not in the goal. The tray may stay on the cabinet.

### Q traps

- There are 20 literals and all score (0/20 true at reset). Q is the max over 54 ground options.
- Many ground options pair a can with itself (`nextto can_1 can_1`). Those literals can never be true, because a can is never in its own adjacency list (PREDICATES §2 and §5). The page shows the best option without them; each can needs a different partner.
  - Cluster all three in a row: the middle can serves both neighbours.
- **nextto gaps are tight (derived from §5 with the asset sizes):**

  | pair | allowed AABB gap |
  | --- | --- |
  | can-can | ≤ ~3.2 cm |
  | wineglass-wineglass | ≤ ~4.2 cm |
  | wineglass-bottle | ≤ ~4.1 cm |
  | corkscrew-bottle | ≤ ~3.2 cm |

  Place them almost touching.
- **Wineglass rays (derived, unverified):** the horizontal rays leave from each glass's AABB centre height, which may be at the thin stem. Rays could slip past the partner's stem. Put the bowls nearly touching.
- `ontop X bar` fails if the item's centre overhangs the bar edge (§4). Place well onto the counter.
- **Ice cubes:** each needs its centre in the bucket's volume. The bucket is rescaled to 0.204 x 0.246 x 0.234 m (`task_custom_lists.json`). Cubes spilled while carrying the bucket are lost.
- Knocking over a placed glass or can loses both its `ontop` and its pairing literals.

### Minimal plan

Group by trip, two items per trip, one per hand.

1. `move to the wineglass`, then `pick up the wineglass from the bottom cabinet` twice. About 45 s.
2. `move to the bar`, then `place the wineglass on the bar`, then `place the wineglass on the bar next to the wineglass`. About 41 s.
3. `move to the wine bottle`, then `pick up the wine bottle from the bottom cabinet`, then `pick up the corkscrew from the bottom cabinet`. About 46 s.
4. `move to the bar`, then `place the wine bottle on the bar` right beside one wineglass, then `place the corkscrew on the bar next to the wine bottle`. About 41 s.
5. `move to the can of soda`, then `pick up the can of soda from the bottom cabinet` twice, then `move to the bar`, then `place the can of soda on the bar` and `place the can of soda on the bar next to the can of soda`. About 85 s.
6. Third can: same pick, then `move to the bar`, then `place the can of soda on the bar next to the can of soda`. About 45 s.
7. `move to the tray`, then `pick up the tray from the bottom cabinet`, then `pour the ice bucket into the tray`. The demo wording actually means tipping the tray into the bucket on the cabinet. Done when no cube remains on the tray. About 45 s.
8. `place the tray on the bottom cabinet`, then `pick up the ice bucket from the bottom cabinet`, then `move to the bar`, then `place the ice bucket on the bar`. Carry it level. About 55 s.

- Totals: about 400 s against a 670.9 s limit.

### What the demos do differently

- The 8 most common orders (148 of 200 demos) all do the ice last: tray pour on the cabinet, then carry the bucket. The other items come in varying two-at-a-time orders (29 orders in total).
- They seldom re-adjust pairings. A planner should re-check each `nextto` gap by depth before moving on.
- Alternative for the ice: carry the empty bucket to the bar first, then carry the tray and pour there. This avoids a loaded-bucket carry, but has no trained prompt beyond the same `pour` sentence and is unverified.

### Hard parts and hacks

- **Grasp sizes (asset bbox; bucket and tray rescaled):**
  - can 0.081 m diameter;
  - wineglass bowl 0.117 m (stem thinner);
  - wine bottle 0.067 m (neck thinner);
  - corkscrew 0.112 x 0.088 x 0.021 m;
  - tray 0.165 x 0.24 x 0.045 m;
  - ice cube ~0.02 m.
- Picking the 6 cubes singly is hopeless in time. The pour is the only practical route.
- The bar top is ~1.1 m high (bar bbox height 1.097 m). Placing near the far side needs reach. Keep items near the bar's front edge, but with centres over the top.
- The bottom cabinet (olgoza) is closed at reset. Nothing needs to go inside it.

### Hints for the VLM

- Everything starts on the single bottom cabinet in bar_0: 3 cans, 2 wineglasses, the bottle, the corkscrew, and the tray with 6 cubes. The ice bucket is on the cabinet too.
- The target "bar" is the large counter (2.28 x 5.76 m bbox) in the same room. It also borders the dining room. A beer tap is in the room, but whether it stands on the bar is unverified.
- The fridge in the bar room is irrelevant.
- Done: 3 cans in a touching cluster on the bar; two glasses touching each other, with one also touching the bottle; the corkscrew against the bottle; the bucket on the bar with no cubes left on the tray.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(ontop wine_bottle.n.01_1 countertop.n.01_1)` | no | yes |
| `(nextto can__of__soda.n.01_1 can__of__soda.n.01_2)` | no | yes |
| `(ontop can__of__soda.n.01_1 countertop.n.01_1)` | no | yes |
| `(nextto can__of__soda.n.01_2 can__of__soda.n.01_1)` | no | yes |
| `(ontop can__of__soda.n.01_2 countertop.n.01_1)` | no | yes |
| `(nextto can__of__soda.n.01_3 can__of__soda.n.01_1)` | no | yes |
| `(ontop can__of__soda.n.01_3 countertop.n.01_1)` | no | yes |
| `(inside ice_cube.n.01_5 bucket.n.01_1)` | no | yes |
| `(inside ice_cube.n.01_1 bucket.n.01_1)` | no | yes |
| `(inside ice_cube.n.01_4 bucket.n.01_1)` | no | yes |
| `(inside ice_cube.n.01_6 bucket.n.01_1)` | no | yes |
| `(inside ice_cube.n.01_2 bucket.n.01_1)` | no | yes |
| `(inside ice_cube.n.01_3 bucket.n.01_1)` | no | yes |
| `(ontop bucket.n.01_1 countertop.n.01_1)` | no | yes |
| `(ontop wineglass.n.01_2 countertop.n.01_1)` | no | yes |
| `(ontop wineglass.n.01_1 countertop.n.01_1)` | no | yes |
| `(nextto wineglass.n.01_2 wine_bottle.n.01_1)` | no | yes |
| `(nextto wineglass.n.01_1 wineglass.n.01_2)` | no | yes |
| `(ontop corkscrew.n.01_1 countertop.n.01_1)` | no | yes |
| `(nextto corkscrew.n.01_1 wine_bottle.n.01_1)` | no | yes |

The goal has 54 ground options (20 literals x54); Q takes the best one, so any valid choice of container or partner object counts.

38 ground options pair an object with itself (for example `nextto can_1 can_1`). Those can never hold, so the option shown above is the best one without them.

BDDL goal:

```lisp
(:goal
        (and
            (ontop ?wine_bottle.n.01_1 ?countertop.n.01_1)
            (forall
                (?can__of__soda.n.01 - can__of__soda.n.01)
                (and
                    (or
                        (nextto ?can__of__soda.n.01 ?can__of__soda.n.01_1)
                        (nextto ?can__of__soda.n.01 ?can__of__soda.n.01_2)
                        (nextto ?can__of__soda.n.01 ?can__of__soda.n.01_3)
                    )
                    (ontop ?can__of__soda.n.01 ?countertop.n.01_1)
                )
            )
            (forall
                (?ice_cube.n.01 - ice_cube.n.01)
                (inside ?ice_cube.n.01 ?bucket.n.01_1)
            )
            (ontop ?bucket.n.01_1 ?countertop.n.01_1)
            (forall
                (?wineglass.n.01 - wineglass.n.01)
                (ontop ?wineglass.n.01 ?countertop.n.01_1)
            )
            (exists
                (?wineglass.n.01 - wineglass.n.01)
                (nextto ?wineglass.n.01 ?wine_bottle.n.01_1)
            )
            (nextto ?wineglass.n.01_1 ?wineglass.n.01_2)
            (ontop ?corkscrew.n.01_1 ?countertop.n.01_1)
            (nextto ?corkscrew.n.01_1 ?wine_bottle.n.01_1)
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `electric_refrigerator.n.01_1` | fridge_juwaoh_0 | fridge / juwaoh | bar_0 | table/counter (0.6-1.1 m), z 0.77 | 3.14 m (range 2.63-3.44) | no (fixed) |
| `wine_bottle.n.01_1` | wine_bottle_61 | wine_bottle / inkqch | bar_0 | table/counter (0.6-1.1 m), z 0.93 | 1.96 m (range 1.01-3.14) | yes, spread 1.93 m |
| `countertop.n.01_1` | bar_xxftww_0 | bar / xxftww | bar_0, dining_room_0 | low (0.25-0.6 m), z 0.59 | 2.17 m (range 1.52-2.63) | no (fixed) |
| `cabinet.n.01_1` | bottom_cabinet_olgoza_0 | bottom_cabinet / olgoza | bar_0 | low (0.25-0.6 m), z 0.43 | 1.77 m (range 1.4-2.2) | no |
| `can__of__soda.n.01_1` | can_of_soda_60 | can_of_soda / evcxlr | bar_0 | table/counter (0.6-1.1 m), z 0.91 | 2.0 m (range 0.92-3.0) | yes, spread 2.02 m |
| `can__of__soda.n.01_2` | can_of_soda_59 | can_of_soda / evcxlr | bar_0 | table/counter (0.6-1.1 m), z 0.9 | 2.08 m (range 0.87-2.82) | yes, spread 1.98 m |
| `can__of__soda.n.01_3` | can_of_soda_58 | can_of_soda / evcxlr | bar_0 | table/counter (0.6-1.1 m), z 0.91 | 1.82 m (range 0.82-2.72) | yes, spread 1.95 m |
| `ice_cube.n.01_1` | ice_cube_57 | ice_cube / dueotq | bar_0 | table/counter (0.6-1.1 m), z 0.86 | 1.66 m (range 1.17-2.79) | yes, spread 1.37 m |
| `ice_cube.n.01_2` | ice_cube_56 | ice_cube / kdlafa | bar_0 | table/counter (0.6-1.1 m), z 0.86 | 1.67 m (range 1.21-2.91) | yes, spread 1.5 m |
| `ice_cube.n.01_3` | ice_cube_55 | ice_cube / kdlafa | bar_0 | table/counter (0.6-1.1 m), z 0.86 | 1.66 m (range 1.23-2.94) | yes, spread 1.55 m |
| `ice_cube.n.01_4` | ice_cube_54 | ice_cube / kdlafa | bar_0 | table/counter (0.6-1.1 m), z 0.86 | 1.73 m (range 1.27-2.85) | yes, spread 1.43 m |
| `ice_cube.n.01_5` | ice_cube_53 | ice_cube / dueotq | bar_0 | table/counter (0.6-1.1 m), z 0.86 | 1.69 m (range 1.2-2.89) | yes, spread 1.49 m |
| `ice_cube.n.01_6` | ice_cube_52 | ice_cube / dueotq | bar_0 | table/counter (0.6-1.1 m), z 0.86 | 1.7 m (range 1.23-2.84) | yes, spread 1.41 m |
| `wineglass.n.01_1` | wineglass_51 | wineglass / kxovsj | bar_0 | table/counter (0.6-1.1 m), z 0.92 | 1.65 m (range 0.75-2.61) | yes, spread 1.85 m |
| `wineglass.n.01_2` | wineglass_50 | wineglass / kxovsj | bar_0 | table/counter (0.6-1.1 m), z 0.92 | 1.93 m (range 0.96-2.83) | yes, spread 1.92 m |
| `bucket.n.01_1` | ice_bucket_49 | ice_bucket / vlurir | bar_0 | table/counter (0.6-1.1 m), z 0.96 | 1.76 m (range 1.25-2.8) | yes, spread 1.35 m |
| `corkscrew.n.01_1` | corkscrew_48 | corkscrew / gqocna | bar_0 | table/counter (0.6-1.1 m), z 0.85 | 1.74 m (range 1.11-2.81) | yes, spread 1.76 m |
| `tray.n.01_1` | tray_47 | tray / vxbtax | bar_0 | table/counter (0.6-1.1 m), z 0.86 | 1.68 m (range 1.21-2.87) | yes, spread 1.43 m |
| `floor.n.01_1` | floors_qqbcva_0 | floors / qqbcva | bar_0 | floor, z -0.0 | 1.15 m (range 0.51-1.53) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "bar"
 ],
 "restaurant_diner": {
  "whitelist": {
   "can__of__soda.n.01": {
    "can_of_soda": {
     "evcxlr": null
    }
   },
   "bucket.n.01": {
    "ice_bucket": {
     "vlurir": [
      0.204,
      0.246,
      0.234
     ]
    }
   },
   "corkscrew.n.01": {
    "corkscrew": {
     "gqocna": null
    }
   },
   "ice_cube.n.01": {
    "ice_cube": {
     "dueotq": null,
     "kdlafa": null
    }
   },
   "shot_glass.n.01": {
    "jigger": {
     "aysfhf": null
    }
   },
   "tray.n.01": {
    "tray": {
     "vxbtax": [
      0.165,
      0.24,
      0.045
     ]
    }
   },
   "water_glass.n.02": {
    "water_glass": {
     "gypzlg": null
    }
   },
   "wine_bottle.n.01": {
    "wine_bottle": {
     "inkqch": null
    }
   },
   "wineglass.n.01": {
    "wineglass": {
     "kxovsj": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(inroom cabinet.n.01_1 bar)
(inroom countertop.n.01_1 bar)
(inroom electric_refrigerator.n.01_1 bar)
(inroom floor.n.01_1 bar)
(ontop agent.n.01_1 floor.n.01_1)
(ontop bucket.n.01_1 cabinet.n.01_1)
(ontop can__of__soda.n.01_1 cabinet.n.01_1)
(ontop can__of__soda.n.01_2 cabinet.n.01_1)
(ontop can__of__soda.n.01_3 cabinet.n.01_1)
(ontop corkscrew.n.01_1 cabinet.n.01_1)
(ontop ice_cube.n.01_1 tray.n.01_1)
(ontop ice_cube.n.01_2 tray.n.01_1)
(ontop ice_cube.n.01_3 tray.n.01_1)
(ontop ice_cube.n.01_4 tray.n.01_1)
(ontop ice_cube.n.01_5 tray.n.01_1)
(ontop ice_cube.n.01_6 tray.n.01_1)
(ontop tray.n.01_1 cabinet.n.01_1)
(ontop wine_bottle.n.01_1 cabinet.n.01_1)
(ontop wineglass.n.01_1 cabinet.n.01_1)
(ontop wineglass.n.01_2 cabinet.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching bucket.n.01_1 cabinet.n.01_1)
(touching cabinet.n.01_1 bucket.n.01_1)
(touching cabinet.n.01_1 can__of__soda.n.01_1)
(touching cabinet.n.01_1 can__of__soda.n.01_2)
(touching cabinet.n.01_1 can__of__soda.n.01_3)
(touching cabinet.n.01_1 corkscrew.n.01_1)
(touching cabinet.n.01_1 tray.n.01_1)
(touching cabinet.n.01_1 wine_bottle.n.01_1)
(touching cabinet.n.01_1 wineglass.n.01_1)
(touching cabinet.n.01_1 wineglass.n.01_2)
(touching can__of__soda.n.01_1 cabinet.n.01_1)
(touching can__of__soda.n.01_2 cabinet.n.01_1)
(touching can__of__soda.n.01_3 cabinet.n.01_1)
(touching corkscrew.n.01_1 cabinet.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching ice_cube.n.01_1 tray.n.01_1)
(touching ice_cube.n.01_2 tray.n.01_1)
(touching ice_cube.n.01_3 tray.n.01_1)
(touching ice_cube.n.01_4 tray.n.01_1)
(touching ice_cube.n.01_5 tray.n.01_1)
(touching ice_cube.n.01_6 tray.n.01_1)
(touching tray.n.01_1 cabinet.n.01_1)
(touching tray.n.01_1 ice_cube.n.01_1)
(touching tray.n.01_1 ice_cube.n.01_2)
(touching tray.n.01_1 ice_cube.n.01_3)
(touching tray.n.01_1 ice_cube.n.01_4)
(touching tray.n.01_1 ice_cube.n.01_5)
(touching tray.n.01_1 ice_cube.n.01_6)
(touching wine_bottle.n.01_1 cabinet.n.01_1)
(touching wineglass.n.01_1 cabinet.n.01_1)
(touching wineglass.n.01_2 cabinet.n.01_1)
```

## What the human demos did

200 annotated demos. Length 425.2 s (range 316.43-646.8). Skills per demo 31.0 (range 29-34). 29 distinct skill orders; the most common one covers 14% of demos.

Most common skill counts per demo (32% of demos): move to x11, pick up from x9, place on x6, place on next to x3, pour x1.

Representative demo `episode_00970660.json` (386.1 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the wineglass` (0.0-8.0 s)
2. `pick up the wineglass from the bottom cabinet` (8.0-25.0 s)
3. `pick up the wineglass from the bottom cabinet` (25.0-38.0 s)
4. `move to the bar` (38.0-53.0 s)
5. `place the wineglass on the bar` (53.0-64.3 s)
6. `place the wineglass on the bar next to the wineglass` (64.3-71.7 s)
7. `move to the wine bottle` (71.7-93.0 s)
8. `pick up the wine bottle from the bottom cabinet` (93.0-101.1 s)
9. `pick up the corkscrew from the bottom cabinet` (101.1-123.0 s)
10. `move to the bar` (123.0-136.0 s)
11. `place the wine bottle on the bar` (136.0-146.5 s)
12. `place the corkscrew on the bar next to the wine bottle` (146.5-163.4 s)
13. `move to the can of soda` (163.4-175.0 s)
14. `pick up the can of soda from the bottom cabinet` (175.0-186.4 s)
15. `pick up the can of soda from the bottom cabinet` (186.4-205.8 s)
16. `move to the bar` (205.8-218.0 s)
17. `place the can of soda on the bar` (218.0-228.1 s)
18. `place the can of soda on the bar next to the can of soda` (228.1-232.0 s)
19. `move to the can of soda` (232.0-251.0 s)
20. `pick up the can of soda from the bottom cabinet` (251.0-263.0 s)
21. `move to the bar` (263.0-277.2 s)
22. `place the can of soda on the bar` (277.2-284.8 s)
23. `move to the tray` (284.8-302.0 s)
24. `pick up the tray from the bottom cabinet` (302.0-318.8 s)
25. `pour the ice bucket into the tray` (318.8-334.7 s)
26. `place the tray on the bottom cabinet` (334.7-347.2 s)
27. `pick up the ice bucket from the bottom cabinet` (347.2-360.5 s)
28. `move to the bar` (360.5-372.0 s)
29. `place the ice bucket on the bar` (372.0-386.1 s)

Mean duration per skill in this task: move to 15.2 s, pick up from 15.3 s, place on 12.7 s, place on next to 13.1 s, pour 14.1 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the bar` | 1002 |
| `pick up the can of soda from the bottom cabinet` | 600 |
| `move to the can of soda` | 414 |
| `pick up the wineglass from the bottom cabinet` | 400 |
| `place the can of soda on the bar` | 400 |
| `move to the wineglass` | 281 |
| `move to the tray` | 206 |
| `place the wineglass on the bar` | 200 |
| `place the wineglass on the bar next to the wineglass` | 200 |
| `move to the wine bottle` | 200 |
| `pick up the wine bottle from the bottom cabinet` | 200 |
| `pick up the corkscrew from the bottom cabinet` | 200 |
| `place the wine bottle on the bar` | 200 |
| `place the can of soda on the bar next to the can of soda` | 200 |
| `pick up the tray from the bottom cabinet` | 200 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/97_setup_a_bar_for_a_cocktail_party.json`. Planner notes: `task_docs/notes/97_setup_a_bar_for_a_cocktail_party.md`.
