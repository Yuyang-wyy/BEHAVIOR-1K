from omnigibson.envs import Environment, EnvironmentWrapper
from omnigibson.eval.utils.eval_utils import get_robot_camera_names, set_sensor_modalities
from omnigibson.utils.ui_utils import create_module_logger


logger = create_module_logger(module_name=__name__)


class RGBDLowResWrapper(EnvironmentWrapper):
    """224px RGB-D observations for memory-constrained parallel rollout collection.

    The policy and phase observer already consume 224x224 RGB/depth tensors.
    Rendering at that final resolution avoids allocating the challenge wrapper's
    720px head and 480px wrist render targets.  This wrapper is for collection
    throughput experiments; challenge-protocol evaluation should continue to
    use :class:`RGBDFullResWrapper`.
    """

    def __init__(self, env: Environment):
        super().__init__(env=env)
        robot = env.robots[0]
        robot_eval_config = getattr(env, "_eval_robot_config", {})
        configured_sensor_names = {
            camera_name.split("::")[1]
            for camera_name in get_robot_camera_names(robot.name, robot_eval_config).values()
        }
        for sensor_name, sensor in robot.sensors.items():
            if sensor_name not in configured_sensor_names:
                continue
            if not hasattr(sensor, "image_height") or not hasattr(sensor, "image_width"):
                continue
            set_sensor_modalities(sensor, {"rgb", "depth_linear"})
            sensor.image_height = 224
            sensor.image_width = 224
            sensor_space = sensor.load_observation_space()
            if env.observation_space is not None:
                env.observation_space.spaces[robot.name].spaces[sensor_name] = sensor_space
        logger.info("Reloaded configured camera observation spaces at 224x224 RGB-D.")
