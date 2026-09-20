# Code block 1
import numpy as np
from scipy.spatial.transform import Rotation

def find_button(rgb, xs, ys, top_only=False):
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    if top_only and (x1 - x0) < .35 * (y1 - y0):
        raise AssertionError("Radio top face is not visible")
    if top_only and (x0 < 10 or y0 < 10 or x1 >= rgb.shape[1] - 10
                     or y1 >= rgb.shape[0] - 10):
        raise AssertionError("Radio top face is clipped")
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
            if component is body or not 60 <= len(component) <= max(400, len(body) // 4):
                continue
            component_x = component[:, 1] + int(xs.min())
            component_y = component[:, 0] + int(ys.min())
            if (component_x.min() < x0 or component_x.max() > x1
                    or component_y.min() < y0 or component_y.max() > y1):
                continue
            height = component_y.max() - component_y.min() + 1
            width = component_x.max() - component_x.min() + 1
            aspect = min(height, width) / max(height, width)
            if aspect < .45:
                continue
            component_center = np.array([component_x.mean(), component_y.mean()])
            relative_center = ((component_center - np.array([x0, y0]))
                               / np.array([max(1, x1 - x0), max(1, y1 - y0)]))
            if np.any(relative_center < .05) or np.any(relative_center > .95):
                continue
            radius = max(5, int(max(height, width) * 1.8))
            crop_x0 = max(0, int(component_center[0] - radius))
            crop_x1 = min(rgb.shape[1], int(component_center[0] + radius + 1))
            crop_y0 = max(0, int(component_center[1] - radius))
            crop_y1 = min(rgb.shape[0], int(component_center[1] + radius + 1))
            ring_y, ring_x = np.ogrid[crop_y0:crop_y1, crop_x0:crop_x1]
            distance = np.hypot(ring_x - component_center[0], ring_y - component_center[1])
            ring = ((distance >= .7 * max(height, width))
                    & (distance <= 1.8 * max(height, width)))
            dark = rgb[crop_y0:crop_y1, crop_x0:crop_x1].max(axis=2) < 100
            dark_surround = float(dark[ring].mean())
            if dark_surround >= .20:
                dots.append((-dark_surround, np.linalg.norm(component_center - center),
                             component_x, component_y))
        if dots:
            _, _, dot_x, dot_y = min(dots, key=lambda item: item[:2])
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

obs = get_observation()

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
assert lift_arm(arm=0, distance=.12, lock_last_trunk=True)
assert lift_arm(arm=1, distance=.12, lock_last_trunk=True)
table_points = observed_support_surface(best_observation, best_radio)
goal = get_navigation_pose(table_points, best_radio)
base, _, _ = get_robot_position()
skill_radius = .80
approach = base[:2] - radio[:2]
if np.linalg.norm(approach) > 1e-6:
    # Edge selection can choose the far side of a wide table. Approach the
    # observed radio from the robot's current side at the demonstrated radius.
    goal[:2] = radio[:2] + approach / np.linalg.norm(approach) * skill_radius
    goal[2] = np.arctan2(radio[1] - goal[1], radio[0] - goal[0])
edge = goal[:2] - radio[:2]
edge_distance = np.linalg.norm(edge)
# Training demonstrations first grasp at median base-to-radio distance .794 m.
if .4 < edge_distance < skill_radius:
    edge_normal = edge / edge_distance
    edge_tangent = np.array([-edge_normal[1], edge_normal[0]])
    tangent_sign = np.sign(np.dot(base[:2] - radio[:2], edge_tangent)) or 1.0
    goal[:2] = (radio[:2] + edge
                + tangent_sign * edge_tangent * np.sqrt(skill_radius ** 2 - edge_distance ** 2))
    bearing = np.arctan2(radio[1] - goal[1], radio[0] - goal[0])
    goal[2] = bearing - np.arcsin(.18 / skill_radius)
if abs(goal[0] - radio[0]) > abs(goal[1] - radio[1]):
    waypoint = np.array([goal[0], base[1], np.arctan2(goal[1] - base[1], 1e-6)])
else:
    waypoint = np.array([base[0], goal[1], np.arctan2(1e-6, goal[0] - base[0])])
if np.linalg.norm(waypoint[:2] - base[:2]) > .1:
    # A straight staging waypoint can be blocked by furniture; the visual
    # dock remains the meaningful goal and the navigation helper is bounded.
    navigate_to_pose(waypoint)
navigated = navigate_to_pose(goal)
save_current_observation("before_grasp")

# The task goal is only toggled_on. Try the visible control on its support
# before incurring the extra uncertainty of picking up and presenting it.
for table_press_attempt in range(2):
    table_button = None
    for table_camera in ("head", "right_wrist", "left_wrist"):
        table_obs = get_observation(table_camera)
        table_radio = observed_radio(table_obs)
        if table_radio is None:
            continue
        table_ys, table_xs = np.nonzero(table_radio[0])
        try:
            table_x, table_y, _ = find_button(
                table_obs["rgb"].astype(float), table_xs, table_ys, top_only=True)
        except AssertionError:
            continue
        table_button = (table_x, table_y, table_camera)
        break
    if table_button is None:
        break
    table_x, table_y, table_camera = table_button
    save_current_observation("table_press_" + str(table_press_attempt), table_camera)
    press_at_pixel(table_x, table_y, camera=table_camera, arm=1, travel=.03,
                   surface_offset=.04 * table_press_attempt, allow_torso=True)

# Code block 2
obs = get_observation()
detected = observed_radio(obs)
assert detected is not None, "Radio was not visible after navigation"
mask, points = detected
radio_center = np.median(points, axis=0)

# Stage the free hand before grasping. This keeps the press arm near the radio
# while allowing IK to choose a trunk state from the current observed geometry.
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
# Capture this staged torso / free-arm posture for post-grasp normalization.
right_position, right_quat = get_current_eef_pose(arm=1)
solve_ik(right_position, right_quat, arm=1, lock_trunk=True)

grasp_probe_count = 0

def radio_is_held(before_height):
    global grasp_probe_count
    hand, quat = get_current_eef_pose(arm=1)
    for camera_name in ("right_wrist", "head"):
        detected = observed_radio(get_observation(camera_name), hand)
        if detected is None:
            continue
        center = np.median(detected[1], axis=0)
        if center[2] - before_height <= .035 or np.linalg.norm(center - hand) >= .30:
            continue
        grasp_probe_count += 1
        stem = "grasp_probe_" + str(grasp_probe_count)
        save_current_observation(stem + "_before", camera_name)
        # Nearby radio pixels alone can describe an empty hand above a table.
        # Require the observed radio to follow a separate closed-gripper lift.
        if not move_hand((hand + np.array([0.0, 0.0, .08]), quat), arm=1,
                         max_joint_step=.01, lock_last_trunk=True):
            return False
        moved_hand, _ = get_current_eef_pose(arm=1)
        displacement = moved_hand - hand
        save_current_observation(stem + "_after", camera_name)
        after = observed_radio(get_observation(camera_name), center + displacement)
        if after is None or np.linalg.norm(displacement) < .045:
            return False
        object_displacement = np.median(after[1], axis=0) - center
        follows = (np.linalg.norm(object_displacement) > .04
                   and np.linalg.norm(object_displacement - displacement) < .035
                   and np.dot(object_displacement, displacement) > .8
                   * np.linalg.norm(object_displacement) * np.linalg.norm(displacement))
        print("grasp_probe", stem, "hand_delta", displacement.tolist(),
              "radio_delta", object_displacement.tolist(), "follows", bool(follows))
        return bool(follows)
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
        detected = observed_radio(obs)
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
        joints = solve_ik(pregrasp_position, grasp_quat, arm=1, lock_last_trunk=True)
        if joints is not None:
            pregrasp_solutions.append(joints)
    if pregrasp_solutions:
        open_gripper(arm=1)
        pregrasp_joints = min(pregrasp_solutions,
                              key=lambda joints: np.linalg.norm(joints - current_joints))
        if not move_to_joints(pregrasp_joints):
            continue
        current_joints = get_current_joint_positions()
        grasp_solutions = []
        for _ in range(6):
            joints = solve_ik(grasp_position, grasp_quat, arm=1, lock_last_trunk=True)
            if joints is not None:
                grasp_solutions.append(joints)
        if grasp_solutions:
            grasp_joints = min(grasp_solutions,
                               key=lambda joints: np.linalg.norm(joints - current_joints))
            if not move_to_joints(grasp_joints, max_joint_step=.005):
                continue
            close_gripper(arm=1)
            motion_ok = lift_arm(arm=1, distance=.12, lock_last_trunk=True)
            grasp_motion_completed = bool(grasp_motion_completed or motion_ok)
            grasp_verified = bool(motion_ok and radio_is_held(before_height))
            if grasp_verified:
                candidate = 0
                grasp_backend = "visual-reference"
                break
            save_current_observation("failed_reference_grasp_" + str(reference_round))
            open_gripper(arm=1)
            move_hand((right_position, right_quat), arm=1, lock_trunk=True)

for grasp_round in range(3):
    if grasp_verified:
        break
    obs = get_observation()
    detected = observed_radio(obs, radio_center)
    if detected is None:
        detected = observed_radio(obs)
    if detected is None:
        break
    mask, points = detected
    radio_center = np.median(points, axis=0)
    before_height = float(radio_center[2])
    pregrasps, grasps = [], []
    for _ in range(2):
        try:
            sampled_pregrasps, sampled_grasps = sample_contact_grasp_pose(
                mask, arm=1, max_candidates=16)
        except (ValueError, RuntimeError):
            continue
        pregrasps.extend(sampled_pregrasps)
        grasps.extend(sampled_grasps)
    if not grasps:
        continue
    current_joints = get_current_joint_positions()
    feasible = []
    for index in range(len(grasps)):
        if grasps[index][0][2] <= radio_center[2] - .20:
            continue
        pregrasp_joints = solve_ik(*pregrasps[index], arm=1)
        grasp_joints = solve_ik(*grasps[index], arm=1)
        if pregrasp_joints is not None and grasp_joints is not None:
            feasible.append((float(np.max(np.abs(pregrasp_joints - current_joints))), index,
                             pregrasp_joints, grasp_joints))
    if feasible:
        _, index, pregrasp_joints, grasp_joints = min(feasible, key=lambda item: item[0])
        open_gripper(arm=1)
        motion_ok = move_to_joints(pregrasp_joints)
        if motion_ok:
            # Seed contact IK from the reached pregrasp, not the earlier pose.
            grasp_joints = solve_ik(*grasps[index], arm=1)
            motion_ok = bool(grasp_joints is not None
                             and move_to_joints(grasp_joints, max_joint_step=.005))
        if motion_ok:
            close_gripper(arm=1)
            motion_ok = lift_arm(arm=1, distance=.12)
        grasp_motion_completed = bool(grasp_motion_completed or motion_ok)
        if motion_ok and radio_is_held(before_height):
            candidate = index
            grasp_verified = True
            break
        save_current_observation("failed_grasp_" + str(grasp_round))
        open_gripper(arm=1)
        move_hand((right_position, right_quat), arm=1, lock_trunk=True)
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
    target_pose = (holder_position + .16 * inward, holder_quat)
    move_hand(target_pose, arm=1, max_joint_step=.008, lock_trunk=True)
    save_current_observation("after_grasp_reposition")

# Normalize the holder after the visual lift. This is one offline posture prior,
# not a trajectory: the medoid of 200 training pre-toggle action postures
# (raw episode 600, frame 1280). Keep the free arm clear during this rotation;
# moving it to a contact posture first can obstruct the differently held radio.
assert move_to_posture(
    arm=0,
    arm_joints=np.zeros(7),
    trunk_joints=np.array([.95217, -1.31700, -.55497, 0.0]),
    max_joint_step=.008,
)
assert move_to_posture(
    arm=1,
    arm_joints=np.array([-.79518, .11351, .20091, -.77596, .24680, .77338, .72667]),
    max_joint_step=.008,
)
save_current_observation("after_demo_press_posture")

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


held_views = []
for view_camera in ("head", "right_wrist", "left_wrist"):
    candidate_view = held_radio_pixels(view_camera)
    held_views.append((len(candidate_view[2]), view_camera, candidate_view))
_, view_camera, (obs, rgb, xs, ys) = max(held_views, key=lambda item: item[0])
assert len(xs) >= 20, "Held radio front is not visible after grasp"

# Recenter the held radio in the head view before rotating it.  Contact-GraspNet
# grasps can otherwise leave the radio clipped at the image edge.
for recenter_step in range(8):
    from_wrist = False
    obs, rgb, xs, ys = held_radio_pixels("head")
    if len(xs) < 20:
        wrist_obs, _, wrist_xs, wrist_ys = held_radio_pixels("right_wrist")
        if len(wrist_xs) < 20:
            break
        obs = wrist_obs
        xs, ys = wrist_xs, wrist_ys
        from_wrist = True
    held_mask = np.zeros(obs["depth"].shape, dtype=bool)
    held_mask[ys, xs] = True
    visible_center = np.median(mask_to_world_points(
        held_mask, obs["depth"], obs["intrinsics"], obs["world_from_camera"]), axis=0)
    if not from_wrist:
        depth = float(np.median(obs["depth"][ys, xs]))
        height, width = obs["depth"].shape
        ray = np.linalg.solve(obs["intrinsics"], np.array([.64 * width, .55 * height, 1.0])) * depth
        desired_center = ((ray * np.array([1.0, -1.0, -1.0]))
                          @ obs["world_from_camera"][:3, :3].T
                          + obs["world_from_camera"][:3, 3])
    else:
        head = get_observation("head")
        depth = float(np.linalg.norm(visible_center - head["world_from_camera"][:3, 3]))
        height, width = head["depth"].shape
        ray = np.linalg.solve(head["intrinsics"], np.array([.5 * width, .55 * height, 1.0])) * depth
        desired_center = ((ray * np.array([1.0, -1.0, -1.0]))
                          @ head["world_from_camera"][:3, :3].T
                          + head["world_from_camera"][:3, 3])
    correction = desired_center - visible_center
    correction *= min(1.0, .10 / max(1e-6, np.linalg.norm(correction)))
    holder_position, holder_quat = get_current_eef_pose(arm=1)
    if not move_hand((holder_position + correction, holder_quat), arm=1,
                     max_joint_step=.008, lock_trunk=True):
        break
    save_current_observation("after_recenter_" + str(recenter_step))

safe_position, safe_quat = get_current_eef_pose(arm=1)
safe_rotation = Rotation.from_quat(safe_quat[[1, 2, 3, 0]])
presentation_rotations = [
    safe_rotation,
    safe_rotation * Rotation.from_euler("z", np.pi / 2),
    safe_rotation * Rotation.from_euler("z", -np.pi / 2),
    safe_rotation * Rotation.from_euler("x", -np.pi / 2),
    safe_rotation * Rotation.from_euler("x", np.pi / 2),
    safe_rotation * Rotation.from_euler("y", -np.pi / 2),
    safe_rotation * Rotation.from_euler("y", np.pi / 2),
    safe_rotation * Rotation.from_euler("x", np.pi),
    safe_rotation * Rotation.from_euler("y", np.pi),
    safe_rotation * Rotation.from_euler("z", np.pi),
]
found_button = False
for presentation_step, presentation_rotation in enumerate(presentation_rotations):
    presentation_quat = presentation_rotation.as_quat()[[3, 0, 1, 2]]
    if presentation_step:
        move_hand((safe_position, presentation_quat), arm=1,
                  max_joint_step=.03, lock_trunk=True)
    for presentation_camera in ("head", "right_wrist", "left_wrist"):
        candidate_view = held_radio_pixels(presentation_camera)
        if len(candidate_view[2]) < 20:
            continue
        save_current_observation("presentation_" + str(presentation_step) + "_" + presentation_camera,
                                 presentation_camera)
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
assert found_button, "Held radio top control is not visible after presentation"
print("candidate", candidate, "held bbox", bbox, "button", [button_x, button_y])
button_mask = np.zeros(obs["depth"].shape, dtype=bool)
button_mask[max(0, button_y - 1):button_y + 2, max(0, button_x - 1):button_x + 2] = True
button_world = np.median(mask_to_world_points(
    button_mask, obs["depth"], obs["intrinsics"], obs["world_from_camera"]), axis=0)
button_direction = button_world - obs["world_from_camera"][:3, 3]
button_direction /= np.linalg.norm(button_direction)
pressed = press_at_pixel(button_x, button_y, camera=view_camera, travel=.03,
                         arm=0, surface_offset=0.0, fixed_torso=True)
# Motor completion does not establish a toggle. If execution is still active,
# reacquire the red control before a second depth-offset attempt.
for retry_camera in ("head", "left_wrist", "right_wrist"):
    retry_view = held_radio_pixels(retry_camera)
    if len(retry_view[2]) < 20:
        continue
    try:
        retry_x, retry_y, _ = find_button(
            retry_view[1], retry_view[2], retry_view[3], top_only=True)
    except AssertionError:
        continue
    button_x, button_y = retry_x, retry_y
    obs = retry_view[0]
    button_mask = np.zeros(obs["depth"].shape, dtype=bool)
    button_mask[max(0, button_y - 1):button_y + 2,
                max(0, button_x - 1):button_x + 2] = True
    button_world = np.median(mask_to_world_points(
        button_mask, obs["depth"], obs["intrinsics"], obs["world_from_camera"]), axis=0)
    button_direction = button_world - obs["world_from_camera"][:3, 3]
    button_direction /= np.linalg.norm(button_direction)
    pressed = press_at_pixel(button_x, button_y, camera=retry_camera, travel=.03,
                             arm=0, surface_offset=.06, allow_torso=True)
    break
if not pressed:
    # The holder may have moved during a failed press attempt. Re-ground the
    # control before any bimanual fallback uses its world position.
    reacquired = False
    for reacquire_camera in (view_camera, "head", "left_wrist", "right_wrist"):
        reacquire_view = held_radio_pixels(reacquire_camera)
        if len(reacquire_view[2]) < 20:
            continue
        try:
            reacquire_x, reacquire_y, _ = find_button(
                reacquire_view[1], reacquire_view[2], reacquire_view[3], top_only=True)
        except AssertionError:
            continue
        button_x, button_y = reacquire_x, reacquire_y
        obs = reacquire_view[0]
        button_mask = np.zeros(obs["depth"].shape, dtype=bool)
        button_mask[max(0, button_y - 1):button_y + 2,
                    max(0, button_x - 1):button_x + 2] = True
        button_world = np.median(mask_to_world_points(
            button_mask, obs["depth"], obs["intrinsics"], obs["world_from_camera"]), axis=0)
        button_direction = button_world - obs["world_from_camera"][:3, 3]
        button_direction /= np.linalg.norm(button_direction)
        reacquired = True
        break
    assert reacquired, "Cannot safely fallback without a fresh button observation"
    left_position, left_quat = get_current_eef_pose(arm=0)
    finger_center = get_current_finger_center(arm=0)
    contact_position = left_position + button_world - finger_center
    holder_position, holder_quat = get_current_eef_pose(arm=1)
    holder_rotation = Rotation.from_quat(holder_quat[[1, 2, 3, 0]])
    button_in_holder = holder_rotation.inv().apply(button_world - holder_position)
    close_gripper(arm=0)
    staged_for_press = False
    for fraction in (.25, .5, .75, 1.0):
        stage_position = left_position + fraction * (contact_position - left_position)
        stage_joints = solve_ik(stage_position, left_quat, arm=0, lock_trunk=True)
        if stage_joints is None:
            continue
        move_to_joints(stage_joints, max_joint_step=.008)
        finger_center = get_current_finger_center(arm=0)
        current_joints = get_current_joint_positions()
        holder_solutions = []
        for delta in ([0.0, 0.0, 0.0], [0.0, 0.0, np.pi / 4],
                      [0.0, 0.0, -np.pi / 4], [np.pi / 4, 0.0, 0.0],
                      [-np.pi / 4, 0.0, 0.0], [0.0, np.pi / 4, 0.0],
                      [0.0, -np.pi / 4, 0.0], [0.0, 0.0, np.pi / 2],
                      [0.0, 0.0, -np.pi / 2], [np.pi / 2, 0.0, 0.0],
                      [-np.pi / 2, 0.0, 0.0], [0.0, np.pi / 2, 0.0],
                      [0.0, -np.pi / 2, 0.0]):
            target_rotation = holder_rotation * Rotation.from_rotvec(delta)
            target_quat = target_rotation.as_quat()[[3, 0, 1, 2]]
            holder_target = (finger_center + .05 * button_direction
                             - target_rotation.apply(button_in_holder))
            holder_joints = solve_ik(holder_target, target_quat, arm=1, lock_trunk=True)
            if holder_joints is not None:
                if np.linalg.norm(holder_joints[6:10] - current_joints[6:10]) > .8:
                    continue
                holder_solutions.append((np.linalg.norm(holder_joints[6:10] - current_joints[6:10]),
                                         np.linalg.norm(delta),
                                         np.linalg.norm(holder_joints - current_joints),
                                         holder_joints))
        if not holder_solutions:
            continue
        _, _, _, holder_joints = min(holder_solutions, key=lambda solution: solution[:3])
        move_to_joints(holder_joints, max_joint_step=.02)
        staged_for_press = True
        break
    if staged_for_press:
        save_current_observation("after_bimanual_stage")
        for contact_camera in ("head", "left_wrist", "right_wrist"):
            contact_view = held_radio_pixels(contact_camera)
            if len(contact_view[2]) < 20:
                continue
            try:
                contact_x, contact_y, _ = find_button(
                    contact_view[1], contact_view[2], contact_view[3], top_only=True)
            except AssertionError:
                continue
            pressed = press_at_pixel(contact_x, contact_y, camera=contact_camera,
                                     travel=.025, arm=0, fixed_torso=True)
            if pressed:
                break
save_current_observation("after_power_press")
RESULT = {"candidate": candidate, "grasp_motor_completed": bool(grasp_motion_completed),
          "grasp_verified": bool(grasp_verified),
          "button_pixel": [button_x, button_y], "press_motor_completed": bool(pressed),
          "grasp_backend": grasp_backend,
          "grounding_backend": "Codex RGB pixels + current depth + Contact-GraspNet"}
