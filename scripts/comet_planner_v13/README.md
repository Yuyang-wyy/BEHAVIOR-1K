# comet_planner_v13 - sorting_vegetables supervision

Harness = v11 + a batched `points` op (pixels -> base-frame 3D) + legal odometry (`odom` in every checkpoint,
integrated from proprio base velocities; a privileged `odom_check` trace line logs the true pose for drift checks only).

Supervisors (run with `run_sup_batch.sh TASK "IDX..." OUT TAG PORT SUPERVISOR.py [args]`, behavior-env python):
* `veg_supervisor_g.py` - **current**: Comet's own global-prompt strategy + code reflex: when a hand has held a vegetable
  (not the basket: wrist-camera wicker fraction < 0.30) for 2 checks and a red bowl is within reach, carry it over the
  bowl and release. `--home-bowl`: all items into one bowl tracked in the odometry frame (groups only score inside one
  bowl). `--drive-home`: drive to the home bowl once per held item when it is out of reach.
* `veg_supervisor.py` / `veg_supervisor_d.py` - basket-carry strategies (v13a-f), all at or below Comet alone; kept for
  the record (bowl finder `find_bowls`, `scripted_place` are imported from veg_supervisor.py).
* `plan_supervisor.py` - demo-plan skill-prompt sequencing: retired (skill-prompt-only arms never beat Comet alone).
Results and failure analysis: research/task_docs/supervision/README.md.
