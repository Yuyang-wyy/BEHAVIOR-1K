# 19 · Outfit A Basic Toolbox

Task name `outfit_a_basic_toolbox`, task index 19.

> In the utility room, put the drill, pliers, flashlight, Allen wrench, and screwdriver from the tabletop into the toolbox, keep the toolbox on the tabletop, and close the toolbox.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | utility_room |
| rooms loaded | corridor_0, dining_room_0, entryway_0, garden_0, utility_room_0 |
| human demo length | 354.6 s mean (10637 steps) |
| episode time limit | 531.9 s (15956 steps at 30 Hz) |
| human base travel | 31.6827 m |
| goal literals (best ground option) | 7 |
| literals already true at start (inferred) | 2 |
| max Q short of full success | 0.714 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.00; ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://player.vimeo.com/video/1114058641 |

## Planner notes

**Tier:** B — five tools go into a toolbox on the same countertop, with short base moves. The screwdriver (0.028 m across) fits the 44 mm span; the flashlight (0.054 m) and drill (0.059 m thinnest side) do not across their bodies, and the pliers and allen wrench (0.02 m thick) lie flat.

### Goal in plain words

The drill, pliers, flashlight, allen wrench and screwdriver must all be inside the toolbox.
The toolbox must still rest on the same countertop (`countertop_fjkase_0`) and its lid must be closed at the end.
There is only one of each tool, so nothing is interchangeable.

### Q traps

- 7 literals. `ontop toolbox countertop` and `not open toolbox` are already true at reset (toolbox lid joint_pos 0.0 in all 20 instances), so they never score. Max partial Q is 5/7 = 0.714; each tool is worth 1/7.
- Full success needs the lid closed again. A tool whose handle sticks out above the rim can block the lid; it must stay within 5 % of closed (PREDICATES §6).
- Closing the lid can push a tool's centre out of the volume (PREDICATES §3). Re-check after closing.
- The room has three countertops. `ontop toolbox tabletop` is bound to `countertop_fjkase_0`. Pushing the toolbox along it is fine; moving it to another countertop or the floor breaks success.
- Opening the lid never costs partial Q: the 5 `inside` literals score with the lid open. If time runs out, leave it open rather than risk knocking tools out.

### Minimal plan

Everything is on one 2.45 m countertop in the utility room, 0.8-3 m from the start.

1. `move to the toolbox` — toolbox centred in view. ~6 s.
2. `push the toolbox to the center countertop` — toolbox away from the wall/edge with room to swing the lid. ~40 s. Only needed if the lid cannot open where it stands (188/200 demos do it).
3. `open the lid of the toolbox` — lid visibly up and staying open. ~40 s.
4. For each tool, `move to the <tool>`, `pick up the <tool> from the countertop`, `move to the toolbox`, `place the <tool> in the toolbox`. Carry two at once (one per hand) as the demos do. Tool names in the prompts: `screwdriver`, `allen wrench`, `drill`, `flashlight`, `plier`. Done-check: the tool no longer visible on the countertop and visible below the toolbox rim. ~6 + 21 + 6 + 17 s per tool.
5. Put the drill in before the long tools so the flat allen wrench and pliers lie on top, not under it. (Heuristic, not verified.)
6. `close the lid of the toolbox` — lid flush with the box body. ~24 s.

Budget: about 330 s against a 532 s limit.

### What the demos do differently

- No single order dominates: the most common non-move sequence covers only 6/200 demos. Tools are picked in pairs in varied orders.
- 188/200 demos first push the toolbox toward the middle of the countertop, some twice.
- About 5-13 demos set a tool back down on the countertop mid-task (re-grasp); not needed.

### Hard parts and hacks

