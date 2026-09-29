## Planner notes

**Tier:** B — seven small toys go into a bookcase in one room, with short moves. The dice (0.04 m) fit the 44 mm span. The board games (0.044 m thick, lying flat) need a push to the edge first, as in the demos. The teddies (0.11 m smallest side) and the train (0.052 m wide) are wider than the span.

### Goal in plain words

Both dice, both teddy bears, both board games and the toy train must all be inside the same bookcase.
Either of the two identical bookcases works (2 ground options), but all seven toys must share it.
Shelf choice inside the bookcase is free.

### Q traps

- 7 literals, all False at reset. Each toy is worth 1/7. ft40k reached 4/7 on instance 311.
- All toys must go in ONE bookcase. Toys split across the two bookcases score only the larger group. The demos use `bookcase_zfpyqe_1` (the one at y 6.93, nearer the start in most instances); stick to it.
- `inside` needs each toy's AABB centre in a shelf volume (PREDICATES §3). A toy on top of the bookcase (1.64 m tall) is not inside. A board game stacked on the other board game still counts if its centre is within the shelf volume.
- Instance 313: `dice_269` starts at z 1.0 m, not 0.44 m like the other 19 instances, at x 21.36, just past the bed's x-extent. It is not on the bed mattress there; look for it higher up (headboard or elsewhere). Unverified what it rests on.

### Minimal plan

Everything is in childs_room_2, 0.3-3.5 m from the start. The teddies are on the floor, the dice and one board game on the bed, the train and the other board game on the desk.

1. `move to the teddy bear`, `pick up the teddy bear from the floors` twice (one per hand). ~15 s + 27 s each.
2. `move to the bookcase`, `place the teddy bear in the layer_3 bookcase` twice. ~15 s + 18 s each.
3. `move to the dice`, `pick up the dice from the bed` twice. ~15 s + 27 s each.
4. `move to the bookcase`, `place the dice in the layer_2 bookcase` twice.
5. `move to the board game`, `push the board game to the to_the_edge_of bed`, `pick up the board game from the bed`. ~15 + 53 + 27 s.
6. `move to the bookcase`, `place the board game in the layer_2 bookcase`.
7. `move to the toy train`, `push the toy train to the to_the_edge_of desk`, `pick up the toy train from the desk`, `move to the bookcase`, `place the toy train in the layer_4 bookcase`.
8. `move to the board game`, `push the board game to the to_the_edge_of desk`, `pick up the board game from the desk`, `move to the bookcase`, `place the board game on the board game` (on the first board game, inside the shelf).

Done-check each time: toy visible between shelf boards, gripper withdrawn, toy not visible at its source.
Budget: about 600 s against a 959 s limit. Do the dice first if Q must be banked fast: they are the most graspable.

### What the demos do differently

- 200/200 demos push the board games and ~196 push the train to the furniture edge before picking; that is the trained route for flat objects.
- All but one demo use `bookcase_zfpyqe_1`. Shelf words (`layer_2`, `layer_3`, `layer_4`) vary by toy.
- ~194 demos stack the second board game on the first (`place the board game on the board game`). This scores only because the stack is inside the shelf.
- A few demos push a chair out of the way at the desk.

### Hard parts and hacks

- Dice: 0.04 m cubes, the easiest grasp. Two dice = 2/7 quickly.
- Teddy bears: 0.24 x 0.16 x 0.11 m, rigid in sim; the span only fits a limb or ear, unverified.
- Toy train: 0.55 x 0.052 x 0.066 m, just wider than the span; placing a 0.55 m object needs the shelf opening wide enough (bookcase 0.85 m wide, fine).
- Board games: 0.13 x 0.20 x 0.044 m. The 0.044 m thickness is at the limit; grasp only after the push overhangs the edge.

### Hints for the VLM

- The two bookcases are identical tall (1.64 m) shelves standing side by side (0.87 m apart, same wall). Use the one the demos use, `bookcase_zfpyqe_1`, which is nearer the robot start in most instances (median 1.23 m vs 1.8 m), and remember it.
- The room also has one bed, one desk, three straight chairs and a floor lamp. Two other children's rooms are loaded; the toys are all in childs_room_2.
- Done: nothing left on the bed, the desk or the floor; all seven toys visible on the shelves of one bookcase.
