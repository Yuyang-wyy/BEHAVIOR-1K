# 81 · Packing Meal For Delivery

Task name `packing_meal_for_delivery`, task index 81.

> Pack each wrapped hamburger into a paper bag, then put the paper bags into the storage box.

## At a glance

| item | value |
| --- | --- |
| scene | `restaurant_diner` |
| rooms in the goal | kitchen |
| rooms loaded | kitchen_0, bar_0 |
| human demo length | 295.3 s mean (8859 steps) |
| episode time limit | 443.0 s (13289 steps at 30 Hz) |
| human base travel | 19.6145 m |
| goal literals (best ground option) | 6 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 6 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | not evaluated yet |
| demo video | https://www.youtube.com/embed/DirqFshrOAA |

## Planner notes

**Tier:** C — container-in-container: three burgers into three paper bags, then the bags onto the floor of an open storage box. The burgers (50 mm thick) and bag bodies exceed the 44 mm jaw span.

### Goal in plain words

Each wrapped hamburger must be inside a different paper bag, and all three bags must rest on the storage box. Which burger goes in which bag is free (`forpairs`, 6 ground options). The tray is not in the goal. Everything starts on one commercial kitchen table.

### Q traps

- Six literals, each 1/6. None is true at reset.
- `forpairs` needs one burger per bag. Two burgers in one bag score only one of those two `inside` literals.
- `ontop sack storage_box` needs the bag to touch the box and the ray down from the bag's centre to hit the box (PREDICATES §4). The storage box has no lid object in the scene (template checked), so a bag standing on the box floor works. A bag leaning on the rim with its centre outside the box does not.
- Box fit (derived from bboxes): the box is 0.50 x 0.51 x 0.21 m (forced size); each bag is 0.137 x 0.291 x 0.508 m. Three bags fit side by side only with their thin sides together (3 x 0.137 = 0.41 m). The interior is smaller than the outer bbox; the exact inner size is not verified.
- The bags are 0.51 m tall and the box only 0.21 m, so a bag can tip out of the box. A tipped bag can also drop its burger. Re-check all six literals at the end.
- Whether the paper bag asset has a fillable volume is not verified (not readable from metadata).

### Minimal plan

1. `move to the paper bag` — bags on the table in view. ~15 s.
2. `pick up the paper bag from the commercial kitchen table` — one bag held by its rim. ~14 s.
3. `move to the wrapped hamburger` — tray with burgers in view. ~15 s.
4. `pick up the wrapped hamburger from the tray` — burger in the free hand. ~14 s.
5. `place the wrapped hamburger in the paper bag` — burger gone into the held bag. ~16 s.
6. `move to the storage box` then `place the paper bag in the storage box` — bag standing upright in the box. ~15 s + 16 s.
7. Repeat 1-6 twice, standing each new bag beside the previous ones.

Budget: 443 s limit vs 295 s demo mean. About 90 s per bag cycle.

### What the demos do differently

- 42% follow the order above: bag in one hand, burger dropped into it, bag into box.
- The demo string `place the paper bag in the storage box` is the trained wording, although the goal predicate is `ontop`.
- All objects stay within about 2.5 m of each other on one table. Most `move to` steps are short turns.

### Hard parts and hacks

- Burger (asset bbox 0.092 x 0.102 x 0.050 m) has no axis under 44 mm. It lies flat on a tray, so the grasp may fail outright.
- The bag must be held by its thin paper wall at the rim; the body is 137 mm across (asset bbox). This grasp is not verified.
- Alternative order (untested): stand all three bags in the box first, then drop one burger into each bag there. This avoids carrying a loaded bag, but the bag opening is then about 1.4 m high on a 0.87 m table (derived).
- Partial-credit route: bags into the box alone give 3/6 even if no burger can be grasped.

### Hints for the VLM

