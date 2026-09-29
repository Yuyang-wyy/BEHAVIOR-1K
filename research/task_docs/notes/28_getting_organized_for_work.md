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
