from pathlib import Path

import numpy as np

from omnigibson.utils.aspire_kinematics import RobotKinematics


def test_r1pro_fk_and_body_frame_odometry():
    urdf = Path(__file__).parents[2] / "datasets/omnigibson-robot-assets/models/r1pro/urdf/r1pro_original.urdf"
    robot = RobotKinematics(urdf)
    cameras, _ = robot.step({"torso_joint1": 0.2}, base_qvel=(1.0, 0.0, 0.0), dt=2.0)
    assert np.allclose(robot.odom_from_base[:2, 3], [2.0, 0.0])
    assert np.allclose(cameras["zed_link"], robot.odom_from_camera("zed_link", {"torso_joint1": 0.2}))
    assert np.allclose(robot.curobo_base_target(robot.odom_from_base), np.eye(4))
