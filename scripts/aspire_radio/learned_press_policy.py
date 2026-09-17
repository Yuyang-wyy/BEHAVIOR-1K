# Code block 1
import numpy as np
from scipy.spatial.transform import Rotation

obs = get_observation()

def dark_control_in(mask, rgb):
    ys, xs = np.nonzero(mask)
    x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
    dark = rgb[y0:y1 + 1, x0:x1 + 1].max(axis=2) < 100
    visited = np.zeros(dark.shape, dtype=bool)
    choices = []
    for start_y, start_x in zip(*np.nonzero(dark)):
        if visited[start_y, start_x]:
            continue
        stack = [(int(start_y), int(start_x))]
        visited[start_y, start_x] = True
        pixels = []
        while stack:
            py, px = stack.pop()
            pixels.append((py, px))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = py + dy, px + dx
                    if (0 <= ny < dark.shape[0] and 0 <= nx < dark.shape[1]
                            and dark[ny, nx] and not visited[ny, nx]):
                        visited[ny, nx] = True
                        stack.append((ny, nx))
        cy, cx = np.asarray(pixels).T
        if not 20 <= len(cx) <= 400:
            continue
        height, width = cy.max() - cy.min() + 1, cx.max() - cx.min() + 1
        aspect = min(height, width) / max(height, width)
        centered = 1.0 - min(1.0, np.hypot(cx.mean() - (x1 - x0) / 2,
                                           cy.mean() - (y1 - y0) / 2) /
                             max(1.0, np.hypot(x1 - x0, y1 - y0) / 2))
        choices.append((2.0 * aspect + .5 * centered, int(np.median(cx)) + x0,
                        int(np.median(cy)) + y0))
    return max(choices, default=None)

def observed_radio(observation, near_position=None):
    image = observation["rgb"].astype(float)
    depth = observation["depth"]
    valid = ((image[..., 0] > 145) & (image[..., 0] > 2 * image[..., 1])
             & (image[..., 0] > 2 * image[..., 2])
             & np.isfinite(depth) & (depth > 0) & (depth < 10))
    visited = np.zeros(valid.shape, dtype=bool)
    components = []
    for start_y, start_x in zip(*np.nonzero(valid)):
        if visited[start_y, start_x]:
            continue
        stack = [(int(start_y), int(start_x))]
        visited[start_y, start_x] = True
        pixels = []
        while stack:
            y0, x0 = stack.pop()
            pixels.append((y0, x0))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    y1, x1 = y0 + dy, x0 + dx
                    if (0 <= y1 < valid.shape[0] and 0 <= x1 < valid.shape[1]
                            and valid[y1, x1] and not visited[y1, x1]):
                        visited[y1, x1] = True
                        stack.append((y1, x1))
        if len(pixels) < 12:
            continue
        pixels = np.asarray(pixels, dtype=int)
        component_mask = np.zeros(valid.shape, dtype=bool)
        component_mask[pixels[:, 0], pixels[:, 1]] = True
        world = mask_to_world_points(component_mask, depth, observation["intrinsics"],
                                     observation["world_from_camera"])
        if len(world) < 12:
            continue
        extent = np.percentile(world, 95, axis=0) - np.percentile(world, 5, axis=0)
        center = np.median(world, axis=0)
        if not .075 <= float(np.max(extent)) <= .45:
            continue
        if near_position is not None and np.linalg.norm(center - near_position) > .55:
            continue
        components.append((len(world), center, pixels))
    if not components:
        return None
    _, center, _ = max(components, key=lambda item: item[0])
    all_y, all_x = np.nonzero(valid)
    all_world = mask_to_world_points(valid, depth, observation["intrinsics"],
                                     observation["world_from_camera"])
    nearby = np.linalg.norm(all_world - center, axis=1) < .35
    mask = np.zeros(valid.shape, dtype=bool)
    mask[all_y[nearby], all_x[nearby]] = True
    points = mask_to_world_points(mask, depth, observation["intrinsics"],
                                  observation["world_from_camera"])
    return mask, points

