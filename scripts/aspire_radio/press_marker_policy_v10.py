# Code block 1
"""Turn on the radio by touching its control where it stands.

The BDDL goal is only ``toggled_on``; carrying the radio is not required, so
this policy never grasps it.  Instead it grounds the control directly in RGB-D.

What the control looks like, and what is and is not used
-------------------------------------------------------
On screen the control is a small raised red cap in the middle of the dark
speaker face.  That cap is the rendered ``togglebutton`` marker mesh, i.e. the
same visual affordance the previous ``learned_press_policy.find_button``
already keyed on.  This policy reads it the same way - as a shape in the camera
image - and never calls a simulator lookup for it.  In particular the marker's
*colour state* is the goal predicate itself (red while off, green once on) and
is deliberately never tested: the detector keys on size, roundness and a dark
surround, and the run stops only when the evaluator ends the episode.

Inputs are RGB-D, proprioception, the official relative camera calibration,
static URDF finger geometry and body-velocity odometry.  One offline shape
prior about this object category is used, and only to order the search: the
body is a box roughly 0.32 m long and 0.14 m deep standing upright on a table,
so the control is on one of the two long upright faces.  No object pose,
registry entry, contact or demonstration action is read.

Sequence
--------
  1. rotating visual scan for the red radio body;
  2. dock by repeated visual re-grounding, because navigation closes the loop
     on dead-reckoned odometry and a pose computed before a multi-rotation
     scan is already stale on arrival;
  3. ground the raised cap by metric size, roundness and dark surround;
  4. push one closed fingertip along the face normal fitted from a horizontal
     depth slice, over a shallow-to-deep offset ladder;
  5. orbit to the next candidate face when the cap is not in view.
"""

import numpy as np
from scipy.spatial.transform import Rotation

TRACE = {"marker_spans": [], "press_attempts": 0, "press_completed": 0,
         "orbit_stops": 0, "marker_views": 0, "dock_iterations": 0}


def connected_components(mask, min_pixels=1):
    height, width = mask.shape
    visited = np.zeros(mask.shape, dtype=bool)
    found = []
    all_y, all_x = np.nonzero(mask)
    for start_y, start_x in zip(all_y, all_x):
        if visited[start_y, start_x]:
            continue
        stack = [(int(start_y), int(start_x))]
        visited[start_y, start_x] = True
        pixels = []
        while stack:
            point_y, point_x = stack.pop()
            pixels.append((point_y, point_x))
            for delta_y in (-1, 0, 1):
                for delta_x in (-1, 0, 1):
                    next_y, next_x = point_y + delta_y, point_x + delta_x
                    if (0 <= next_y < height and 0 <= next_x < width
                            and mask[next_y, next_x] and not visited[next_y, next_x]):
                        visited[next_y, next_x] = True
                        stack.append((next_y, next_x))
        if len(pixels) >= min_pixels:
            found.append(np.asarray(pixels, dtype=int))
    return found


def red_pixels(image):
    return ((image[..., 0] > 145) & (image[..., 0] > 2 * image[..., 1])
            & (image[..., 0] > 2 * image[..., 2]))


def observed_radio(observation, near_position=None):
    """Largest red, radio-sized point cluster, returned as (mask, world points)."""
    image = observation["rgb"].astype(float)
    depth = observation["depth"]
    valid = (red_pixels(image) & np.isfinite(depth) & (depth > 0) & (depth < 10))
    candidates = []
    for pixels in connected_components(valid, 12):
        component_mask = np.zeros(valid.shape, dtype=bool)
        component_mask[pixels[:, 0], pixels[:, 1]] = True
        world = mask_to_world_points(component_mask, depth, observation["intrinsics"],
                                     observation["world_from_camera"])
        if len(world) < 12:
            continue
        extent = np.percentile(world, 95, axis=0) - np.percentile(world, 5, axis=0)
        center = np.median(world, axis=0)
        if not .085 <= float(np.max(extent)) <= .50:
            continue
        if near_position is not None and np.linalg.norm(center - near_position) > .55:
            continue
        candidates.append((len(world), center, pixels))
    if not candidates:
        return None
    _, center, _ = max(candidates, key=lambda item: item[0])
    all_y, all_x = np.nonzero(valid)
    all_world = mask_to_world_points(valid, depth, observation["intrinsics"],
                                     observation["world_from_camera"])
    nearby = np.linalg.norm(all_world - center, axis=1) < .35
    mask = np.zeros(valid.shape, dtype=bool)
    mask[all_y[nearby], all_x[nearby]] = True
    points = mask_to_world_points(mask, depth, observation["intrinsics"],
                                  observation["world_from_camera"])
    return mask, points


