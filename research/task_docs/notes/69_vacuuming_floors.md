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