def observed_support_surface(observation, object_points):
    depth = observation["depth"]
    valid = np.isfinite(depth) & (depth > 0) & (depth < 10)
    ys, xs = np.nonzero(valid)
    world = mask_to_world_points(valid, depth, observation["intrinsics"],
                                 observation["world_from_camera"])
    object_center = np.median(object_points, axis=0)
    surface_height = float(np.percentile(object_points[:, 2], 2) - .075)
    on_surface = ((np.abs(world[:, 2] - surface_height) < .03)
                  & (np.linalg.norm(world[:, :2] - object_center[:2], axis=1) < 1.5))
    surface = np.zeros(valid.shape, dtype=bool)
    surface[ys[on_surface], xs[on_surface]] = True
    visited = np.zeros(valid.shape, dtype=bool)
    components = []
    for start_y, start_x in zip(*np.nonzero(surface)):
        if visited[start_y, start_x]:
            continue
        stack = [(int(start_y), int(start_x))]
        visited[start_y, start_x] = True
        pixels = []
        while stack:
            y0, x0 = stack.pop()
            pixels.append((y0, x0))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    y1, x1 = y0 + dy, x0 + dx
                    if (0 <= y1 < surface.shape[0] and 0 <= x1 < surface.shape[1]
                            and surface[y1, x1] and not visited[y1, x1]):
                        visited[y1, x1] = True
                        stack.append((y1, x1))
        if len(pixels) >= 500:
            pixels = np.asarray(pixels, dtype=int)
            component_mask = np.zeros(valid.shape, dtype=bool)
            component_mask[pixels[:, 0], pixels[:, 1]] = True
            points = mask_to_world_points(component_mask, depth, observation["intrinsics"],
                                          observation["world_from_camera"])
            distance = np.linalg.norm(np.median(points[:, :2], axis=0) - object_center[:2])
            components.append((distance, points))
    assert components, "No visual support surface found under radio"
    return min(components, key=lambda item: item[0])[1]

best_radio = None
best_observation = None
for search_step in range(8):
    obs = get_observation()
    detected = observed_radio(obs)
    if detected is not None:
        mask, points = detected
        if best_radio is None or len(points) > len(best_radio):
            best_radio = points
            best_observation = obs
            save_current_observation("radio_search_candidate_" + str(search_step))
        if len(points) >= 500:
            break
    assert rotate_base(np.pi / 4)
assert best_radio is not None, "No radio-sized red object found in a full visual scan"
radio = np.median(best_radio, axis=0)
assert lift_arm(arm=0, distance=.2, lock_last_trunk=True)
assert lift_arm(arm=1, distance=.2, lock_last_trunk=True)
table_points = observed_support_surface(best_observation, best_radio)
goal = get_navigation_pose(table_points, best_radio)
base, _, _ = get_robot_position()
edge = goal[:2] - radio[:2]
edge_distance = np.linalg.norm(edge)
skill_radius = float(np.hypot(1.18, .18))
if .4 < edge_distance < skill_radius:
    edge_normal = edge / edge_distance
    edge_tangent = np.array([-edge_normal[1], edge_normal[0]])
    tangent_sign = np.sign(np.dot(base[:2] - radio[:2], edge_tangent)) or 1.0
    goal[:2] = (radio[:2] + edge
                + tangent_sign * edge_tangent * np.sqrt(skill_radius ** 2 - edge_distance ** 2))
    bearing = np.arctan2(radio[1] - goal[1], radio[0] - goal[0])
    goal[2] = bearing - np.arctan2(.18, 1.18)
if abs(goal[0] - radio[0]) > abs(goal[1] - radio[1]):
    waypoint = np.array([goal[0], base[1], np.arctan2(goal[1] - base[1], 1e-6)])
else:
    waypoint = np.array([base[0], goal[1], np.arctan2(1e-6, goal[0] - base[0])])
if np.linalg.norm(waypoint[:2] - base[:2]) > .1:
    assert navigate_to_pose(waypoint)