def observed_table(observation, object_points):
    """Support-surface points under the observed radio."""
    depth = observation["depth"]
    valid = np.isfinite(depth) & (depth > 0) & (depth < 10)
    pixel_y, pixel_x = np.nonzero(valid)
    world = mask_to_world_points(valid, depth, observation["intrinsics"],
                                 observation["world_from_camera"])
    object_center = np.median(object_points, axis=0)
    surface_height = float(np.percentile(object_points[:, 2], 2) - .04)
    on_surface = ((np.abs(world[:, 2] - surface_height) < .05)
                  & (np.linalg.norm(world[:, :2] - object_center[:2], axis=1) < 1.6))
    if int(on_surface.sum()) < 200:
        return None
    return world[on_surface]


def find_marker(observation, radio_center):
    """Ground the raised red control cap; returns (score, x, y, point, span)."""
    image = observation["rgb"].astype(float)
    depth = observation["depth"]
    valid = (red_pixels(image) & np.isfinite(depth) & (depth > 0) & (depth < 6))
    best = None
    for pixels in connected_components(valid, 10):
        rows, columns = pixels[:, 0], pixels[:, 1]
        height = int(rows.max() - rows.min() + 1)
        width = int(columns.max() - columns.min() + 1)
        if max(height, width) > 110:
            continue
        # A blob clipped by the frame edge is not a whole cap: it only looks
        # small and round because the rest of it is off-screen, and the depth
        # there is unreliable enough to backproject it through the table.
        if (rows.min() < 2 or columns.min() < 2
                or rows.max() > image.shape[0] - 3 or columns.max() > image.shape[1] - 3):
            continue
        aspect = min(height, width) / max(height, width)
        fill = len(pixels) / float(height * width)
        if aspect < .45 or fill < .5:
            continue
        blob = np.zeros(valid.shape, dtype=bool)
        blob[rows, columns] = True
        world = mask_to_world_points(blob, depth, observation["intrinsics"],
                                     observation["world_from_camera"])
        if len(world) < 6:
            continue
        point = np.median(world, axis=0)
        if np.linalg.norm(point - radio_center) > .24:
            continue
        # The cap is on the body, not under it: the radio is only ~0.24 m tall.
        if abs(float(point[2] - radio_center[2])) > .12:
            continue
        span = float(np.max(np.percentile(world, 90, axis=0) - np.percentile(world, 10, axis=0)))
        if not .002 <= span <= .05:
            continue
        center_y, center_x = float(rows.mean()), float(columns.mean())
        radius = float(max(height, width))
        crop_y0 = max(0, int(center_y - 2.4 * radius))
        crop_y1 = min(image.shape[0], int(center_y + 2.4 * radius) + 1)
        crop_x0 = max(0, int(center_x - 2.4 * radius))
        crop_x1 = min(image.shape[1], int(center_x + 2.4 * radius) + 1)
        grid_y, grid_x = np.ogrid[crop_y0:crop_y1, crop_x0:crop_x1]
        distance = np.hypot(grid_x - center_x, grid_y - center_y)
        ring = (distance >= .85 * radius) & (distance <= 2.2 * radius)
        patch = image[crop_y0:crop_y1, crop_x0:crop_x1]
        dark = patch.max(axis=2) < 115
        surround = float(dark[ring].mean()) if bool(ring.any()) else 0.0
        if surround < .12:
            continue
        score = 2.0 * surround + fill + aspect
        if best is None or score > best[0]:
            best = (float(score), int(np.median(columns)), int(np.median(rows)), point, span)
    return best


