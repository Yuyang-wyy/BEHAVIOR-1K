# 76 · Dispose Of Glass

Task name `dispose_of_glass`, task index 76.

> Pick up the water glasses and put them into the trash can.

## At a glance

| item | value |
| --- | --- |
| scene | `hotel_suite_large` |
| rooms in the goal | bathroom, bedroom |
| rooms loaded | bathroom_0, bedroom_0 |
| human demo length | 306.5 s mean (9195 steps) |
| episode time limit | 459.8 s (13792 steps at 30 Hz) |
| human base travel | 18.1259 m |
| goal literals (best ground option) | 4 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | not evaluated yet |
| demo video | https://www.youtube.com/embed/dzVB9aAmnNU |

## Planner notes

**Tier:** C — four glasses whose 82 mm bodies are about twice the 44 mm jaw span; only a rim-wall grasp can work.

### Goal in plain words

All four water glasses must end inside the trash can. The glasses start on the bathroom vanity (the wall-mounted sink unit), and the trash can starts somewhere in bedroom_0. Where the trash can ends up does not matter, so it may be moved.

### Q traps

- 4 literals, all false at reset. Each glass is worth 0.25.
- Not yet evaluated closed-loop.
- `inside` tests the glass's AABB centre against the can's volume (PREDICATES §3). A glass balanced on the rim, or leaning out with its centre above the rim, fails.
- The can is open-topped: `trash_can_cjmezk` has no lid link. Nothing needs opening or closing.
- If the can is knocked over while being moved, glasses already inside can fall out. Move the can first, before any glass goes in (as the demos do).

### Minimal plan

1. `move to the trash can`, `pick up the trash can from the floors` — lift it by the rim. ~16 + 20 s.
2. `move to the floors`, `place the trash can on the floors` — set it down in the bathroom next to the vanity. ~16 + 24 s. This saves three round trips of 2-9 m.
3. `move to the water glass`, `pick up the water glass from the countertop` ~16 + 20 s.
4. `move to the water glass`, `pick up the water glass from the countertop` — second hand. ~16 + 20 s.
5. `move to the trash can`, `place the water glass in the trash can` ×2 — each glass drops below the rim. ~16 + 2 × 17 s.
6. Repeat steps 3-5 for the last two glasses. Use `pick up the water glass from the wall mounted sink` if a glass stands in or at the basin.

Demo mean 307 s against a 460 s limit.

### What the demos do differently

- All 200 carry the trash can into the bathroom first. That is not required, but it is sensible: the can starts 1.9-8.6 m from the robot.
- They carry two glasses per trip.
- The demo labels say "from the countertop" (684 segments) and "from the wall mounted sink" (116) for the same vanity. Both strings are trained.

### Hard parts and hacks

- **Glass grasp:** `water_glass_evaida` is 0.082 × 0.082 × 0.155 m, and the body does not fit the 44 mm span. A grasp must pinch the rim wall, one finger inside and one outside.
  - That is the whole difficulty of the task. It is not verified that the assisted-grasp ray registers on a thin wall.
- Glasses stand 0.87-0.90 m high along the 2.6 m vanity (x ~1.9-2.1, y 2.5-4.8). In half the instances the closest pair has centres only 9-15 cm apart, a gap of 1-7 cm. A finger going outside the rim can hit the neighbour; knocking one over makes it harder to grasp.
- **Trash can:** 0.38 × 0.38 × 0.42 m. Carrying it needs a rim pinch too; if that fails, carry glasses to the can instead.
- Dropping a glass from 0.3 m above the can is fine: there is no breakage in sim. Aim the drop over the can's centre.

### Hints for the VLM