assert navigate_to_pose(goal)
save_current_observation("before_grasp")

# Code block 2
obs = get_observation()
detected = observed_radio(obs)
assert detected is not None, "Radio was not visible after navigation"
mask, points = detected
radio_center = np.median(points, axis=0)

# Stage the free hand before grasping.  This keeps the press arm near the
# demonstrated contact posture while the holder later takes the radio.
base, _, yaw = get_robot_position()
base_forward = np.array([np.cos(yaw), np.sin(yaw), 0.0])
base_left = np.array([-np.sin(yaw), np.cos(yaw), 0.0])
direction = radio_center - obs["world_from_camera"][:3, 3]
direction /= np.linalg.norm(direction)
reference = np.array([0, 0, 1]) if abs(direction[2]) < 0.9 else np.array([0, 1, 0])
axis_x = np.cross(reference, direction)
axis_x /= np.linalg.norm(axis_x)
axis_y = np.cross(direction, axis_x)
stage_quat = Rotation.from_matrix(np.column_stack([axis_x, axis_y, direction])).as_quat()[[3, 0, 1, 2]]
stage_position = (radio_center - .18 * base_forward + .18 * base_left
                  - .02 * direction + np.array([0.0, 0.0, .08]))
stage_solutions = []
for _ in range(12):
    joints = solve_ik(stage_position, stage_quat, arm=0, lock_last_trunk=True)
    if joints is not None:
        stage_solutions.append(joints)
if stage_solutions:
    stage_posture = np.array([.574, .142, .425, 0.0])
    stage_joints = min(stage_solutions, key=lambda joints:
                       np.linalg.norm(joints[6:10] - stage_posture))
    move_to_joints(stage_joints)
    save_current_observation("after_left_stage")

def radio_is_held(before_height):
    hand, _ = get_current_eef_pose(arm=1)
    for camera_name in ("head", "right_wrist"):
        current = get_observation(camera_name)
        image = current["rgb"].astype(float)
        depth = current["depth"]
        red_pixels = ((image[..., 0] > 145) & (image[..., 0] > 2 * image[..., 1])
                      & (image[..., 0] > 2 * image[..., 2])
                      & np.isfinite(depth) & (depth > 0) & (depth < 10))
        world = mask_to_world_points(red_pixels, depth, current["intrinsics"],
                                     current["world_from_camera"])
        if len(world) < 20:
            continue
        nearby = world[np.linalg.norm(world - hand, axis=1) < .30]
        if len(nearby) < 20:
            continue
        center = np.median(nearby, axis=0)
        if center[2] - before_height > .04 and np.linalg.norm(center - hand) < .25:
            return True
    return False

candidate = -1
grasp_motion_completed = False
grasp_verified = False
grasp_backend = "contact-graspnet"

