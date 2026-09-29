# 86 · Make Gift Bags For Baby Showers

Task name `make_gift_bags_for_baby_showers`, task index 86.

> Make baby-shower gift bags by putting a toy die and a wafer into each paper bag.

## At a glance

| item | value |
| --- | --- |
| scene | `Rs_int` |
| rooms in the goal | living_room |
| rooms loaded | bedroom_0, entryway_0, kitchen_0, living_room_0 |
| human demo length | 321.7 s mean (9650 steps) |
| episode time limit | 482.5 s (14476 steps at 30 Hz) |
| human base travel | 16.7904 m |
| goal literals (best ground option) | 6 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 4 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | not evaluated yet |
| demo video | https://www.youtube.com/embed/EY42jyNoEh8 |

## Planner notes

**Tier:** C — the die (33 mm) and wafer (33 x 199 x 18 mm) fit the jaws, but it is container-in-container work: the wafers start inside closed cabinet drawers and the filled paper bags must be carried to the coffee table.

### Goal in plain words

Both paper bags must rest on the coffee table. Each bag must hold one toy die and one wafer. Which die and which wafer go into which bag is free (two independent `forpairs`, 4 ground options). The cabinet drawers may be left open: there is no `not open` literal.

### Q traps

- Six literals, each 1/6, all false at reset.
- Each `forpairs` needs one item per bag. Two dice in one bag, or two wafers in one bag, score only one of that pair.
- `ontop sack coffee_table` is read at the end. A bag that tips over on the table still touches it, but its items may fall out and lose `inside`.
- Whether the paper bag asset has a fillable volume is not verified (not readable from metadata).
- The wafers start inside `bottom_cabinet_jhymlr_0`, whose six openable links are all closed at reset (joint_pos 0 in all 20 instances). Which drawer holds a wafer varies by instance: the wafers lie near the cabinet front at z 0.61, anywhere along its 1.65 m width. Two wafers can share one drawer (instance 311: same x-y, stacked).
- The two dice start on top of the same cabinet (z 0.77).

### Minimal plan

1. `move to the paper bag` then `pick up the paper bag from the breakfast table` — one bag in each hand (repeat the pick). ~12 s + 2 x 17 s.
2. `move to the coffee table` then `place the paper bag on the coffee table` twice — both bags standing on the coffee table. ~12 s + 2 x 14 s.
3. `move to the bottom cabinet` then `open the drawer of the bottom cabinet` — drawer out, wafer visible. ~12 s + 14 s.
4. `pick up the wafer from the bottom cabinet` and `pick up the toy dice from the bottom cabinet` — one item per hand. ~17 s each.
5. `move to the paper bag`, `place the wafer in the paper bag`, `place the toy dice in the paper bag` — both into the same bag. ~12 s + 2 x 12 s.
6. Repeat 3-5 for the second wafer and die, into the other bag. Open another drawer if the second wafer is not in the first.

Budget: 483 s limit vs 322 s demo mean. Placing the empty bags first (steps 1-2) is not the demo order but avoids carrying loaded bags.

### What the demos do differently

- 94 distinct orders; the most common covers only 4.5%. The usual pattern fills the bags on the breakfast table and carries both full bags to the coffee table at the end.
- Demos close the drawer after each wafer (314 closes over 200 demos). Not needed.
- `move to the wafer` (275) and `move to the toy dice` (154) are alternative approach prompts.

### Hard parts and hacks

- Finding the wafer: it is hidden in one of six closed drawers or doors. The planner may need to open more than one; each open costs ~14 s.
- The bag (asset bbox 0.101 x 0.150 x 0.240 m) must be held by its thin paper wall at the rim. Not verified.
- Distances: breakfast table `breakfast_table_skczfi_0` at (1.47, 0.41); cabinet at (1.66, -1.50), facing -x; coffee table at (-0.48, -1.22). The bags move about 2.5 m.
- Alternative (untested): dropping a wafer into a bag already on the low coffee table (top about 0.39 m, bag rim about 0.63 m) is a lower reach than the breakfast table.

### Hints for the VLM

