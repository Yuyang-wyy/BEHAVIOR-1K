# 73 · Organizing School Stuff

Task name `organizing_school_stuff`, task index 73.

> Put the school supplies into the tote, place the tote on the bed, and keep the folder and notebook next to it.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | bedroom |
| rooms loaded | bedroom_0, closet_0, closet_1, garden_0, corridor_0, bathroom_1 |
| human demo length | 486.4 s mean (14591 steps) |
| episode time limit | 729.6 s (21887 steps at 30 Hz) |
| human base travel | 26.1584 m |
| goal literals (best ground option) | 6 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://www.youtube.com/embed/GO2Bw-0OY7M |

## Planner notes

**Tier:** C — five items go into a tote bag that must sit on the bed, and three of them (folder, notebook, calculator) are flat and wider than the 44 mm jaw span.

### Goal in plain words

The folder, notebook, pencil, pen and calculator must all end inside the tote, and the tote must rest on the bed. The instruction says to keep the folder and notebook "next to" the tote, but the BDDL wants all five **inside** it; the BDDL is what scores. The nightstands and floor are only start locations.

### Q traps

- 6 literals, all false at reset. Each is worth 1/6.
- Result on 311 (ft40k): Q = 0.00.
- `inside` tests each item's AABB centre against the tote's volume (PREDICATES §3). A long item poking out still counts if its centre is inside.
- `ontop tote bed` needs the tote touching the bed with the bed below its centre. If the tote tips over on the mattress, items can spill, and `inside` is lost for each one.
- Order choice:
  - **Tote on the bed first** (all demos): items then go in at bed height, ~0.5 m.
  - Filling on the floor, then lifting a loaded tote, risks spilling everything at once.

### Minimal plan

1. `move to the tote`, `pick up the tote from the floors` ~17 + 25 s.
2. `move to the bed`, `place the tote on the bed` — upright, near the bed edge closest to the items. ~17 + 22 s.
3. `move to the calculator`, `pick up the calculator from the floors` ~17 + 25 s (the demo representative took 35 s).
4. `move to the tote`, `place the calculator in the tote` ~17 + 16 s.
5. `move to the pencil`, `pick up the pencil from the bed`, `move to the tote`, `place the pencil in the tote`.
6. `move to the pen`, `pick up the pen from the floors`, `move to the tote`, `place the pen in the tote`.
7. `move to the folder`, `push the folder to the bed` — slide it until an edge overhangs the mattress edge. ~23 s. Then `pick up the folder from the bed`, `move to the tote`, `place the folder in the tote`.
8. `move to the notebook`, `push the notebook to the bed`, `pick up the notebook from the bed`, `move to the tote`, `place the notebook in the tote`.

Demo mean 486 s against a 730 s limit. All items and the tote are within ~3.3 m of the start, so walking is short; the time goes into grasps.

### What the demos do differently

- 184/200 follow exactly this order. 11/200 swap the pen and the pencil.
- "push … to the bed" is the demos' trick for flat items: shove them to the mattress edge so a finger gets under the overhang. All 200 do it for both the folder and the notebook.

### Hard parts and hacks

- Sizes (forced where `task_custom_lists` sets them):
  - pen 0.17 × 0.015 × 0.015 m and pencil 0.19 × 0.015 × 0.015 m: easy top-down grasps.
  - calculator 0.15 × 0.118 × 0.024 m, flat **on the floor**: no edge to push it over, so it needs a side pinch on 24 mm. The hardest grasp here.
  - notebook 0.15 × 0.12 × 0.027 m and folder 0.29 × 0.20 × 0.033 m, flat on the bed: use the push-to-edge trick.
  - tote 0.34 × 0.24 × 0.47 m: grasp a handle or the rim; handle width unverified.
- The folder (0.29 × 0.20 m) must enter the tote opening (0.34 × 0.24 m outer) nearly edge-on.
- Calculator has a toggle button. Touching it may switch it on; that is harmless, as it is not in the goal.
- Starts vary per instance: the pen and calculator lie on the floor anywhere in bedroom_0 (spread ~5 m), and the pencil, notebook and folder on the bed.

