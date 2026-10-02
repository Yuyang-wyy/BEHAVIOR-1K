# Supervision findings

Goal: find where a supervisor (Claude, every 5 s checkpoint, global prompt by default, skill prompts to recover)
raises Q over Comet alone, and document failure points that supervision cannot fix, with the reason.
All numbers: v2 checkpoint (`local_eval/exports/v2-step-00040000`, served with B1K_MAX_TOKEN_LEN=256), seed 0
unless noted, one episode per cell. Noise on a 5-instance mean is about +-0.1 to 0.2.

## Supervisor toolbox and measured reliability

| tool | what it does | measured |
| --- | --- | --- |
| global prompt | task sentence | baseline |
| skill prompt "pick up X from Y" | Comet grasps the object in front of it | upright cans: fast and reliable. Lying cans: 0/3 at trash 311. Sandals: works when a hand is over it. Book: rarely |
| skill prompt "place X in/on Y" | Comet releases at the target | trash bin held tilted: often misses. Nightstand: 1/2 |
| skill prompt "move to X" | Comet navigates | "move to the can of soda" / "move to the trash can" ok; "move to the hardback" and "move to the nightstand" went to the TV bench 3/4 |
| skill prompt "push the hardback to the edge of bed" | demo trick before picking a flat book | 1/3 |
| auto_grasp (scripted) | depth detection + IK grasp of a can-sized floor object | held ~80% on cans; needs range 0.4-0.85 m |
| auto_place (scripted) | levels the held bin (demo release pose), drops into mouth | 18/18 released on trash, 1 miss at 315; spills cans if started with <30 s left |
| hand / reach / grip / point | manual IK moves, pixel-to-3D, jaw close/open | flat sandal or book grasp ~1/3; placing a held object ~reliable |
| base / look / trunk | drive in robot frame, 4-view look-around, straighten trunk | reliable |
| stuck recovery (back off + turn) | when facing a wall | rescued the fridge case |

## picking_up_trash (311-315)

| arm | 311 | 312 | 313 | 314 | 315 | mean |
| --- | --- | --- | --- | --- | --- | --- |
| Comet alone | 0.67 | 0.67 | 0.33 | 0.33 | 0.67 | 0.53 |
| fixed-rule v5 (scripted grasp + place) | 0.67 | 1.0 | 1.0 | 1.0 | 0.67 | 0.87 |
| Claude live | 0.67 | 0.67 | 0.33 | 0.33 | 0.33 | 0.47 |

Failure points:
1. Hover stall: Comet stops with an open hand beside a can. Solvable: scripted grasp fixes it (v5). A skill
   prompt fixes it for upright cans only.
2. Tilted held bin: Comet releases beside it. Solvable: auto_place levels the bin first.
3. Time. Live supervision notices a stall only after 6-17 s and each correction costs checkpoints; 5/10 lost
   literals ran out of clock with the last can in sight. Not solvable by judgement at a 5 s cadence: this task
   rewards reacting within ~2 s, which rules do and a human-speed supervisor does not.
Verdict: supervision helps a lot here (+0.3 to +0.4), but through fast scripted fixes, not live judgement.

## tidying_bedroom (311-315)

| arm | 311 | 312 | 313 | 314 | 315 | mean |
| --- | --- | --- | --- | --- | --- | --- |
| Comet alone seed 0 | 0.67 | 0.33 | 0.33 | 0.67 | 1.0 | 0.60 |
| Comet alone seed 1 | 0.67 | 0.67 | 0.33 | 0.33 | 0.33 | 0.47 |
| Claude live | 1.0 | 0.67 | 0.67 | 0.67 | 0.0 | 0.60 |

Literal-level: Comet alone gets `sandal_1 nextto bed` in 10/10 baseline runs, `sandal_2 nextto sandal_1` in 7/10,
and the book on a nightstand in 1/10. The book is the literal worth supervising.

Failure points:
1. Book grasp. The hardback is 2 cm thick lying flat; nothing can close on it until it overhangs the mattress edge
   or stands on its side. Comet's push skill worked 1/3; my manual pinches 1/5. Partly solvable: the demo sequence
   push -> pick -> move to nightstand -> place gave the only full success (311).
2. Navigation to the nightstand. "move to the nightstand" / "move to the hardback" drove to the TV bench (a
   low cabinet that looks like a nightstand) 3/4 times. Solvable with `look` + a base turn toward the real nightstand,
   at the cost of ~15 s.
3. Sandals. Comet alone already does them; my manual moves (flat-object grasps ~1/3) cost time and at 315 lost both
   sandal literals that Comet alone would have scored. Not worth supervising: leave them to the global prompt.
Verdict: no net gain yet. Plan: leave sandals to Comet, supervise only the book (push/pick skill prompts,
look + turn for navigation), no manual grasps.

## spraying_for_bugs (311-312 so far)

| arm | 311 | 312 | 313 | 314 | 315 |
| --- | --- | --- | --- | --- | --- |
| Comet alone seed 0 | 0 | 0 | 0 | 0 | 0.5 |
| Comet alone seed 1 | 0.5 | 0 | 0 | 0.5 | - |
| Claude live | 0.5 | 0 | | | |

Plant-to-plant distance per instance (from the instance json): 311 7.8 m, 312 0.7, 313 3.9, 314 2.1, 315 2.4
(301-320 range 0.7-10.7 m).

