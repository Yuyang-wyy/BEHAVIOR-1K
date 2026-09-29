## Planner notes

**Tier:** C. Four flat 0.45 x 0.42 x 0.03 m tiles (forced size, `task_custom_lists.json`) are picked off the floor and carried 8-21 m through a closed door. A tile lying flat has no edge the jaws can straddle.

### Goal in plain words

- All 4 ceramic tiles must rest on the **bathroom** floor (`floors_mlogeo_0`, floor.n.01_2).
- Each tile must be `nextto` at least one other tile. The tiles are interchangeable, so a 2 x 2 block or a row of 4 both work.
- The tiles start on the corridor floor (floor.n.01_1). Leaving them there scores nothing.

### Q traps

- There are 8 literals and all score (0/8 true at reset). Q is the max over 256 options.
- Some ground options pair a tile with itself (`nextto tile_1 tile_1`); those can never hold (PREDICATES §2 and §5). The page shows the best option without them. Each tile needs a different partner.
- **nextto gap (derived from §5):** for two tiles, L = mean(0.90, 0.84, 0.06) = 0.60 m, so the AABB gap must be ≤ ~0.10 m. Butt the tiles edge to edge on the same floor.
- **ontop needs direct contact with the floor** (§4). A tile resting partly on another tile's edge may not touch the floor, and then it scores neither literal. Lay them flat and without overlap.
- A tile carried into the bathroom but dropped in the doorway may be over the corridor floor. The literal needs the bathroom floor object under its centre.

### Minimal plan

1. `move to the ceramic tile`. About 37 s.
2. `pick up the ceramic tile from the floors`. Done when the tile is off the floor and held. About 22 s.
3. `move to the ceramic tile`, then `pick up the ceramic tile from the floors` with the other hand. About 59 s.
4. `move to the brown door`. This is presumably the bathroom door (`door_lztyfn_0`, the only door in bathroom_0); the annotation colour is not verified against the asset. About 37 s.
5. `open the door of the brown door`. The bathroom door starts closed (`joint_pos` 0). Done when the doorway is clear. About 14 s.
6. `move to the window`. Inside the bathroom. About 37 s.
7. `place the ceramic tile on the floors next to the window`, then `place the ceramic tile on the floors next to the ceramic tile`. Done when both lie flat, edge to edge. About 38 s.
8. Repeat steps 1-3 for the last two tiles, then `move to the brown door` and `move to the ceramic tile` (the placed ones). About 150 s.
9. `place the ceramic tile on the floors next to the ceramic tile`, twice. Done when 4 tiles lie flat in a block on the bathroom floor, each edge gap under ~5 cm. About 38 s.

- Totals: about 430 s against a 717.5 s limit.
- The human mean is 478 s, which leaves little slack for failed grasps.

### What the demos do differently

- The demos match this plan: two tiles per trip, first pair placed next to a window (bathroom_0 has two fixed windows).
- `turn to the ceramic tile` (159 demos) re-orients before the last placements. It is short (4 s) and optional.
- 45 segments use plain `place the ceramic tile on the floors`. That is fine when the tile lands within 10 cm of a partner.

### Hard parts and hacks

- **Grasp.** Tiles are 3 cm thick but lie flat, so a top-down grasp cannot straddle them (see memory: R1Pro grasp span; same problem as plates and books). The demos did lift them, but a registered assisted grasp at eval is unverified.
- **Distance.** The tiles are spread along a 16.6 m corridor (instance spread ~15 m), 0.8-14 m from the start. The bathroom floor is 7.7-21 m from the start. Carrying two 0.45 m tiles extended risks tipping (as in the keyboard work). Carry low.
- **The door.** A closed swing door must be opened with a handle grasp. If Comet fails it, nothing downstream scores.
- **Unverified hack:** pushing a tile along the floor with the gripper avoids the grasp, but 15+ m of pushing through a doorway is unlikely to fit in time.
- ft40k scored Q=0 on instance 311.

### Hints for the VLM

- The corridor is long, with many identical doors (8 corridor doors, 6 elevator doors). The tiles are the only flat square slabs on its floor.
- The bathroom is presumably behind the brown door (`door_lztyfn_0`). Inside are 5 toilets, 5 urinals, 5 tabletop sinks, 5 shower stalls and two fixed windows. Free floor space for a 0.9 x 0.84 m block is not verified; look for it by depth.
- Done: 4 tiles lie flat on the bathroom floor (depth shows them 3 cm proud), each touching or within a few cm of a neighbour.