# The successful reference rollouts use this object-relative side grasp after
# staging the free hand.  Recompute it from current RGB-D rather than replaying
# demonstration coordinates.
for reference_round, grasp_height in enumerate((.068, .048, .088)):
    obs = get_observation()
    detected = observed_radio(obs, radio_center)
    if detected is None:
        break
    _, points = detected
    radio_center = np.median(points, axis=0)
    before_height = float(radio_center[2])
    base, _, yaw = get_robot_position()
    base_forward = np.array([np.cos(yaw), np.sin(yaw), 0.0])
    base_left = np.array([-np.sin(yaw), np.cos(yaw), 0.0])
    local_grasp_rotation = Rotation.from_quat(np.array([.11519, .99248, .03530, .02166]))
    grasp_rotation = Rotation.from_euler("z", yaw) * local_grasp_rotation
    grasp_quat = grasp_rotation.as_quat()[[3, 0, 1, 2]]
    grasp_position = (radio_center + .023 * base_forward - .008 * base_left
                      + np.array([0.0, 0.0, grasp_height]))
    pregrasp_position = (radio_center + .017 * base_forward - .015 * base_left
                         + np.array([0.0, 0.0, .188]))
    current_joints = get_current_joint_positions()
    pregrasp_solutions = []
    for _ in range(6):
        joints = solve_ik(pregrasp_position, grasp_quat, arm=1, lock_trunk=True)
        if joints is not None:
            pregrasp_solutions.append(joints)
    if pregrasp_solutions:
        open_gripper(arm=1)
        pregrasp_joints = min(pregrasp_solutions,
                              key=lambda joints: np.linalg.norm(joints - current_joints))
        move_to_joints(pregrasp_joints)
        current_joints = get_current_joint_positions()
        grasp_solutions = []
        for _ in range(6):
            joints = solve_ik(grasp_position, grasp_quat, arm=1, lock_trunk=True)
            if joints is not None:
                grasp_solutions.append(joints)
        if grasp_solutions:
            grasp_joints = min(grasp_solutions,
                               key=lambda joints: np.linalg.norm(joints - current_joints))
            move_to_joints(grasp_joints, max_joint_step=.005)
            close_gripper(arm=1)
            motion_ok = lift_arm(arm=1, distance=.12, lock_trunk=True)
            grasp_motion_completed = bool(grasp_motion_completed or motion_ok)
            grasp_verified = bool(motion_ok and radio_is_held(before_height))
            if grasp_verified:
                candidate = 0
                grasp_backend = "visual-reference"
                break
            save_current_observation("failed_reference_grasp_" + str(reference_round))
            open_gripper(arm=1)

for grasp_round in range(3):
    if grasp_verified:
        break
    obs = get_observation()
    detected = observed_radio(obs, radio_center)
    if detected is None:
        break
    mask, points = detected
    radio_center = np.median(points, axis=0)
    before_height = float(radio_center[2])
    try:
        pregrasps, grasps = sample_contact_grasp_pose(mask, arm=1, max_candidates=16)
    except (ValueError, RuntimeError):
        continue
    order = sorted(
        range(len(grasps)),
        key=lambda index: (
            not (abs(float(grasps[index][1][0])) < .20
                 and abs(float(grasps[index][1][1])) > .85),
            float(np.linalg.norm(grasps[index][0] - radio_center)),
        ),
    )
    for index in order:
        if grasps[index][0][2] <= radio_center[2] - .20:
            continue
        if solve_ik(*pregrasps[index], arm=1) is not None and solve_ik(*grasps[index], arm=1) is not None:
            motion_ok = execute_grasp(pregrasps[index], grasps[index], arm=1, lift=.12)
            grasp_motion_completed = bool(grasp_motion_completed or motion_ok)
            if motion_ok and radio_is_held(before_height):
                candidate = index
                grasp_verified = True
                break
            save_current_observation("failed_grasp_" + str(grasp_round))
            open_gripper(arm=1)
            break
    if grasp_verified:
        break
assert candidate >= 0 and grasp_verified, "No visually verified radio grasp"
save_current_observation("after_grasp")
save_current_observation("after_grasp_right", camera="right_wrist")

# Slide the grasped radio into the fixed-torso workspace shared by both arms.
base, _, _ = get_robot_position()
holder_position, holder_quat = get_current_eef_pose(arm=1)
inward = base - holder_position
inward[2] = 0.0
if np.linalg.norm(inward) > 1e-6:
    inward /= np.linalg.norm(inward)
    move_hand((holder_position + .16 * inward, holder_quat), arm=1,
              max_joint_step=.008, lock_trunk=True)
    save_current_observation("after_grasp_reposition")

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
        if x0 < 4 or y0 < 4 or x1 >= rgb.shape[1] - 4 or y1 >= rgb.shape[0] - 4:
            raise AssertionError("Radio top face is clipped")
        if (x1 - x0) < .8 * (y1 - y0):
            raise AssertionError("Radio top face is not visible")
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

held_views = []
for view_camera in ("head", "right_wrist", "left_wrist"):
    candidate_view = held_radio_pixels(view_camera)
    held_views.append((len(candidate_view[2]), view_camera, candidate_view))
