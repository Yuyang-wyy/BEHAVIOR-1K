# 67 · Boxing Food After Dinner

Task name `boxing_food_after_dinner`, task index 67.

> Pack the food from the plates into the tupperware container, put the container in the refrigerator, and close the refrigerator.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | kitchen |
| rooms loaded | corridor_0, dining_room_0, entryway_0, garden_0, kitchen_0, living_room_0, living_room_1 |
| human demo length | 223.3 s mean (6697 steps) |
| episode time limit | 334.9 s (10046 steps at 30 Hz) |
| human base travel | 16.1108 m |
| goal literals (best ground option) | 6 |
| literals already true at start (inferred) | 1 |
| max Q short of full success | 0.833 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.50; ft40k@local Q=0.50 |
| demo video | https://www.youtube.com/embed/OmpbFiXPwMo |

## Planner notes

**Tier:** C — container-in-container work: tacos are poured from plates into a tupperware, and the tupperware goes into the fridge. The tacos themselves cannot be grasped.

### Goal in plain words

Both tacos end inside the tupperware, and the tupperware ends inside the fridge. Both plates end resting on the kitchen's drop-in sink. The fridge must be closed at the end. The bottom cabinet the tupperware comes from is not in the goal.

### Q traps

- 6 literals. `not open fridge` is true at reset, so it never scores but blocks success. Max partial Q = 5/6 = 0.833.
- Result on 311 (ft40k): Q = 0.50, i.e. 3 of 6.
- **Close the fridge last**, after checking the tupperware is still inside. `inside` tests the AABB centre only; the door can shove the box out when it closes (PREDICATES §3).
- **Plates on the sink:** the sink asset has a faucet (`fluidsource`), and the faucet spout sits ~0.26 m above the basin near the drain.
  - If a plate's centre lies under the faucet, the up-ray hits the sink itself and `ontop` is False (PREDICATES §4, derived). Keep each plate's centre off the drain/spout line.
- **Two plates in one sink:** each plate is 0.35 × 0.41 m and the sink is 0.54 × 0.77 m overall, so the second plate will likely overlap the first.
  - `ontop` needs the plate itself to touch the sink. A plate resting only on the other plate fails (PREDICATES §4). Make sure it also rests on the basin or rim.
- A taco that bounces out of the tupperware during the carry scores 0 for that taco. Carry the tupperware level.

### Minimal plan

1. `move to the bottom cabinet no top` ~9 s.
2. `open the door of the bottom cabinet no top` — the door is open and the tupperware is visible. ~26 s. The cabinet has 4 doors; which one hides the tupperware varies (tupperware x 5.1-6.4).
3. `pick up the tupperware from the bottom cabinet no top` ~9 s.
4. `place the tupperware on the countertop` — next to the plates. ~8 s.
5. Skip `close the door of the bottom cabinet no top`; it is not in the goal. Close it only if it blocks the base.
6. `pick up the plate from the countertop` — lift a plate with its taco. ~9 s.
7. `pour the taco into the plate` (trained wording; it means tipping the plate over the tupperware) — the taco is visibly inside the box. ~6 s.
8. `place the plate on the sink` — the plate lies in or on the sink, off the spout line. ~8 s.
9. `move to the plate`, `pick up the plate from the countertop`, `move to the tupperware`, `pour the taco into the plate`, `place the plate in the sink` — the same steps for plate 2. ~40 s.
10. `move to the tupperware`, `pick up the tupperware from the countertop` ~12 s.
11. `move to the fridge` ~9 s. `open the door of the fridge` — single door. ~26 s.
12. `place the tupperware in the fridge` — the box is on a shelf, fully past the door line. ~9 s.
13. `close the door of the fridge` — the door is flush (within 5 % of closed). ~13 s.

About 200 s against a 335 s limit.

### What the demos do differently

- All demos close the cabinet door after taking the tupperware out (not needed).
- Plates go on the sink right after pouring. The demos place the second plate with `place the plate in the sink`, and both strings appear 200 times each.
- The tacos are never picked by hand; every demo pours from the plate.

### Hard parts and hacks