- hotel_suite_large. The robot starts in bathroom_0; the vanity is the long wall-mounted sink counter with four identical tumblers standing on it.
- The trash can is the only bin, standing on the bedroom_0 floor. No door had to be opened in any demo.
- Done: four glasses visible inside the can, none on the rim or the floor.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside water_glass.n.02_4 ashcan.n.01_1)` | no | yes |
| `(inside water_glass.n.02_1 ashcan.n.01_1)` | no | yes |
| `(inside water_glass.n.02_3 ashcan.n.01_1)` | no | yes |
| `(inside water_glass.n.02_2 ashcan.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (forall
                (?water_glass.n.02 - water_glass.n.02)
                (inside ?water_glass.n.02 ?ashcan.n.01_1)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `water_glass.n.02_1` | water_glass_68 | water_glass / evaida | bathroom_0 | table/counter (0.6-1.1 m), z 0.87 | 2.74 m (range 0.91-3.66) | yes, spread 2.42 m |
| `water_glass.n.02_2` | water_glass_67 | water_glass / evaida | bathroom_0 | table/counter (0.6-1.1 m), z 0.87 | 2.86 m (range 0.95-3.66) | yes, spread 2.31 m |
| `water_glass.n.02_3` | water_glass_66 | water_glass / evaida | bathroom_0 | table/counter (0.6-1.1 m), z 0.87 | 2.76 m (range 0.84-3.74) | yes, spread 2.35 m |
| `water_glass.n.02_4` | water_glass_65 | water_glass / evaida | bathroom_0 | table/counter (0.6-1.1 m), z 0.87 | 2.71 m (range 1.05-3.86) | yes, spread 2.28 m |
| `ashcan.n.01_1` | trash_can_64 | trash_can / cjmezk | bedroom_0 | floor, z 0.19 | 6.07 m (range 1.86-8.63) | yes, spread 7.43 m |
| `floor.n.01_1` | floors_kudtlk_0 | floors / kudtlk | bathroom_0 | floor, z -0.14 | 0.98 m (range 0.24-1.79) | no (fixed) |
| `floor.n.01_2` | floors_nwjrkc_0 | floors / nwjrkc | bedroom_0 | floor, z -0.14 | 5.56 m (range 4.96-6.24) | no (fixed) |
| `sink.n.01_1` | wall_mounted_sink_jbborl_0 | wall_mounted_sink / jbborl | bathroom_0 | table/counter (0.6-1.1 m), z 0.71 | 2.8 m (range 0.93-3.57) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "bathroom",
  "bedroom"
 ],
 "hotel_suite_large": {
  "whitelist": {
   "ashcan.n.01": {
    "trash_can": {
     "cjmezk": null
    }
   },
   "water_glass.n.02": {
    "water_glass": {
     "evaida": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(inroom floor.n.01_1 bathroom)
(inroom floor.n.01_2 bedroom)
(inroom sink.n.01_1 bathroom)
(ontop agent.n.01_1 floor.n.01_1)
(ontop ashcan.n.01_1 floor.n.01_2)
(ontop water_glass.n.02_1 sink.n.01_1)
(ontop water_glass.n.02_2 sink.n.01_1)
(ontop water_glass.n.02_3 sink.n.01_1)
(ontop water_glass.n.02_4 sink.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching ashcan.n.01_1 floor.n.01_2)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_2 ashcan.n.01_1)
(touching sink.n.01_1 water_glass.n.02_1)
(touching sink.n.01_1 water_glass.n.02_2)
(touching sink.n.01_1 water_glass.n.02_3)
(touching sink.n.01_1 water_glass.n.02_4)
(touching water_glass.n.02_1 sink.n.01_1)
(touching water_glass.n.02_2 sink.n.01_1)
(touching water_glass.n.02_3 sink.n.01_1)
(touching water_glass.n.02_4 sink.n.01_1)
```

## What the human demos did

200 annotated demos. Length 297.27 s (range 193.57-473.17). Skills per demo 17.0 (range 16-19). 6 distinct skill orders; the most common one covers 41% of demos.

Most common skill counts per demo (50% of demos): move to x7, pick up from x5, place in x4, place on x1.

Representative demo `episode_00760590.json` (298.1 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the trash can` (0.0-19.0 s)
2. `pick up the trash can from the floors` (19.0-42.0 s)
3. `move to the floors` (42.0-62.0 s)
4. `place the trash can on the floors` (62.0-83.0 s)
5. `move to the water glass` (83.0-100.9 s)
6. `pick up the water glass from the countertop` (100.9-117.0 s)
7. `move to the water glass` (117.0-128.6 s)
8. `pick up the water glass from the countertop` (128.6-143.0 s)
9. `move to the trash can` (143.0-154.0 s)
10. `place the water glass in the trash can` (154.0-170.0 s)
11. `place the water glass in the trash can` (170.0-188.0 s)
12. `move to the water glass` (188.0-199.0 s)
13. `pick up the water glass from the wall mounted sink` (199.0-223.0 s)
14. `move to the water glass` (223.0-241.8 s)
15. `pick up the water glass from the countertop` (241.8-254.0 s)
16. `move to the trash can` (254.0-267.0 s)
17. `place the water glass in the trash can` (267.0-281.0 s)
18. `place the water glass in the trash can` (281.0-298.0 s)

Mean duration per skill in this task: move to 15.5 s, pick up from 19.7 s, place in 17.4 s, place on 23.6 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `place the water glass in the trash can` | 801 |
| `pick up the water glass from the countertop` | 684 |
| `move to the water glass` | 665 |
| `move to the trash can` | 601 |
| `pick up the trash can from the floors` | 200 |
| `move to the floors` | 200 |
| `place the trash can on the floors` | 200 |
| `pick up the water glass from the wall mounted sink` | 116 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/76_dispose_of_glass.json`. Planner notes: `task_docs/notes/76_dispose_of_glass.md`.
