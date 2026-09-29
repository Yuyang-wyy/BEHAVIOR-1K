# 62 · Halve An Egg

Task name `halve_an_egg`, task index 62.

> Take the hard-boiled egg from the refrigerator, cut it in half on the cutting board, and leave the egg halves on the plate.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | kitchen |
| rooms loaded | corridor_0, dining_room_0, entryway_0, garden_0, kitchen_0, living_room_0, living_room_1 |
| human demo length | 212.6 s mean (6377 steps) |
| episode time limit | 318.9 s (9565 steps at 30 Hz) |
| human base travel | 14.0643 m |
| goal literals (best ground option) | 5 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://www.youtube.com/embed/c1YJezdD7oM |

## Planner notes

**Tier:** D — one slice transition (knife touches egg) plus four small pick-and-places, one of them from a closed fridge.

### Goal in plain words

The egg must be cut once, so that both `half__hard-boiled_egg` slots are real. Both halves must rest on the one plate (`plate_232`). The carving knife must end inside the drop-in sink. Nothing is said about the fridge, the cutting board, or where the cut happens, so the fridge may stay open and the egg may be cut anywhere.

### Q traps

- All 5 literals start false, so max partial Q is 1.0 (page is right).
- The two `real` literals are free once the egg is cut (2/5 = 0.4). Cutting is the highest-value single action.
- Halves are diceable (PREDICATES §7). If the knife stays in contact with a half for 2 s after the cut, it re-arms and dices that half: its slot goes `None`, losing `real` and `ontop` for it. Lift the knife straight away.
- Any knife contact with the whole egg slices it, including handle contact and contact while the egg is still held (§7). Do not brush the knife against the egg before it is where you want the halves.
- `ontop half plate` needs the half's centre over the plate and touching it. A half resting on the other half, or half off the rim, does not count.
- `inside knife sink` only checks the knife's AABB centre in the sink volume. Whether `drop_in_sink/awvzkn` has a fillable volume at runtime is unverified; demos place it there 200/200, so assume yes.
- The fridge (`fridge_dszchb_0`, one joint) starts closed (joint_pos 0.0 in all 20 instances). It is not in the goal; leaving it open costs nothing.

### Minimal plan

1. `move to the fridge` — fridge door fills the view. ~13 s.
2. `open the door of the fridge` — door visibly swung open, shelves visible. ~27 s.
3. `pick up the hard boiled egg from the fridge` — gripper closed but not fully; egg gone from shelf. ~15 s.
4. Skip `close the door of the fridge` (goal does not need it; saves ~18 s). Close it only if the open door blocks the base path.
5. `move to the carving knife` (or `move to the cutting board`) — board and knife in view. ~13 s.
6. `pick up the carving knife from the cutting board` with the free hand — knife lifted off the board. ~15 s.
7. `place the hard boiled egg on the cutting board` — egg resting on the board, hand open. ~9 s.
   - Shortcut (untested): place the egg on the plate instead, then cut it there; the halves spawn on the plate and steps 10-13 disappear. No trained prompt; closest: `place the half hard boiled egg on the plate`. Only worth it when plate and board are within one arm's reach.
8. `chop the carving knife with the hard boiled egg` — whole egg replaced by two halves in the image. Lift the knife within 2 s. ~7 s.
9. `move to the drop in sink`, then `place the carving knife in the drop in sink` — knife no longer in hand, visible in the basin. ~5 s + ~8 s.
10. `move to the cutting board` — halves in view. ~13 s.
11. `pick up the half hard boiled egg from the cutting board` twice (one per hand) — both grippers closed, board empty. ~15 s each.
12. `move to the plate` — plate in view. ~13 s.
13. `place the half hard boiled egg on the plate` twice — both halves on the plate surface, hands open. ~9 s each.

Total about 190 s against a 319 s limit.

### What the demos do differently

- 197/200 demos close the fridge right after taking the egg. The goal does not need it.
- The egg is held in one hand while the other hand picks the knife; the cut happens with both hands busy, then the egg hand is free again.
- 11 demos push the cutting board along the counter first (`push the cutting board to the countertop`); not needed.
- Halves are picked one per hand, then placed together, so only one trip to the plate.

### Hard parts and hacks

