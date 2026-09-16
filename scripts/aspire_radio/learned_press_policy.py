# Code block 1
import numpy as np
from scipy.spatial.transform import Rotation

obs = get_observation()
rgb = obs["rgb"].astype(float)
roi = np.zeros(obs["depth"].shape, dtype=bool)
roi[373:432, 603:668] = True
red = (rgb[..., 0] > 150) & (rgb[..., 0] > 2 * rgb[..., 1]) & (rgb[..., 0] > 2 * rgb[..., 2])
points = mask_to_world_points(roi & red, obs["depth"], obs["intrinsics"], obs["world_from_camera"])
if len(points) < 20:
    for search_step in range(8):
        assert rotate_base(np.pi / 4)
        obs = get_observation()
        rgb = obs["rgb"].astype(float)
        red = ((rgb[..., 0] > 120) & (rgb[..., 0] > 1.35 * rgb[..., 1])
               & (rgb[..., 0] > 1.35 * rgb[..., 2]))
        valid = red & np.isfinite(obs["depth"]) & (obs["depth"] > 0) & (obs["depth"] < 10)
        visited = np.zeros(valid.shape, dtype=bool)
        components = []
        for start_y, start_x in zip(*np.nonzero(valid)):
            if visited[start_y, start_x]:
                continue
            stack = [(int(start_y), int(start_x))]
            visited[start_y, start_x] = True
            component = []
            while stack:
                y0, x0 = stack.pop()
                component.append((y0, x0))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        y1, x1 = y0 + dy, x0 + dx
                        if (0 <= y1 < valid.shape[0] and 0 <= x1 < valid.shape[1]
                                and valid[y1, x1] and not visited[y1, x1]):
                            visited[y1, x1] = True
                            stack.append((y1, x1))
            if len(component) >= 20:
                array = np.asarray(component)
                height = array[:, 0].max() - array[:, 0].min() + 1
                width = array[:, 1].max() - array[:, 1].min() + 1
                aspect = min(height, width) / max(height, width)
                center_y = array[:, 0].mean() / valid.shape[0]
                score = (aspect - .20 * abs(np.log(len(component) / 1500.0))
                         - .50 * abs(center_y - .60))
                components.append((score, component))
        if components:
            component = np.asarray(max(components, key=lambda item: item[0])[1])
            mask = np.zeros(valid.shape, dtype=bool)
            mask[component[:, 0], component[:, 1]] = True
            points = mask_to_world_points(mask, obs["depth"], obs["intrinsics"], obs["world_from_camera"])
        if len(points) >= 20:
            save_current_observation("after_search_rotate")
            break
assert len(points) >= 20
radio = np.median(points, axis=0)
assert lift_arm(arm=0, distance=.2, lock_last_trunk=True)
assert lift_arm(arm=1, distance=.2, lock_last_trunk=True)
base, _, _ = get_robot_position()
direction = radio[:2] - base[:2]
direction /= np.linalg.norm(direction)
xy = radio[:2] - .65 * direction
assert navigate_to_pose(np.array([xy[0], xy[1], np.arctan2(direction[1], direction[0])]))
save_current_observation("before_grasp")

# Code block 2
obs = get_observation()
rgb = obs["rgb"].astype(float)
red = (rgb[..., 0] > 145) & (rgb[..., 0] > 2 * rgb[..., 1]) & (rgb[..., 0] > 2 * rgb[..., 2])
valid = red & np.isfinite(obs["depth"]) & (obs["depth"] > 0) & (obs["depth"] < 10)
ys, xs = np.nonzero(valid)
points = mask_to_world_points(valid, obs["depth"], obs["intrinsics"], obs["world_from_camera"])
near = np.linalg.norm(points - radio, axis=1) < .45
mask = np.zeros(valid.shape, dtype=bool)
mask[ys[near], xs[near]] = True
assert np.count_nonzero(mask) >= 20
radio_center = np.median(points[near], axis=0)

