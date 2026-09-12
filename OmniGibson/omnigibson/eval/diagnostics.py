"""Evaluator-only primitive and navigation diagnostics.

The policy observation path must never import or call this module. Object poses are
privileged simulator state and are used only to score a completed rollout. Visibility
and primitive-completion events are deliberately external inputs so a future legal
RGB observer or oracle scheduler can supply them without exposing state to the policy.
"""

from __future__ import annotations

import dataclasses
from typing import Any

import numpy as np


@dataclasses.dataclass(frozen=True)
class MilestoneConfig:
    target_scope: str
    workspace_scope: str | None = None
    approach_distance_m: float = 0.8
    workspace_distance_m: float = 1.5

    def __post_init__(self) -> None:
        if self.approach_distance_m <= 0 or self.workspace_distance_m <= 0:
            raise ValueError("Milestone distance thresholds must be positive")


def _position(entity: Any) -> np.ndarray:
    position = entity.get_position_orientation()[0]
    if hasattr(position, "detach"):
        position = position.detach()
    if hasattr(position, "cpu"):
        position = position.cpu()
    return np.asarray(position, dtype=np.float64)


def _planar_distance(left: Any, right: Any) -> float:
    return float(np.linalg.norm(_position(left)[:2] - _position(right)[:2]))


def _scope_entity(env: Any, scope_name: str) -> Any:
    object_scope = env.task.object_scope
    if scope_name not in object_scope:
        available = ", ".join(sorted(str(key) for key in object_scope))
        raise KeyError(f"Unknown BDDL scope {scope_name!r}. Available scopes: {available}")
    entity = object_scope[scope_name]
    if entity is None:
        raise ValueError(f"BDDL scope {scope_name!r} does not currently resolve to a real object")
    return entity


def _is_target_grasped(robot: Any, target: Any) -> bool:
    # IsGraspingState.FALSE is -1, so bool(state) would be an incorrect True.
    return any(int(robot.is_grasping(arm=arm, candidate_obj=target)) == 1 for arm in robot.arm_names)


class PrimitiveMilestoneTracker:
    """Track one target primitive without modifying or augmenting policy observations."""

    def __init__(self, env: Any, robot: Any, config: MilestoneConfig):
        self._robot = robot
        self._config = config
        self._target = _scope_entity(env, config.target_scope)
        self._workspace = _scope_entity(env, config.workspace_scope) if config.workspace_scope else self._target

        self._initial_target_distance: float | None = None
        self._minimum_target_distance: float | None = None
        self._final_target_distance: float | None = None
        self._final_workspace_distance: float | None = None
        self._workspace_step: int | None = None
        self._visible_step: int | None = None
        self._approach_step: int | None = None
        self._grasp_step: int | None = None
        self._completion_step: int | None = None
        self._visibility_observed = False
        self._completion_observed = False

    def observe(
        self,
        step: int,
        *,
        target_visible: bool | None = None,
        primitive_complete: bool | None = None,
    ) -> None:
        """Record a timestep; optional events must come from a legal external observer."""
        if step < 0:
            raise ValueError("step must be non-negative")
        target_distance = _planar_distance(self._robot, self._target)
        workspace_distance = _planar_distance(self._robot, self._workspace)
        if self._initial_target_distance is None:
            self._initial_target_distance = target_distance
            self._minimum_target_distance = target_distance
        self._minimum_target_distance = min(self._minimum_target_distance, target_distance)
        self._final_target_distance = target_distance
        self._final_workspace_distance = workspace_distance

        if self._workspace_step is None and workspace_distance <= self._config.workspace_distance_m:
            self._workspace_step = step
        if self._approach_step is None and target_distance <= self._config.approach_distance_m:
            self._approach_step = step
        if self._grasp_step is None and _is_target_grasped(self._robot, self._target):
            self._grasp_step = step

        if target_visible is not None:
            self._visibility_observed = True
            if target_visible and self._visible_step is None:
                self._visible_step = step
        if primitive_complete is not None:
            self._completion_observed = True
            if primitive_complete and self._completion_step is None:
                self._completion_step = step

    def aggregate(self) -> dict[str, Any]:
        if self._initial_target_distance is None:
            raise RuntimeError("observe() must be called before aggregate()")
        progress_m = self._initial_target_distance - self._minimum_target_distance
        progress_fraction = (
            progress_m / self._initial_target_distance if self._initial_target_distance > 1e-8 else 0.0
        )
        return {
            "schema_version": "b1k-primitive-milestones-v1",
            "target_scope": self._config.target_scope,
            "workspace_scope": self._config.workspace_scope,
            "privileged_state_usage": "evaluator_logger_only",
            "distance": {
                "source": "privileged_simulator_pose_evaluator_only",
                "initial_target_planar_m": self._initial_target_distance,
                "minimum_target_planar_m": self._minimum_target_distance,
                "final_target_planar_m": self._final_target_distance,
                "final_workspace_planar_m": self._final_workspace_distance,
            },
            "correct_workspace_reached": {
                "success": self._workspace_step is not None,
                "first_step": self._workspace_step,
                "threshold_m": self._config.workspace_distance_m,
            },
            "target_first_visible_time": {
                "first_step": self._visible_step if self._visibility_observed else None,
                "observed": self._visibility_observed,
                "source": "external_legal_observer_event",
            },
            "progress_toward_target": {
                "meters": progress_m,
                "fraction_of_initial_distance": progress_fraction,
            },
            "approach_success": {
                "success": self._approach_step is not None,
                "first_step": self._approach_step,
                "threshold_m": self._config.approach_distance_m,
            },
            "grasp_success": {
                "success": self._grasp_step is not None,
                "first_step": self._grasp_step,
            },
            "final_primitive_completion": {
                "success": self._completion_step is not None if self._completion_observed else None,
                "first_step": self._completion_step,
                "observed": self._completion_observed,
                "source": "external_oracle_or_legal_predicate_event",
            },
        }


__all__ = ["MilestoneConfig", "PrimitiveMilestoneTracker"]
