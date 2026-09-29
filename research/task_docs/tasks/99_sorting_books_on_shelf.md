# 99 · Sorting Books On Shelf

Task name `sorting_books_on_shelf`, task index 99.

> Sort the comic books, notebooks, and hardbacks on the bookcase shelves so the books of each type are grouped together.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_upper` |
| rooms in the goal | living_room |
| rooms loaded | living_room_0 |
| human demo length | 258.0 s mean (7739 steps) |
| episode time limit | 387.0 s (11609 steps at 30 Hz) |
| human base travel | 10.2308 m |
| goal literals (best ground option) | 11 |
| literals already true at start (inferred) | 4 |
| max Q short of full success | **0.36** realistic; 0.636 from `:init` alone. all 7 books start inside the bookcase in all 20 instances, so only the 4 `ontop` literals can score (notes). |
| ground goal options | 1296 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://www.youtube.com/embed/wXUyDWyvpRA |

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

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside comic_book.n.01_1 bookcase.n.01_1)` | yes | never (already true) |
| `(inside comic_book.n.01_3 bookcase.n.01_1)` | yes | never (already true) |
| `(inside comic_book.n.01_2 bookcase.n.01_1)` | no | yes |
| `(ontop comic_book.n.01_3 comic_book.n.01_1)` | no | yes |
| `(ontop comic_book.n.01_2 comic_book.n.01_1)` | no | yes |
| `(inside notebook.n.01_1 bookcase.n.01_1)` | yes | never (already true) |
| `(inside notebook.n.01_2 bookcase.n.01_1)` | no | yes |
| `(ontop notebook.n.01_1 notebook.n.01_2)` | no | yes |
| `(inside hardback.n.01_1 bookcase.n.01_1)` | yes | never (already true) |
| `(inside hardback.n.01_2 bookcase.n.01_1)` | no | yes |
| `(ontop hardback.n.01_1 hardback.n.01_2)` | no | yes |

The goal has 1296 ground options (11 literals x1296); Q takes the best one, so any valid choice of container or partner object counts.

1152 ground options pair an object with itself (for example `nextto can_1 can_1`). Those can never hold, so the option shown above is the best one without them.

BDDL goal:

