## Planner notes

**Tier:** C. Seven flat books are restacked inside one bookcase. No book can be straddled while it lies flat: they are 0.11-0.15 m wide and 0.19-0.25 m long (forced sizes, `task_custom_lists.json`). Each must first be pushed to overhang a shelf edge, then pinched by its edge.

### Goal in plain words

- All 7 books stay inside bookcase `bookcase_otwukr_3`.
- The 3 comic books form one stack of three, so exactly two comics rest on another comic.
- One notebook rests on the other notebook.
- One hardback rests on the other hardback.
- Which book goes on top within a type is free.

### Q traps

- **The page overstates the reachable Q. Realistic max partial Q is 4/11 = 0.36, not 0.636.**
  - The page marks only 4 `inside` literals as true at reset. The other three books (comic 2, notebook 2, hardback 2) start stacked on books that are inside, and are inside the bookcase themselves.
  - Verified from the 20 instance files: in the bookcase frame, every book's centre lies within |x| ≤ 0.12, |y| ≤ 0.23, z ∈ [-0.14, 0.24] m. The bookcase AABB half-extents are 0.15 x 0.38 x 0.525 m.
  - So all 7 `inside` literals are very likely true at reset. The shelf volume itself is unverified.
  - Only the 4 `ontop` literals can score: 2 comic, 1 notebook, 1 hardback.
- **Keep every book inside.** A book dropped on the floor or left overhanging with its centre past the shelf front loses an `inside` literal and blocks success. That literal never scores back.
- Some ground options put a book on itself (`ontop notebook_1 notebook_1`); those are never true. The page shows the best option without them; the real options pair two different books.
- **`forn (2)` is exact** (PREDICATES §0). Two comics each on a comic means all three in one stack. Two separate pairs are impossible with 3 comics, and a pair alone gives only 1 of 2.
- **Direct contact only** (§4). A comic on a notebook on a comic does not count.
- **Start stacks** (from `:init`): comic 2 on notebook 1, hardback 2 on comic 3, notebook 2 on comic 1, hardback 1 alone. No same-type pair starts stacked.

### Minimal plan

This is the demo order, which frees each base book just before it is needed.

1. `move to the bookcase`. About 17 s.
2. `push the hardback to the comic book`, then `pick up the hardback from the comic book`, then `place the hardback on the hardback`. This moves hardback 2 onto hardback 1. Done when both hardbacks sit squarely stacked on the shelf. About 52 s.
3. `push the notebook to the comic book`, then `pick up the notebook from the comic book`. This takes notebook 2 off comic 1 and keeps holding it. About 35 s.
4. `push the comic book to the notebook`, then `pick up the comic book from the notebook`, then `place the comic book on the comic book`. This moves comic 2 onto comic 1. About 55 s.
5. `place the notebook on the notebook`. This puts notebook 2 on notebook 1, which is now bare. About 18 s.
6. `push the comic book to the bookcase`, then `pick up the comic book from the bookcase`, then `place the comic book on the comic book`. This moves comic 3, bare since step 2, onto the comic stack. About 55 s.

- Totals: about 230 s against a 387.0 s limit.
- Human mean is 258 s.

### What the demos do differently

- The demos match this plan (the modal order covers 52%, 45 orders in total).
- In the modal order every pick is preceded by a `push ... to ...`. That push slides the book toward the shelf edge so an edge can be grasped. It is not a transport step.
- The modal order has a single `move to`: the robot stands in front of the bookcase throughout.

### Hard parts and hacks

- **Grasp.** Books lie flat and are 0.11-0.15 m wide (see memory: R1Pro grasp span; flat books are the worst case). Only an edge pinch after the push can work. Thickness: notebooks 0.01 m, comics 0.02 m, hardbacks 0.03 m.
- **Shelf heights (verified from instance poses):** books sit on two shelves at about 0.40 m and 0.73 m world z (bookcase centre z 0.53 m, books at local z ≈ -0.13 and +0.20). There are two stacks per shelf, about 0.35 m apart side to side. The low shelf needs a deep trunk bend.
- **Pushing too far** drops the book off the shelf front onto the floor. That costs an `inside` literal permanently in Q terms, because that literal was true at reset.
- **Stacking alignment.** A top book whose centre overhangs the lower one fails `ontop` (§4). Centre it.
- ft40k scored Q=0 on instance 311.

### Hints for the VLM

- The room is living_room_0, with 4 bookcases. The target is the one holding all 7 books (0.30 x 0.76 x 1.05 m). The others are distractors and may be the same model.
- Types by size: comic books 0.19 x 0.13 or 0.25 x 0.15 m and 2 cm thick; notebooks 0.25 x 0.15 or 0.16 x 0.11 m and 1 cm thick; hardbacks 0.20 x 0.13 m and 3 cm thick. Thickness from depth is the easiest separator.
- Done: three piles on the shelves, namely one pile of three comics, one of two notebooks and one of two hardbacks, with every book fully back on a shelf.