### Hints for the VLM

- house_single_floor bedroom_0: one double bed (2.1 × 1.8 m, mattress ~0.48 m), two nightstands, a bench and a wall TV.
- The tote is the bag standing on the floor, ~0.47 m tall.
- Pen and pencil are thin sticks, ~17-19 cm long. The calculator is a small 15 × 12 cm slab lying on the floor. The folder and notebook are flat on the bed cover.
- Done: the tote upright on the mattress with all five items below its rim.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside folder.n.02_1 carryall.n.01_1)` | no | yes |
| `(inside book.n.02_1 carryall.n.01_1)` | no | yes |
| `(inside pencil.n.01_1 carryall.n.01_1)` | no | yes |
| `(inside pen.n.01_1 carryall.n.01_1)` | no | yes |
| `(inside calculator.n.02_1 carryall.n.01_1)` | no | yes |
| `(ontop carryall.n.01_1 bed.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (inside ?folder.n.02_1 ?carryall.n.01_1) 
            (inside ?book.n.02_1 ?carryall.n.01_1)
            (inside ?pencil.n.01_1 ?carryall.n.01_1) 
            (inside ?pen.n.01_1 ?carryall.n.01_1) 
            (inside ?calculator.n.02_1 ?carryall.n.01_1) 
            (ontop ?carryall.n.01_1 ?bed.n.01_1)
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `bed.n.01_1` | bed_gxfipj_0 | bed / gxfipj | bedroom_0 | low (0.25-0.6 m), z 0.27 | 2.11 m (range 1.81-2.97) | no (fixed) |
| `pencil.n.01_1` | pencil_213 | pencil / almpve | bedroom_0 | low (0.25-0.6 m), z 0.49 | 1.89 m (range 0.94-3.88) | yes, spread 2.22 m |
| `pen.n.01_1` | pen_212 | pen / enfumt | bedroom_0 | floor, z 0.01 | 1.73 m (range 0.2-3.26) | yes, spread 5.2 m |
| `floor.n.01_1` | floors_htolat_0 | floors / htolat | bedroom_0 | floor, z -0.14 | 1.01 m (range 0.53-1.79) | no (fixed) |
| `calculator.n.02_1` | calculator_211 | calculator / kwmmty | bedroom_0 | floor, z 0.01 | 2.05 m (range 0.12-2.93) | yes, spread 5.4 m |
| `book.n.02_1` | notebook_210 | notebook / aanuhi | bedroom_0 | low (0.25-0.6 m), z 0.5 | 2.25 m (range 0.95-3.09) | yes, spread 2.24 m |
| `folder.n.02_1` | folder_209 | folder / guhatz | bedroom_0 | low (0.25-0.6 m), z 0.5 | 1.99 m (range 1.11-2.67) | yes, spread 1.86 m |
| `table.n.02_1` | nightstand_wbxekb_1 | nightstand / wbxekb | bedroom_0 | floor, z 0.16 | 3.01 m (range 2.59-4.07) | no (fixed) |
| `carryall.n.01_1` | tote_208 | tote / bnkjle | bedroom_0 | floor, z 0.19 | 1.3 m (range 0.88-3.33) | yes, spread 4.6 m |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "bedroom"
 ],
 "house_single_floor": {
  "whitelist": {
   "carryall.n.01": {
    "tote": {
     "bnkjle": null
    }
   },
   "book.n.02": {
    "paperback_book": {
     "xxknda": null
    },
    "notebook": {
     "aanuhi": null
    },
    "hardback": {
     "acbrnv": null
    }
   },
   "calculator.n.02": {
    "calculator": {
     "kwmmty": null
    }
   },
   "folder.n.02": {
    "folder": {
     "guhatz": null
    }
   },
   "marker.n.03": {
    "marker": {
     "ablbdc": [
      0.15,
      0.02,
      0.01
     ]
    }
   },
   "pen.n.01": {
    "pen": {
     "enfumt": [
      0.17,
      0.015,
      0.015
     ]
    }
   },
   "pencil.n.01": {
    "colored_pencil": {
     "bkdqwb": [
      0.15,
      0.015,
      0.015
     ]
    },
    "pencil": {
     "almpve": [
      0.19,
      0.015,
      0.015
     ]
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(inroom bed.n.01_1 bedroom)
(inroom floor.n.01_1 bedroom)
(inroom table.n.02_1 bedroom)
(ontop agent.n.01_1 floor.n.01_1)
(ontop book.n.02_1 bed.n.01_1)
(ontop calculator.n.02_1 floor.n.01_1)
(ontop carryall.n.01_1 floor.n.01_1)
(ontop folder.n.02_1 bed.n.01_1)
(ontop pen.n.01_1 floor.n.01_1)
(ontop pencil.n.01_1 bed.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching bed.n.01_1 book.n.02_1)
(touching bed.n.01_1 folder.n.02_1)
(touching bed.n.01_1 pencil.n.01_1)
(touching book.n.02_1 bed.n.01_1)
(touching calculator.n.02_1 floor.n.01_1)
(touching carryall.n.01_1 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 calculator.n.02_1)
(touching floor.n.01_1 carryall.n.01_1)
(touching floor.n.01_1 pen.n.01_1)
(touching folder.n.02_1 bed.n.01_1)
(touching pen.n.01_1 floor.n.01_1)
(touching pencil.n.01_1 bed.n.01_1)
```

## What the human demos did

200 annotated demos. Length 445.08 s (range 332.23-928.13). Skills per demo 25.0 (range 24-27). 12 distinct skill orders; the most common one covers 44% of demos.

Most common skill counts per demo (44% of demos): move to x11, pick up from x6, place in x5, push to x2, place on x1.

Representative demo `episode_00732350.json` (464.6 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the tote` (0.0-13.0 s)
2. `pick up the tote from the floors` (13.0-28.0 s)
3. `move to the bed` (28.0-32.1 s)
4. `place the tote on the bed` (32.1-45.0 s)
5. `move to the calculator` (45.0-60.0 s)
6. `pick up the calculator from the floors` (60.0-95.0 s)
7. `move to the tote` (95.0-106.8 s)
8. `place the calculator in the tote` (106.8-125.3 s)
9. `move to the pencil` (125.3-136.0 s)
10. `pick up the pencil from the bed` (136.0-150.0 s)
11. `move to the tote` (150.0-160.0 s)
12. `place the pencil in the tote` (160.0-180.6 s)
13. `move to the pen` (180.6-198.0 s)
14. `pick up the pen from the floors` (198.0-225.1 s)
15. `move to the tote` (225.1-250.5 s)
16. `place the pen in the tote` (250.5-262.0 s)
17. `move to the folder` (262.0-279.0 s)
18. `push the folder to the bed` (279.0-312.0 s)
19. `pick up the folder from the bed` (312.0-333.0 s)
20. `move to the tote` (333.0-346.9 s)
21. `place the folder in the tote` (346.9-361.0 s)
22. `move to the notebook` (361.0-378.0 s)
23. `push the notebook to the bed` (378.0-403.4 s)
24. `pick up the notebook from the bed` (403.4-423.2 s)
25. `move to the tote` (423.2-443.0 s)
26. `place the notebook in the tote` (443.0-464.6 s)

Mean duration per skill in this task: move to 16.6 s, pick up from 25.2 s, place in 15.7 s, place on 21.6 s, push to 22.6 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the tote` | 1155 |
| `place the tote on the bed` | 202 |
| `place the folder in the tote` | 201 |
| `pick up the tote from the floors` | 200 |
| `move to the calculator` | 200 |
| `pick up the calculator from the floors` | 200 |
| `place the calculator in the tote` | 200 |
| `pick up the pencil from the bed` | 200 |
| `place the pencil in the tote` | 200 |
| `move to the pen` | 200 |
| `pick up the pen from the floors` | 200 |
| `place the pen in the tote` | 200 |
| `move to the folder` | 200 |
| `push the folder to the bed` | 200 |
| `pick up the folder from the bed` | 200 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/73_organizing_school_stuff.json`. Planner notes: `task_docs/notes/73_organizing_school_stuff.md`.
