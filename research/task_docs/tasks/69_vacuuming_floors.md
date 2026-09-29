# 69 · Vacuuming Floors

Task name `vacuuming_floors`, task index 69.

> Use the vacuum to clean the dirty floor until the floor is no longer covered in dirt.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_upper` |
| rooms in the goal | bedroom |
| rooms loaded | bedroom_0, bedroom_1, bedroom_2, living_room_0 |
| human demo length | 80.4 s mean (2411 steps) |
| episode time limit | 120.6 s (3617 steps at 30 Hz) |
| human base travel | 4.9572 m |
| goal literals (best ground option) | 1 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.00; ft24k@sulab1 Q=0.00; ft40k@sulab1 Q=0.00; ft40k@local Q=0.00; ft10k@sulab1 Q=0.00 |
| demo video | https://www.youtube.com/embed/RqYuT-aj21A |

## Planner notes

**Tier:** D — a cleaning state change done with a tool. The upright vacuum has to be held, switched on with a tiny button, and driven over every dust speck, all within 120 s.

### Goal in plain words

The bedroom_0 floor must carry zero dust particles at the end. Only the vacuum can remove them, and only while it is toggled on. Where the vacuum ends up does not matter.

### Q traps

- A single literal, so Q is 0 or 1. **One missed speck gives Q = 0** (PREDICATES §12, visual threshold 1).
- Dust count per public instance (`dust.n.01_1.n_particles` in each `-tro_state.json`): 2 to 11, median 6. Instance 311 has 4 and 315 has 2.
  - The specks lie on the open floor at x -6.0 to -2.9, y 0.3 to 3.1. None fall under the bed, desk, nightstand, taboret or floor lamp footprints, all 20 instances checked against those AABBs.
  - The farthest speck is 0.7-2.4 m from the robot start.
- The vacuum only removes dust while `toggled_on` (remover condition `dust: toggled_on`, runtime KB). A second touch on the button turns it off again (PREDICATES §11).
- Result on 311: Q = 0.00 for all five checkpoints tried (zs_pt50, ft10k, ft24k, ft40k ×2).

### Minimal plan

1. `move to the vacuum` ~8 s. The vacuum starts 0.7-2.7 m away, upright, and off.
2. `pick up the vacuum from the floors` — gripper closed on the handle, and the vacuum still upright with its head on the floor. ~13 s.
3. `turn on the vacuum` — the toggle marker at the top of the handle turns from red to green. ~8 s.
4. `move to the dirt`, `sweep the dirt` — repeat until no specks are visible. ~8 s + ~4 s per pass. Demos use 2-7 passes, 3 is most common.
5. Skip `place the vacuum on the floors`: success ends the episode as soon as the last speck is gone.

About 60-80 s against a **120.6 s limit**. There is no slack for a failed grasp or a second button press.

### What the demos do differently

- 51/200 demos log a `sweep the vacuum` segment. The string is odd but trained.
- All 200 put the vacuum back on the floor at the end. This is not needed.
- All 200 pick the vacuum up before turning it on.

### Hard parts and hacks

- **Button:** the `togglebutton` sphere is ~9 mm (metadata size 0.0093), smaller than the radio's ~11 mm. It sits on the handle ~0.92 m above the floor, 9 cm below the handle top, right where a hand grips.
  - Derived: a fingertip resting on that sphere while grasping counts as a press. So a grasp at the top of the handle can switch the vacuum on or off by itself, and every regrasp there flips it again. Check the marker colour after each grasp.
- **Removal volume:** the `particleremover` meta link is a 0.30 × 0.12 × 0.02 m box at the underside of the head (PROJECTION method, particles must lie inside it).
  - From metadata only: with the vacuum standing upright (root z 0.29), that box spans z ≈ -0.026 to -0.006. The dust sits at z ≈ 0.00.
  - It is therefore not verified that an upright head reaches the dust at all. This may explain 0/5 in closed loop. Test whether tilting or pressing the head changes it before investing in this task.
- Coverage: the head is only 0.30 m wide. Specks spread up to ~3 m apart need separate passes; plan passes from the specks seen, not a blind raster.
- Carrying the 1 m vacuum at arm's length can tip the robot (robot facts). Keep the head on the floor and push.

### Hints for the VLM

- bedroom_0 of house_double_floor_upper, the room with the bed (y > 2.5), desk and bookcases. The vacuum is the only tall, thin upright appliance standing free on the floor.
- The dust is a set of small flat specks on the floor. Count them at the start from a high, wide view and tick them off.
- Done: no specks left on the floor. The episode ends by itself on success.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(not covered floor.n.01_1 dust.n.01_1))` | no | yes |

BDDL goal:

```lisp
(:goal
        (and
            (not
                (covered ?floor.n.01_1 ?dust.n.01_1)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `dust.n.01_1` | particle system | dust | - | - | - | - |
| `floor.n.01_1` | floors_nlswvt_0 | floors / nlswvt | bedroom_0 | floor, z -0.15 | 0.82 m (range 0.11-1.49) | no (fixed) |
| `vacuum.n.04_1` | vacuum_89 | vacuum / bdmsbr | bedroom_0 | low (0.25-0.6 m), z 0.29 | 1.15 m (range 0.7-2.7) | yes, spread 3.61 m |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "bedroom"
 ],
 "house_double_floor_upper": {
  "whitelist": {
   "vacuum.n.04": {
    "vacuum": {
     "bdmsbr": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(covered floor.n.01_1 dust.n.01_1)
(inroom floor.n.01_1 bedroom)
(ontop agent.n.01_1 floor.n.01_1)
(ontop vacuum.n.04_1 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 vacuum.n.04_1)
(touching vacuum.n.04_1 floor.n.01_1)
```

## What the human demos did

200 annotated demos. Length 77.45 s (range 40.37-152.03). Skills per demo 10.0 (range 6-22). 34 distinct skill orders; the most common one covers 46% of demos.

Most common skill counts per demo (46% of demos): move to x4, sweep surface x3, pick up from x1, place on x1, turn on switch x1.

Representative demo `episode_00692680.json` (76.4 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the vacuum` (0.0-11.0 s)
2. `pick up the vacuum from the floors` (11.0-19.0 s)
3. `turn on the vacuum` (19.0-29.0 s)
4. `move to the dirt` (29.0-35.8 s)
5. `sweep the dirt` (35.8-39.8 s)
6. `move to the dirt` (39.8-47.8 s)
7. `sweep the dirt` (47.8-51.8 s)
8. `move to the dirt` (51.8-59.4 s)
9. `sweep the dirt` (59.4-69.0 s)
10. `place the vacuum on the floors` (69.0-76.4 s)

Mean duration per skill in this task: move to 7.6 s, pick up from 12.6 s, place on 6.2 s, push to 17.4 s, sweep surface 4.3 s, turn on switch 8.3 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the dirt` | 769 |
| `sweep the dirt` | 655 |
| `move to the vacuum` | 201 |
| `pick up the vacuum from the floors` | 200 |
| `turn on the vacuum` | 200 |
| `place the vacuum on the floors` | 200 |
| `sweep the vacuum` | 107 |
| `push the vacuum to the floors` | 1 |
| `move to the floors` | 1 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/69_vacuuming_floors.json`. Planner notes: `task_docs/notes/69_vacuuming_floors.md`.
