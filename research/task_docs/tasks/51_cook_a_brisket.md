# 51 · Cook A Brisket

Task name `cook_a_brisket`, task index 51.

> Take the brisket from the refrigerator, cook it in a frying pan on the burner, and place the cooked brisket on the chopping board.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | kitchen |
| rooms loaded | corridor_0, garden_0, kitchen_0, living_room_0 |
| human demo length | 244.5 s mean (7334 steps) |
| episode time limit | 366.7 s (11002 steps at 30 Hz) |
| human base travel | 14.2032 m |
| goal literals (best ground option) | 3 |
| literals already true at start (inferred) | 1 |
| max Q short of full success | 0.667 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://www.youtube.com/embed/RCSy8B0_s5Y |

## Planner notes

**Tier:** D — heat one brisket to 63 °C, then place it on a board. The pan literal is already true and only has to be kept.

### Goal in plain words

The brisket must be `cooked`, meaning `MaxTemperature` of at least 63 °C (brisket `cook_temperature`, §15; latched). It must end resting on the chopping board `chopping_board_80`. The frying pan must still be on `bar_egwapq_0` (the BDDL `countertop`) at the end. **Heat source:** any active one works; the goal does not name one. There are three in the scene:

- the burner `burner_mdanhg_0` (1980 °C, within 0.2 m of its working point);
- the microwave `microwave_hjjxmi_0` (closed, on, brisket inside);
- the oven `oven_ffitak_0` (closed including racks, on, brisket inside).

**Container:** none is needed. The pan is optional, because heat does not pass through it (§2).

### Q traps

- 3 literals. `ontop frying_pan countertop` is true at start, so it never scores. Max partial Q is 2/3 = 0.667 (page is right).
- **Two bars.** The BDDL `countertop` is `bar_egwapq_0`, the counter along the x ≈ 8.2 wall with the sink, where the pan and board start. The cooktop is on the other counter, `bar_byvbuc_0`, which the prompts also call "bar". If the pan is used, it must go back onto `bar_egwapq_0`, not onto the cooktop counter. Otherwise success is lost.
- **Simplest: do not touch the pan at all.** Cook the brisket without it and the pan literal stays true.
- `ontop brisket board` needs the brisket's centre over the board and touching it (§4). A brisket resting half on the pan rim or on the bar fails.
- Brisket starts at -2.2 °C. The microwave takes about 11 s to reach 63 °C (derived from §2: T_ss ≈ 87 °C, time constant 8.3 s). A burner takes well under 1 s.

### Minimal plan

This is the microwave route. It is derived, and it keeps the pan untouched.

1. `move to the fridge`, `open the door of the fridge` — ~12 s + ~39 s. The fridge has two doors, so open the one in front of the brisket.
2. `pick up the brisket from the fridge` — ~20 s. The fridge is not in the goal, so leave it open.
3. `move to the microwave`, then `open the door of the microwave`, then place the brisket in it. There is no trained prompt for this task; closest: `place the popcorn bag in the microwave` (make_microwave_popcorn). Then `close the door of the microwave` and `turn on the microwave`, and wait about 12 s. Times: ~12 + 17 + 14 + 8 + 9 s.
4. `open the door of the microwave`, pick the brisket out — ~17 + 20 s.
5. `move to the chopping board`, then place the brisket on the board. No trained prompt; closest: `place the brisket in the frying pan`. ~12 + 10 s.

The plan takes about 230 s against a 367 s limit.

Demo route (in distribution; the pan must be returned to the right bar):
1. `move to the frying pan`, `pick up the frying pan from the bar`.
2. `move to the burner`, `place the frying pan on the burner`.
3. `move to the fridge`, `open the door of the fridge`, `pick up the brisket from the fridge`, `close the door of the fridge`.
4. `move to the frying pan`, `place the brisket in the frying pan`, `turn on the burner`.
5. `pick up the frying pan from the burner`, `move to the chopping board`, `pour the brisket into the frying pan` (sic; pan onto board).
6. `place the frying pan on the bar`, on `bar_egwapq_0`.

Mean total about 240 s.

### What the demos do differently

- All 200 use the pan on the burner. They turn the burner on and off within about 10 s, then tip the brisket from the pan onto the board.
- 136 demos pass the brisket between hands (`hand over the brisket`) to free a hand for the fridge door. 30 demos push the brisket (`push the brisket to the fridge`).
- `turn off the burner` is not needed for the goal.

### Hard parts and hacks

- **Brisket grasp.** The brisket is forced to 150 x 100 x 20 mm (`task_custom_lists.json`) and lies flat. The 20 mm thickness can only be straddled from the side, so a top-down grasp does not fit the 44 mm span. Shelf height varies from z 0.72 to 1.67. The ft40k checkpoint scored 0 on instance 311. The demos' pour from the pan onto the board sidesteps the second grasp. The pan (`jpzusm`, 465 x 286 x 57 mm) has a handle.
- **Burner route caveat.** `burner_mdanhg` has 5 heat points and 5 knobs, and only the first of each works (`link_based_state_mixin.py:90`). Which one is first is not verified.
- **Microwave.** It sits right next to the fridge (x 6.12 against 5.2) at z 1.01, so it is the shortest heat source from the fridge. The door must be flush before pressing (§11).
- The oven works too, but it is low (root at z 0.54). All 3 of its joints count for "open" (no `openable_joint_ids`). Avoid it.

### Hints for the VLM