Failure points:
1. Toggle state. The atomizer's ball is a legal on/off indicator: red = off, green = on. Each press toggles.
   Comet's right hand grasps and releases the atomizer top repeatedly, under the global prompt and under every
   skill prompt tried ("spray ...", "move to the pot plant"), so it switches the atomizer off again within
   ~3 s of turning it on. The spray skill itself starts with a grasp-release and turned a green atomizer red.
   Partly solvable: the supervisor can see the colour and re-issue "turn on the insectifuge atomizer" (worked
   2/3), but cannot stop Comet's next press; the on-window stayed ~3 s.
2. Aim. The spray is a projection cone from the nozzle, which points sideways when Comet holds the atomizer.
   Several seconds of "on" right over plant A in 312 left no particle. In 311 the one covered plant came from
   the "spray" skill driving the robot toward the plant with the nozzle pointing at it. Not solvable with the
   current tools: no primitive rotates the held atomizer to aim the nozzle, and the cone size is unknown.
3. Finding the second plant. 311: the second plant was 7.8 m away and never in any camera view (4-view look from
   the first plant). "move to the pot plant" returned to the sprayed plant and knocked it over. Solvable only by
   systematic exploration, which the 324 s limit barely allows after pick + first spray (~120 s used).
4. Manual button press: works when the right hand can reach the ball (1 of 3 poses); arm-arm collision
   blocked the other two.
Verdict so far: supervision gave +0.5 on 311 (spray skill at the right moment) and 0 on 312. The binding
constraint is the toggle/aim loop inside Comet's own manipulation, which prompts cannot fix.

## cook_hot_dogs (313 so far)

Comet alone (v2): seed 0 = 0, 0.5, 0, 0.5, 0 (311-315); seed 1 = 0.5, 1, 0.5, 1, 1. First hot dog is never cooked
before step ~8500 of 13717: the task is time-bound. Video diagnosis of seed-0 failures:
* 311: ~80 s fiddling with the oven next to the fridge before opening the fridge; microwave door opened at ~440 s.
* 313: first hot dog in hand at 120 s, second on the fridge's low shelf; Comet retries it for the remaining 5 min.
Claude live on 313: 0.0. Fridge opened with "open the door of the fridge" (~20 s), hot dog 1 at 100 s, hot dog 2 by
Comet under "move to the microwave" at 170 s, idle at the oven -> look + turn -94 deg to face the microwave (~40 s),
"place the hotdog on the countertop", "open the door of the microwave", "place the hotdog in the microwave" all
worked (door open 330 s, hot dog 1 inside 352 s). With 86 s left Comet picked hot dog 2 up again under "close the
door"; I went for 1.0 instead of closing, the place stalled, the dropped hot dog jammed the door -> 0.
Failure points: (1) navigation to the microwave (not visible from the fridge) - solvable with look + turn;
(2) time: every skill costs 15-40 s and the whole chain takes ~350 s of 457 s - partly solvable by skipping the
countertop step (load hot dog 1 straight in); (3) supervisor greed: close+start as soon as one hot dog is inside
once < ~100 s remain.
Claude live on 311: SUCCESS at step 11141 (Comet alone seed 0: 0, seed 1: 0.5). Interventions:
"open the door of the fridge" as soon as Comet stood at the oven (fridge open at 60 s vs ~120 s alone);
global prompt grabbed both hot dogs by 120 s; "move to the microwave" drove back to the OVEN twice (it seems to
take the oven for the microwave) -> look + turn 176 deg + scripted base drive 3 m down the aisle; then the demo
chain "place the hotdog on the countertop" -> "open the door of the microwave" -> "place the hotdog in the
microwave" -> "pick up the hotdog from the countertop" -> "place ... in the microwave" -> "close the door of the
microwave" (Comet also pressed start: the button went green) -> cooked.
Key fix: navigation to the microwave is the failure point; skill prompts do every manipulation step well.
Claude live on 315: 0 (Comet alone seed 0: 0, seed 1: 1.0). Robot starts at the microwave; fridge ~5 m away:
look + turn + "move to the fridge" + "open the door of the fridge" + "pick up the hotdog from the middle_level
fridge" had both hot dogs by 180 s; the drive back (look, turn, 3.7 m scripted drive, "move to the microwave")
reached it at 295 s with 163 s left; "place on countertop" ok, then "open the door of the microwave" idled for
90 s and my manual door pull missed (head camera tilted after the drive -> pointed 0.3 m too high).
Failure: microwave door opening, a manipulation step with no reliable fallback; plus ~115 s of navigation.
Running tally cook_hot_dogs live: 311 1.0, 313 0, 315 0 (alone seed 0: 0, 0, 0; seed 1: 0.5, 0.5, 1.0).

## turning_out_all_lights_before_sleep (311, 313, 314)

| arm | 311 | 312 | 313 | 314 | 315 |
| --- | --- | --- | --- | --- | --- |
| Comet alone seed 0 | 0.4 | 0.4 | 0 | 0 | 0 |
| Claude live | 0.2 | | 0.4 | 0.4 | |