- **Tacos cannot be grasped:** 0.164 × 0.063 × 0.059 m. Both short axes exceed 44 mm. Pouring from the plate is the only route.
- **Plates:** 0.35 × 0.41 × 0.036 m, lying flat on the counter. A grasp must pinch the rim from the side. That is hard for the VLA; expect regrasps.
- **Tupperware:** 0.22 × 0.22 × 0.14 m, grasped by the wall/rim. It starts at 0.56 m inside a low cabinet (door closed).
- **Fridge:** `fridge_dszchb`, one door, fixed at x 7.82. The plates start on the countertop on both sides of the sink, 1-2 m away.
- Pouring over a 22 cm box from a 41 cm plate: a taco can land on the rim. Check it is below the rim before moving on.

### Hints for the VLM

- Kitchen, house_single_floor. The long countertop (`countertop_kelzer`) holds the sink in its middle and the two plates with tacos, one on each side of the sink (x ~5.1-5.3 and ~7.2-7.3).
- The tupperware is hidden in the low cabinet under that counter. It is not visible until a door opens.
- The fridge stands at the +x end of the same counter run (x 7.8), next to the plate on that side.
- Done: the sink holds two plates; the fridge interior holds the tupperware with two tacos in it; the fridge door is shut.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside taco.n.02_2 tupperware.n.01_1)` | no | yes |
| `(inside taco.n.02_1 tupperware.n.01_1)` | no | yes |
| `(ontop plate.n.04_1 sink.n.01_1)` | no | yes |
| `(ontop plate.n.04_2 sink.n.01_1)` | no | yes |
| `(inside tupperware.n.01_1 electric_refrigerator.n.01_1)` | no | yes |
| `(not open electric_refrigerator.n.01_1))` | yes | never (already true) |

BDDL goal:

```lisp
(:goal
        (and
            (forall
                (?taco.n.02 - taco.n.02)
                (inside ?taco.n.02 ?tupperware.n.01_1)
            )
	    (ontop ?plate.n.04_1 sink.n.01_1)
	    (ontop ?plate.n.04_2 sink.n.01_1)
            (inside ?tupperware.n.01_1 ?electric_refrigerator.n.01_1)
            (not
                (open ?electric_refrigerator.n.01_1)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `countertop.n.01_1` | countertop_kelzer_0 | countertop / kelzer | kitchen_0 | table/counter (0.6-1.1 m), z 0.87 | 2.28 m (range 1.26-4.44) | no (fixed) |
| `sink.n.01_1` | drop_in_sink_awvzkn_0 | drop_in_sink / awvzkn | kitchen_0 | table/counter (0.6-1.1 m), z 0.87 | 2.22 m (range 1.12-4.55) | no (fixed) |
| `cabinet.n.01_1` | bottom_cabinet_no_top_rkgjer_0 | bottom_cabinet_no_top / rkgjer | kitchen_0 | low (0.25-0.6 m), z 0.42 | 2.3 m (range 1.26-4.57) | no (fixed) |
| `electric_refrigerator.n.01_1` | fridge_dszchb_0 | fridge / dszchb | kitchen_0 | table/counter (0.6-1.1 m), z 0.98 | 3.37 m (range 0.93-4.42) | no (fixed) |
| `taco.n.02_1` | taco_235 | taco / werkla | kitchen_0 | table/counter (0.6-1.1 m), z 0.94 | 2.63 m (range 1.34-3.99) | yes, spread 2.18 m |
| `taco.n.02_2` | taco_234 | taco / werkla | kitchen_0 | table/counter (0.6-1.1 m), z 0.94 | 2.66 m (range 0.96-4.71) | yes, spread 2.26 m |
| `plate.n.04_1` | plate_233 | plate / amhlqh | kitchen_0 | table/counter (0.6-1.1 m), z 0.9 | 2.66 m (range 1.33-3.99) | yes, spread 2.16 m |
| `plate.n.04_2` | plate_232 | plate / amhlqh | kitchen_0 | table/counter (0.6-1.1 m), z 0.9 | 2.65 m (range 0.94-4.76) | yes, spread 2.2 m |
| `tupperware.n.01_1` | tupperware_231 | tupperware / mkstwr | kitchen_0 | low (0.25-0.6 m), z 0.56 | 2.14 m (range 1.07-4.85) | yes, spread 1.79 m |
| `floor.n.01_1` | floors_kxcpgy_0 | floors / kxcpgy | kitchen_0 | floor, z -0.14 | 1.52 m (range 1.32-2.8) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "dining_room",
  "kitchen"
 ],
 "house_single_floor": {
  "whitelist": {
   "plate.n.04": {
    "plate": {
     "amhlqh": null
    }
   },
   "taco.n.02": {
    "taco": {
     "werkla": null
    }
   },
   "tupperware.n.01": {
    "tupperware": {
     "mkstwr": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(inroom cabinet.n.01_1 kitchen)
(inroom countertop.n.01_1 kitchen)
(inroom electric_refrigerator.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(inroom sink.n.01_1 kitchen)
(inside tupperware.n.01_1 cabinet.n.01_1)
(ontop agent.n.01_1 floor.n.01_1)
(ontop plate.n.04_1 countertop.n.01_1)
(ontop plate.n.04_2 countertop.n.01_1)
(ontop taco.n.02_1 plate.n.04_1)
(ontop taco.n.02_2 plate.n.04_2)
(touching agent.n.01_1 floor.n.01_1)
(touching countertop.n.01_1 plate.n.04_1)
(touching countertop.n.01_1 plate.n.04_2)
(touching floor.n.01_1 agent.n.01_1)
(touching plate.n.04_1 countertop.n.01_1)
(touching plate.n.04_1 taco.n.02_1)
(touching plate.n.04_2 countertop.n.01_1)
(touching plate.n.04_2 taco.n.02_2)
(touching taco.n.02_1 plate.n.04_1)
(touching taco.n.02_2 plate.n.04_2)
```

## What the human demos did

200 annotated demos. Length 219.28 s (range 162.7-342.1). Skills per demo 22.0 (range 19-24). 20 distinct skill orders; the most common one covers 24% of demos.

Most common skill counts per demo (33% of demos): move to x8, pick up from x4, close door x2, open door x2, place in x2, place on x2, pour x2.

Representative demo `episode_00670750.json` (228.0 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the bottom cabinet no top` (0.0-17.0 s)
2. `open the door of the bottom cabinet no top` (17.0-56.0 s)
3. `pick up the tupperware from the bottom cabinet no top` (56.0-68.0 s)
4. `place the tupperware on the countertop` (68.0-75.5 s)
5. `close the door of the bottom cabinet no top` (75.5-93.0 s)
6. `pick up the plate from the countertop` (93.0-98.9 s)
7. `pour the taco into the plate` (98.9-109.5 s)
8. `place the plate on the sink` (109.5-116.8 s)
9. `move to the plate` (116.8-122.4 s)
10. `pick up the plate from the countertop` (122.4-126.8 s)
11. `move to the tupperware` (126.8-136.3 s)
12. `pour the taco into the plate` (136.3-142.0 s)
13. `place the plate in the sink` (142.0-150.0 s)
14. `move to the tupperware` (150.0-159.0 s)
15. `pick up the tupperware from the countertop` (159.0-162.0 s)
16. `move to the fridge` (162.0-179.0 s)
17. `open the door of the fridge` (179.0-206.0 s)
18. `place the tupperware in the fridge` (206.0-219.0 s)
19. `close the door of the fridge` (219.0-227.0 s)

Mean duration per skill in this task: close door 12.5 s, move to 9.0 s, open door 25.6 s, pick up from 8.6 s, place in 9.4 s, place on 7.5 s, pour 6.3 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the tupperware` | 521 |
| `pick up the plate from the countertop` | 401 |
| `pour the taco into the plate` | 400 |
| `move to the plate` | 297 |
| `close the door of the bottom cabinet no top` | 204 |
| `open the door of the bottom cabinet no top` | 202 |
| `move to the bottom cabinet no top` | 201 |
| `pick up the tupperware from the bottom cabinet no top` | 200 |
| `place the tupperware on the countertop` | 200 |
| `place the plate on the sink` | 200 |
| `place the plate in the sink` | 200 |
| `pick up the tupperware from the countertop` | 200 |
| `move to the fridge` | 200 |
| `open the door of the fridge` | 200 |
| `place the tupperware in the fridge` | 200 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/67_boxing_food_after_dinner.json`. Planner notes: `task_docs/notes/67_boxing_food_after_dinner.md`.
