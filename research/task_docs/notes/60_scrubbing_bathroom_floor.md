## Planner notes

**Tier:** D — one tool grasp, then a cleaning state change (`not covered`) that needs the brush swept over every dirt patch.

### Goal in plain words

- The bathroom_0 floor (`floors_mawnss_0`) must carry zero dirt particles at the end.
- One literal, one ground option. Q is all or nothing: 1.0 if every patch is gone, else 0.
- Only the scrub brush is in scope; no other tool is needed or scored.

### Q traps

- `not covered` on a visual system needs **every** particle removed; one missed patch keeps Q at 0 (PREDICATES §12).
- Dirt count per instance, from the 20 `*-tro_state.json` files: 1 to 7 particles (301: 6, 302: 2, 303: 3, 304: 4, 305: 5, 306: 3, 307: 7, 308: 7, 309: 6, 310: 3; dev 311: 4, 312: 1, 320: 1). The leaderboard set 301-310 averages ~4.6.
- Patches are spread over the whole room: relative to the floor origin, x from -2.25 to +2.1 m and y from -1.04 to +0.84 m. Instance 311 is unusually compact (all 4 within x -0.63 to 0.40, y 0.12 to 0.25), so a pass on 311 overstates 301-310.
- Particle meshes are scaled 1-3.8x per patch, so patches look different sizes, but removal is tested on the particle's centre point only (PREDICATES §12). Aim the brush at the centre of each patch.
- The scrub brush removes dirt "always" (no water needed; PREDICATES §12 table).
- Only a closed-loop test can say whether patches sampled near the bathtub, toilet or cabinet bases are reachable (unverified).

### Minimal plan

1. `move to the scrub brush` — brush centred in view on the floor; ~14 s.
2. `pick up the scrub brush from the floors` — gripper closed short of fully shut, brush off the floor; ~14 s.
3. `hand over the scrub brush` — brush in the other gripper, first gripper open; ~7 s. Every one of the 200 demos does this, so the wiping motion was learned with the brush in the receiving hand. Keep it.
4. `move to the floors` — base stopped with a visible dirt patch within arm reach in front; ~12 s.
5. `wipe the scrub brush` — brush head pressed to the floor and dragged across the patch; done when that patch is no longer visible; ~9 s.
6. Repeat 4-5 per remaining patch, nearest first.

Budget: ~35 s for steps 1-3, then ~21 s per patch. With the 157.7 s limit that allows about 5-6 patches at demo pace, so 7-patch instances (307, 308) are tight.

### What the demos do differently

- Demos do 1 to 7 wipes (708 wipes over 200 demos, 3.5 on average), with a `move to the floors` before most wipes.
- 42 wipe segments are labelled navigation: the human drove the base while wiping. Scrubbing while moving is in distribution.
- There are no extra objects or detours. The demo is already minimal.

### Hard parts and hacks

- **Removal geometry.** The brush has no `particleremover` meta link in its metadata, so the root link's visual AABB grown by 2 cm is the removal box (PREDICATES §12). The brush is forced to 0.156 x 0.048 x 0.024 m, so the box is about 0.20 x 0.09 m in plan. The patch centre must fall inside it, and the brush bottom must be within ~2 cm of the floor.
- The AABB is world-axis-aligned; a brush held at 45° has a larger plan box, which helps.
- **Brush grasp.** The forced width 0.048 m is over the 44 mm jaw span, so the grasp must close on a narrower part (the handle); unverified.
- **Seeing every patch.** Dirt is a flat decal on the floor. After each wipe, look at the whole floor before declaring done; patches behind the toilet or bathtub are easy to miss.
- **200-particle saturation** is irrelevant here (at most 7 particles).
- **Scripted option:** once the brush is held, a coded "lower to floor and raster a 0.3 x 0.3 m square" around a patch seen in RGB-D is legal and more reliable than hoping the VLA stroke crosses the centre.
- Every closed-loop run so far, including zero-shot and three fine-tunes, scored Q 0.00 on 311.

### Hints for the VLM

- Work only in bathroom_0 (bathtub, toilet, bottom cabinet, two tabletop sinks, two mirrors). bathroom_1 is also loaded and its floor is not the goal floor.
- The scrub brush is a small (~16 cm) brush lying on the bathroom floor, median 0.76 m from the start (0.23-2.7 m).
- Dirt is a visual particle system drawn on the floor surface (exact look not checked here).
- Done: no dirt patch visible anywhere on the bathroom_0 floor from a full look around the room.