Baseline flips: Comet alone turns off the kitchen and dining switches when it happens to reach them (311, 312),
double-presses (312 kitchen switch off-on-off, 314 lamp off-on within 3 s), and never enters the utility room.
Legal cue: every toggleable object shows a marker sphere, green = on, red = off (also the microwave button).
Live 311 (0.2): followed the demo order (utility room first). Sliding door took 70 s (skill + scripted hand
slide + base drag); utility switch turned off by the skill; utility lamp defeated both the skill and a scripted
fingertip poke (marker under the shade) and got knocked to the floor. Too little time left for the far rooms.
Live 313 (0.4): global prompt drove 13 m to the dining area; dining switch ended off; kitchen switch turned off
by a scripted poke (head-camera point at the green marker -> IK fingertip 5 cm in front -> push 6.5 cm -> pull
back), first try, twin untouched. "move to the table lamp" went to the MICROWAVE (its green button is a lure);
base moves in the kitchen were blocked by the island and stools; ran out of time before the living-room lamp.
Failure points: (1) navigation between rooms is ~60 % of the time budget and Comet's move skills are unreliable
here; (2) utility lamp button unreachable (under the shade); (3) green-marker lures (microwave).
Promising reflex: "poke the green marker" worked on a wall switch 1/1; not on the lamp 0/1.
Code skill `poke_marker.py` (comet_planner_v10): auto-detects green (ON) toggle markers in the head image,
back-projects with depth, IK-approaches 5 cm in front with closed fingers (re-issuing the move until within
2 cm), pushes 6.5 cm, retracts. Results: kitchen switch at 0.94 m worked (313, done by hand before the script);
dining switch at 1.44 m failed 4x on 314: at that height the gripper points down, so the wrist meets the wall
~4 cm before the fingertips reach the button (press blocked after ~1 cm). Needs a wrist-pitch approach
(fingers horizontal) for high switches - not built yet. Also: after any pose that bends the trunk, `trunk`
straightening pulls the hand back ~0.45 m, so manual follow-up moves must re-read the hand pose.
Live 314 (0.4, alone 0): drove to the dining switch myself (poke skill found it 5 m ahead); pokes failed,
but after my repositioning Comet on the global prompt turned off both the dining (at ~322 s) and the kitchen switch.
Tally on 311/313/314: live 0.33 mean vs alone 0.13 (seed 0). Gains came from getting Comet to the right room
(scripted drives, look) and one scripted poke; losses from the utility room detour on 311.

### High-switch poke (update)
`poke_marker.py --horizontal --normal --square` now handles 1.44 m wall switches: fit the wall plane from 8
depth points around the marker, drive the base to 0.65 m in front of the wall facing it, point the gripper
horizontally at the switch (base-frame quat = yaw toward the wall * 90 deg pitch), approach from 15 cm, push until
blocked, retract. Dev test on 314 (snapshot, dining switch): 3/4 presses toggled it (one from the angled
start view with full square-up). Kitchen switch (0.94 m) with --horizontal: 1/1.
`green_watch.py` is the reflex trigger: runs Comet checkpoints until a green marker is within 1.2 m.
Live 315: robot starts in a closed stub room (7/20 instances do); neither Comet nor manual grips opened the
sliding door in 330 s (handle at 1.18 m needs the base within ~0.6 m; two grips closed on air). That door, not
the switches, is the failure point for stub-room starts.

## thawing_frozen_food - diagnosis (Comet alone v2, 311-315 seed 0: 0.33, 0.22 x4)
Every run: Comet opens the fridge within ~20-55 s, both foods thaw on their own (2 of 9 literals = 0.22), and
Comet never carries a plate out (311 briefly lifted the chicken plate). The missing literals need the demo chain
pick plate -> bar / microwave -> close door -> turn on, the same pattern that succeeded on cook_hot_dogs 311.
Candidate for skill-prompt supervision.

