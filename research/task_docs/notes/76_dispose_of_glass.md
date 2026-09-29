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