# Stage the free hand beside the observed radio before the holding grasp moves the torso.
base, _, yaw = get_robot_position()
base_forward = np.array([np.cos(yaw), np.sin(yaw), 0.0])
base_left = np.array([-np.sin(yaw), np.cos(yaw), 0.0])
camera = obs["world_from_camera"]
direction = radio_center - camera[:3, 3]
direction /= np.linalg.norm(direction)
reference = np.array([0, 0, 1]) if abs(direction[2]) < 0.9 else np.array([0, 1, 0])
axis_x = np.cross(reference, direction)
axis_x /= np.linalg.norm(axis_x)
axis_y = np.cross(direction, axis_x)
stage_rotation = np.column_stack([axis_x, axis_y, direction])
stage_quat = Rotation.from_matrix(stage_rotation).as_quat()[[3, 0, 1, 2]]
stage_position = (radio_center - .18 * base_forward + .18 * base_left
                  - .02 * direction + np.array([0.0, 0.0, .08]))
current_joints = get_current_joint_positions()
stage_solutions = []
for _ in range(12):
    joints = solve_ik(stage_position, stage_quat, arm=0, lock_last_trunk=True)
    if joints is not None:
        stage_solutions.append(joints)
if stage_solutions:
    stage_posture = np.array([.574, .142, .425, 0.0])
    stage_joints = min(stage_solutions, key=lambda joints:
                       np.linalg.norm(joints[6:10] - stage_posture)
                       + .05 * np.linalg.norm(joints - current_joints))
    move_to_joints(stage_joints)
    save_current_observation("after_left_stage")

# Staging may move the unlocked torso, so pixel masks must match this current camera.
obs = get_observation()
rgb = obs["rgb"].astype(float)
red = (rgb[..., 0] > 145) & (rgb[..., 0] > 2 * rgb[..., 1]) & (rgb[..., 0] > 2 * rgb[..., 2])
valid = red & np.isfinite(obs["depth"]) & (obs["depth"] > 0) & (obs["depth"] < 10)
ys, xs = np.nonzero(valid)
points = mask_to_world_points(valid, obs["depth"], obs["intrinsics"], obs["world_from_camera"])
near = np.linalg.norm(points - radio_center, axis=1) < .45
mask = np.zeros(valid.shape, dtype=bool)
mask[ys[near], xs[near]] = True
assert np.count_nonzero(mask) >= 20
radio_center = np.median(points[near], axis=0)

# The successful visual rollout supplies a grasp skill relative to the current
# observed center and base frame, not an action sequence or simulator pose.
local_grasp_rotation = Rotation.from_quat(np.array([.11519, .99248, .03530, .02166]))
grasp_rotation = Rotation.from_euler("z", yaw) * local_grasp_rotation
grasp_quat = grasp_rotation.as_quat()[[3, 0, 1, 2]]
grasp_position = radio_center + .023 * base_forward - .008 * base_left + np.array([0.0, 0.0, .068])
pregrasp_position = radio_center + .017 * base_forward - .015 * base_left + np.array([0.0, 0.0, .188])
candidate = -1
completed = False
pregrasp_solutions = []
current_joints = get_current_joint_positions()
for _ in range(6):
    joints = solve_ik(pregrasp_position, grasp_quat, arm=1)
    if joints is not None:
        pregrasp_solutions.append(joints)