- Easiest: screwdriver (0.028 m wide). Hardest: flashlight (0.054 m round body, wider than the span) and drill (0.059 m at its thinnest). A narrower drill handle is not listed as a separate link; unverified.
- Pliers (0.30 x 0.08 x 0.02 m) and allen wrench (0.30 x 0.06 x 0.02 m) lie flat; a top-down grasp must straddle a handle (width unknown). The pliers are articulated (one joint, closed at start).
- The toolbox interior dimensions are unknown; five tools including a 0.2 m drill must fit under the lid.
- Best banked Q without the hard grasps is 1/7 (screwdriver) plus whatever flat tools succeed.

### Hints for the VLM

- The toolbox is the 0.26 x 0.61 x 0.35 m box on the countertop (`countertop_fjkase_0`); all five tools lie on the same countertop around it.
- The utility room has two other countertops, five low cabinets, a washer, a dryer, a wardrobe and a tabletop sink. None hold task objects.
- Done: countertop clear of tools, lid down and flush, toolbox still on the countertop.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside drill.n.01_1 toolbox.n.01_1)` | no | yes |
| `(inside pliers.n.01_1 toolbox.n.01_1)` | no | yes |
| `(inside flashlight.n.01_1 toolbox.n.01_1)` | no | yes |
| `(inside allen_wrench.n.01_1 toolbox.n.01_1)` | no | yes |
| `(inside screwdriver.n.01_1 toolbox.n.01_1)` | no | yes |
| `(ontop toolbox.n.01_1 tabletop.n.01_1)` | yes | never (already true) |
| `(not open toolbox.n.01_1))` | yes | never (already true) |

BDDL goal:

```lisp
(:goal 
        (and 
            (inside ?drill.n.01_1 ?toolbox.n.01_1)
            (inside ?pliers.n.01_1 ?toolbox.n.01_1)
            (inside ?flashlight.n.01_1 ?toolbox.n.01_1)
            (inside ?allen_wrench.n.01_1 ?toolbox.n.01_1)
            (inside ?screwdriver.n.01_1 ?toolbox.n.01_1)
            (ontop ?toolbox.n.01_1 ?tabletop.n.01_1)
            (not
                (open ?toolbox.n.01_1)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `drill.n.01_1` | drill_193 | drill / nzgmza | utility_room_0 | table/counter (0.6-1.1 m), z 1.03 | 1.67 m (range 0.83-2.77) | yes, spread 2.18 m |
| `floor.n.01_1` | floors_glwobe_0 | floors / glwobe | utility_room_0 | floor, z -0.14 | 0.9 m (range 0.06-1.86) | no (fixed) |
| `tabletop.n.01_1` | countertop_fjkase_0 | countertop / fjkase | utility_room_0 | table/counter (0.6-1.1 m), z 0.9 | 1.54 m (range 1.12-2.43) | no (fixed) |
| `pliers.n.01_1` | plier_192 | plier / zwzncq | utility_room_0 | table/counter (0.6-1.1 m), z 0.93 | 1.6 m (range 0.97-2.46) | yes, spread 2.07 m |
| `toolbox.n.01_1` | toolbox_191 | toolbox / redmtl | utility_room_0 | table/counter (0.6-1.1 m), z 1.0 | 1.56 m (range 0.99-2.62) | yes, spread 1.55 m |
| `flashlight.n.01_1` | flashlight_190 | flashlight / jtrbkc | utility_room_0 | table/counter (0.6-1.1 m), z 0.94 | 1.86 m (range 0.99-3.08) | yes, spread 2.23 m |
| `allen_wrench.n.01_1` | allen_wrench_189 | allen_wrench / neqlcn | utility_room_0 | table/counter (0.6-1.1 m), z 0.93 | 1.38 m (range 0.76-3.02) | yes, spread 2.13 m |
| `screwdriver.n.01_1` | screwdriver_188 | screwdriver / irtslw | utility_room_0 | table/counter (0.6-1.1 m), z 0.93 | 1.49 m (range 0.9-2.82) | yes, spread 2.25 m |

Initial conditions from `:init`:

```lisp
(inroom floor.n.01_1 utility_room)
(inroom tabletop.n.01_1 utility_room)
(ontop agent.n.01_1 floor.n.01_1)
(ontop allen_wrench.n.01_1 tabletop.n.01_1)
(ontop drill.n.01_1 tabletop.n.01_1)
(ontop flashlight.n.01_1 tabletop.n.01_1)
(ontop pliers.n.01_1 tabletop.n.01_1)
(ontop screwdriver.n.01_1 tabletop.n.01_1)
(ontop toolbox.n.01_1 tabletop.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching allen_wrench.n.01_1 tabletop.n.01_1)
(touching drill.n.01_1 tabletop.n.01_1)
(touching flashlight.n.01_1 tabletop.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching pliers.n.01_1 tabletop.n.01_1)
(touching screwdriver.n.01_1 tabletop.n.01_1)
(touching tabletop.n.01_1 allen_wrench.n.01_1)
(touching tabletop.n.01_1 drill.n.01_1)
(touching tabletop.n.01_1 flashlight.n.01_1)
(touching tabletop.n.01_1 pliers.n.01_1)
(touching tabletop.n.01_1 screwdriver.n.01_1)
(touching tabletop.n.01_1 toolbox.n.01_1)
(touching toolbox.n.01_1 tabletop.n.01_1)
```

## What the human demos did

200 annotated demos. Length 333.02 s (range 195.1-650.2). Skills per demo 21.5 (range 16-29). 90 distinct skill orders; the most common one covers 22% of demos.

Most common skill counts per demo (22% of demos): move to x9, pick up from x5, place in x5, close lid x1, open lid x1, push to x1.

Representative demo `episode_00192220.json` (341.0 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the toolbox` (3.0-8.3 s)
2. `push the toolbox to the center countertop` (8.3-69.8 s)
3. `open the lid of the toolbox` (69.8-109.8 s)
4. `move to the allen wrench` (109.8-114.0 s)
5. `pick up the allen wrench from the countertop` (114.0-129.8 s)
6. `move to the screwdriver` (129.8-132.7 s)
7. `pick up the screwdriver from the countertop` (132.7-147.7 s)
8. `move to the toolbox` (147.7-150.6 s)
9. `place the allen wrench in the toolbox` (150.6-165.1 s)
10. `place the screwdriver in the toolbox` (165.1-190.2 s)
11. `move to the drill` (190.2-195.8 s)
12. `pick up the drill from the countertop` (195.8-208.7 s)
13. `move to the flashlight` (208.7-213.6 s)
14. `pick up the flashlight from the countertop` (213.6-230.7 s)
15. `move to the toolbox` (230.7-235.1 s)
16. `place the drill in the toolbox` (235.1-249.8 s)
17. `place the flashlight in the toolbox` (249.8-266.9 s)
18. `move to the plier` (266.9-273.7 s)
19. `pick up the plier from the countertop` (273.7-296.2 s)
20. `move to the toolbox` (296.2-309.7 s)
21. `place the plier in the toolbox` (309.7-321.3 s)
22. `close the lid of the toolbox` (321.3-344.0 s)

Mean duration per skill in this task: close lid 23.8 s, move to 5.8 s, open lid 40.0 s, pick up from 20.5 s, place in 17.2 s, place on 11.9 s, push to 40.2 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the toolbox` | 708 |
| `push the toolbox to the center countertop` | 226 |
| `pick up the screwdriver from the countertop` | 213 |
| `pick up the flashlight from the countertop` | 209 |
| `pick up the plier from the countertop` | 207 |
| `pick up the allen wrench from the countertop` | 206 |
| `pick up the drill from the countertop` | 205 |
| `open the lid of the toolbox` | 200 |
| `place the drill in the toolbox` | 200 |
| `place the flashlight in the toolbox` | 200 |
| `place the screwdriver in the toolbox` | 200 |
| `place the allen wrench in the toolbox` | 200 |
| `place the plier in the toolbox` | 200 |
| `close the lid of the toolbox` | 200 |
| `move to the plier` | 185 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/19_outfit_a_basic_toolbox.json`. Planner notes: `task_docs/notes/19_outfit_a_basic_toolbox.md`.