## chop_an_onion - diagnosis (Comet alone v2, 311-315: 0 x5)
Dicing needs two knife contacts with the onion, then a pour; Comet never gets there. But 2 of the 4 literals are
"parer inside sink" and "cutting board inside sink", reachable with trained skills ("pick up the parer from the
bar", "place the parer in the drop in sink", "pick up the cutting board from the bar"). Supervision plan: bank
those two for Q 0.5 first, then try the dice.
Live chop_an_onion 311: 0 (alone 0). Comet picked the cutting board by its handle hole within 50 s, but
"place the cutting board in the drop in sink" drove to the cooktop (sink lookalike), then idled at the sink edge;
my manual move over the basin went the wrong way (IK with the arm near its limit) and dropped it on the counter.
Time limit is only 320 s; the dice chain (onion to board, knife, 3 chops, pour) needs ~250 s of skills alone.
Verdict: sink literals are the only realistic Q here; needs a reliable scripted "carry held object over a
container and release" skill, which exists only for the trash bin (auto_place).
Live thawing_frozen_food 312: 0.33 (alone 0.22). look -> turn -> "move to the fridge" -> "open the door of the
fridge" -> "pick up the plate from the fridge" (bread plate, 128 s) -> "move to the bar" -> "place the plate on the
bar" (+1 literal at 163 s). The chicken plate was never reached: the fridge door swung shut twice while Comet
was away and "pick up the plate from the fridge" then idled at the closed door for 60+ s. Same pattern as
cook_hot_dogs: manipulation skills work, the time budget is lost to doors and repositioning.
New code skill `place_at.py`: carry the held object over a head-camera pixel and release (lift, move over,
lower, open, lift, straighten). Drive mode is unreliable (turn odometry drifts), so position first, re-point,
then `--no-drive`. Dev on onion 311: "move to the drop in sink" with the board held put it right over the basin,
plain release -> `inside board sink` true (1/1). Comet's "pick up the parer from the bar" 0/4 from a hover right
over the handle (the parer lies against the backsplash); manual grip 0/1.
Live chop_an_onion 312: 0.25 (alone 0). Comet grabbed the bowl instead of the board and knocked the parer into
the sink while carrying it (+0.25 at 111 s). Then board: "move to the cutting board" + "pick up the cutting board
from the bar" (held at 227 s) + "move to the drop in sink" + place_at: board landed tilted on the rim (centre
above the basin), missed by a few cm.
Live chop_an_onion 313: 0.25 (alone 0). "move to the cutting board" -> Comet picked the PARER (right hand,
width 0.034) next to the sink -> place_at into the basin: `inside parer sink` at 128 s. The board then:
pick skill grasped/released it on the counter twice; a base-driven sweep failed (arm could not get past the
board's far edge); ran out. Tally live 0 / 0.25 / 0.25 vs alone 0 / 0 / 0.
Recipe that generalises: whatever tool Comet grasps first (board or parer), carry it to the sink and release
with place_at; one sink literal (0.25) per episode is reliable, the second is ~50/50.
Live 314: 0.25 (Comet itself dropped the parer in the sink after the recipe start; board pick never grasped).
Live 315: 0.25 (Comet grasped the parer; place_at into the basin at 110 s; then Comet picked the onion and
drove to the board, but "place the vidalia onion on the cutting board" did not release in 40 s).
**chop_an_onion total: live 0 / 0.25 / 0.25 / 0.25 / 0.25 = 0.20 vs alone 0 x5.** Every gain is one sink
literal via the tool Comet grasps first + place_at. Not solvable in 320 s: dicing (needs onion on board + 2
chop contacts + pour) and the second tool (board pick succeeded 2/5, never placed flat inside).

## Correction: second-seed baselines (Comet alone, v2)
- turning_out_all_lights seed 1: 0.6, 0, 0.4, 0.4, 0.4 = 0.36. Seed 0 was 0.16. Live 0.25 (311, 313-315) is
  within noise of Comet alone - no demonstrated gain on lights.
- cook_hot_dogs seed 1: 0.5, 1, 0.5, 1, 1 = 0.80 (seed 0: 0.20). Live 0.33 on 311/313/315 is BELOW the seed-1
  baseline; the 311 success is a single-instance result, not a gain.
- chop_an_onion and thawing seed-1 baselines queued to check those two claims the same way.
Rule from now on: a supervision gain is claimed only against the mean of both baseline seeds.

### chop_an_onion, seed 1 (second seed)
Live seed 1: 0.25, 0, 0.25, 0.25, 0 = 0.15. Comet alone seed 1: 0, 0, 0, 0, 0.25.
**Over both seeds: supervised 0.175 (7/10 episodes score) vs Comet alone 0.025 (1/10).** First task with a
live-supervision gain that holds across seeds. Mechanism in 5 of the 7: Comet grasps a tool in the
recipe's first minute; the carry to the sink knocks or drops the parer into it (3x) or place_at releases it
(2x); board-in-sink twice. Failures: "pick up the parer from the bar" 0/5 when the parer lies flat; board
dropped on the counter and not re-grasped (2x); long IK reaches from a low arm pose stop ~0.4 m short.
Live thawing 311: 0.11 (alone 0.33). Bread plate out of the fridge by skill at 129 s (plate rim grip reads 0.005,
thin), then Comet did a "hand over the plate" (trained, 447 demos) under "move to the bar", the left hand closed
on nothing and the plate fell to the floor; no trained floor-plate pick. Thawing total live 0.11/0.33 vs alone
0.33/0.22: no gain. Failure point: plate hand-overs and flat plates; not fixable with current skills.

## Candidate search (zero-Q tasks with one cheap literal)
Explore-agent ranking of 43 zero-Q task pages (see chat log 2026-09-28): carrying_in_groceries (close the car
trunk, 1/4), composting_waste (one half into the bin, 1/2), picking_up_toys, make_microwave_popcorn (burner path),
hiding_Easter_eggs, installing_a_scanner, cleaning_up_plates_and_food, outfit_a_basic_toolbox. Baselines queued.

## carrying_in_groceries
Live 311: 0.25 (trunk closed at 105 s). Comet grabbed the bag within 15 s; "close the lid of the car" brought
the left hand under the raised lid but stalled 50 s; scripted push: left hand up 0.35, forward, down 0.6 ->
`not open car` true. Then "move to the door" + "open the door of the door" opened the garage door, but the bag
(and tomato) were dropped on the way; nothing else scored in 600 s.
Groceries 313-315 were run by a script that replays my 311/312 decision (close skill until the trunk literal
is true, then global, re-close if lost; `planner_runs/groceries_episode.sh`) - i.e. not live-supervised.
Results 0.25, 0, 0: on 314/315 "close the lid of the car" never closed it in 3 tries of 90 s (the manual push
from 311 was not in the script). Groceries total 0.25/0.25/0.25/0/0 = 0.15 vs Comet alone 0.5, 0, 0.25, 0.25, 0.5 = 0.30:
supervision hurts. Note: Comet alone on 311 scored 0.5 - it can carry the groceries when not
interrupted; banking the trunk first locks the bag in the trunk and caps the episode at 0.25.
Thawing seed-1 baseline 0.33/0.22/0.11/0.22/0.33 = 0.24 (seed 0 0.24): live 0.22 on 2 instances, no gain.

## composting_waste (182 s limit)
Live 311: 0.5 - skill move+pick stalled, my manual grasp (2nd try, hand 18 cm lower) held the pomegranate
(0.082), "move to the trash can" + "place the half pomegranate in the trash can" released it inside at 113 s.
Live 312: 0 - Comet wandered to the hallway, counter found by turning, two manual pomegranate grasps missed.
Live 313: 0 - manual banana grasp missed; skill picked the banana (0.046) but "place ... in the trash can"
never released in 25 s.
Manual grasps on small fruit: 1/5. Time is the binding constraint (182 s).
Comet alone (seed 0, run locally): 1.0, 0.5, 0.5, 0, 0.5 = 0.50 with one success. Live 0.5, 0, 0 on 311-313
= **supervision hurts** (-0.33 on the same instances). Comet already picks and bins the fruit in ~60 s per item;
my interventions (turns, manual grasps) cost the 182 s budget. Stopped.

## Pattern across all tasks so far
Supervision raised Q only where Comet alone was stuck at ~0 on a literal that a code skill or a single skill
prompt can reach (picking_up_trash: scripted grasp/place; chop_an_onion: tool into the sink). Where Comet alone
already scores (composting 0.50, groceries, cook_hot_dogs seed 1, lights seed 1), interventions lower Q.
Rule: only intervene on tasks where Comet alone is ~0 on the target literal across 2 seeds.

## make_microwave_popcorn, burner shortcut (dev only)
`poke_marker.py --color red` turned the cooktop burner on from 0.7 m (red marker on the cooktop front -> green,
flame on the left-back burner), 1/1 when the red marker nearest in range is the burner's. A second run picked a
different red marker (1.23 m high, 0.43 m away) - the choice of marker needs a height/position filter.
Moving the bag next to the flame (heat radius 0.2 m, ~0.35 m away) failed: a single hand push moved it 7 cm.
`push_to.py` (iterative push skill) written, not yet validated. In one run Comet grasped the bag itself and
spilled popcorn (spilled kernels no longer count). The v2 baseline for popcorn is still queued; parked until then.

### popcorn burner pipeline (`popcorn_burner.py`, code-as-policy + Comet navigation)
Comet alone v2 seed 0: 0 x5. Dev (snapshot reloads, not a legal run): burner on by poke, bag pushed toward the
flame with push_to.py -> SUCCESS at step 3601 (Q 1.0).
Live v1 on 311-315: 0 x5. Burner on 3/5 (red cooktop marker, height filter 0.85-0.97 m; the first press often
hits another red marker). Failures: bag tracker lost the bag (template match) or colour-matched tan furniture
2.5 m away; one navigation phase used the whole episode. Live v2: per-round colour re-detection with a 1.2 m range
filter, navigation capped at 60 s.
Live v2 seed 0: 0, **1.0, 1.0**, 0, 0 = **0.40 with 2 full successes** (Comet alone 0 x5).
- 312: burner on 1st press, 2 pushes, cooked at step 3988. 313: 2nd poke attempt, pushes, cooked at 4447.
- 311: navigation ran out the clock (robot starts in the living room, kitchen far).
- 314/315: flame detector fired on a yellow object before any press, so the burner was never lit -> v3 requires
  a successful press before accepting the flame.
Live v3 seed 1: 0, 0, 0, 0, **1.0** (315 cooked at step 3362). **Popcorn total: 3 successes / 10 episodes
(Q 0.30) vs Comet alone 0/5 seed 0 (seed-1 baseline pending).** Failures v3: 311/313 navigation ran out
(kitchen far from the start); 312 burner pressed but pushes didn't close the 0.2 m gap in time; 314 never found
the burner marker (arrived at step 1950).

### Correction: chop_an_onion with a third baseline seed
Comet alone seed 2: 0.25, 0, 0.25, 0, 0.25 = 0.15. Over 3 seeds Comet alone = 0.067 (0, 0.05, 0.15); supervised
0.175 over 2 seeds. The gain shrinks to ~0.1, i.e. at the noise level. Comet alone also sometimes drops the parer
in the sink. **Not a demonstrated gain.**
Live v4 (stop pressing once a green cooktop marker is seen), both seeds: 0/10. In 6 of 10 runs no red cooktop
marker was in reach after Comet's "move to the popcorn bag" (arrival pose varies), so nothing was pressed; in the
others the first presses hit other red markers (oven knob) before the burner.
**Popcorn over all live runs: 3 full successes / 20 episodes (0.15) vs Comet alone 0/5 seed 0.** The success
rate is limited by where Comet parks the robot, not by the press or push once the burner is in view (dev: 1/1).
Next fix would be a scripted approach to a fixed stand-off in front of the cooktop (look + drive), not built.

### picking_up_trash, second seed
Comet alone seed 1: 0, 0.67, 0.33, 0.33, 0.33, 0.67, 0.33, 1.0, 0.67, 0.67 = 0.50 (seed 0: 0.40).
Scripted grasp/place (v5) seed 1 in progress (1.0, 0.33 so far). v5 seed 0 was 0.70.
Live v5 (search up to 2 m + square-up drive to the cooktop before pressing), both seeds: 0/10; several episodes
crashed in the square-up drive and the rest pressed the wrong marker or none. **Popcorn over all 30 live episodes
(v1-v5): 3 successes = 0.10**, all from v2/v3 (3/10). Later "fixes" did not help; the result is fragile and
dominated by where Comet parks the robot. Treat as a weak, unconfirmed gain.

### picking_up_trash scripted grasp/place (v5) on seed 1 - weakens the headline result
v5 seed 1 (8 of 10 so far): 1.0, 0.33, 0, 0.33, 0.67, 0.33, 0.67, 0.67 = 0.50; Comet alone seed 1 = 0.50.
So on the v2 checkpoint: seed 0 0.70 vs 0.40, seed 1 0.50 vs 0.50. On the old checkpoint the gain held on two
seeds (0.77 vs 0.37, 0.73 vs 0.27). The v2 checkpoint may already fix part of the stall the reflexes target.

## picking_up_trash on the leaderboard instances 301-310 (v2 ckpt)
| seed | Comet alone | v5 scripted grasp/place |
| --- | --- | --- |
| 0 | 0.23 | 0.63 |
| 1 | 0.63 | 0.40 |
Dev 311-320 seed 1 v5 finished: 0.50 (= Comet alone 0.50). Pooled over v2, 40 episodes per arm:
Comet alone 0.45, v5 0.56 - a small gain, inconsistent across seeds.
Failure found: on 303 and 307 (both seeds) the robot starts next to the cans and the grasp reflex fires before
either hand holds the bin, so nothing can be placed and the hands are full. v11 (`comet_planner_v11`) only
grasps when the other hand holds the bin. Being evaluated on LB seeds 0/1 (biased: fix came from them),
dev seeds 0/1, and a fresh LB seed 2 with its own Comet-alone baseline.

## Correction: make_microwave_popcorn
Comet alone seed 1: 0, 0, 1.0, 0, 1.0 = 0.40 (2 successes). Pooled Comet alone 2/10 vs burner pipeline 3/30.
**No gain; the burner pipeline is worse than Comet alone.**

### v11 results (grasp only when the other hand holds the bin) - v2 checkpoint, picking_up_trash
| instances | seed | Comet alone | v5 | v11 |
| --- | --- | --- | --- | --- |
| LB 301-310 | 0 | 0.23 | 0.63 | 0.67 |
| LB 301-310 | 1 | 0.63 | 0.40 | 0.70 |
| LB 301-310 | 2 (fresh, untuned) | 0.43 | - | 0.63 |
| dev 311-320 | 0 | 0.40 | 0.70 | 0.47 |
| dev 311-320 | 1 | 0.50 | 0.53 | 0.90 |
| dev 311-320 | 2 | 0.57 (sulab1) | - | 0.63 |
Paired over all 50 v11 episodes: **Comet alone 0.44 -> v11 0.67**, 28 wins / 8 losses / 14 ties, sign test
p = 0.001, full successes 8 -> 22. v5 over its 40: 0.44 -> 0.57, 15/9, p = 0.31 (not significant).
The fresh held-out LB seed 2 (+0.20) was never used for tuning. Weak spot: dev seed 0, where v11 (0.47) is
below v5 (0.70) - the gate delays grasps when Comet has not picked up the bin yet.
**This is the one statistically solid supervision result on the v2 checkpoint.**

## dispose_of_glass and dispose_of_batteries (v2 ckpt, Comet alone, 311-315)
| task | seed 0 | seed 1 |
| --- | --- | --- |
| dispose_of_glass | 1.0, 0, 0.5, 0, 1.0 = 0.50 | 0.5, 0.25, 0.5, 0, 0 = 0.25 |
| dispose_of_batteries | 0.25, 0.5, 0, 0.25, 0 = 0.20 | 0.25, 0.25, 0.25, 0.25, 0 = 0.20 |
Glass diagnosis: in 7/10 runs Comet grabs the trash can early, then a glass with the other hand, then carries
both for 2-4 min (or to the end) without releasing. That is the trash pattern (held container + item), so v12
(`comet_planner_v12`) adds one reflex: both hands closed for 2 checks -> scripted auto_place of the second-grasped
item into the first-grasped container. Running on the same instances/seeds.
**v12 result: hurts badly.** seed 0: 0, 0, 0, 0.25, 0 = 0.05 (alone 0.50); seed 1: 0, 0, 0, 0.25, 0.5 = 0.15
(alone 0.25). Causes: (1) "both hands closed" used width < 0.09, but an empty closed jaw reads ~0.008, so the
reflex fired on empty hands and pulled Comet off tasks it was completing (311/315 seed 0 were full successes
alone); (2) auto_place's release pose was tuned for the trash can and drops glasses outside this bin.
Lesson: a reflex needs a hold detector that separates "holding an item" from "closed on nothing"; jaw width
alone cannot (see [[comet-planner-harness]] memory: jaw width cannot detect holds). Stopped.

**v11 over 60 paired episodes (dev 3 seeds + LB 3 seeds): Comet alone 0.46 -> v11 0.67, 32 wins / 11 losses /
17 ties, sign test p = 0.002, full successes 10 -> 25.** Dev seed 2 alone is a small gain (+0.06).

## putting_away_toys on the v2 checkpoint (311-315, seed 0)
Comet alone 0.75, 0.625, 0.75, 0.75, 0.875 = 0.75; v8 (hover-gated grasp takeover) 0.875, 0.625, 1.0, 0.75,
0.625 = 0.78. Every v8 log reads "grasps 0": the hover trigger never fired, so the difference is noise. Same
as on the old checkpoint. Comet does not stall on toys; at ~0.75 alone this is not a supervision target.
collecting_aluminum_cans v8 runs were dropped from the queues for the same reason (old ckpt: takeovers hurt).

## sorting_vegetables - diagnosis (Comet alone v2, 311-315 seed 0: 0.23, 0.15, 0.23, 0.23, 0.23)
Failure is strategy, not a stall. partial_q rises by one vegetable every 60-150 s from ~130 s on: Comet walks
each vegetable (one per hand) from a floor basket to the counter bowls; the end frames show it in the corridor
carrying two leeks. All 200 demos instead carry a whole basket to the counter and sort from it while holding it.
(Note: `diag.py`'s "true at end" list is wrong for multi-option goals - the trace's `changed` field re-lists every
literal when the best ground option switches; use the per-tick `partial_q` instead.)
Supervisor v13 (`comet_planner_v13/veg_supervisor.py`): imposes the demo strategy with Comet's own skill
sentences, gated on jaw widths and base idle: move to / pick up the wicker basket -> move to the mixing bowl ->
pick up the <item> from the wicker basket / place the <item> in the mixing bowl (item names tried in turn, a name
is dropped after 2 failed picks) -> place the wicker basket on the floors -> next basket; any skill over budget
gets the global prompt for 3 checks (recovery). Running on 311-315 seed 0.

## Generic demo-plan supervisor (`comet_planner_v13/plan_supervisor.py`)
For long-horizon tasks where Comet alone scores near zero, Claude gives Comet the representative human demo's
skill-sentence plan (`comet_planner_v13/plans/<task>.json`, exported from task_docs/facts) and code gates each
step on legal signals: move = base moved then idle 3 s; pick = number of holding hands rose for 2 checks;
place = a holding hand opened; other skills = demo duration elapsed and robot still. Over budget
(2.5 x demo time) -> global prompt for 3 checks -> one retry -> skip. Place steps with nothing held are skipped.
This is v9's skill-prompt idea made task-agnostic. Queued: clearing_food_from_table_into_fridge (alone 0.08 /
seed 1 so far 0.07) and boxing_food_after_dinner (alone 0.13 / 0.27), 311-315.