def local_normal(observation, point):
    """Outward normal of the upright face carrying the control.

    The radio rests on a table and its control sits on a vertical face, so the
    face is recovered from a horizontal depth slice at the control's height.
    That keeps the push horizontal instead of driving the fingertip downwards
    along the depressed head-camera ray.
    """
    depth = observation["depth"]
    valid = np.isfinite(depth) & (depth > 0) & (depth < 6)
    world = mask_to_world_points(valid, depth, observation["intrinsics"],
                                 observation["world_from_camera"])
    planar = np.linalg.norm(world[:, :2] - point[:2], axis=1)
    slab = (np.abs(world[:, 2] - point[2]) < .045) & (planar > .012) & (planar < .095)
    if int(slab.sum()) < 50:
        return None
    patch = world[slab][:, :2]
    centered = patch - patch.mean(axis=0)
    values, vectors = np.linalg.eigh(centered.T @ centered)
    if values[0] > .16 * values[1]:
        return None
    normal = np.array([vectors[0, 0], vectors[1, 0], 0.0])
    camera = observation["world_from_camera"][:3, 3]
    if float(np.dot(normal[:2], camera[:2] - point[:2])) < 0:
        normal = -normal
    return normal / np.linalg.norm(normal)


def face_bearings(points, camera_position):
    """Bearings of the four upright faces of the observed radio body.

    The body is a box roughly 0.32 m long and 0.14 m deep, so the dominant
    horizontal direction of the visible footprint is one of its two box axes.
    The control sits on one of the two long faces, whose outward normals are
    perpendicular to the long axis, so those two bearings are tried first.
    Everything here comes from the current point cloud; no object pose is read.
    """
    footprint = points[:, :2] - np.median(points[:, :2], axis=0)
    values, vectors = np.linalg.eigh(footprint.T @ footprint)
    major, minor = vectors[:, 1], vectors[:, 0]
    major_extent = float(np.percentile(footprint @ major, 98)
                         - np.percentile(footprint @ major, 2))
    minor_extent = float(np.percentile(footprint @ minor, 98)
                         - np.percentile(footprint @ minor, 2))
    if major_extent < .18 and minor_extent > .05:
        major, minor = minor, major
    normal_angle = np.arctan2(minor[1], minor[0])
    along_angle = np.arctan2(major[1], major[0])
    center = np.median(points, axis=0)
    viewing = np.arctan2(camera_position[1] - center[1], camera_position[0] - center[0])
    primary = [normal_angle, normal_angle + np.pi]
    secondary = [along_angle, along_angle + np.pi]
    extra = [angle + delta for angle in primary for delta in (.61, -.61)]

    def by_travel(angles):
        return sorted(angles, key=lambda angle: abs(
            np.arctan2(np.sin(angle - viewing), np.cos(angle - viewing))))

    return by_travel(primary) + by_travel(extra) + by_travel(secondary)


def table_clearance(target_xy, table_points):
    if table_points is None or len(table_points) < 50:
        return 10.0
    return float(np.min(np.linalg.norm(table_points[:, :2] - target_xy, axis=1)))


def dock_pose(radio_xy, table_points, bearing, base_xy, clearance=.30):
    """Stand at ``bearing`` around the radio, outside the support surface.

    Search standoff, not press standoff.  Docking closer narrows the head
    camera's view of an upright face and steepens its depression angle, which
    loses control sightings; ``dock_closer`` gives the distance back only once
    a control has actually been grounded.
    """
    for radius in (.60, .68, .78, .90, 1.05):
        target = radio_xy + radius * np.array([np.cos(bearing), np.sin(bearing)])
        if table_clearance(target, table_points) < clearance:
            continue
        if np.linalg.norm(target - base_xy) > 2.8:
            continue
        return np.array([target[0], target[1],
                         np.arctan2(radio_xy[1] - target[1], radio_xy[0] - target[0])])
    return None