_, view_camera, (obs, rgb, xs, ys) = max(held_views, key=lambda item: item[0])
assert len(xs) >= 20, "Held radio front is not visible after grasp"

# Keep the radio supported by the table and stabilized by the right grasp while
# the already-staged left fingers press the visible front control.
table_obs, table_rgb, table_xs, table_ys = held_radio_pixels("head")
held_mask = np.zeros(table_obs["depth"].shape, dtype=bool)
held_mask[table_ys, table_xs] = True
table_control = dark_control_in(held_mask, table_rgb)
if table_control is not None:
    _, table_x, table_y = table_control
    button_mask = np.zeros(table_obs["depth"].shape, dtype=bool)
    button_mask[max(0, table_y - 1):table_y + 2,
                max(0, table_x - 1):table_x + 2] = True
    button_point = np.median(mask_to_world_points(
        button_mask, table_obs["depth"], table_obs["intrinsics"],
        table_obs["world_from_camera"]), axis=0)
    close_gripper(arm=0)
    holder_position, holder_quat = get_current_eef_pose(arm=1)
    holder_rotation = Rotation.from_quat(holder_quat[[1, 2, 3, 0]])
    button_in_holder = holder_rotation.inv().apply(button_point - holder_position)
    left_position, left_quat = get_current_eef_pose(arm=0)
    finger_center = get_current_finger_center(arm=0)
    contact_position = left_position + button_point - finger_center
    print("table geometry", "button", button_point.tolist(),
          "left", left_position.tolist(), "right", holder_position.tolist())
    paired = False
    for fraction in (.2, .4, .6, .8, 1.0):
        stage_position = left_position + fraction * (contact_position - left_position)
        stage_solutions = []
        for _ in range(3):
            joints = solve_ik(stage_position, left_quat, arm=0, lock_trunk=True)
            if joints is not None:
                stage_solutions.append(joints)
        if not stage_solutions:
            continue
        current_joints = get_current_joint_positions()
        move_to_joints(min(stage_solutions,
                           key=lambda joints: np.linalg.norm(joints - current_joints)),
                       max_joint_step=.008)
        finger_center = get_current_finger_center(arm=0)
        holder_target = finger_center - holder_rotation.apply(button_in_holder)
        holder_solutions = []
        for _ in range(4):
            joints = solve_ik(holder_target, holder_quat, arm=1, lock_trunk=True)
            if joints is not None:
                holder_solutions.append(joints)
        if not holder_solutions:
            continue
        current_joints = get_current_joint_positions()
        move_to_joints(min(holder_solutions,
                           key=lambda joints: np.linalg.norm(joints - current_joints)),
                       max_joint_step=.005)
        save_current_observation("after_stationary_table_press")
        paired = True
        break
    if not paired:
        press_at_pixel(table_x, table_y, camera="head", arm=0, surface_offset=.02)
    save_current_observation("after_table_press")

# Rotate only after lifting clear of the table, then keep the first pose where
# RGB exposes the round control on the upper face.
assert lift_arm(arm=1, distance=.18, lock_last_trunk=True), "Could not raise radio for presentation"
base, _, yaw = get_robot_position()
base_forward = np.array([np.cos(yaw), np.sin(yaw), 0.0])
base_left = np.array([-np.sin(yaw), np.cos(yaw), 0.0])
ready_position = base + 1.05 * base_forward - .12 * base_left
ready_position[2] = .85
ready_local_rotation = Rotation.from_quat(np.array([.91720, .14978, .36443, -.05926]))
ready_rotation = Rotation.from_euler("z", yaw) * ready_local_rotation
ready_quat = ready_rotation.as_quat()[[3, 0, 1, 2]]
current_joints = get_current_joint_positions()
ready_solutions = []
for _ in range(12):
    joints = solve_ik(ready_position, ready_quat, arm=0)
    if joints is not None:
        ready_solutions.append(joints)