### sorting_vegetables v13 results (311-315 seed 0, local 4090)
* v13a (skill prompts only + open-the-second-hand reflex): 0.15, 0.23, 0, 0.08, 0.15 = **0.12** (alone 0.21).
  Comet picks the basket up with the skill prompt in 30-80 s and picks items from it reliably, but it often holds
  the basket with BOTH hands (left jaw 0.043 on the rim), which blocks picking -> reflex: open the non-holder hand.
  The place skill then misses the bowls: items land on the counter next to the bowl or in the sink. Item names
  hardly matter (Comet picks whatever is in the held basket).
* v13b (+ scripted place over the nearest red bowl): bowls found from head RGB (red mask) + depth via a new batched
  `points` op; red points in xy cells that also contain points above 1.25 m are the red backsplash and are dropped.
  i11: 6 scripted places, the 2 where the arm got over the bowl (residual 2 mm) both scored; 4 where IK stalled
  0.25-0.38 m short (counter/basket in the way, trunk disabled to keep the basket level) released on the counter.
  Fix (from i12 on): release only when the hand is within 6 cm of the over-bowl point, otherwise the place skill.
* boxing_food_after_dinner with the demo-plan supervisor (seed 0): 0, 0, 0.33, 0, ... vs alone 0.13. The plan
  reaches only 4-8 of 19 steps in the 335 s limit; "pick up the tupperware from the bottom cabinet" never closes
  a jaw (cabinet open, arms idle). Low-level skill failure, not sequencing; seed 1 dropped.