- Egg size: 58 x 44 x 44 mm (asset bbox, scale 1.0). That is at the ~44 mm jaw limit on every axis, so the grasp may not register. Approach along its long axis so the jaws close across the 44 mm width.
- Halves are 58 x 44 x 22 mm. Lying flat, a top-down grasp must straddle the 44 mm width; the 22 mm edge is easier if the half lands on its side.
- Egg shelf height varies: z 0.49 (6 instances), 0.90 (8), 1.30 (6). The top shelf at 1.3 m needs the trunk raised; the bottom one needs a low reach into the fridge.
- The knife (fqqbop) is 323 x 39 x 24 mm, so its handle fits the jaws.
- Knife re-arm dicing is the silent killer: a VLA that keeps "chopping" will destroy the halves. Stop sending the chop prompt as soon as two halves are visible.
- The halves spawn ~11 mm either side of the egg centre (asset `object_parts`). Cutting on the plate would leave them on the plate directly, but the knife may push them off the plate edge.

### Hints for the VLM

- Kitchen of `house_single_floor`. One counter run along the wall at y ≈ -1.9: fridge at the right end (x 7.8), drop-in sink near x 5.8, board and plate between x 4.6 and 7.3 (they move per instance).
- The egg is a small white oval on a fridge shelf. It is the only egg in the scene.
- The cutting board is a light rectangle 36 x 24 cm with the knife lying on it at start.
- The plate is a 25 cm round flat plate; it is the only plate in the kitchen.
- There is only one sink in the kitchen (the drop-in sink). Other sinks exist in other rooms; ignore them.
- Done: two egg halves on the plate, knife in the sink basin, no whole egg anywhere.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(real half__hard-boiled_egg.n.01_1)` | no | yes |
| `(real half__hard-boiled_egg.n.01_2)` | no | yes |
| `(ontop half__hard-boiled_egg.n.01_1 plate.n.04_1)` | no | yes |
| `(ontop half__hard-boiled_egg.n.01_2 plate.n.04_1)` | no | yes |
| `(inside carving_knife.n.01_1 sink.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (real ?half__hard-boiled_egg.n.01_1)
            (real ?half__hard-boiled_egg.n.01_2)
            (ontop ?half__hard-boiled_egg.n.01_1 ?plate.n.04_1)
            (ontop ?half__hard-boiled_egg.n.01_2 ?plate.n.04_1)
            (inside ?carving_knife.n.01_1 ?sink.n.01_1)
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `carving_knife.n.01_1` | carving_knife_234 | carving_knife / fqqbop | kitchen_0 | table/counter (0.6-1.1 m), z 0.93 | 3.34 m (range 0.87-3.97) | yes, spread 2.16 m |
| `chopping_board.n.01_1` | cutting_board_233 | cutting_board / nsvnai | kitchen_0 | table/counter (0.6-1.1 m), z 0.9 | 3.33 m (range 0.88-3.95) | yes, spread 2.11 m |
| `countertop.n.01_1` | countertop_kelzer_0 | countertop / kelzer | kitchen_0 | table/counter (0.6-1.1 m), z 0.87 | 3.32 m (range 1.1-4.43) | no (fixed) |
| `electric_refrigerator.n.01_1` | fridge_dszchb_0 | fridge / dszchb | kitchen_0 | table/counter (0.6-1.1 m), z 0.98 | 3.94 m (range 1.35-4.51) | no (fixed) |
| `sink.n.01_1` | drop_in_sink_awvzkn_0 | drop_in_sink / awvzkn | kitchen_0 | table/counter (0.6-1.1 m), z 0.87 | 3.34 m (range 1.13-4.54) | no (fixed) |
| `plate.n.04_1` | plate_232 | plate / qtfzeq | kitchen_0 | table/counter (0.6-1.1 m), z 0.89 | 3.3 m (range 0.98-4.31) | yes, spread 2.47 m |
| `hard-boiled_egg.n.01_1` | hard_boiled_egg_231 | hard_boiled_egg / xzucin | kitchen_0 | table/counter (0.6-1.1 m), z 0.9 | 3.91 m (range 1.29-4.44) | yes, spread 0.39 m |
| `half__hard-boiled_egg.n.01_1` | does not exist at reset; created by a transition (slicing, cooking, etc.) | half_hard_boiled_egg | - | - | - | - |
| `half__hard-boiled_egg.n.01_2` | does not exist at reset; created by a transition (slicing, cooking, etc.) | half_hard_boiled_egg | - | - | - | - |
| `floor.n.01_1` | floors_kxcpgy_0 | floors / kxcpgy | kitchen_0 | floor, z -0.14 | 2.17 m (range 0.74-2.79) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "kitchen"
 ],
 "house_single_floor": {
  "whitelist": {
   "carving_knife.n.01": {
    "carving_knife": {
     "fqqbop": null
    }
   },
   "chopping_board.n.01": {
    "chopping_board": {
     "afwefw": null
    },
    "cutting_board": {
     "nsvnai": null
    }
   },
   "hard-boiled_egg.n.01": {
    "hard_boiled_egg": {
     "xzucin": null
    }
   },
   "plate.n.04": {
    "plate": {
     "qtfzeq": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(cooked hard-boiled_egg.n.01_1)
(future half__hard-boiled_egg.n.01_1)
(future half__hard-boiled_egg.n.01_2)
(inroom countertop.n.01_1 kitchen)
(inroom electric_refrigerator.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(inroom sink.n.01_1 kitchen)
(inside hard-boiled_egg.n.01_1 electric_refrigerator.n.01_1)
(ontop agent.n.01_1 floor.n.01_1)
(ontop carving_knife.n.01_1 chopping_board.n.01_1)
(ontop chopping_board.n.01_1 countertop.n.01_1)
(ontop plate.n.04_1 countertop.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching carving_knife.n.01_1 chopping_board.n.01_1)
(touching chopping_board.n.01_1 carving_knife.n.01_1)
(touching chopping_board.n.01_1 countertop.n.01_1)
(touching countertop.n.01_1 chopping_board.n.01_1)
(touching countertop.n.01_1 plate.n.04_1)
(touching floor.n.01_1 agent.n.01_1)
(touching plate.n.04_1 countertop.n.01_1)
```

## What the human demos did

200 annotated demos. Length 212.95 s (range 116.37-303.13). Skills per demo 16.0 (range 15-17). 6 distinct skill orders; the most common one covers 90% of demos.

Most common skill counts per demo (90% of demos): move to x5, pick up from x4, place on x3, chop x1, close door x1, open door x1, place in x1.

Representative demo `episode_00622380.json` (211.6 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the fridge` (0.0-20.0 s)
2. `open the door of the fridge` (20.0-47.0 s)
3. `pick up the hard boiled egg from the fridge` (47.0-64.0 s)
4. `close the door of the fridge` (64.0-81.0 s)
5. `move to the carving knife` (81.0-87.0 s)
6. `pick up the carving knife from the cutting board` (87.0-107.0 s)
7. `place the hard boiled egg on the cutting board` (107.0-123.0 s)
8. `chop the carving knife with the hard boiled egg` (123.0-130.2 s)
9. `move to the drop in sink` (130.7-135.4 s)
10. `place the carving knife in the drop in sink` (135.4-145.0 s)
11. `move to the half hard boiled egg` (145.0-155.6 s)
12. `pick up the half hard boiled egg from the cutting board` (155.6-170.1 s)
13. `pick up the half hard boiled egg from the cutting board` (170.1-180.5 s)
14. `move to the plate` (180.5-188.7 s)
15. `place the half hard boiled egg on the plate` (188.7-197.0 s)
16. `place the half hard boiled egg on the plate` (197.0-211.6 s)

Mean duration per skill in this task: chop 7.3 s, close door 18.3 s, move to 12.6 s, open door 26.7 s, pick up from 14.7 s, place in 7.6 s, place on 9.4 s, push to 17.2 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `pick up the half hard boiled egg from the cutting board` | 400 |
| `place the half hard boiled egg on the plate` | 400 |
| `move to the cutting board` | 310 |
| `move to the fridge` | 200 |
| `open the door of the fridge` | 200 |
| `pick up the hard boiled egg from the fridge` | 200 |
| `close the door of the fridge` | 200 |
| `pick up the carving knife from the cutting board` | 200 |
| `place the hard boiled egg on the cutting board` | 200 |
| `chop the carving knife with the hard boiled egg` | 200 |
| `place the carving knife in the drop in sink` | 200 |
| `move to the plate` | 198 |
| `move to the drop in sink` | 196 |
| `move to the half hard boiled egg` | 62 |
| `move to the carving knife` | 30 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/62_halve_an_egg.json`. Planner notes: `task_docs/notes/62_halve_an_egg.md`.
