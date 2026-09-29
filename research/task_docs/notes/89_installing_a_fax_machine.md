## Planner notes

**Tier:** C — lifting the fax (forced size 0.14 x 0.26 x 0.06 m, wider than the 44 mm jaws) from the floor to a cubicle desk. The `toggled_on` half is Tier A: a fingertip press, no grasp.

### Goal in plain words

The fax machine must be switched on and must rest on any of the ten cubicles in the shared office. The order is free. Nothing else is checked.

### Q traps

- Two literals, each 1/2, both false at reset (`ToggledOn` false in all 20 instances).
- The toggle is a stored bool (PREDICATES §11). Pressing it on the floor scores 0.5 and stays on while the fax is carried. A second separate 5-step press turns it back off.
- Button geometry (asset metadata, derived with the template scale 2.03 x 2.0 x 1.76): a sphere of radius about 9 mm, near the top face and about 9 cm from the centre along the long axis. Pressing elsewhere on the body does nothing.
- Carrying risk: a grasp whose finger overlaps that sphere for 5 steps flips it. Check fingers are clear of the button end.
- `ontop fax cubicle` fails if any part of the cubicle is directly above the fax's centre (PREDICATES §4). The cubicles have glass partition links; whether a cubicle has an overhead shelf is not verified. The open desk surface is the demo target.
- Both closed-loop runs on 311 scored Q = 0 (ft40k, sulab1 and local), ending at the step limit.

### Minimal plan

1. `move to the facsimile` — fax on the floor in view. ~28 s.
2. `turn on the facsimile` — fingertip on the button, then withdraw. ~12 s. Doing it on the floor first banks 0.5 before the hard lift.
3. `pick up the facsimile from the floors` — fax lifted. ~26 s.
4. `move to the chair` then `push the chair to the cubicle` — only if a swivel chair blocks the desk. ~28 s + 9 s.
5. `move to the cubicle` then `place the facsimile on the cubicle` — fax resting flat on the desk. ~28 s + 13 s.

Budget: 204 s limit vs 136 s demo mean. Tight; step 4 is the first thing to drop.

### What the demos do differently

- 70% of demos pick up the fax first and press the button while holding it, then push the chair and place the fax. Pressing on the floor first is not the demo order but gives the same literal and banks it early.
- `push the chair to the cubicle` (197 of 200 demos) moves the swivel chair out of the desk's knee space. It earns nothing.

### Hard parts and hacks

- Grasp: forced size 0.14 x 0.26 x 0.06 m; no axis fits 44 mm, and it lies flat on the floor. This is the likely point of failure.
- Any of the ten cubicles counts. Pick the nearest one to the fax; the fax moves up to 8.6 m between instances (three clusters of start positions around x 9-10.8, y -6.9, -2.6 and 1.5).
- Scripted shortcut: the press is a legal no-grasp action. A scripted fingertip press on the button end (seen from the head camera) secures Q = 0.5 without the VLA.

### Hints for the VLM

- Scene office_cubicles_right, shared_office_0: ten identical-size cubicles (two models), ten swivel chairs and sixteen bottom cabinets. None of the cabinets is a target.
- The fax is the only fax, a flat box on the floor 0.65-8.2 m from the start.
- Done: fax resting on a cubicle desk; toggled state is not verified to be visible, so press once and do not touch the button again.
