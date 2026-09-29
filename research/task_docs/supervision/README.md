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
