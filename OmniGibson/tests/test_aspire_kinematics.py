from pathlib import Path

import numpy as np

from omnigibson.utils.aspire_kinematics import RobotKinematics


def test_r1pro_fk_and_body_frame_odometry():
    urdf = Path(__file__).parents[2] / "datasets/omnigibson-robot-assets/models/r1pro/urdf/r1pro_original.urdf"
    robot = RobotKinematics(urdf)
    encoders = {"torso_joint1": 0.2, "base_footprint_x_joint": 99.0}
    cameras, fk = robot.step(encoders, base_qvel=(1.0, 0.0, np.pi / 2), dt=1.0)
    assert np.allclose(robot.odom_from_base[:2, 3], [2 / np.pi, 2 / np.pi])
    expected_zed = robot.odom_from_base @ fk["zed_link"] @ robot.camera_extrinsics["zed_link"]
    assert np.allclose(cameras["zed_link"], expected_zed)
    assert np.allclose(robot.odom_from_camera("zed_link", encoders), expected_zed)
    assert np.allclose(robot.odom_from_link("torso_link1", encoders), robot.odom_from_base @ fk["torso_link1"])
    assert np.allclose(robot.curobo_base_target(robot.odom_from_base), np.eye(4))


def test_r1pro_camera_calibration_and_validation():
    urdf = Path(__file__).parents[2] / "datasets/omnigibson-robot-assets/models/r1pro/urdf/r1pro_original.urdf"
    robot = RobotKinematics(urdf)
    assert np.allclose(robot.camera_extrinsics["zed_link"][:3, 3], [0.06, 0.0, 0.01], atol=1e-7)
    assert np.allclose(robot.camera_extrinsics["left_realsense_link"][:3, 3], [0.0, 0.0, 0.0])
    for bad in ((float("nan"), 0, 0), (0, 0, 0)):
        try:
            robot.step({}, bad, -1 if bad == (0, 0, 0) else 0)
        except ValueError:
            pass
        else:
            assert bad != (0, 0, 0)
