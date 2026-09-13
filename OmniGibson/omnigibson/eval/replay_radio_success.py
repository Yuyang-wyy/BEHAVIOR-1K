"""Replay a previously successful radio action trace and measure the grasp event."""
import argparse, json
from pathlib import Path
import numpy as np


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--replay", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--instance", type=int, default=199)
    p.add_argument("--seed", type=int, default=291844035)
    p.add_argument("--video-path", type=Path)
    p.add_argument("--side-video-path", type=Path)
    a = p.parse_args(); a.output_dir.mkdir(parents=True, exist_ok=True)
    import warp; import warp.torch  # noqa: F401
    warp.init()
    import curobo.geom.sdf.world_mesh  # noqa: F401
    import omnigibson as og
    import torch as th
    from omegaconf import OmegaConf
    from omnigibson.eval.evaluator import Evaluator
    from omnigibson.eval.collect_radio_recovery_oracle import (
        _radio_and_toggle_state,
        _require_physical_grasp_config,
        _step_target,
    )
    from omnigibson.eval.utils.eval_utils import seed_everything
    from omnigibson.macros import gm
    gm.HEADLESS = True; seed_everything(a.seed)
    robot_cfg = OmegaConf.load(str(Path(__file__).with_name("r1pro.yaml")))
    _require_physical_grasp_config(robot_cfg)
    cfg = OmegaConf.create({
        "env_wrapper": {"_target_": "omnigibson.eval.wrappers.RGBDFullResWrapper"},
        "policy_name": "local", "model": {"_target_": "omnigibson.eval.policies.LocalPolicy", "action_dim": None},
        "headless": True, "partial_scene_load": True, "max_steps": 10000,
        "write_video": False, "write_side_video": False, "chunk_boundary_observations": False,
        "training_fail_fast": False, "mode": "train", "seed": a.seed,
        "task": {"name": "turning_on_radio"},
        "robot": robot_cfg,
    })
    trace = np.load(a.replay, allow_pickle=False)
    actions = np.asarray(trace["actions"], dtype=np.float32)[..., :23]
    summary = {"replay": str(a.replay.resolve()), "chunks": int(len(actions)), "chunk_horizon": int(actions.shape[1])}
    with Evaluator(cfg) as evaluator:
        evaluator.reset(seed=a.seed); evaluator.load_task_instance(a.instance); evaluator.reset(seed=a.seed)
        evaluator.start_recording(str(a.video_path.resolve()) if a.video_path else None,
                                  side_fpath=str(a.side_video_path.resolve()) if a.side_video_path else None)
        radio, toggle = _radio_and_toggle_state(evaluator)
        initial_height = float(radio.get_position_orientation()[0][2]); held_step = None; max_height = initial_height
        executed = 0
        for chunk in actions:
            for raw in chunk:
                _step_target(evaluator, th.as_tensor(raw), capture_observation=False)
                executed += 1
                height = float(radio.get_position_orientation()[0][2]); max_height = max(max_height, height)
                if held_step is None and evaluator.robot._ag_obj_in_hand["right"] is radio:
                    held_step = executed
                if bool(toggle.get_value()):
                    break
            if bool(toggle.get_value()):
                break
        summary.update(executed_steps=executed, held_step=held_step, initial_radio_height=initial_height,
                       max_radio_height=max_height, radio_height_delta=max_height-initial_height,
                       toggled=bool(toggle.get_value()), task_success=bool(evaluator.env.task.success))
        (a.output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
        print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__": main()