def dock_closer(target_center, table_points, step=.13, nearest=.40):
    """Give up standoff on the current bearing.

    A control that is grounded but whose press IK has no solution is simply out
    of reach: every candidate wrist roll fails without the arm moving at all,
    which costs nothing but also achieves nothing until the base closes in.
    """
    base = get_robot_position()[0]
    bearing = np.arctan2(base[1] - target_center[1], base[0] - target_center[0])
    radius = max(nearest, float(np.linalg.norm(base[:2] - target_center[:2])) - step)
    target = target_center[:2] + radius * np.array([np.cos(bearing), np.sin(bearing)])
    if table_clearance(target, table_points) < .20:
        return False
    return navigate_to_pose(np.array([
        target[0], target[1],
        np.arctan2(target_center[1] - target[1], target_center[0] - target[0])]))


def tuck_arms():
    """Return both arms to a compact posture before driving the base."""
    for arm in (0, 1):
        open_gripper(arm)
        try:
            move_to_posture(arm=arm, arm_joints=np.zeros(7), max_joint_step=.03)
        except (ValueError, RuntimeError):
            pass


def current_radio(cameras=("head",), near=None):
    for camera in cameras:
        observation = get_observation(camera)
        detected = observed_radio(observation, near)
        if detected is not None:
            return observation, detected[0], detected[1]
    return None


def reacquire_radio(near=None):
    """Re-find the radio after a drive, rotating in place if it left the view.

    Blocked straight-line docking can leave the base pointing at a wall, and
    the odometry frame the dock pose was computed in has drifted by then, so
    a fresh sighting is the only way to recover the geometry.
    """
    found = current_radio(("head",), near)
    if found is not None:
        return found
    for _ in range(8):
        rotate_base(np.pi / 4)
        found = current_radio(("head",), near)
        if found is not None:
            return found
    return current_radio(("head",))


def settle_at(bearing, center, table, iterations=2, tolerance=.18):
    """Drive to ``bearing`` around the radio and correct a bad standoff.

    ``navigate_to_pose`` dead-reckons, so a hop of about a metre can land 0.3 m
    off: too close and the head camera (pitched 23 degrees down, 50 degree
    vertical half-angle) clips the radio at the bottom of the frame instead of
    showing its upright face; too far and the press IK has no solution.  One
    correction is worth its ~250 steps, but refining to convergence is not -
    the whole episode is only 6000 steps and every one spent driving is one not
    spent looking from another side.
    """
    observation = None
    points = None
    for step in range(iterations):
        base = get_robot_position()[0]
        goal = dock_pose(center[:2], table, bearing, base[:2])
        if goal is None:
            break
        if step and np.linalg.norm(goal[:2] - base[:2]) < tolerance:
            break
        TRACE["dock_iterations"] += 1
        navigate_to_pose(goal)
        found = reacquire_radio(center)
        if found is None:
            return None
        observation, points = found[0], found[2]
        center = np.median(points, axis=0)
        refreshed = observed_table(observation, points)
        if refreshed is not None:
            table = refreshed
    if observation is None:
        found = reacquire_radio(center)
        if found is None:
            return None
        observation, points = found[0], found[2]
        center = np.median(points, axis=0)
    return observation, points, center, table


# ---------------------------------------------------------------- locate ----
scan = None
for scan_step in range(12):
    found = current_radio()
    if found is not None and len(found[2]) >= 60:
        scan = found
        save_current_observation("scan_hit_" + str(scan_step))
        break
    if found is not None and scan is None:
        scan = found
    rotate_base(np.pi / 6)