assert ready_solutions, "Could not solve free-finger staging pose"
ready_joints = min(ready_solutions, key=lambda joints: np.linalg.norm(joints - current_joints))
move_to_joints(ready_joints)
ready_actual, _ = get_current_eef_pose(arm=0)
assert np.linalg.norm(ready_actual - ready_position) < .03, "Could not stage free fingers"
safe_position, safe_quat = get_current_eef_pose(arm=1)
safe_rotation = Rotation.from_quat(safe_quat[[1, 2, 3, 0]])
presentation_rotations = [safe_rotation]
for axis in ("x", "y", "z"):
    for angle in (np.pi / 2, -np.pi / 2):
        presentation_rotations.append(safe_rotation * Rotation.from_euler(axis, angle))
found_button = False
for presentation_step, presentation_rotation in enumerate(presentation_rotations):
    presentation_quat = presentation_rotation.as_quat()[[3, 0, 1, 2]]
    if presentation_step and not move_hand((safe_position, presentation_quat), arm=1,
                                           lock_last_trunk=True):
        move_hand((safe_position, safe_quat), arm=1, lock_last_trunk=True)
        continue
    for presentation_camera in ("head", "right_wrist", "left_wrist"):
        candidate_view = held_radio_pixels(presentation_camera)
        if len(candidate_view[2]) < 20:
            continue
        try:
            button_x, button_y, bbox = find_button(candidate_view[1], candidate_view[2],
                                                   candidate_view[3], top_only=True)
        except AssertionError:
            continue
        view_camera = presentation_camera
        obs, rgb, xs, ys = candidate_view
        found_button = True
        break
    if found_button:
        break
assert found_button, "Held radio top control is not visible after raised presentation"
button_mask = np.zeros(obs["depth"].shape, dtype=bool)
button_mask[max(0, button_y - 1):button_y + 2, max(0, button_x - 1):button_x + 2] = True
button_points = mask_to_world_points(button_mask, obs["depth"], obs["intrinsics"],
                                     obs["world_from_camera"])
button_point = np.median(button_points, axis=0)
print("candidate", candidate, "raised held bbox", bbox, "button", [button_x, button_y])
finger_center = get_current_finger_center(arm=0)
hand, hand_quat = get_current_eef_pose(arm=1)
holder_rotation = Rotation.from_quat(hand_quat[[1, 2, 3, 0]])
button_in_holder = holder_rotation.inv().apply(button_point - hand)
current_joints = get_current_joint_positions()
holder_solutions = []
for holder_delta in ([0.0, 0.0, 0.0], [0.0, 0.0, np.pi / 4],
                     [0.0, 0.0, -np.pi / 4], [np.pi / 4, 0.0, 0.0],
                     [-np.pi / 4, 0.0, 0.0], [0.0, np.pi / 4, 0.0],
                     [0.0, -np.pi / 4, 0.0], [0.0, 0.0, np.pi / 2],
                     [0.0, 0.0, -np.pi / 2], [np.pi / 2, 0.0, 0.0],
                     [-np.pi / 2, 0.0, 0.0], [0.0, np.pi / 2, 0.0],
                     [0.0, -np.pi / 2, 0.0]):
    target_rotation = holder_rotation * Rotation.from_rotvec(holder_delta)
    target_quat = target_rotation.as_quat()[[3, 0, 1, 2]]
    holder_target = finger_center - target_rotation.apply(button_in_holder)
    for _ in range(3):
        joints = solve_ik(holder_target, target_quat, arm=1, lock_trunk=True)
        if joints is not None:
            holder_solutions.append(joints)
pressed = False
if holder_solutions:
    holder_joints = min(holder_solutions,
                        key=lambda joints: np.linalg.norm(joints - current_joints))
    pressed = move_to_joints(holder_joints, max_joint_step=.005)
save_current_observation("after_power_press")
RESULT = {"candidate": candidate, "grasp_motor_completed": bool(grasp_motion_completed),
          "grasp_verified": bool(grasp_verified),
          "button_pixel": [button_x, button_y], "press_motor_completed": bool(pressed),
          "grasp_backend": grasp_backend,
          "grounding_backend": "Codex RGB pixels + current depth + Contact-GraspNet"}