**Rule (2026-10-01): no skill-prompt-only arms.** Every skill-prompt-only supervisor so far scored at or below Comet
alone (veg v13a 0.12 vs 0.23, boxing demo-plan 0.08 vs 0.13, trash v9 < v5). `plan_supervisor.py` is retired and its
queued clearing_food run was removed. Skill prompts stay only as navigation/recovery inside supervisors whose
main lever is a code reflex aimed at the measured failure point.

### sorting_vegetables: failure points behind "placed but not scored" (v13b, 2026-10-01) and the v13d/e fixes
Per-place Q bookkeeping (partial_q 20 s after each release) over v13b seed 0:
1. **Held basket tilts and spills** (312): basket hangs low in the right hand while the left searches for 30+ s,
   tips over, all vegetables on the floor. The supervisor then mistook a held onion (jaw 0.070) for the basket and
   every later "place" was floor-to-floor.
2. **"move to the mixing bowl" stops ~2 m short** (315): base idle was taken as arrival; picks from the low basket
   then stalled for minutes and only 2 items were placed.
3. **Scripted bowl place scores when the arm gets there** (313: 7/8). Misses were all IK stalls 0.25-0.4 m short
   (trunk disabled to keep the held basket level), since gated (release only within 6 cm).
Fix attempts (`veg_supervisor_d.py`):
* APPROACH (code): bowls from head RGB-D, turn to face + drive until the nearest bowl is ~0.65 m ahead. First version
  drove to the stove: the red backsplash strip at counter level passed as a bowl. Bowl test tightened to rim
  z 0.98-1.12 m, xy spread <= 0.25 m, fragments < 0.22 m apart merged. Now one hop to a real bowl.