assert scan is not None, "No radio-sized red object found in a full visual scan"

observation, radio_mask, radio_points = scan
radio_center = np.median(radio_points, axis=0)
table_points = observed_table(observation, radio_points)

# Visual servo: re-ground the radio after every hop so that scan-time odometry
# drift does not carry into the dock pose.
bearing = np.arctan2(get_robot_position()[0][1] - radio_center[1],
                     get_robot_position()[0][0] - radio_center[0])
settled = settle_at(bearing, radio_center, table_points)
if settled is not None:
    observation, radio_points, radio_center, table_points = settled
    base = get_robot_position()[0]
    bearing = np.arctan2(base[1] - radio_center[1], base[0] - radio_center[0])
save_current_observation("after_dock")
print("dock", TRACE["dock_iterations"], "radio", np.round(radio_center, 3).tolist())

# Code block 2
# ------------------------------------------------------- press the control ---
# (surface_offset, travel).  The control cap is a ~11 mm sphere, so the
# fingertip target is only a centimetre or two past the depth surface;
# larger offsets shove the radio across the table instead of touching it.
# The cap's rendered radius is ~6 mm, so a fingertip driven
# (surface_offset + travel) past the depth surface should stop within a
# couple of centimetres of the cap centre.  Deeper commands only shove
# the radio across the table.
PRESS_LADDER = ((.004, .008), (.012, .014), (.022, .020))
MAX_COMPLETED_PER_VIEW = 2


def press_marker(observation, camera, marker):
    """Push one closed fingertip into the grounded control cap."""
    _, pixel_x, pixel_y, point, span = marker
    TRACE["marker_spans"].append(round(span, 4))
    normal = local_normal(observation, point)
    camera_ray = point - observation["world_from_camera"][:3, 3]
    camera_ray[2] = 0.0
    camera_ray /= max(1e-6, np.linalg.norm(camera_ray))
    if normal is None or float(np.dot(-normal, camera_ray)) < .60:
        direction = camera_ray
    else:
        direction = -normal
    base, _, yaw = get_robot_position()
    lateral = (-np.sin(yaw) * (point[0] - base[0]) + np.cos(yaw) * (point[1] - base[1]))
    arms = (0, 1) if lateral > 0 else (1, 0)
    completed = 0
    for arm in arms:
        for surface_offset, travel in PRESS_LADDER:
            TRACE["press_attempts"] += 1
            # press_at_pixel closes the pressing gripper and leaves it closed.
            # A closed free gripper makes the next call believe that arm is
            # holding the radio, which sends it down the holder-preserving
            # fixed-trunk path instead of a plain reach.
            open_gripper(1 - arm)
            try:
                pressed = press_at_pixel(pixel_x, pixel_y, camera=camera, arm=arm,
                                         travel=travel, surface_offset=surface_offset,
                                         direction_override=direction, allow_torso=True)
            except ValueError:
                continue
            if pressed:
                TRACE["press_completed"] += 1
                completed += 1
                save_current_observation("pressed_" + str(TRACE["press_attempts"]), camera)
                if completed >= MAX_COMPLETED_PER_VIEW:
                    break
            # Re-ground between attempts: the cap may have shifted under contact.
            refreshed = get_observation(camera)
            again = find_marker(refreshed, point)
            if again is None:
                break
            _, pixel_x, pixel_y, point, _ = again
            observation = refreshed
        if completed:
            break
    return completed > 0


def look_for_marker():
    for camera in ("head", "left_wrist", "right_wrist"):
        observation = get_observation(camera)
        # Stay anchored to the tracked radio.  An unconstrained red search can
        # latch onto wall switches or artwork after the base has turned away,
        # and then drags the whole search off to a phantom target.
        detected = observed_radio(observation, radio_center)
        if detected is None:
            continue
        center = np.median(detected[1], axis=0)
        marker = find_marker(observation, center)
        if marker is not None:
            return observation, camera, marker, center
    return None


