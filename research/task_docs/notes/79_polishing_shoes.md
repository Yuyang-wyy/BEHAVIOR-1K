## Planner notes

**Tier:** D — a cleaning transition (every dust particle on both shoes swept off with the scrub brush) on top of placing two shoes side by side at an ottoman. The shoes (86 x 91 mm cross-section) are wider than the 44 mm jaw span.

### Goal in plain words

Both shoes must be dust-free, next to each other, and both next to the same ottoman (either of the two). The scrub brush must end on its nightstand, where it starts. Either ottoman works; Q takes the better one.

### Q traps

- `ontop scrub_brush stand` is true at reset (brush z 0.46 on nightstand_maeowc_2 in all 20 instances). It never scores but blocks success if the brush is not put back. Max partial Q is 5/6.
- `not covered` needs every particle gone (PREDICATES §12). The dust system holds 40 particles in the template and in the instances, so about 20 per shoe (derived). One missed particle keeps the literal false.
- `scrub_brush.n.01` removes dust "always": no water or soap needed. Removal is by the brush's AABB + 2 cm (ADJACENCY, root link; the asset has no `particleremover` meta link).
- `nextto` thresholds (derived from asset bboxes, PREDICATES §5): shoe to shoe needs an AABB gap of about 4.6 cm or less. Shoe to ottoman allows about 15 cm.
- Keep both shoes on the floor. A shoe on the ottoman sits above its centre height, and the horizontal rays likely miss (derived).
- The rays must hit the ottoman from the shoe's centre height (~4.5 cm). Whether the ottoman has open legs at that height is not verified. Pushing the shoe against the ottoman's side is the safe choice.
- Cleaning before placing is not required: `not covered` and `nextto` are independent. But brushing a placed shoe can shove it out of `nextto`; re-check both at the end.

### Minimal plan

1. `move to the scrub brush` — brush on the nightstand in view. ~20 s.
2. `pick up the scrub brush from the nightstand` — brush in hand (handle is 24 mm thick). ~24 s.
3. `move to the shoe` — shoe on the floor in view. ~20 s.
4. `wipe the shoe` — brush passes over every side of the shoe; no dust specks visible. ~34 s. Demo humans hold the shoe in the other hand (`pick up the shoe from the floors`, `hand over the scrub brush` first); brushing it on the floor is the untested alternative.
5. `move to the bed` then `place the shoe on the floors` — shoe on the floor touching the ottoman at the foot of a bed. ~20 s + 23 s.
6. Repeat 3-5 for the second shoe, placed within a few cm of the first, both against the same ottoman.
7. `move to the nightstand` then `place the scrub brush on the nightstand` — brush resting on the nightstand top. ~20 s + 23 s.

Budget: 537 s limit vs 358 s demo mean. Enough for one extra wipe pass per shoe.

### What the demos do differently

- 57% follow one order: brush, hand-over, then per shoe pick up, wipe, carry to the bed, place on the floor; then return the brush.
- `move to the bed` is the demo word for walking to the ottoman at the foot of the bed.
- 56 segments use `place on next to the shoe with the floors`. It is an odd, ungrammatical string; use `place the shoe on the floors`.
- The demo `hand over the scrub brush` moves the brush to the other hand so one hand can hold the shoe.

### Hard parts and hacks

- The shoe (asset bbox 0.239 x 0.086 x 0.091 m) is wider than 44 mm on both short axes. Picking it up may fail; the heel collar might fit but that is unverified. Pushing the shoe along the floor to the ottoman needs no grasp.
- Full coverage is the hard part: the brush's removal box (about 0.20 x 0.09 x 0.06 m, from the forced 0.156 x 0.048 x 0.024 size) must reach the sides and toe of the shoe, not just the top.
- The shoes start up to 6.9 m from the robot and anywhere in the bedroom. The ottomans are fixed in every instance at (0.14, -2.54) and (0.14, -0.28): the foot of each bed.
- Scripted shortcut (unverified): keep the brush moving over the shoe from several sides until the time limit. Success ends the episode the moment all six literals hold, so extra sweeping costs nothing.

### Hints for the VLM

- Room: bedroom_0 of hotel_suite_large. Two beds side by side, each with a long ottoman bench (1.47 m) across its foot.
- The brush is a small (16 cm) brush on nightstand_maeowc_2 at (-1.97, 0.82), beside the head of the bed at y -0.29. There are three identical nightstands; it must go back on this one.
- The two shoes (category "walker") are the only footwear on the floor.
- Done: two clean shoes side by side, touching or nearly touching, pressed against one ottoman; brush back on its nightstand.