- Scene Rs_int, living_room_0. Two small paper bags stand on the breakfast table near the kitchen side. The dice sit on top of the long living-room bottom cabinet; the wafers are inside it.
- A second breakfast table stands at (0.17, -3.77); it holds no task objects.
- Done: two bags upright on the coffee table, each holding one die and one wafer.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(ontop sack.n.01_1 coffee_table.n.01_1)` | no | yes |
| `(ontop sack.n.01_2 coffee_table.n.01_1)` | no | yes |
| `(inside toy_dice.n.01_2 sack.n.01_1)` | no | yes |
| `(inside toy_dice.n.01_1 sack.n.01_2)` | no | yes |
| `(inside wafer.n.02_2 sack.n.01_1)` | no | yes |
| `(inside wafer.n.02_1 sack.n.01_2)` | no | yes |

The goal has 4 ground options (6 literals x4); Q takes the best one, so any valid choice of container or partner object counts.

BDDL goal:

```lisp
(:goal 
        (and 
            (forall 
                (?sack.n.01 - sack.n.01) 
                (ontop ?sack.n.01 ?coffee_table.n.01_1)
            ) 
            (forpairs 
                (?toy_dice.n.01 - toy_dice.n.01) 
                (?sack.n.01 - sack.n.01) 
                (inside ?toy_dice.n.01 ?sack.n.01)
            ) 
            (forpairs 
                (?wafer.n.02 - wafer.n.02) 
                (?sack.n.01 - sack.n.01) 
                (inside ?wafer.n.02 ?sack.n.01)
            ) 
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `floor.n.01_1` | floors_ptwlei_0 | floors / ptwlei | living_room_0 | floor, z -0.15 | 1.57 m (range 0.65-2.06) | no (fixed) |
| `toy_dice.n.01_1` | toy_dice_52 | toy_dice / akguod | living_room_0 | table/counter (0.6-1.1 m), z 0.77 | 1.18 m (range 0.8-2.79) | yes, spread 1.51 m |
| `toy_dice.n.01_2` | toy_dice_51 | toy_dice / akguod | living_room_0 | table/counter (0.6-1.1 m), z 0.77 | 1.49 m (range 0.7-3.28) | yes, spread 1.48 m |
| `breakfast_table.n.01_1` | breakfast_table_skczfi_0 | breakfast_table / skczfi | living_room_0 | low (0.25-0.6 m), z 0.6 | 2.43 m (range 1.39-3.37) | no |
| `coffee_table.n.01_1` | coffee_table_fqluyq_0 | coffee_table / fqluyq | living_room_0 | low (0.25-0.6 m), z 0.26 | 1.46 m (range 1.04-2.39) | no |
| `cabinet.n.01_1` | bottom_cabinet_jhymlr_0 | bottom_cabinet / jhymlr | living_room_0 | low (0.25-0.6 m), z 0.38 | 1.54 m (range 1.0-3.06) | no (fixed) |
| `wafer.n.02_1` | wafer_50 | wafer / ramcrb | living_room_0 | table/counter (0.6-1.1 m), z 0.61 | 1.19 m (range 0.86-3.14) | yes, spread 1.17 m |
| `wafer.n.02_2` | wafer_49 | wafer / ramcrb | living_room_0 | table/counter (0.6-1.1 m), z 0.61 | 1.69 m (range 0.83-2.81) | yes, spread 1.24 m |
| `sack.n.01_1` | paper_bag_48 | paper_bag / bzsxgw | living_room_0 | table/counter (0.6-1.1 m), z 0.87 | 2.3 m (range 1.48-3.6) | yes, spread 0.91 m |
| `sack.n.01_2` | paper_bag_47 | paper_bag / bzsxgw | living_room_0 | table/counter (0.6-1.1 m), z 0.87 | 2.32 m (range 0.92-3.34) | yes, spread 0.92 m |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "living_room"
 ],
 "Rs_int": {
  "whitelist": {
   "sack.n.01": {
    "paper_bag": {
     "bzsxgw": null
    }
   },
   "toy_dice.n.01": {
    "toy_dice": {
     "akguod": 0.8,
     "cmqtch": 0.8
    }
   },
   "wafer.n.02": {
    "wafer": {
     "ramcrb": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(inroom breakfast_table.n.01_1 living_room)
(inroom cabinet.n.01_1 living_room)
(inroom coffee_table.n.01_1 living_room)
(inroom floor.n.01_1 living_room)
(inside wafer.n.02_1 cabinet.n.01_1)
(inside wafer.n.02_2 cabinet.n.01_1)
(ontop agent.n.01_1 floor.n.01_1)
(ontop sack.n.01_1 breakfast_table.n.01_1)
(ontop sack.n.01_2 breakfast_table.n.01_1)
(ontop toy_dice.n.01_1 cabinet.n.01_1)
(ontop toy_dice.n.01_2 cabinet.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching breakfast_table.n.01_1 sack.n.01_1)
(touching breakfast_table.n.01_1 sack.n.01_2)
(touching cabinet.n.01_1 toy_dice.n.01_1)
(touching cabinet.n.01_1 toy_dice.n.01_2)
(touching floor.n.01_1 agent.n.01_1)
(touching sack.n.01_1 breakfast_table.n.01_1)
(touching sack.n.01_2 breakfast_table.n.01_1)
(touching toy_dice.n.01_1 cabinet.n.01_1)
(touching toy_dice.n.01_2 cabinet.n.01_1)
```

## What the human demos did

200 annotated demos. Length 302.63 s (range 197.43-527.43). Skills per demo 24.0 (range 19-30). 94 distinct skill orders; the most common one covers 4% of demos.

Most common skill counts per demo (11% of demos): move to x8, pick up from x6, place in x4, close drawer x2, open drawer x2, place on x2.

Representative demo `episode_00861010.json` (287.6 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the bottom cabinet` (0.0-2.4 s)
2. `open the drawer of the bottom cabinet` (2.4-12.0 s)
3. `pick up the wafer from the bottom cabinet` (12.0-32.3 s)
4. `close the drawer of the bottom cabinet` (32.3-44.2 s)
5. `pick up the toy dice from the bottom cabinet` (44.2-55.0 s)
6. `move to the paper bag` (55.0-64.0 s)
7. `place the wafer in the paper bag` (64.0-77.3 s)
8. `place the toy dice in the paper bag` (77.3-95.1 s)
9. `move to the bottom cabinet` (95.1-111.9 s)
10. `open the drawer of the bottom cabinet` (111.9-123.2 s)
11. `pick up the wafer from the bottom cabinet` (123.2-148.7 s)
12. `close the drawer of the bottom cabinet` (148.7-152.7 s)
13. `pick up the toy dice from the bottom cabinet` (152.7-166.0 s)
14. `move to the paper bag` (166.0-186.0 s)
15. `place the wafer in the paper bag` (186.0-200.3 s)
16. `place the toy dice in the paper bag` (200.3-209.4 s)
17. `pick up the paper bag from the breakfast table` (209.4-227.0 s)
18. `move to the paper bag` (227.0-235.6 s)
19. `pick up the paper bag from the breakfast table` (235.6-251.0 s)
20. `move to the coffee table` (251.0-262.0 s)
21. `place the paper bag on the coffee table` (262.0-273.6 s)
22. `place the paper bag on the coffee table` (273.6-287.6 s)

Mean duration per skill in this task: close drawer 7.5 s, move to 12.0 s, open drawer 14.3 s, pick up from 17.1 s, place in 12.3 s, place on 14.1 s, turn to 7.1 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the paper bag` | 630 |
| `move to the bottom cabinet` | 519 |
| `place the wafer in the paper bag` | 402 |
| `pick up the wafer from the bottom cabinet` | 401 |
| `pick up the toy dice from the bottom cabinet` | 400 |
| `pick up the paper bag from the breakfast table` | 400 |
| `place the paper bag on the coffee table` | 398 |
| `place the toy dice in the paper bag` | 396 |
| `close the drawer of the bottom cabinet` | 314 |
| `open the drawer of the bottom cabinet` | 311 |
| `move to the wafer` | 275 |
| `move to the coffee table` | 199 |
| `move to the toy dice` | 154 |
| `open the drawer of the wafer` | 3 |
| `place the paper bag in the coffee table` | 2 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/86_make_gift_bags_for_baby_showers.json`. Planner notes: `task_docs/notes/86_make_gift_bags_for_baby_showers.md`.