* SETDOWN on a free counter spot (code): impossible in this kitchen - a depth dump (i11) shows the counter strip
  within arm reach (x 0.65-0.85 m) is taken by the 3 bowls; the only flat points left are at the edge.
  Replaced by Comet's demo skill "place the wicker basket on the floors" issued at the counter (works, ~70 s),
  then both hands are free and the bowl place may use the trunk.
* After a floor pick the head looks down and no bowl is visible -> `trunk` op (upright) before the bowl search.
One remote episode died of a physics NaN (finger link quaternion) during an approach drive with the basket held.

### sorting_vegetables: v13f (held basket, colour naming, sticky bowl) and v13g/h (Comet's own strategy + bowl reflex)
* v13f seed 0: 0, 0.15, 0.15, 0, 0.23 = 0.11; seed 1: 0, 0, 0.15, 0.15, 0.08 = 0.08 (alone 0.21 / 0.17). Basket dropped or
  re-fetched 2-3x per episode, 1-7 picks per episode, colour naming often saw no basket in the head view. Every variant
  that makes Comet carry the basket to the counter (v13a-f) scored at or below Comet alone.
* Comet alone grasps ~5 items per episode and ~3 score, so v13g keeps the global prompt and adds only the bowl reflex
  (hand closed on something for 2 checks + red bowl within 0.8 m -> carry over it, release; trunk allowed).
  seed 0: 0.38, 0.15, 0.08, 0.23, 0 = 0.17; seed 1: 0.31, 0.23, 0.08, 0.15, 0 = 0.15 -> no gain.
  Cause: the reflex fired on the BASKET. Under the global prompt Comet often carries a basket; rim widths (0.036-0.07)
  overlap vegetables. Wrist-camera wicker fraction at each fire: 315 = 0.36-0.49 on all 5 fires (all baskets, Q 0),
  313 both fires baskets; it dumped the basket at the bowls and broke Comet's progress.
