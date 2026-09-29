# 70 · Thawing Frozen Food

Task name `thawing_frozen_food`, task index 70.

> Take the frozen food from the refrigerator, put it in the microwave, and heat it until it is thawed.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | kitchen |
| rooms loaded | corridor_0, garden_0, kitchen_0, living_room_0 |
| human demo length | 274.3 s mean (8229 steps) |
| episode time limit | 411.5 s (12344 steps at 30 Hz) |
| human base travel | 17.4536 m |
| goal literals (best ground option) | 9 |
| literals already true at start (inferred) | 2 |
| max Q short of full success | 0.778 |
| ground goal options | 4 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.33; ft40k@local Q=0.33 |
| demo video | https://www.youtube.com/embed/FF3HiYSHGdc |

## Planner notes

**Tier:** D — a thaw state change via a running microwave, on top of two plate pick-and-places out of a French-door fridge.

### Goal in plain words

- The chicken breast must be not frozen, lying on a plate that is inside the closed microwave, with the microwave on.
- The bread slice must be not frozen, lying on the other plate, which rests on the bar (`bar_byvbuc_0`, the counter carrying the microwave and the cooktop).
- The fridge must be closed at the end.
- Either plate can serve either food (4 ground options), but each food starts on its own plate, so carry each plate with its food.

### Q traps

- 9 literals. `not open microwave` and `not open fridge` are true at reset, so they never score; max partial Q = 7/9 = 0.778.
- Result on 311 (ft40k): Q = 0.33, i.e. 3 of 7 scorable.
- **Thawing is nearly free** (PREDICATES §16):
  - At reset the foods are at -44 to -10 °C, depending on the instance, and the plates are at -2 °C.
  - Once the fridge door is open, the fridge stops cooling. At room temperature a food passes 0 °C in ~18-55 s (derived from §2).
  - So the bread thaws on the bar on its own. The chicken thaws in ~4 s once the microwave runs.
- `frozen` is not latched. A food put back in a closed fridge refreezes.
- **Microwave order:** plate in → door fully closed → press. It is a `requires_closed` toggleable, so a press with the door open does nothing, and opening the door later turns it off (§11).
- **Bread plate location:** the bar top is crowded.
  - The microwave takes x 5.86-6.38; the cooktop `burner_mdanhg` takes x ~6.5-7.3; the bar runs x 5.67-7.83.
  - A plate on the cooktop touches the burner, not the bar, so `ontop plate bar` is False (§4, derived).
  - The clear stretch is x ~7.3-7.8, past the cooktop.
- A second bar (`bar_egwapq_0`, at x 7.8-8.5 forming an L) is a distractor. A plate on it does not count.

### Minimal plan

1. `move to the fridge` ~12 s.
2. `open the door of the fridge` — it has two doors (French). Open the side the plates are behind; both start closed. ~30 s.
3. `pick up the plate from the fridge` — take the plate with the bread slice first. Shelf order varies: in 9/20 instances the bread is on the higher shelf. The plates sit at 0.72, 0.98, 1.22, 1.33 or 1.67 m. ~24 s.
4. `move to the bar`, `place the plate on the bar` — on the clear end past the cooktop. ~12 + 11 s.
5. `move to the fridge`, `pick up the plate from the fridge` — the plate with the chicken. ~12 + 24 s.
6. `close the door of the fridge` ~16 s (with the other hand, or after `hand over the plate` ~13 s).
7. `move to the microwave` ~12 s. `open the door of the microwave` ~30 s.
8. `place the plate in the microwave` — plate flat inside, chicken still on it. ~15 s.
9. `close the door of the microwave` — the door is flush. ~16 s.
10. `turn on the microwave` — the button marker turns green. ~10 s.

About 230 s against a 411 s limit.

### What the demos do differently

- 100/200 carry the bread plate first, then hold the chicken plate while closing the fridge, using `hand over the plate` twice to free a hand.
- 82/200 close and reopen the fridge between the two plates. This is not needed.
- All 200 thaw the bread by leaving it out; none microwave it.

### Hard parts and hacks