```lisp
(:goal 
        (and 
            (forall 
                (?comic_book.n.01 - comic_book.n.01)
                (inside ?comic_book.n.01 ?bookcase.n.01_1)
            )
            (forn
                (2)
                (?comic_book.n.01 - comic_book.n.01)
                (or 
                    (ontop ?comic_book.n.01 ?comic_book.n.01_1)
                    (ontop ?comic_book.n.01 ?comic_book.n.01_2)
                    (ontop ?comic_book.n.01 ?comic_book.n.01_3)
                )
            )
            (forall 
                (?notebook.n.01 - notebook.n.01)
                (inside ?notebook.n.01 ?bookcase.n.01_1)
            )
            (exists
                (?notebook.n.01 - notebook.n.01)
                (or 
                    (ontop ?notebook.n.01 ?notebook.n.01_1)
                    (ontop ?notebook.n.01 ?notebook.n.01_2)
                )
            )
            (forall 
                (?hardback.n.01 - hardback.n.01)
                (inside ?hardback.n.01 ?bookcase.n.01_1)
            )
            (exists
                (?hardback.n.01 - hardback.n.01)
                (or 
                    (ontop ?hardback.n.01 ?hardback.n.01_1)
                    (ontop ?hardback.n.01 ?hardback.n.01_2)
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
| `hardback.n.01_1` | hardback_57 | hardback / uzmhnf | living_room_0 | low (0.25-0.6 m), z 0.57 | 3.35 m (range 0.82-6.08) | yes, spread 0.48 m |
| `hardback.n.01_2` | hardback_56 | hardback / trlvhd | living_room_0 | table/counter (0.6-1.1 m), z 0.75 | 3.17 m (range 0.85-6.4) | yes, spread 0.41 m |
| `comic_book.n.01_1` | comic_book_55 | comic_book / nekxsh | living_room_0 | table/counter (0.6-1.1 m), z 0.73 | 3.45 m (range 0.88-6.36) | yes, spread 0.4 m |
| `comic_book.n.01_2` | comic_book_54 | comic_book / qkczyc | living_room_0 | low (0.25-0.6 m), z 0.44 | 3.44 m (range 0.88-6.1) | yes, spread 0.42 m |
| `comic_book.n.01_3` | comic_book_53 | comic_book / scycof | living_room_0 | table/counter (0.6-1.1 m), z 0.73 | 3.16 m (range 0.85-6.41) | yes, spread 0.41 m |
| `notebook.n.01_1` | notebook_52 | notebook / eijrqw | living_room_0 | low (0.25-0.6 m), z 0.42 | 3.46 m (range 0.89-6.09) | yes, spread 0.42 m |
| `notebook.n.01_2` | notebook_51 | notebook / gqkaqu | living_room_0 | table/counter (0.6-1.1 m), z 0.74 | 3.45 m (range 0.9-6.35) | yes, spread 0.4 m |
| `bookcase.n.01_1` | bookcase_otwukr_3 | bookcase / otwukr | living_room_0 | low (0.25-0.6 m), z 0.53 | 3.29 m (range 0.9-6.24) | no (fixed) |
| `floor.n.01_1` | floors_rfqizg_0 | floors / rfqizg | living_room_0 | floor, z -0.15 | 1.95 m (range 0.57-3.72) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "living_room"
 ],
 "house_double_floor_upper": {
  "whitelist": {
   "comic_book.n.01": {
    "comic_book": {
     "nekxsh": [
      0.19,
      0.13,
      0.02
     ],
     "qkczyc": [
      0.19,
      0.13,
      0.02
     ],
     "scycof": [
      0.25,
      0.15,
      0.02
     ]
    }
   },
   "notebook.n.01": {
    "notebook": {
     "eijrqw": [
      0.25,
      0.15,
      0.01
     ],
     "gqkaqu": [
      0.16,
      0.11,
      0.01
     ]
    }
   },
   "hardback.n.01": {
    "hardback": {
     "uzmhnf": [
      0.2,
      0.13,
      0.03
     ],
     "trlvhd": [
      0.2,
      0.13,
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
(inroom bookcase.n.01_1 living_room)
(inroom floor.n.01_1 living_room)
(inside comic_book.n.01_1 bookcase.n.01_1)
(inside comic_book.n.01_3 bookcase.n.01_1)
(inside hardback.n.01_1 bookcase.n.01_1)
(inside notebook.n.01_1 bookcase.n.01_1)
(ontop agent.n.01_1 floor.n.01_1)
(ontop comic_book.n.01_2 notebook.n.01_1)
(ontop hardback.n.01_2 comic_book.n.01_3)
(ontop notebook.n.01_2 comic_book.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching comic_book.n.01_1 notebook.n.01_2)
(touching comic_book.n.01_2 notebook.n.01_1)
(touching comic_book.n.01_3 hardback.n.01_2)
(touching floor.n.01_1 agent.n.01_1)
(touching hardback.n.01_2 comic_book.n.01_3)
(touching notebook.n.01_1 comic_book.n.01_2)
(touching notebook.n.01_2 comic_book.n.01_1)
```

## What the human demos did

200 annotated demos. Length 240.85 s (range 162.53-411.5). Skills per demo 13.0 (range 12-24). 45 distinct skill orders; the most common one covers 52% of demos.

Most common skill counts per demo (52% of demos): pick up from x4, place on x4, push to x4, move to x1.

Representative demo `episode_00992560.json` (224.8 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the bookcase` (0.0-16.0 s)
2. `push the hardback to the comic book` (16.0-44.7 s)
3. `pick up the hardback from the comic book` (47.0-56.0 s)
4. `place the hardback on the hardback` (56.0-68.0 s)
5. `push the notebook to the comic book` (68.0-93.5 s)
6. `pick up the notebook from the comic book` (93.5-105.0 s)
7. `push the comic book to the notebook` (105.0-130.6 s)
8. `pick up the comic book from the notebook` (130.6-145.0 s)
9. `place the comic book on the comic book` (145.0-159.2 s)
10. `place the notebook on the notebook` (159.2-172.0 s)
11. `push the comic book to the bookcase` (172.0-196.0 s)
12. `pick up the comic book from the bookcase` (196.0-210.0 s)
13. `place the comic book on the comic book` (210.0-224.8 s)

Mean duration per skill in this task: move to 16.9 s, pick up from 12.2 s, place in 17.4 s, place on 17.7 s, push to 22.5 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `place the comic book on the comic book` | 411 |
| `place the hardback on the hardback` | 200 |
| `push the comic book to the notebook` | 200 |
| `push the notebook to the comic book` | 199 |
| `pick up the notebook from the comic book` | 199 |
| `pick up the comic book from the notebook` | 199 |
| `push the hardback to the comic book` | 198 |
| `pick up the hardback from the comic book` | 197 |
| `pick up the comic book from the bookcase` | 196 |
| `push the comic book to the bookcase` | 195 |
| `place the notebook on the notebook` | 188 |
| `move to the bookcase` | 130 |
| `move to the comic book` | 118 |
| `move to the hardback` | 86 |
| `move to the notebook` | 75 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/99_sorting_books_on_shelf.json`. Planner notes: `task_docs/notes/99_sorting_books_on_shelf.md`.