- Scene restaurant_diner, kitchen_0. The target table is `commercial_kitchen_table_vxvtec_0`; a second commercial kitchen table stands at the other end of the kitchen (about 4.5 m away) and is empty of task objects.
- Three identical tall (0.51 m) paper bags, a tray with three wrapped burgers, and an open storage box, all on one table.
- Done: three bags standing inside the open box, each with one burger at its bottom.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside wrapped_hamburger.n.01_1 sack.n.01_1)` | no | yes |
| `(inside wrapped_hamburger.n.01_3 sack.n.01_2)` | no | yes |
| `(inside wrapped_hamburger.n.01_2 sack.n.01_3)` | no | yes |
| `(ontop sack.n.01_1 storage_container.n.01_1)` | no | yes |
| `(ontop sack.n.01_2 storage_container.n.01_1)` | no | yes |
| `(ontop sack.n.01_3 storage_container.n.01_1)` | no | yes |

The goal has 6 ground options (6 literals x6); Q takes the best one, so any valid choice of container or partner object counts.

BDDL goal:

```lisp
(:goal
        (and
            (forpairs
                (?wrapped_hamburger.n.01 - wrapped_hamburger.n.01)
                (?sack.n.01 - sack.n.01)
                (inside ?wrapped_hamburger.n.01 ?sack.n.01)
            )
            (forall
                (?sack.n.01 - sack.n.01)
                (ontop ?sack.n.01 ?storage_container.n.01_1)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `wrapped_hamburger.n.01_1` | wrapped_hamburger_81 | wrapped_hamburger / rerdmy | kitchen_0 | table/counter (0.6-1.1 m), z 0.9 | 2.66 m (range 1.58-4.44) | yes, spread 2.18 m |
| `wrapped_hamburger.n.01_2` | wrapped_hamburger_80 | wrapped_hamburger / rerdmy | kitchen_0 | table/counter (0.6-1.1 m), z 0.9 | 2.68 m (range 1.51-4.55) | yes, spread 2.37 m |
| `wrapped_hamburger.n.01_3` | wrapped_hamburger_79 | wrapped_hamburger / rerdmy | kitchen_0 | table/counter (0.6-1.1 m), z 0.9 | 2.65 m (range 1.5-4.42) | yes, spread 2.37 m |
| `tray.n.01_1` | tray_78 | tray / mhhoga | kitchen_0 | table/counter (0.6-1.1 m), z 0.88 | 2.69 m (range 1.59-4.47) | yes, spread 2.27 m |
| `storage_container.n.01_1` | storage_box_77 | storage_box / izcglf | kitchen_0 | table/counter (0.6-1.1 m), z 0.94 | 3.1 m (range 1.21-3.85) | yes, spread 1.78 m |
| `countertop.n.01_1` | commercial_kitchen_table_vxvtec_0 | commercial_kitchen_table / vxvtec | kitchen_0 | low (0.25-0.6 m), z 0.54 | 2.84 m (range 2.07-3.61) | no |
| `sack.n.01_1` | paper_bag_76 | paper_bag / wvhmww | kitchen_0 | table/counter (0.6-1.1 m), z 1.05 | 2.17 m (range 0.88-3.75) | yes, spread 2.57 m |
| `sack.n.01_2` | paper_bag_75 | paper_bag / wvhmww | kitchen_0 | table/counter (0.6-1.1 m), z 1.05 | 2.73 m (range 0.94-4.15) | yes, spread 2.05 m |
| `sack.n.01_3` | paper_bag_74 | paper_bag / wvhmww | kitchen_0 | table/counter (0.6-1.1 m), z 1.05 | 2.43 m (range 1.16-3.35) | yes, spread 1.95 m |
| `floor.n.01_1` | floors_vikfyd_0 | floors / vikfyd | kitchen_0 | floor, z 0.0 | 2.48 m (range 1.24-3.41) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "kitchen"
 ],
 "restaurant_diner": {
  "whitelist": {
   "sack.n.01": {
    "paper_bag": {
     "wvhmww": null
    }
   },
   "tray.n.01": {
    "tray": {
     "mhhoga": null
    }
   },
   "storage_container.n.01": {
    "storage_box": {
     "izcglf": [
      0.5,
      0.512,
      0.21
     ]
    }
   },
   "wrapped_hamburger.n.01": {
    "wrapped_hamburger": {
     "rerdmy": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(inroom countertop.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(ontop agent.n.01_1 floor.n.01_1)
(ontop sack.n.01_1 countertop.n.01_1)
(ontop sack.n.01_2 countertop.n.01_1)
(ontop sack.n.01_3 countertop.n.01_1)
(ontop storage_container.n.01_1 countertop.n.01_1)
(ontop tray.n.01_1 countertop.n.01_1)
(ontop wrapped_hamburger.n.01_1 tray.n.01_1)
(ontop wrapped_hamburger.n.01_2 tray.n.01_1)
(ontop wrapped_hamburger.n.01_3 tray.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching countertop.n.01_1 sack.n.01_1)
(touching countertop.n.01_1 sack.n.01_2)
(touching countertop.n.01_1 sack.n.01_3)
(touching countertop.n.01_1 storage_container.n.01_1)
(touching countertop.n.01_1 tray.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching sack.n.01_1 countertop.n.01_1)
(touching sack.n.01_2 countertop.n.01_1)
(touching sack.n.01_3 countertop.n.01_1)
(touching storage_container.n.01_1 countertop.n.01_1)
(touching tray.n.01_1 countertop.n.01_1)
(touching tray.n.01_1 wrapped_hamburger.n.01_1)
(touching tray.n.01_1 wrapped_hamburger.n.01_2)
(touching tray.n.01_1 wrapped_hamburger.n.01_3)
(touching wrapped_hamburger.n.01_1 tray.n.01_1)
(touching wrapped_hamburger.n.01_2 tray.n.01_1)
(touching wrapped_hamburger.n.01_3 tray.n.01_1)
```

## What the human demos did

200 annotated demos. Length 293.9 s (range 211.97-393.57). Skills per demo 20.0 (range 16-27). 26 distinct skill orders; the most common one covers 42% of demos.

Most common skill counts per demo (42% of demos): move to x9, pick up from x6, place in x6.

Representative demo `episode_00812620.json` (303.4 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the paper bag` (0.0-15.7 s)
2. `pick up the paper bag from the commercial kitchen table` (15.7-32.0 s)
3. `move to the wrapped hamburger` (32.0-39.8 s)
4. `pick up the wrapped hamburger from the tray` (39.8-48.0 s)
5. `place the wrapped hamburger in the paper bag` (48.0-56.0 s)
6. `move to the storage box` (56.0-84.0 s)
7. `place the paper bag in the storage box` (84.0-104.0 s)
8. `move to the paper bag` (104.0-120.0 s)
9. `pick up the paper bag from the commercial kitchen table` (120.0-136.0 s)
10. `move to the wrapped hamburger` (136.0-142.8 s)
11. `pick up the wrapped hamburger from the tray` (142.8-150.0 s)
12. `place the wrapped hamburger in the paper bag` (150.0-164.0 s)
13. `move to the storage box` (164.0-173.4 s)
14. `place the paper bag in the storage box` (173.4-185.0 s)
15. `move to the paper bag` (185.0-197.0 s)
16. `pick up the paper bag from the commercial kitchen table` (197.0-212.0 s)
17. `move to the wrapped hamburger` (212.0-236.0 s)
18. `pick up the wrapped hamburger from the tray` (236.0-250.0 s)
19. `place the wrapped hamburger in the paper bag` (250.0-259.0 s)
20. `move to the storage box` (259.0-282.0 s)
21. `place the paper bag in the storage box` (282.0-303.0 s)

Mean duration per skill in this task: move to 14.9 s, pick up from 13.6 s, place in 15.9 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the paper bag` | 604 |
| `pick up the wrapped hamburger from the tray` | 601 |
| `place the wrapped hamburger in the paper bag` | 601 |
| `place the paper bag in the storage box` | 601 |
| `pick up the paper bag from the commercial kitchen table` | 600 |
| `move to the storage box` | 515 |
| `move to the wrapped hamburger` | 446 |
| `pick up the paper bag from the storage box` | 1 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/81_packing_meal_for_delivery.json`. Planner notes: `task_docs/notes/81_packing_meal_for_delivery.md`.
