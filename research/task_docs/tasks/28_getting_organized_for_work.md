# 28 · Getting Organized For Work

Task name `getting_organized_for_work`, task index 28.

> In the bedroom, organize the workspace by keeping the computer under the desk, ensuring the monitor is on the desk, placing the keyboard on the desk next to the monitor, placing the mouse on the desk next to the keyboard, moving the folder from the swivel chair onto the desk next to the mouse, stacking the notebook on top of the folder with the pen on top of the notebook, and positioning the swivel chair next to the desk.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_upper` |
| rooms in the goal | bedroom |
| rooms loaded | bedroom_0, bedroom_1, bedroom_2 |
| human demo length | 522.4 s mean (15671 steps) |
| episode time limit | 783.6 s (23506 steps at 30 Hz) |
| human base travel | 47.3433 m |
| goal literals (best ground option) | 10 |
| literals already true at start (inferred) | 3 |
| max Q short of full success | 0.7 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.00; ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://player.vimeo.com/video/1114059683 |

## Planner notes

**Tier:** B — desk-top rearrangement of small office items plus one chair push. No doors, no state changes. The difficulty is precision: three small–small `nextto` literals and a three-level stack (folder, notebook, pen). Item widths vs 44 mm are unknown (no custom list).

### Goal in plain words

On the one desk in bedroom_2: keyboard on the desk touching-close to the monitor, mouse on the desk close to the keyboard, folder close to the mouse, notebook on the folder, pen on the notebook. The computer stays under the desk and the monitor stays on the desk. The swivel chair ends next to the desk. One ground option only.

### Q traps

- Three literals are true at reset and never score: `under computer desk`, `ontop monitor desk`, `ontop mouse desk`. Max partial Q is 7/10 = 0.7. Moving the monitor off the desk or the mouse off the desk still blocks success.
- The keyboard starts **on the notebook**, not on the desk. Lift the keyboard off before moving the notebook.
- The pen starts on the folder, and the folder starts on the swivel chair. Take the pen off before carrying the folder.
- `nextto` for small pairs needs a gap of about L/6, a few cm (PREDICATES §5). Mouse–keyboard and folder–mouse are the tight ones. Place each item right against its partner.
- The `nextto` chain is keyboard–monitor, mouse–keyboard, folder–mouse. Keep the mouse between the keyboard and the folder, or on the side of the keyboard where the folder can also touch it.
- `ontop notebook folder` and `ontop pen notebook` need direct contact and the upper item's centre over the lower one (§4). Placing the notebook can shove the folder away from the mouse; re-check folder–mouse after stacking.
- `nextto chair desk` is inferred false only because `:init` does not mention it. The chair centre is 0.65 m from the desk centre in all 20 instances (chair and desk do not move between instances). Desk and chair sizes are unknown, so the chair may already satisfy `nextto` at reset (unverified). Either way, pushing it flush against the desk is safe.
- All three closed-loop runs on 311 scored Q 0.00.

### Minimal plan

1. `move to the keyboard`. ~7 s.
2. `pick up the keyboard from the notebook` — keyboard lifted, notebook visible below. ~14 s. If the grasp fails, `push the keyboard to the to_the_edge_of desk` first (demo aid).
3. `place the keyboard on the desk next to the in_front_of monitor` — keyboard lying flat in front of the monitor, nearly touching its base. ~11 s.
4. `move to the mouse`; `pick up the mouse from the desk`. ~21 s.
5. `place the mouse on the desk next to the left keyboard` — mouse touching-close to the keyboard's end. ~11 s.
6. `move to the pen`; `pick up the pen from the folder`. ~21 s.
7. `place the pen on the desk next to the left notebook` — temporary spot, off the folder. ~11 s.
8. `move to the folder`; `pick up the folder from the swivel chair`. ~21 s. If needed, `push the folder to the to_the_edge_of swivel chair` first.
9. No trained prompt; closest: `place the folder on the desk next to the right notebook` — the goal needs the folder next to the **mouse**, so aim it right against the mouse's free side. ~11 s.
10. `move to the notebook`; `pick up the notebook from the desk`; `place the notebook on the folder` — notebook centred on the folder. ~30 s.
11. `move to the pen`; `pick up the pen from the desk`; `move to the notebook`; `place the pen on the notebook` — pen lying on the notebook's top. ~35 s.
12. `move to the swivel chair`; `push the swivel chair to the right desk` — chair flush against the desk. ~35 s.

Budget: ~500 s demo mean vs a 784 s limit. The plan above skips the monitor re-centring and the first chair push.

### What the demos do differently

- 199 demos first `push the swivel chair to the left desk` to clear access, then push it back at the end (198). Only the final push matters.
- 273 pick-ups of the monitor and 428 `turn to the monitor`: humans re-centre the monitor (`place the monitor on the center desk`). The goal already holds for the monitor; skip it, it only risks dropping it.
- Humans first lay keyboard, notebook and pen out side by side, then rebuild the stack. 189 distinct orders; no dominant one.
- Frequent `push ... to the to_the_edge_of ...` before a pick: slide a flat item to the desk edge so the gripper can get under it.

### Hard parts and hacks

- Flat items (keyboard, notebook, folder) are hard to grasp from a flat surface. Push-to-edge then grasp is the demo trick. Widths vs the 44 mm span are unknown.
- The pen is thin and small; placing it so its centre lands on the notebook needs precision.
- Three chained `nextto` with a few-cm tolerance. A VLA tends to drop items "near"; the planner should re-issue a place when a gap is visible in depth.
- The folder starts on the swivel chair at z ~0.52 m; the chair can roll when the arm presses on it.

### Hints for the VLM

- Everything is in bedroom_2: one desk, one swivel chair, one desktop computer on the floor under the desk, one monitor (z ~1.0 m) on the desk. No same-category distractors in the room.
- At reset the keyboard lies on the notebook on the desk; the folder with the pen on it lies on the swivel chair seat.
- Done looks like: monitor on the desk, keyboard just in front of it, mouse against the keyboard's end, folder against the mouse with notebook on it and pen on top, chair pushed against the desk.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(nextto keyboard.n.01_1 monitor.n.04_1)` | no | yes |
| `(ontop keyboard.n.01_1 desk.n.01_1)` | no | yes |
| `(under computer.n.01_1 desk.n.01_1)` | yes | never (already true) |
| `(ontop monitor.n.04_1 desk.n.01_1)` | yes | never (already true) |
| `(nextto mouse.n.04_1 keyboard.n.01_1)` | no | yes |
| `(ontop mouse.n.04_1 desk.n.01_1)` | yes | never (already true) |
| `(nextto folder.n.02_1 mouse.n.04_1)` | no | yes |
| `(ontop notebook.n.01_1 folder.n.02_1)` | no | yes |
| `(ontop pen.n.01_1 notebook.n.01_1)` | no | yes |
| `(nextto swivel_chair.n.01_1 desk.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (nextto ?keyboard.n.01_1 ?monitor.n.04_1) 
            (ontop ?keyboard.n.01_1 ?desk.n.01_1)
            (under ?computer.n.01_1 ?desk.n.01_1)
            (ontop ?monitor.n.04_1 ?desk.n.01_1)
            (nextto ?mouse.n.04_1 ?keyboard.n.01_1) 
            (ontop ?mouse.n.04_1 ?desk.n.01_1)
            (nextto ?folder.n.02_1 ?mouse.n.04_1) 
            (ontop ?notebook.n.01_1 ?folder.n.02_1)
            (ontop ?pen.n.01_1 ?notebook.n.01_1) 
            (nextto ?swivel_chair.n.01_1 ?desk.n.01_1)
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `mouse.n.04_1` | mouse_92 | mouse / oydobn | bedroom_2 | table/counter (0.6-1.1 m), z 0.73 | 1.73 m (range 1.11-2.6) | yes, spread 1.88 m |
| `swivel_chair.n.01_1` | swivel_chair_iiihwn_0 | swivel_chair / iiihwn | bedroom_2 | low (0.25-0.6 m), z 0.48 | 1.34 m (range 0.96-2.01) | no |
| `keyboard.n.01_1` | keyboard_91 | keyboard / injrgc | bedroom_2 | table/counter (0.6-1.1 m), z 0.74 | 2.08 m (range 1.12-2.68) | yes, spread 1.77 m |
| `notebook.n.01_1` | notebook_90 | notebook / eijrqw | bedroom_2 | table/counter (0.6-1.1 m), z 0.72 | 2.07 m (range 1.12-2.68) | yes, spread 1.79 m |
| `pen.n.01_1` | pen_89 | pen / enfumt | bedroom_2 | low (0.25-0.6 m), z 0.54 | 1.42 m (range 1.02-2.12) | yes, spread 0.23 m |
| `folder.n.02_1` | folder_88 | folder / guhatz | bedroom_2 | low (0.25-0.6 m), z 0.52 | 1.41 m (range 1.02-2.08) | yes, spread 0.12 m |
| `desk.n.01_1` | desk_uqcmzf_0 | desk / uqcmzf | bedroom_2 | table/counter (0.6-1.1 m), z 0.61 | 1.89 m (range 1.57-2.55) | no (fixed) |
| `floor.n.01_1` | floors_dcxicr_0 | floors / dcxicr | bedroom_2 | floor, z -0.15 | 1.12 m (range 0.66-1.56) | no (fixed) |
| `computer.n.01_1` | desktop_computer_87 | desktop_computer / eantds | bedroom_2 | floor, z 0.2 | 1.84 m (range 1.23-2.73) | yes, spread 1.16 m |
| `monitor.n.04_1` | monitor_86 | monitor / qvpbge | bedroom_2 | table/counter (0.6-1.1 m), z 1.0 | 1.75 m (range 1.2-2.57) | yes, spread 0.96 m |

Initial conditions from `:init`:

```lisp
(inroom desk.n.01_1 bedroom)
(inroom floor.n.01_1 bedroom)
(inroom swivel_chair.n.01_1 bedroom)
(ontop agent.n.01_1 floor.n.01_1)
(ontop folder.n.02_1 swivel_chair.n.01_1)
(ontop keyboard.n.01_1 notebook.n.01_1)
(ontop monitor.n.04_1 desk.n.01_1)
(ontop mouse.n.04_1 desk.n.01_1)
(ontop notebook.n.01_1 desk.n.01_1)
(ontop pen.n.01_1 folder.n.02_1)
(touching agent.n.01_1 floor.n.01_1)
(touching desk.n.01_1 monitor.n.04_1)
(touching desk.n.01_1 mouse.n.04_1)
(touching desk.n.01_1 notebook.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching folder.n.02_1 pen.n.01_1)
(touching folder.n.02_1 swivel_chair.n.01_1)
(touching keyboard.n.01_1 notebook.n.01_1)
(touching monitor.n.04_1 desk.n.01_1)
(touching mouse.n.04_1 desk.n.01_1)
(touching notebook.n.01_1 desk.n.01_1)
(touching notebook.n.01_1 keyboard.n.01_1)
(touching pen.n.01_1 folder.n.02_1)
(touching swivel_chair.n.01_1 folder.n.02_1)
(under computer.n.01_1 desk.n.01_1)
```

## What the human demos did

200 annotated demos. Length 497.23 s (range 334.57-959.1). Skills per demo 43.0 (range 27-52). 189 distinct skill orders; the most common one covers 2% of demos.

Most common skill counts per demo (4% of demos): move to x17, pick up from x10, place on next to x6, push to x5, place on x4, turn to x2.

Representative demo `episode_00282290.json` (533.3 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the swivel chair` (2.7-28.1 s)
2. `push the swivel chair to the left desk` (28.1-65.8 s)
3. `move to the mouse` (65.8-73.4 s)
4. `pick up the mouse from the desk` (73.4-85.6 s)
5. `move to the to_the_edge_of desk` (85.6-90.3 s)
6. `place the mouse on the to_the_edge_of desk` (90.3-101.9 s)
7. `move to the keyboard` (101.9-108.8 s)
8. `push the keyboard to the to_the_edge_of desk` (108.8-131.3 s)
9. `pick up the keyboard from the notebook` (131.3-140.4 s)
10. `move to the mouse` (140.4-146.8 s)
11. `place the keyboard on the desk next to the right mouse` (146.8-155.0 s)
12. `move to the notebook` (155.0-160.0 s)
13. `push the notebook to the to_the_edge_of desk` (160.0-173.9 s)
14. `pick up the notebook from the desk` (173.9-189.9 s)
15. `move to the keyboard` (189.9-193.3 s)
16. `place the notebook on the desk next to the right keyboard` (193.3-205.8 s)
17. `move to the monitor` (205.8-209.4 s)
18. `turn to the monitor` (209.4-227.9 s)
19. `pick up the monitor from the desk` (227.9-235.0 s)
20. `place the monitor on the center desk` (235.0-255.7 s)
21. `turn to the monitor` (255.7-268.2 s)
22. `move to the keyboard` (268.2-275.7 s)
23. `pick up the keyboard from the desk` (275.7-289.4 s)
24. `move to the monitor` (289.4-293.5 s)
25. `place the keyboard on the desk next to the in_front_of monitor` (293.5-308.6 s)
26. `move to the mouse` (308.6-312.3 s)
27. `pick up the mouse from the desk` (312.3-322.9 s)
28. `move to the keyboard` (322.9-326.0 s)
29. `place the mouse on the desk next to the left keyboard` (326.0-334.5 s)
30. `move to the pen` (334.5-341.2 s)
31. `pick up the pen from the folder` (341.2-354.2 s)
32. `move to the notebook` (354.2-357.1 s)
33. `place the pen on the desk next to the left notebook` (357.1-361.1 s)
34. `move to the folder` (361.1-366.0 s)
35. `push the folder to the to_the_edge_of swivel chair` (366.0-377.1 s)
36. `pick up the folder from the swivel chair` (377.1-393.6 s)
37. `move to the notebook` (393.6-400.0 s)
38. `place the folder on the desk next to the right notebook` (400.0-417.1 s)
39. `pick up the notebook from the desk` (417.1-425.4 s)
40. `place the notebook on the folder` (425.4-436.2 s)
41. `move to the pen` (436.2-444.2 s)
42. `pick up the pen from the desk` (444.2-461.5 s)
43. `move to the notebook` (461.5-467.1 s)
44. `place the pen on the notebook` (467.1-478.1 s)
45. `move to the swivel chair` (478.1-502.9 s)
46. `push the swivel chair to the right desk` (502.9-536.0 s)

Mean duration per skill in this task: hand over 18.4 s, move to 7.2 s, pick up from 13.6 s, place on 9.3 s, place on next to 10.5 s, push to 28.1 s, turn to 14.4 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the keyboard` | 701 |
| `move to the notebook` | 575 |
| `move to the mouse` | 485 |
| `turn to the monitor` | 428 |
| `move to the swivel chair` | 400 |
| `move to the monitor` | 372 |
| `pick up the mouse from the desk` | 370 |
| `pick up the notebook from the desk` | 369 |
| `move to the pen` | 280 |
| `pick up the monitor from the desk` | 273 |
| `place the mouse on the desk next to the left keyboard` | 239 |
| `pick up the keyboard from the desk` | 236 |
| `place the notebook on the folder` | 200 |
| `pick up the pen from the desk` | 200 |
| `place the pen on the notebook` | 200 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/28_getting_organized_for_work.json`. Planner notes: `task_docs/notes/28_getting_organized_for_work.md`.
