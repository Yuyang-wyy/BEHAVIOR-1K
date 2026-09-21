"""Developer diagnostic: can a task's goal literals actually be satisfied?

NOT a policy. This loads a task instance and inspects the simulator directly -
object scope, meta links, AABBs and the current truth of every goal literal -
so that feasibility questions can be answered before any policy is written.
Nothing here is available to, or used by, a policy.

Motivation: `misc/metadata.json` records only 9 meta-link kinds and never
`fillable`/`openfillable`, yet `Inside._get_value` requires a container volume.
Whether a bookcase has one is therefore only answerable at runtime.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--instance", type=int, default=301)
    parser.add_argument("--seed", type=int, default=2026092501)
    parser.add_argument("--mode", default="public_test")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    import warp
    import warp.torch  # noqa: F401

    warp.init()
    from omegaconf import OmegaConf
    from omnigibson.eval.evaluator import Evaluator
    from omnigibson.macros import gm

    gm.HEADLESS = True
    root = Path(__file__).resolve().parents[2]
    cfg = OmegaConf.create({
        "env_wrapper": {"_target_": "omnigibson.eval.wrappers.RGBDFullResWrapper"},
        "policy_name": "feasibility_probe",
        "model": {"_target_": "omnigibson.eval.policies.LocalPolicy", "action_dim": None},
        "headless": True, "partial_scene_load": True, "max_steps": 10,
        "write_video": False, "write_side_video": False,
        "mode": args.mode, "task": {"name": args.task},
        "robot": OmegaConf.load(root / "OmniGibson/omnigibson/eval/r1pro.yaml"),
    })
    import sys, traceback
    report = {"task": args.task, "instance": args.instance, "objects": [], "goal": []}
    try:
      with Evaluator(cfg) as evaluator:
          evaluator.reset(seed=args.seed)
          evaluator.load_task_instance(args.instance)
          evaluator.reset(seed=args.seed)
          task = evaluator.env.task

          for inst, obj in sorted(task.object_scope.items()):
              entry = {"bddl": inst, "object": None, "category": None,
                       "meta_links": [], "aabb": None}
              if obj is not None and hasattr(obj, "links"):
                  entry["object"] = getattr(obj, "name", None)
                  entry["category"] = getattr(obj, "category", None)
                  entry["meta_links"] = sorted({
                      link.meta_link_type for link in obj.links.values()
                      if getattr(link, "is_meta_link", False)})
                  # The container volume is the actual drop target for Inside;
                  # metadata.json never records it, so read it from the sim.
                  entry["fillable"] = []
                  for link in obj.links.values():
                      if getattr(link, "is_meta_link", False) and \
                              link.meta_link_type in ("fillable", "openfillable"):
                          try:
                              pos = link.get_position_orientation()[0]
                              info = {"link": link.name,
                                      "origin": [round(float(v), 3) for v in pos]}
                              try:
                                  vol = link.visual_meshes if hasattr(link, "visual_meshes") else {}
                                  for mname, mesh in (vol or {}).items():
                                      pts = mesh.points
                                      if pts is None:
                                          continue
                                      import numpy as _np
                                      arr = _np.asarray([[float(q[0]), float(q[1]), float(q[2])] for q in pts])
                                      sc = mesh.scale
                                      sc = _np.asarray([float(v) for v in sc]) if sc is not None else _np.ones(3)
                                      info["local_extent"] = [round(float(v), 3) for v in (arr.max(0) - arr.min(0)) * sc]
                                      break
                              except Exception as err:
                                  info["local_extent"] = "unavailable: %s" % err
                              entry["fillable"].append(info)
                          except Exception as err:
                              entry["fillable"].append({"error": str(err)})
                  if entry["fillable"]:
                      print("      fillable:", entry["fillable"])
                  try:
                      from omnigibson.object_states.aabb import AABB
                      lo, hi = obj.states[AABB].get_value()
                      entry["aabb"] = [[round(float(v), 3) for v in lo],
                                       [round(float(v), 3) for v in hi]]
                  except Exception as error:
                      entry["aabb"] = "unavailable: %s" % error
              report["objects"].append(entry)
              print("%-20s %-22s meta=%-28s aabb=%s"
                    % (inst, entry["object"], ",".join(entry["meta_links"]) or "none", entry["aabb"]))

          options = task.ground_goal_state_options or []
          # What can this gripper actually hold? Assisted grasping needs the
          # object between the fingers: contact AND a ray from a start point on
          # one finger to an end point on the other passing through it. The
          # span of those rays is therefore the hard ceiling on object width.
          robot = evaluator.robot
          try:
              import numpy as _np
              starts = robot.assisted_grasp_start_points
              ends = robot.assisted_grasp_end_points
              print("\ngripper grasp-ray span (the ceiling on graspable width):")
              for arm in robot.arm_names:
                  sp = starts.get(arm) if starts else None
                  ep = ends.get(arm) if ends else None
                  if not sp or not ep:
                      print("   %-6s no assisted grasp points defined" % arm)
                      continue
                  spa = _np.asarray([[float(v) for v in g.position] for g in sp])
                  epa = _np.asarray([[float(v) for v in g.position] for g in ep])
                  widest = max(float(_np.linalg.norm(a - b)) for a in spa for b in epa)
                  print("   %-6s %d start x %d end points, widest ray %.3f m"
                        % (arm, len(spa), len(epa), widest))
                  report.setdefault("grasp_span", {})[arm] = round(widest, 4)
          except Exception as error:
              print("   grasp span unavailable: %s" % error)

          print("\n%d ground goal option(s); literals of each:" % len(options))
          for index, option in enumerate(options):
              satisfied = 0
              for cond in option:
                  terms = list(getattr(cond, "terms", []) or [])
                  ok = "?"
                  if terms:
                      try:
                          ok = bool(task._evaluate_predicate(terms[0], *terms[1:]))
                      except Exception as error:
                          ok = "error: %s" % str(error)[:60]
                  satisfied += 1 if ok is True else 0
                  if index == 0:
                      print("   %-6s %s" % (ok, terms))
                  report["goal"].append({"option": index, "literal": str(terms),
                                         "satisfied": str(ok)})
              print("   option %d: %d/%d satisfied" % (index, satisfied, len(option)))
          print("\ntask.success =", bool(task.success))
          report["success_at_init"] = bool(task.success)

    except Exception:
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        raise
    finally:
        sys.stdout.flush()

    if args.output:
        args.output.write_text(json.dumps(report, indent=2, default=str) + "\n")
        print("wrote", args.output)


if __name__ == "__main__":
    main()