- Kitchen of `house_double_floor_lower`. The two-door fridge is at (5.2, -0.57). Along the y ≈ -0.7 wall come the microwave (6.1) and the cooktop over the oven (6.9) on `bar_byvbuc_0`. The pan and the chopping board are on `bar_egwapq_0` along the x ≈ 8.2 wall, next to the sink.
- The brisket is a flat brown slab on a fridge shelf. The board is a light wooden rectangle, 25 x 37 cm.
- Done: the brisket lies on the board, the pan is still on the sink-side bar, and the brisket was hot at some point. The episode ends by itself on success.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(cooked brisket.n.01_1)` | no | yes |
| `(ontop brisket.n.01_1 chopping_board.n.01_1)` | no | yes |
| `(ontop frying_pan.n.01_1 countertop.n.01_1)` | yes | never (already true) |

BDDL goal:

```lisp
(:goal 
        (and 
            (cooked ?brisket.n.01_1) 
            (ontop ?brisket.n.01_1 ?chopping_board.n.01_1)
            (ontop ?frying_pan.n.01_1 ?countertop.n.01_1)
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `chopping_board.n.01_1` | chopping_board_80 | chopping_board / afwefw | kitchen_0 | table/counter (0.6-1.1 m), z 0.9 | 3.02 m (range 1.35-5.82) | yes, spread 2.08 m |
| `brisket.n.01_1` | brisket_79 | brisket / nnnnqw | kitchen_0 | high (1.1-1.6 m), z 1.15 | 3.41 m (range 1.98-3.88) | yes, spread 0.78 m |
| `frying_pan.n.01_1` | frying_pan_78 | frying_pan / jpzusm | kitchen_0 | table/counter (0.6-1.1 m), z 0.91 | 4.11 m (range 1.32-6.33) | yes, spread 2.04 m |
| `countertop.n.01_1` | bar_egwapq_0 | bar / egwapq | kitchen_0 | low (0.25-0.6 m), z 0.45 | 3.57 m (range 2.17-6.13) | no (fixed) |
| `electric_refrigerator.n.01_1` | fridge_petcxr_0 | fridge / petcxr | kitchen_0 | table/counter (0.6-1.1 m), z 0.96 | 3.54 m (range 2.0-4.21) | no (fixed) |
| `oven.n.01_1` | oven_ffitak_0 | oven / ffitak | kitchen_0 | low (0.25-0.6 m), z 0.54 | 3.51 m (range 2.27-5.49) | no (fixed) |
| `floor.n.01_1` | floors_zqjkvm_0 | floors / zqjkvm | kitchen_0 | floor, z -0.15 | 2.08 m (range 0.99-3.05) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "kitchen"
 ],
 "house_double_floor_lower": {
  "whitelist": {
   "brisket.n.01": {
    "brisket": {
     "nnnnqw": [
      0.15,
      0.1,
      0.02
     ]
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
   "frying_pan.n.01": {
    "frying_pan": {
     "jpzusm": null
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
(inroom electric_refrigerator.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(inroom oven.n.01_1 kitchen)
(inside brisket.n.01_1 electric_refrigerator.n.01_1)
(ontop agent.n.01_1 floor.n.01_1)
(ontop chopping_board.n.01_1 countertop.n.01_1)
(ontop frying_pan.n.01_1 countertop.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching chopping_board.n.01_1 countertop.n.01_1)
(touching countertop.n.01_1 chopping_board.n.01_1)
(touching countertop.n.01_1 frying_pan.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching frying_pan.n.01_1 countertop.n.01_1)
```

## What the human demos did

200 annotated demos. Length 242.32 s (range 134.07-355.2). Skills per demo 17.0 (range 6-19). 16 distinct skill orders; the most common one covers 50% of demos.

Most common skill counts per demo (50% of demos): move to x5, pick up from x3, place on x2, close door x1, hand over x1, open door x1, place in x1, pour x1, turn off switch x1, turn on switch x1.

Representative demo `episode_00511640.json` (252.0 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the frying pan` (0.0-12.0 s)
2. `pick up the frying pan from the bar` (12.0-33.0 s)
3. `move to the burner` (33.0-38.0 s)
4. `place the frying pan on the burner` (38.0-51.0 s)
5. `move to the fridge` (51.0-71.0 s)
6. `open the door of the fridge` (71.0-113.1 s)
7. `pick up the brisket from the fridge` (113.1-131.0 s)
8. `hand over the brisket` (131.0-146.0 s)
9. `close the door of the fridge` (146.0-169.0 s)
10. `move to the frying pan` (169.0-178.0 s)
11. `place the brisket in the frying pan` (178.0-187.0 s)
12. `turn on the burner` (187.0-198.8 s)
13. `turn off the burner` (198.8-203.0 s)
14. `pick up the frying pan from the burner` (203.0-219.0 s)
15. `move to the chopping board` (219.0-230.0 s)
16. `pour the brisket into the frying pan` (230.0-235.1 s)
17. `place the frying pan on the bar` (235.1-251.0 s)

Mean duration per skill in this task: close door 20.1 s, hand over 13.4 s, move to 11.8 s, open door 39.2 s, pick up from 20.1 s, place in 10.3 s, place on 9.8 s, pour 7.3 s, push to 28.9 s, turn off switch 3.9 s, turn on switch 8.5 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the burner` | 313 |
| `move to the frying pan` | 276 |
| `turn on the burner` | 200 |
| `turn off the burner` | 200 |
| `pick up the frying pan from the burner` | 200 |
| `move to the chopping board` | 200 |
| `pour the brisket into the frying pan` | 200 |
| `move to the fridge` | 199 |
| `pick up the brisket from the fridge` | 199 |
| `place the brisket in the frying pan` | 199 |
| `open the door of the fridge` | 198 |
| `close the door of the fridge` | 198 |
| `place the frying pan on the bar` | 198 |
| `pick up the frying pan from the bar` | 197 |
| `place the frying pan on the burner` | 197 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/51_cook_a_brisket.json`. Planner notes: `task_docs/notes/51_cook_a_brisket.md`.