- **Plates:** forced to 0.248 × 0.248 × 0.016 m, lying flat on fridge shelves at 0.72-1.67 m. The grasp must pinch the 16 mm rim from the side. In 10/20 instances one plate is on the 1.67 m shelf.
- Food slides: the chicken (0.135 × 0.105 × 0.04 m) and the bread (0.15 × 0.15 × 0.02 m) sit loose on the plates. Tilting the plate drops them, and the `ontop food plate` literals are lost.
- **Microwave:** outer box 0.34 deep × 0.52 wide × 0.26 m high (`microwave_hjjxmi`), on the bar top at ~0.88 m. The plate just fits; all 200 demos do it.
  - Button: a ~21 mm sphere on the front panel, beside the door.
- Hack for the bread: opening the fridge alone thaws everything within a minute. Its bread literals then only need the plate on the bar.

### Hints for the VLM

- Kitchen, house_double_floor_lower. The fridge is a tall two-door unit (`fridge_petcxr`, x 5.2). The bar continues on its +x side, which is on the left when facing the fridge front: first the microwave, then a cooktop under a range hood, then free counter.
- Frozen food looks no different from thawed food in RGB. Rely on time out of the fridge, not appearance.
- Done: microwave closed with the chicken plate inside and its marker green; bread plate on the free bar end; fridge doors shut.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(not frozen chicken_breast.n.02_1))` | no | yes |
| `(ontop chicken_breast.n.02_1 plate.n.04_2)` | no | yes |
| `(inside plate.n.04_2 microwave.n.02_1)` | no | yes |
| `(toggled_on microwave.n.02_1)` | no | yes |
| `(not open microwave.n.02_1))` | yes | never (already true) |
| `(not open electric_refrigerator.n.01_1))` | yes | never (already true) |
| `(not frozen bread_slice.n.01_1))` | no | yes |
| `(ontop bread_slice.n.01_1 plate.n.04_1)` | no | yes |
| `(ontop plate.n.04_1 countertop.n.01_1)` | no | yes |

The goal has 4 ground options (9 literals x4); Q takes the best one, so any valid choice of container or partner object counts.

BDDL goal:

```lisp
(:goal
        (and
            (not
                (frozen chicken_breast.n.02_1)
            )
            (exists
                (?plate.n.04 - plate.n.04)
                (and
                    (ontop chicken_breast.n.02_1 ?plate.n.04)
                    (inside ?plate.n.04 microwave.n.02_1)
                )
            )
            (toggled_on microwave.n.02_1)
            (not
                (open microwave.n.02_1)
            )
            (not
                (open electric_refrigerator.n.01_1)
            )
            (not
                (frozen bread_slice.n.01_1)
            )
            (exists
                (?plate.n.04 - plate.n.04)
                (and
                    (ontop bread_slice.n.01_1 ?plate.n.04)
                    (ontop ?plate.n.04 countertop.n.01_1)
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
| `chicken_breast.n.02_1` | chicken_breast_81 | chicken_breast / iuuyre | kitchen_0 | high (1.1-1.6 m), z 1.33 | 2.59 m (range 1.24-4.34) | yes, spread 0.67 m |
| `bread_slice.n.01_1` | bread_slice_80 | bread_slice / pfggnm | kitchen_0 | high (1.1-1.6 m), z 1.22 | 2.48 m (range 1.03-4.43) | yes, spread 0.64 m |
| `plate.n.04_1` | plate_79 | plate / kkmkbd | kitchen_0 | high (1.1-1.6 m), z 1.32 | 2.6 m (range 1.23-4.34) | yes, spread 0.64 m |
| `plate.n.04_2` | plate_78 | plate / kkmkbd | kitchen_0 | high (1.1-1.6 m), z 1.21 | 2.48 m (range 1.03-4.43) | yes, spread 0.63 m |
| `microwave.n.02_1` | microwave_hjjxmi_0 | microwave / hjjxmi | kitchen_0 | table/counter (0.6-1.1 m), z 1.01 | 2.23 m (range 1.32-5.46) | no (fixed) |
| `countertop.n.01_1` | bar_byvbuc_0 | bar / byvbuc | kitchen_0 | low (0.25-0.6 m), z 0.4 | 2.2 m (range 1.24-5.96) | no (fixed) |
| `electric_refrigerator.n.01_1` | fridge_petcxr_0 | fridge / petcxr | kitchen_0 | table/counter (0.6-1.1 m), z 0.96 | 2.49 m (range 1.33-4.69) | no (fixed) |
| `floor.n.01_1` | floors_zqjkvm_0 | floors / zqjkvm | kitchen_0 | floor, z -0.15 | 1.97 m (range 1.1-3.35) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "kitchen"
 ],
 "house_double_floor_lower": {
  "whitelist": {
   "bread_slice.n.01": {
    "bread_slice": {
     "pfggnm": null
    }
   },
   "chicken_breast.n.02": {
    "chicken_breast": {
     "iuuyre": [
      0.135,
      0.105,
      0.04
     ]
    }
   },
   "plate.n.04": {
    "plate": {
     "kkmkbd": [
      0.248,
      0.248,
      0.016
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
(frozen bread_slice.n.01_1)
(frozen chicken_breast.n.02_1)
(inroom countertop.n.01_1 kitchen)
(inroom electric_refrigerator.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(inroom microwave.n.02_1 kitchen)
(inside plate.n.04_1 electric_refrigerator.n.01_1)
(inside plate.n.04_2 electric_refrigerator.n.01_1)
(ontop agent.n.01_1 floor.n.01_1)
(ontop bread_slice.n.01_1 plate.n.04_2)
(ontop chicken_breast.n.02_1 plate.n.04_1)
(touching agent.n.01_1 floor.n.01_1)
(touching bread_slice.n.01_1 plate.n.04_2)
(touching chicken_breast.n.02_1 plate.n.04_1)
(touching floor.n.01_1 agent.n.01_1)
(touching plate.n.04_1 chicken_breast.n.02_1)
(touching plate.n.04_2 bread_slice.n.01_1)
```

## What the human demos did

200 annotated demos. Length 259.83 s (range 178.57-530.67). Skills per demo 15.0 (range 15-19). 17 distinct skill orders; the most common one covers 50% of demos.

Most common skill counts per demo (52% of demos): move to x4, close door x2, hand over x2, open door x2, pick up from x2, place in x1, place on x1, turn on switch x1.

Representative demo `episode_00702220.json` (226.7 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the fridge` (0.0-12.0 s)
2. `open the door of the fridge` (12.0-47.3 s)
3. `pick up the plate from the fridge` (47.3-62.0 s)
4. `move to the bar` (62.0-66.0 s)
5. `place the plate on the bar` (66.0-75.0 s)
6. `move to the fridge` (75.0-88.4 s)
7. `pick up the plate from the fridge` (88.4-114.0 s)
8. `hand over the plate` (114.0-134.0 s)
9. `close the door of the fridge` (134.0-157.0 s)
10. `move to the microwave` (157.0-161.0 s)
11. `open the door of the microwave` (161.0-183.9 s)
12. `hand over the plate` (183.9-197.8 s)
13. `place the plate in the microwave` (197.8-211.0 s)
14. `close the door of the microwave` (211.0-219.0 s)
15. `turn on the microwave` (219.0-226.0 s)

Mean duration per skill in this task: close door 15.5 s, hand over 12.5 s, move to 12.1 s, open door 30.1 s, pick up from 24.1 s, place in 15.2 s, place on 11.4 s, push to 18.0 s, turn on switch 9.6 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `hand over the plate` | 447 |
| `pick up the plate from the fridge` | 400 |
| `move to the fridge` | 398 |
| `open the door of the fridge` | 295 |
| `close the door of the fridge` | 292 |
| `move to the bar` | 200 |
| `move to the microwave` | 200 |
| `open the door of the microwave` | 200 |
| `place the plate in the microwave` | 200 |
| `close the door of the microwave` | 200 |
| `turn on the microwave` | 200 |
| `place the plate on the bar` | 192 |
| `place the plate in the bar` | 7 |
| `move to the plate` | 2 |
| `place the plate on the countertop` | 1 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/70_thawing_frozen_food.json`. Planner notes: `task_docs/notes/70_thawing_frozen_food.md`.