if pregrasp_solutions:
    open_gripper(arm=1)
    pregrasp_joints = min(pregrasp_solutions, key=lambda joints: np.linalg.norm(joints - current_joints))
    move_to_joints(pregrasp_joints)
    hand, _ = get_current_eef_pose(arm=1)
    grasp_solutions = []
    current_joints = get_current_joint_positions()
    if np.linalg.norm(hand - pregrasp_position) < .025:
        for _ in range(6):
            joints = solve_ik(grasp_position, grasp_quat, arm=1)
            if joints is not None:
                grasp_solutions.append(joints)
    if grasp_solutions:
        grasp_joints = min(grasp_solutions, key=lambda joints: np.linalg.norm(joints - current_joints))
        move_to_joints(grasp_joints, max_joint_step=.005)
        hand, _ = get_current_eef_pose(arm=1)
        if np.linalg.norm(hand - grasp_position) < .025:
            close_gripper(arm=1)
            completed = lift_arm(arm=1, distance=.12)
    if completed:
        candidate = 0
        grasp_backend = "visual-reference"
if not completed:
    reference_quat = np.array([.0672, .8865, -.4578, -.0015])
    pregrasps = []
    grasps = []
    for _ in range(3):
        try:
            sampled_pregrasps, sampled_grasps = sample_contact_grasp_pose(mask, arm=1, max_candidates=16)
        except (ValueError, RuntimeError):
            continue
        pregrasps += sampled_pregrasps
        grasps += sampled_grasps
    order = sorted(
        range(len(grasps)),
        key=lambda index: float(np.linalg.norm(grasps[index][0] - radio_center))
        + .30 * (1.0 - abs(float(np.dot(grasps[index][1], reference_quat)))),
    )
    for index in order:
        if (grasps[index][0][2] <= radio_center[2] - .20
                or abs(float(np.dot(grasps[index][1], reference_quat))) < .60):
            continue
        if solve_ik(*pregrasps[index], arm=1) is not None and solve_ik(*grasps[index], arm=1) is not None:
            if execute_grasp(pregrasps[index], grasps[index], arm=1, lift=.12):
                candidate = index
                completed = True
                grasp_backend = "contact-graspnet"
                break
assert candidate >= 0, "No reachable current visual grasp"
assert completed, "Learned grasp motor sequence did not complete"
save_current_observation("after_grasp")
save_current_observation("after_grasp_right", camera="right_wrist")

# Code block 3
def held_radio_pixels(camera="head"):
    current = get_observation(camera)
    image = current["rgb"].astype(float)
    depth = current["depth"]
    red_pixels = (image[..., 0] > 145) & (image[..., 0] > 2 * image[..., 1]) & (image[..., 0] > 2 * image[..., 2])
    valid_pixels = red_pixels & np.isfinite(depth) & (depth > 0) & (depth < 10)
    pixel_y, pixel_x = np.nonzero(valid_pixels)
    world = mask_to_world_points(valid_pixels, depth, current["intrinsics"], current["world_from_camera"])
    hand, _ = get_current_eef_pose(arm=1)
    held = np.linalg.norm(world - hand, axis=1) < (.75 if camera != "head" else .35)
    return current, image, pixel_x[held], pixel_y[held]