* v13h = v13g + fire only if the holding hand's wrist view is < 0.30 wicker (basket views 0.42-0.58, vegetables
  0.02-0.25). Running seed 0 (local) and seed 1 (remote).
* v13h result: seed 0 0, 0.31, 0.08, 0.23, 0.23 = 0.17; seed 1 0.08, 0.08, 0.15, 0.31, 0.08 = 0.14 -> still no gain.
  Every reflex place now reaches a bowl, but most add nothing: items go to DIFFERENT bowls (base-frame bowl xy changes
  as the robot moves, so "sticky" failed). Q credits a group only inside one bowl; groups may share a bowl.
* v13i = v13h + one "home bowl" for every item, tracked in a legal odometry frame (planner_episode now integrates
  proprio base_qvel every sim step and reports `odom`; drift vs true pose < 2 cm while working at the counter,
  0.5 m mid-trip, recovered). seed 0: 0.08, 0.31, 0.31, 0.38, 0.15 = 0.25 (alone 0.21, 3W/2L);
  seed 1: 0.23, 0.23, 0.31, 0, 0.38 = 0.23 (alone 0.17, 2W/1L/2T). First positive direction; not significant yet.
  Seed 2 running (alone seed 2 = 0.23, 0.31, 0.23, 0, 0.08 = 0.17). The reflex fires only 1-2x per episode: it waits
  2-13x per episode because Comet holds a vegetable next to another bowl while the home bowl is 1.5 m away.
* v13j = v13i + drive to the home bowl (turn + gentle drive to 0.65 m) once per held item when it is < 2.5 m away.
* v13i seed 2: 0.15, 0.08, 0.15, 0.15, 0.23 = 0.15 (alone 0.17). v13i over 15 paired episodes: 0.21 vs 0.19, 7W/6L/2T = noise.
* v13j (drive to the home bowl): seed 0 0.15, 0.23, 0.15, 0, 0.15 = 0.14 (alone 0.21); seed 1 0.08, 0.31, 0.23, 0.15, 0.08
  = 0.17 (alone 0.17); seed 2 (sulab1, 1 ep) 0.31. No gain; stopped.

### sorting_vegetables: CONCLUSION - not improvable with the current Comet skills + code reflexes
Comet alone scores a steady 0.17-0.21 (3 seeds x 5 instances). Ten supervisor versions (v13a-j) were measured;
none beat it beyond noise. Failure points found and fixed along the way (each verified in logs/frames):
- item names wrong for the basket (colour classifier), second hand stuck on the rim (open reflex), place skill misses
  the bowl (scripted bowl place: 85-90 % score when the arm reaches; reach-gated), red backsplash/onions mistaken for
  bowls (rim-height/spread/merge test), reflex firing on the basket (wrist wicker gate), items spread over 3 bowls
  (odometry-tracked home bowl), home bowl out of reach (drive-to-home-bowl).
Why the score does not move:
1. Throughput cap. Comet alone grasps ~5 items per 595 s episode (one trip per 1-2 vegetables, ~100 s each); 3 score.
   A perfect place reflex on top of Comet's own strategy can add at most the ~2 lost items (+0.15), and in practice
   it fires only 1-4 times per episode, and each intervention (a ~10-30 s scripted carry, base drives) costs Comet time
   and sometimes its next grasp - the net is zero.
2. The only route to a large gain is the demo strategy (carry a basket of 6-7 items to the counter). Comet cannot do it
   reliably: the held basket tilts and spills or is dropped (~1x per episode), picking from the held low basket stalls
   for minutes, there is no free counter area within reach to set the basket down (depth dump: the 0.65-0.85 m strip is
   occupied by the 3 bowls), and a basket set on the floor makes every pick 40-80 s and hides the bowls from the head
   camera. Making this work would need a code skill that grasps the basket and keeps it level while Comet picks from it
   (full basket pose control), which the harness does not have.
