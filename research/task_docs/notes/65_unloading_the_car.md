## Planner notes

**Tier:** C — the car's articulated trunk lid has to be opened, and two bags have to be carried ~10 m through a doorway.

### Goal in plain words

The briefcase and the satchel must both end `nextto` the sofa in living_room_0. They start in the car's trunk in the garage. The instruction says "on the floor outside the car", but the BDDL only checks nearness to the sofa. The car lid, the garage door and the garage/corridor door are not in the goal, so leaving them open costs nothing.

### Q traps

- 2 literals, both false at reset. Each bag is worth 0.5.
- `nextto` (PREDICATES §5): the AABB gap must be at most L/6. Here that allows about **0.35 m** (briefcase) and **0.38 m** (satchel) to the sofa's AABB. The sofa is 1.79 × 3.29 × 0.67 m (x 1.0-2.8, y 4.4-7.7). In addition, a horizontal ray from one AABB centre must hit the other object.
  - A bag on the floor has its centre ~5-11 cm above the floor. Whether those rays hit the sofa body or pass under it is unverified. Put the bag right against the sofa's side or front, not 30 cm away.
- A bag dropped on the sofa seat also passes the distance test, because the gap is 0. It is not the demo behaviour and is untested.
- Only the final state counts. A bag left by the car scores 0.

### Minimal plan

1. `move to the door` — facing the garage→corridor door `door_bexenl_0` (x -3.89, y 2.38). ~28 s.
2. `open the door of the door` — it starts closed (joint_pos 0), and all 200 demos open it. ~18 s.
3. `move to the car` — at the car's rear. The car is 5 m long, centred at x -4.43, and its rear is at x ≈ -6.96. The bags sit ~0.5 m inside the rear. ~28 s.
4. `open the lid of the car` — the trunk lid is visibly raised. ~49 s, the slowest skill in the demos.
5. `pick up the briefcase from the car` — gripper closed on the handle, briefcase lifted clear. ~28 s.
6. `pick up the satchel from the car` — other hand. ~28 s.
7. `move to the sofa` — carrying both bags. ~45 s. Route: garage → door → corridor → living_room_0. The template has no door object between the corridor and living_room_0.
8. `place the satchel on the floors` — against the sofa. ~20 s.
9. `place the briefcase on the floors` — against the sofa. ~20 s.

About 290 s against a 566 s limit. There is no trained "place … next to the sofa" sentence; the demos use `place the <bag> on the floors` after `move to the sofa`.

### What the demos do differently

- 138/200 pick both bags, put the satchel down on the garage floor, `close the lid of the car`, then `pick up the satchel from the floors` again. The lid close is not in the goal; skipping it saves ~40 s and one regrasp.
- 26/200 pick the satchel first. 20/200 add `push … to the car` or `turn to` to reach a bag deeper in the trunk.
- All 200 open the interior door first. All 200 also end with both bags placed on the floor after `move to the sofa`.

### Hard parts and hacks

- **Trunk lid:** a heavy articulated link (the car has one joint, link `trunk`). Opening it is the longest demo skill. Nothing verifies that a closed-gripper push can lift it.
- **Bag sizes:** briefcase 0.26 × 0.30 × 0.09 m, satchel 0.41 × 0.49 × 0.22 m. Neither body fits the 44 mm span, so the grasp must be on a handle or strap. Handle widths are not in the metadata (unverified).
- The bag poses vary slightly (spread 0.6-0.8 m, random yaw), so the handle direction changes per instance.
- Carrying two bags at arm's length over ~10 m risks tipping (robot facts). Keep the loads low while driving.
- Possible cheap shortcut: one bag per trip. It is slower, but a drop only costs that bag.

### Hints for the VLM

- The garage holds one car (`car_ssxsje`); a second car stands outside in the garden (`car_xxsgpq`). Use the one in the garage.
- The bags are in the rear trunk at ~0.8-0.86 m height.
- living_room_0 has exactly one sofa. It is a large 3.3 m sofa and the only upholstered seat there.
- Done looks like: both bags resting on the floor touching or almost touching the sofa, with no gap wider than a hand.
