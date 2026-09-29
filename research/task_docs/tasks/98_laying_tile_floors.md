# 98 · Laying Tile Floors

Task name `laying_tile_floors`, task index 98.

> Lay the ceramic tiles on the floor next to each other.

## At a glance

| item | value |
| --- | --- |
| scene | `office_cubicles_right` |
| rooms in the goal | bathroom, corridor |
| rooms loaded | bathroom_0, corridor_0, empty_room_0, private_office_0, private_office_1, private_office_2, private_office_3, copy_room_0, shared_office_0, conference_hall_0, meeting_room_0 |
| human demo length | 478.4 s mean (14350 steps) |
| episode time limit | 717.5 s (21526 steps at 30 Hz) |
| human base travel | 64.8431 m |
| goal literals (best ground option) | 8 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 256 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://www.youtube.com/embed/a3OjMFaaSs8 |

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

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(ontop tile.n.01_1 floor.n.01_2)` | no | yes |
| `(ontop tile.n.01_2 floor.n.01_2)` | no | yes |
| `(ontop tile.n.01_3 floor.n.01_2)` | no | yes |
| `(ontop tile.n.01_4 floor.n.01_2)` | no | yes |
| `(nextto tile.n.01_1 tile.n.01_2)` | no | yes |
| `(nextto tile.n.01_2 tile.n.01_1)` | no | yes |
| `(nextto tile.n.01_3 tile.n.01_1)` | no | yes |
| `(nextto tile.n.01_4 tile.n.01_1)` | no | yes |

The goal has 256 ground options (8 literals x256); Q takes the best one, so any valid choice of container or partner object counts.

175 ground options pair an object with itself (for example `nextto can_1 can_1`). Those can never hold, so the option shown above is the best one without them.

BDDL goal:

```lisp
(:goal 
        (and 
            (forall 
                (?tile.n.01 - tile.n.01) 
                (ontop ?tile.n.01 ?floor.n.01_2)
            )
            (forall
                (?tile.n.01 - tile.n.01)
                (or
                    (nextto ?tile.n.01 tile.n.01_1)
                    (nextto ?tile.n.01 tile.n.01_2)
                    (nextto ?tile.n.01 tile.n.01_3)
                    (nextto ?tile.n.01 tile.n.01_4)
                )
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `tile.n.01_1` | ceramic_tile_188 | ceramic_tile / bpaedx | corridor_0 | floor, z 0.03 | 4.29 m (range 0.94-12.43) | yes, spread 14.75 m |
| `tile.n.01_2` | ceramic_tile_187 | ceramic_tile / bpaedx | corridor_0 | floor, z 0.03 | 3.08 m (range 0.78-11.71) | yes, spread 15.0 m |
| `tile.n.01_3` | ceramic_tile_186 | ceramic_tile / bpaedx | corridor_0 | floor, z 0.03 | 4.46 m (range 1.19-11.08) | yes, spread 15.2 m |
| `tile.n.01_4` | ceramic_tile_185 | ceramic_tile / bpaedx | corridor_0 | floor, z 0.03 | 4.32 m (range 1.11-14.0) | yes, spread 15.23 m |
| `floor.n.01_1` | floors_ulczuz_0 | floors / ulczuz | corridor_0 | floor, z -0.15 | 2.48 m (range 0.53-7.18) | no (fixed) |
| `floor.n.01_2` | floors_mlogeo_0 | floors / mlogeo | bathroom_0 | floor, z -0.15 | 15.48 m (range 7.74-21.24) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "bathroom",
  "corridor"
 ],
 "office_cubicles_right": {
  "whitelist": {
   "tile.n.01": {
    "ceramic_tile": {
     "bpaedx": [
      0.45,
      0.42,
      0.03
     ]
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(inroom floor.n.01_1 corridor)
(inroom floor.n.01_2 bathroom)
(ontop agent.n.01_1 floor.n.01_1)
(ontop tile.n.01_1 floor.n.01_1)
(ontop tile.n.01_2 floor.n.01_1)
(ontop tile.n.01_3 floor.n.01_1)
(ontop tile.n.01_4 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 tile.n.01_1)
(touching floor.n.01_1 tile.n.01_2)
(touching floor.n.01_1 tile.n.01_3)
(touching floor.n.01_1 tile.n.01_4)
(touching tile.n.01_1 floor.n.01_1)
(touching tile.n.01_2 floor.n.01_1)
(touching tile.n.01_3 floor.n.01_1)
(touching tile.n.01_4 floor.n.01_1)
```

## What the human demos did

200 annotated demos. Length 474.8 s (range 363.8-633.27). Skills per demo 18.0 (range 16-19). 12 distinct skill orders; the most common one covers 40% of demos.

Most common skill counts per demo (42% of demos): move to x8, pick up from x4, place on next to x4, open door x1, turn to x1.

Representative demo `episode_00980310.json` (486.1 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the ceramic tile` (0.0-31.0 s)
2. `pick up the ceramic tile from the floors` (31.0-58.0 s)
3. `move to the ceramic tile` (58.0-84.0 s)
4. `pick up the ceramic tile from the floors` (84.0-102.0 s)
5. `move to the brown door` (102.0-148.0 s)
6. `open the door of the brown door` (148.0-164.5 s)
7. `move to the window` (164.5-186.0 s)
8. `place the ceramic tile on the floors next to the window` (186.0-197.8 s)
9. `place the ceramic tile on the floors next to the ceramic tile` (197.8-214.0 s)
10. `move to the ceramic tile` (214.0-310.0 s)
11. `pick up the ceramic tile from the floors` (310.0-327.0 s)
12. `move to the ceramic tile` (327.0-334.0 s)
13. `pick up the ceramic tile from the floors` (334.0-348.0 s)
14. `move to the brown door` (348.0-419.0 s)
15. `turn to the ceramic tile` (421.0-428.0 s)
16. `move to the ceramic tile` (428.0-451.0 s)
17. `place the ceramic tile on the floors next to the ceramic tile` (451.0-466.0 s)
18. `place the ceramic tile on the floors next to the ceramic tile` (466.0-486.0 s)

Mean duration per skill in this task: move to 36.5 s, open door 14.4 s, pick up from 21.8 s, place on 16.0 s, place on next to 19.2 s, turn to 4.3 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the ceramic tile` | 1031 |
| `pick up the ceramic tile from the floors` | 800 |
| `place the ceramic tile on the floors next to the ceramic tile` | 595 |
| `move to the brown door` | 392 |
| `open the door of the brown door` | 200 |
| `move to the window` | 200 |
| `turn to the ceramic tile` | 159 |
| `place the ceramic tile on the floors next to the window` | 155 |
| `place the ceramic tile on the floors` | 45 |
| `place on next to the ceramic tile with the floors` | 5 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/98_laying_tile_floors.json`. Planner notes: `task_docs/notes/98_laying_tile_floors.md`.