pressed_any = False
# Two estimated faces first, then the blind ring that the earlier revision
# searched.  The estimate is usually right and saves several hops, but it is a
# PCA of one partial view and is sometimes wrong, so it orders the search
# rather than replacing it.
targets = (face_bearings(radio_points, observation["world_from_camera"][:3, 3])[:2]
           + [bearing + offset for offset in (np.pi, np.pi / 2, -np.pi / 2,
                                              3 * np.pi / 4, -3 * np.pi / 4,
                                              np.pi / 4, -np.pi / 4)])
visited = [bearing]
for orbit_index in range(9):
    if orbit_index:
        base = get_robot_position()[0]
        current_bearing = np.arctan2(base[1] - radio_center[1], base[0] - radio_center[0])
        goal, chosen = None, None
        for candidate in targets:
            if any(abs(np.arctan2(np.sin(candidate - seen), np.cos(candidate - seen))) < .30
                   for seen in visited):
                continue
            goal = dock_pose(radio_center[:2], table_points, candidate, base[:2])
            if goal is not None:
                chosen = candidate
                break
        if goal is None:
            break
        visited.append(chosen)
        TRACE["orbit_stops"] += 1
        tuck_arms()
        sweep = np.arctan2(np.sin(chosen - current_bearing), np.cos(chosen - current_bearing))
        if abs(sweep) > 2.2:
            # Only a near-opposite hop needs a staging waypoint; shorter chords
            # clear the table on their own and the extra drive is not free.
            waypoint = dock_pose(radio_center[:2], table_points,
                                 current_bearing + sweep / 2,
                                 get_robot_position()[0][:2])
            if waypoint is not None:
                navigate_to_pose(waypoint)
        settled = settle_at(chosen, radio_center, table_points)
        if settled is not None:
            observation, radio_points, radio_center, table_points = settled
            # Append, never prepend: re-ordering the queue from every fresh
            # (often end-on) view starves the opposite long face, which is the
            # single most likely place for the control to be hiding.
            targets = targets + face_bearings(
                radio_points, observation["world_from_camera"][:3, 3])
        save_current_observation("orbit_view_" + str(orbit_index))
    sighting = look_for_marker()
    if sighting is None:
        continue
    observation, camera, marker, center = sighting
    radio_center = center
    TRACE["marker_views"] += 1
    save_current_observation("marker_view_" + str(orbit_index), camera)
    print("marker", orbit_index, camera, "pixel", marker[1], marker[2],
          "span", round(marker[4], 4))
    if press_marker(observation, camera, marker):
        pressed_any = True
        # A completed touch that did not toggle is worth repeating from a
        # slightly different stand-off before paying for another orbit hop.
        retry = look_for_marker()
        if retry is not None:
            press_marker(retry[0], retry[1], retry[2])
    else:
        # Sighted but unreachable: close in on this bearing rather than paying
        # for an orbit hop away from the one face that shows the control.
        for approach in range(2):
            if not dock_closer(radio_center, table_points):
                break
            closer = look_for_marker()
            if closer is None:
                break
            radio_center = closer[3]
            TRACE["marker_views"] += 1
            save_current_observation("closer_view_" + str(orbit_index) + "_" + str(approach),
                                     closer[1])
            if press_marker(closer[0], closer[1], closer[2]):
                pressed_any = True
                break

save_current_observation("after_press_phase")
print("press attempts", TRACE["press_attempts"], "completed", TRACE["press_completed"],
      "marker views", TRACE["marker_views"], "spans", TRACE["marker_spans"][:8])
RESULT = {"press_attempts": TRACE["press_attempts"],
          "press_motor_completed": bool(pressed_any),
          "marker_views": TRACE["marker_views"],
          "orbit_stops": TRACE["orbit_stops"],
          "marker_spans": TRACE["marker_spans"][:16],
          "grounding_backend": "RGB-D red-cap grounding + depth plane normal"}