def find_button(rgb, xs, ys, top_only=False):
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    if top_only and (x1 - x0) < .8 * (y1 - y0):
        raise AssertionError("Radio top face is not visible")
    red_shape = np.zeros((y1 - y0 + 1, x1 - x0 + 1), dtype=bool)
    red_shape[ys - y0, xs - x0] = True
    visited = np.zeros(red_shape.shape, dtype=bool)
    red_components = []
    for start_y, start_x in zip(*np.nonzero(red_shape)):
        if visited[start_y, start_x]:
            continue
        stack = [(int(start_y), int(start_x))]
        visited[start_y, start_x] = True
        points = []
        while stack:
            point_y, point_x = stack.pop()
            points.append((point_y, point_x))
            for delta_y in (-1, 0, 1):
                for delta_x in (-1, 0, 1):
                    next_y, next_x = point_y + delta_y, point_x + delta_x
                    if (0 <= next_y < red_shape.shape[0] and 0 <= next_x < red_shape.shape[1]
                            and red_shape[next_y, next_x] and not visited[next_y, next_x]):
                        visited[next_y, next_x] = True
                        stack.append((next_y, next_x))
        red_components.append(np.asarray(points, dtype=int))
    body = max(red_components, key=len)
    if len(body) >= 20:
        x0, x1 = int(body[:, 1].min()) + x0, int(body[:, 1].max()) + x0
        y0, y1 = int(body[:, 0].min()) + y0, int(body[:, 0].max()) + y0
    if top_only:
        center = np.array([(x0 + x1) / 2, (y0 + y1) / 2])
        dots = []
        for component in red_components:
            if not 3 <= len(component) <= 200:
                continue
            component_x = component[:, 1] + int(xs.min())
            component_y = component[:, 0] + int(ys.min())
            if (component_x.min() >= x0 and component_x.max() <= x1
                    and component_y.min() >= y0 and component_y.max() <= y1):
                dots.append((np.linalg.norm(
                    np.array([component_x.mean(), component_y.mean()]) - center),
                    component_x, component_y))
        if dots:
            _, dot_x, dot_y = min(dots, key=lambda item: item[0])
            return (int(np.median(dot_x)), int(np.median(dot_y)), [x0, y0, x1, y1])
        raise AssertionError("Radio top control is not visible")
    crop = rgb[y0:y1 + 1, x0:x1 + 1]
    dark = crop.max(axis=2) < 100
    visited = np.zeros(dark.shape, dtype=bool)
    components = []
    for start_y, start_x in zip(*np.nonzero(dark)):
        if visited[start_y, start_x]:
            continue
        stack = [(int(start_y), int(start_x))]
        visited[start_y, start_x] = True
        points = []
        while stack:
            point_y, point_x = stack.pop()
            points.append((point_y, point_x))
            for delta_y in (-1, 0, 1):
                for delta_x in (-1, 0, 1):
                    next_y, next_x = point_y + delta_y, point_x + delta_x
                    if (0 <= next_y < dark.shape[0] and 0 <= next_x < dark.shape[1]
                            and dark[next_y, next_x] and not visited[next_y, next_x]):
                        visited[next_y, next_x] = True
                        stack.append((next_y, next_x))
        if not 20 <= len(points) <= 400:
            continue
        component = np.asarray(points, dtype=int)
        center_y, center_x = component.mean(axis=0)
        height = int(component[:, 0].max() - component[:, 0].min() + 1)
        width = int(component[:, 1].max() - component[:, 1].min() + 1)
        aspect = min(height, width) / max(height, width)
        fill = len(points) / (height * width)
        if top_only and (len(points) < 20 or width < height or aspect < .25 or fill > .5):
            continue
        local = crop[max(0, int(center_y) - 8):min(crop.shape[0], int(center_y) + 9),
                     max(0, int(center_x) - 8):min(crop.shape[1], int(center_x) + 9)]
        bright_face = ((local.min(axis=2) > 100)
                       & ((local.max(axis=2) - local.min(axis=2)) < 80)).mean()
        red_center = ((local[:, :, 0] > 145)
                      & (local[:, :, 0] > 2 * local[:, :, 1])
                      & (local[:, :, 0] > 2 * local[:, :, 2])).mean()
        centered = 1.0 - min(1.0, np.linalg.norm(
            np.array([center_x, center_y]) - np.array([(x1 - x0) / 2, (y1 - y0) / 2])
        ) / max(1.0, np.hypot(x1 - x0, y1 - y0) / 2))
        if top_only:
            vertical = 1.0 - min(1.0, abs(center_y / max(1, y1 - y0) - .4) / .4)
            score = 2.0 * centered + vertical + .2 * aspect + .2 * bright_face
        else:
            score = 2.0 * aspect + 1.5 * red_center + .5 * centered + .25 * bright_face
        components.append((float(score), component))
    assert components, "Dark front control is not visible"
    _, component = max(components, key=lambda item: item[0])
    return (int(np.median(component[:, 1])) + x0,
            int(np.median(component[:, 0])) + y0,
            [x0, y0, x1, y1])

