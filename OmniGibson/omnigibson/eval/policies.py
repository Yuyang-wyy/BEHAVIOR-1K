import logging
import torch as th
from omnigibson.eval.utils.network_utils import WebsocketClientPolicy
from typing import Optional


__all__ = [
    "LocalPolicy",
    "WebsocketPolicy",
]


class LocalPolicy:
    """
    Local policy that directly queries action from policy,
        outputs zero delta action if policy is None.
    """

    def __init__(self, *args, action_dim: Optional[int] = None, **kwargs) -> None:
        self.policy = None  # To be set later
        self.action_dim = action_dim

    def set_action_dim(self, action_dim: int) -> None:
        self.action_dim = action_dim

    @property
    def needs_fresh_observation(self) -> bool:
        return True

    @property
    def rollout_status(self) -> None:
        return None

    def act(self, obs: dict) -> th.Tensor:
        return self.forward(obs)

    def forward(self, obs: dict, *args, **kwargs) -> th.Tensor:
        """
        Directly return a zero action tensor of the specified action dimension.
        """
        if self.policy is not None:
            return self.policy.act(obs).detach().cpu()
        else:
            assert self.action_dim is not None
            return th.zeros(self.action_dim, dtype=th.float32)

    def reset(self, seed: int | None = None) -> None:
        if self.policy is not None:
            self.policy.reset(seed=seed)

    def finish_rollout(self, success: bool, metadata: dict | None = None) -> Optional[str]:
        if self.policy is not None and hasattr(self.policy, "finish_rollout"):
            return self.policy.finish_rollout(success=success, metadata=metadata)
        return None


class WebsocketPolicy:
    """
    Websocket policy for controlling the robot over a websocket connection.
    """

    def __init__(
        self,
        *args,
        host: Optional[str] = None,
        port: Optional[int] = None,
        allow_reconnect: bool = False,
        **kwargs,
    ) -> None:
        logging.info(f"Creating websocket client policy with host: {host}, port: {port}")
        self.last_action = None
        self.policy = None
        self._allow_reconnect = allow_reconnect
        if host is not None or port is not None:
            self.policy = WebsocketClientPolicy(host=host, port=port, allow_reconnect=allow_reconnect)

    def update_host(self, host: str, port: int) -> None:
        self.policy = WebsocketClientPolicy(host=host, port=port, allow_reconnect=self._allow_reconnect)

    @property
    def needs_fresh_observation(self) -> bool:
        return self.policy is None or self.policy.needs_fresh_observation

    @property
    def rollout_status(self) -> dict | None:
        return None if self.policy is None else self.policy.rollout_status

    def forward(self, obs: dict, *args, **kwargs) -> th.Tensor:
        if "need_new_action" in obs and not obs["need_new_action"] and self.last_action is not None:
            return self.last_action
        self.last_action = self.policy.act(obs).detach().cpu()
        return self.last_action

    def reset(self, seed: int | None = None) -> None:
        if self.policy is not None:
            self.policy.reset(seed=seed)
        self.last_action = None

    def finish_rollout(self, success: bool, metadata: dict | None = None) -> Optional[str]:
        if self.policy is None:
            return None
        return self.policy.finish_rollout(success=success, metadata=metadata)