view_camera = "right_wrist"
obs, rgb, xs, ys = held_radio_pixels(view_camera)
if len(xs) < 20:
    view_camera = "head"
    obs, rgb, xs, ys = held_radio_pixels(view_camera)
assert len(xs) >= 20, "Held radio front is not visible after grasp"
hand, hand_quat = get_current_eef_pose(arm=1)
camera = obs["world_from_camera"]
camera_hand = np.linalg.inv(camera) @ np.array([hand[0], hand[1], hand[2], 1.0])
shift = min(.03, max(0.0, camera_hand[0] - .10))
if shift > 0 and move_hand((hand - camera[:3, 0] * shift, hand_quat), arm=1, lock_last_trunk=True):
    save_current_observation("after_presentation_0")

# The demonstration exposes the top control by rolling the held radio. Probe a
# few wrist poses and keep the first RGB view containing the round control.
base_rotation = Rotation.from_quat(hand_quat[[1, 2, 3, 0]])
presentation_poses = [("current", base_rotation)]
for axis in ("x", "y", "z"):
    for angle in (np.pi / 2, -np.pi / 2):
        presentation_poses.append((axis + str(angle), base_rotation * Rotation.from_euler(axis, angle)))
found_button = False
for presentation_step, (_, presentation_rotation) in enumerate(presentation_poses):
    hand, _ = get_current_eef_pose(arm=1)
    presentation_quat = presentation_rotation.as_quat()[[3, 0, 1, 2]]
    if presentation_step and not move_hand((hand, presentation_quat), arm=1, lock_last_trunk=True):
        continue
    save_current_observation("after_presentation_" + str(presentation_step))
    for presentation_camera in ("head", "right_wrist", "left_wrist"):
        save_current_observation("after_presentation_" + str(presentation_step) + "_" + presentation_camera,
                                 presentation_camera)
        candidate_obs, candidate_rgb, candidate_xs, candidate_ys = held_radio_pixels(presentation_camera)
        if len(candidate_xs) < 20:
            continue
        try:
            find_button(candidate_rgb, candidate_xs, candidate_ys, top_only=True)
        except AssertionError:
            continue
        view_camera = presentation_camera
        obs, rgb, xs, ys = candidate_obs, candidate_rgb, candidate_xs, candidate_ys
        found_button = True
        break
    if found_button:
        break
assert found_button, "Held radio top control is not visible after presentation"

pressed = False
button_x = button_y = -1
for press_attempt in range(3):
    obs, rgb, xs, ys = held_radio_pixels(view_camera)
    assert len(xs) >= 20, "Held radio front is not visible after press"
    button_x, button_y, bbox = find_button(rgb, xs, ys, top_only=True)
    print("candidate", candidate, "press_attempt", press_attempt,
          "held bbox", bbox, "button", [button_x, button_y])
    press_ok = press_at_pixel(button_x, button_y, camera=view_camera, travel=.03, arm=0,
                              surface_offset=.08)
    pressed = bool(pressed or press_ok)
    save_current_observation("after_power_press_" + str(press_attempt))
    if not press_ok:
        continue
    current, current_rgb, current_xs, current_ys = held_radio_pixels(view_camera)
    if len(current_xs) < 20:
        break
    green = ((current_rgb[current_ys, current_xs, 1] > 80)
             & (current_rgb[current_ys, current_xs, 1] > 1.25 * current_rgb[current_ys, current_xs, 0])
             & (current_rgb[current_ys, current_xs, 1] > 1.10 * current_rgb[current_ys, current_xs, 2]))
    if np.count_nonzero(green) >= 3:
        break
RESULT = {"candidate": candidate, "grasp_motor_completed": bool(completed),
          "button_pixel": [button_x, button_y], "press_motor_completed": bool(pressed),
          "grasp_backend": grasp_backend,
          "grounding_backend": "Codex RGB pixels + current depth + Contact-GraspNet"}
