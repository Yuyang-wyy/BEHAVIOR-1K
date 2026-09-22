# Code block 1
"""Clean the keyboard by sweeping the pipe cleaner over it.

Task mechanics, read from the simulator source rather than guessed:

* The goal literal is `not (covered keyboard dust)` and `Covered` uses
  `VISUAL_PARTICLE_THRESHOLD = 1`, so every one of the 20 dust particles has
  to go.
* `pipe_cleaner.n.01` is a `ParticleRemover` whose condition list for dust is
  `[]`, which means "always": no water, no soap, no soaking.
* Its method is ADJACENCY, for which `requires_meta_link` is False and
  `_default_link` falls back to the object's root link, so the removal volume
  is the tool's own AABB grown by 0.02 m. Nothing requires the robot to hold
  it, and every inbound particle goes in one step (the limit is 200, far above
  20).

So the task is "sweep the pipe cleaner over the whole keyboard top once".

Geometry, measured from the two assets:

* the keyboard is a flat slab, 0.477 x 0.181 x 0.016 m;
* every pipe_cleaner model is 0.20-0.30 m long and 0.017-0.037 m thick, inside
  the 0.044 m assisted-grasp ray span, so it can be picked up;
* held crosswise, the tool plus its 0.02 m margin spans 0.24-0.34 m and covers
  the keyboard's 0.18 m width in one pass, while the dust spans the full
  0.45 m length, so one sweep along the long axis is needed.

Perception. The tool is a saturated cyan against a dark wood desk, so it is
found by colour the way the radio was found by red, then confirmed by shape.
The desk plane is the dominant height near the tool, and the keyboard is the
flat 0.48 x 0.18 m slab resting on that same plane. Searching near the tool is
what makes this tractable: a bare height histogram over the whole room picks
partitions and other desks.

Only RGB-D, proprioception, the official relative camera calibration, static
URDF finger geometry and body-velocity odometry are used. No object poses,
registry entries, particle state or demonstrations are read.
"""
import math

import numpy as np
from scipy.spatial.transform import Rotation

TRACE = {"views": 0, "tool_seen": 0, "keyboard_seen": 0,
         "grasp_attempts": 0, "grasp_verified": 0, "waypoints": 0}

# Asset-derived shape gates, loose enough for depth noise and partial views.
KEYBOARD_LONG = (.30, .65)
KEYBOARD_SHORT = (.09, .30)
TOOL_LONG = (.06, .40)
TOOL_SHORT = (.004, .14)
DESK_SEARCH = 1.2                   # radius for estimating the desk plane
SCENE_SEARCH = 2.9                  # the two objects are 0.22-2.67 m apart
ON_SURFACE = (.004, .07)            # how far proud of the desk a flat object sits
# The keyboard is 16 mm thick and measures 30-35 mm proud of the observed desk
# plane. A taller slab of about the right footprint is some other desk object:
# at one heading a 62 mm-proud tray was picked instead of the keyboard.
KEYBOARD_RISE = .05
DOCK_SEARCH = 1.0                   # desk surface considered when choosing a dock
FINGER_MARGIN = .006                # finger opening above empty-closed that means "held"


def teal_mask(rgb):
    """The pipe cleaner is a saturated cyan, about RGB (24, 118, 150)."""
    rgb = np.asarray(rgb, dtype=int)
    red, green, blue = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return (blue > 90) & (blue > red + 35) & (green > red + 30)


def world_points(observation, stride=2):
    """Backproject the depth image into odometry-frame points.

    The camera pose uses the OpenGL convention (+Y up, -Z forward), so the
    camera-frame ray must be flipped in y and z before being rotated into the
    world. Hand-rolling this without the flip mirrors the entire cloud and was
    why every earlier version of this detector measured nonsense heights.
    `mask_to_world_points` is the reference implementation, so use it.
    """
    depth = observation["depth"]
    keep = np.zeros(depth.shape, dtype=bool)
    keep[::stride, ::stride] = True
    keep &= np.isfinite(depth) & (depth > .15) & (depth < 4.5)
    return mask_to_world_points(keep, depth, observation["intrinsics"],
                                observation["world_from_camera"])


def masked_points(observation, mask):
    depth = observation["depth"]
    keep = np.asarray(mask, dtype=bool) & np.isfinite(depth) & (depth > .15) & (depth < 4.5)
    if int(keep.sum()) < 10:
        return np.zeros((0, 3))
    return mask_to_world_points(keep, depth, observation["intrinsics"],
                                observation["world_from_camera"])


def footprint(points):
    """Oriented 2-D extent of a cluster: (long, short, long-axis unit vector)."""
    flat = points[:, :2] - points[:, :2].mean(axis=0)
    if len(flat) < 8:
        return 0., 0., np.array([1., 0.])
    _, _, basis = np.linalg.svd(flat, full_matrices=False)
    projected = flat @ basis.T
    spans = projected.max(axis=0) - projected.min(axis=0)
    if spans[1] > spans[0]:
        spans = spans[::-1]
        basis = basis[::-1]
    return float(spans[0]), float(spans[1]), basis[0]


def clusters(points, tolerance=.035, minimum=25):
    """Grid-linked clustering in the horizontal plane."""
    if len(points) == 0:
        return []
    keys = np.floor(points[:, :2] / tolerance).astype(np.int64)
    table = {}
    for index, key in enumerate([(int(a), int(b)) for a, b in keys]):
        table.setdefault(key, []).append(index)
    seen, found = set(), []
    for key in table:
        if key in seen or len(found) >= 400:
            continue
        stack, members = [key], []
        seen.add(key)
        while stack:
            cell = stack.pop()
            members.extend(table[cell])
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    other = (cell[0] + dx, cell[1] + dy)
                    if other in table and other not in seen:
                        seen.add(other)
                        stack.append(other)
        if len(members) >= minimum:
            found.append(points[np.array(members)])
    return found


def entry_for(cluster):
    long_side, short_side, axis = footprint(cluster)
    return {"centre": cluster.mean(axis=0), "long": long_side, "short": short_side,
            "axis": axis, "top": float(np.percentile(cluster[:, 2], 90)),
            "points": cluster}


def find_tool(observation):
    """Largest cyan blob that is the right size for a pipe cleaner."""
    mask = teal_mask(observation["rgb"])
    if int(mask.sum()) < 40:
        return None
    points = masked_points(observation, mask)
    if len(points) < 20:
        return None
    blobs = clusters(points, tolerance=.04, minimum=15)
    if not blobs:
        return None
    tool = entry_for(max(blobs, key=len))
    if not (TOOL_LONG[0] <= tool["long"] <= TOOL_LONG[1]
            and TOOL_SHORT[0] <= tool["short"] <= TOOL_SHORT[1]):
        return None
    return tool


def desk_level(points, around):
    """The dominant horizontal height near a point: the desk the tool sits on."""
    near = points[np.linalg.norm(points[:, :2] - around[:2], axis=1) < DESK_SEARCH]
    if len(near) < 150:
        return None
    counts, edges = np.histogram(near[:, 2], bins=np.arange(.35, 1.35, .005))
    if counts.max() < 60:
        return None
    return float(edges[int(counts.argmax())] + .0025)


def find_keyboard(points, level, around):
    """The flat 0.48 x 0.18 m slab resting on the same desk as the tool."""
    near = points[np.linalg.norm(points[:, :2] - around[:2], axis=1) < SCENE_SEARCH]
    slab = near[(near[:, 2] > level + ON_SURFACE[0]) & (near[:, 2] < level + ON_SURFACE[1])]
    best = None
    for cluster in clusters(slab):
        candidate = entry_for(cluster)
        if (KEYBOARD_LONG[0] <= candidate["long"] <= KEYBOARD_LONG[1]
                and KEYBOARD_SHORT[0] <= candidate["short"] <= KEYBOARD_SHORT[1]
                and candidate["top"] - level <= KEYBOARD_RISE):
            if best is None or len(cluster) > len(best["points"]):
                best = candidate
    return best


def survey(observation):
    """(level, keyboard, tool) from one view, or None."""
    TRACE["views"] += 1
    tool = find_tool(observation)
    if tool is None:
        return None
    TRACE["tool_seen"] += 1
    points = world_points(observation)
    level = desk_level(points, tool["centre"])
    if level is None:
        return None
    keyboard = find_keyboard(points, level, tool["centre"])
    if keyboard is None:
        return None
    TRACE["keyboard_seen"] += 1
    return level, keyboard, tool


def look_around(limit=12):
    for attempt in range(limit):
        found = survey(get_observation())
        if found is not None:
            return found
        rotate_base(math.pi / 6)
    return None


save_current_observation("start")
SCENE = look_around()
assert SCENE is not None, "Never saw the cyan pipe cleaner and a keyboard on one desk"
LEVEL, KEYBOARD, TOOL = SCENE
TOOL_HOME = TOOL["centre"].copy()
KEYBOARD_HOME = KEYBOARD["centre"].copy()
KEYBOARD_AXIS = KEYBOARD["axis"].copy()
KEYBOARD_TOP = float(KEYBOARD["top"])
KEYBOARD_SPAN = float(KEYBOARD["long"])
print("desk %.3f | tool %s %.2fx%.2f | keyboard %s %.2fx%.2f top %.3f | gap %.3f"
      % (LEVEL, np.round(TOOL_HOME, 3), TOOL["long"], TOOL["short"],
         np.round(KEYBOARD_HOME, 3), KEYBOARD_SPAN, KEYBOARD["short"], KEYBOARD_TOP,
         float(np.linalg.norm(TOOL_HOME[:2] - KEYBOARD_HOME[:2]))))
save_current_observation("scene")

# Code block 2
"""Dock beside the pipe cleaner and pick it up.

Verification needs positive evidence on both sides: the tool must be gone from
where it lay, and a cyan blob must be visible near the gripper and clear of the
desk. A "couldn't see it any more" check passed three times earlier in this
work on runs where the saved image showed the tool still on the desk.
"""


def dock_near(target_xy, level, observation):
    """Stand off the desk edge nearest a target, facing it."""
    points = world_points(observation)
    # Only this desk's own surface. Feeding every point at desk height in the
    # room gave get_navigation_pose a polygon spanning other furniture, so it
    # docked 1.08 m from the tool and the arm reached it only by contorting the
    # trunk, which swung the head camera away and missed the grasp.
    desk = points[(np.abs(points[:, 2] - level) < .012)
                  & (np.linalg.norm(points[:, :2] - np.asarray(target_xy)[:2], axis=1) < DOCK_SEARCH)]
    if len(desk) < 40:
        print("  too little desk surface to dock against")
        return False
    try:
        pose = np.asarray(get_navigation_pose(desk, np.array([[target_xy[0], target_xy[1], level]])),
                          dtype=float)
    except Exception as error:
        print("  navigation geometry failed:", str(error)[:90])
        return False
    here = get_robot_position()[0][:2]
    if np.linalg.norm(pose[:2] - here) > 2.9:
        direction = pose[:2] - here
        direction = direction / (np.linalg.norm(direction) + 1e-9)
        waypoint = here + 2.4 * direction
        navigate_to_pose(np.array([waypoint[0], waypoint[1],
                                   math.atan2(direction[1], direction[0])]))
    return bool(navigate_to_pose(pose))


def tool_near(observation, centre_xy, radius=.30):
    """A cyan blob within `radius` of a point, at any height."""
    mask = teal_mask(observation["rgb"])
    if int(mask.sum()) < 25:
        return None
    points = masked_points(observation, mask)
    if len(points) < 12:
        return None
    points = points[np.linalg.norm(points[:, :2] - centre_xy, axis=1) < radius]
    blobs = clusters(points, tolerance=.05, minimum=10)
    return entry_for(max(blobs, key=len)) if blobs else None


def reacquire(target_xy, radius=.45, turns=5):
    """Re-find the tool after driving, turning if it fell out of frame."""
    for _ in range(turns):
        view = get_observation()
        found = tool_near(view, target_xy, radius=radius)
        if found is not None:
            return found, view
        rotate_base(math.pi / 8)
    return None, get_observation()


def calibrate_fingers():
    """Which joints are the right-hand fingers, and how far they close empty.

    Measured rather than assumed: open, then close on nothing, and whichever
    joints moved are the fingers. A gripper that closes on the 0.02-0.04 m rod
    stops partway, so after the lift a finger opening above the empty-closed
    value is direct evidence that something is still held.
    """
    open_gripper(1)
    opened = get_current_joint_positions()
    close_gripper(1)
    shut = get_current_joint_positions()
    fingers = [index for index in range(len(opened)) if abs(opened[index] - shut[index]) > .005]
    open_gripper(1)
    return fingers, float(sum(shut[index] for index in fingers)), \
        float(sum(opened[index] for index in fingers))


def finger_opening(fingers):
    joints = get_current_joint_positions()
    return float(sum(joints[index] for index in fingers))


FINGERS, EMPTY_SHUT, FULL_OPEN = calibrate_fingers()
print("fingers %s | empty-closed opening %.4f | fully open %.4f"
      % (FINGERS, EMPTY_SHUT, FULL_OPEN))

dock_near(TOOL_HOME[:2], LEVEL, get_observation())
save_current_observation("docked_at_tool")
FOUND, VIEW = reacquire(TOOL_HOME[:2])
if FOUND is not None:
    TOOL_HOME = FOUND["centre"].copy()
    TOOL = FOUND
    print("re-found the tool after docking at", np.round(TOOL_HOME, 3))

HELD = False
for attempt in range(3):
    TRACE["grasp_attempts"] += 1
    pregrasps, grasps = sample_grasp_pose_from_points(TOOL["points"])
    # The helper offers the box yaw and yaw+90 degrees. The jaws must close
    # across the 0.02-0.04 m thickness, not along the 0.2-0.3 m length, so try
    # both and keep whichever actually lifts it.
    index = attempt % len(grasps)
    print("  attempt %d: grasp at %s" % (attempt, np.round(grasps[index][0], 3)))
    completed = execute_grasp(pregrasps[index], grasps[index], 1, lift=.12)
    # Measured after the lift: if the rod slipped out on the way up, the
    # fingers will have closed the rest of the way.
    opening = finger_opening(FINGERS)
    stopped = opening > EMPTY_SHUT + FINGER_MARGIN
    check = get_observation()
    save_current_observation("after_grasp_%d" % attempt)
    eef = get_current_eef_pose(1)[0]
    in_hand = tool_near(check, eef[:2], radius=.30)
    left_behind = tool_near(check, TOOL_HOME[:2], radius=.15)
    print("    motors %s | finger opening %.4f vs empty %.4f -> %s | cyan near hand %s | still on desk %s"
          % (completed, opening, EMPTY_SHUT, "blocked" if stopped else "closed",
             "yes" if in_hand is not None else "no",
             "yes" if left_behind is not None else "no"))
    # The fingers are the primary evidence: they do not depend on the head
    # camera, which a long reach swings off the desk. Seeing the rod still
    # lying where it was overrules them - then the fingers caught something
    # else.
    if stopped and left_behind is None:
        HELD = True
        TRACE["grasp_verified"] += 1
        print("    GRASPED (fingers held open by the rod, and it has left the desk)")
        break
    open_gripper(1)
    refound, _ = reacquire(TOOL_HOME[:2], radius=.35, turns=2)
    if refound is not None:
        TOOL, TOOL_HOME = refound, refound["centre"].copy()

print("held", HELD, "attempts", TRACE["grasp_attempts"])

# Code block 3
"""Carry the tool over the keyboard and sweep it along the long axis.

The sweep is planned for the *tool*, not the gripper, because the removal
volume is the tool's AABB grown by 0.02 m. The hand-to-tool offset is measured
after the wrist is turned, since turning the wrist rotates that offset too.

Height: the tool rides about 0.02 m clear of the keyboard top. Its removal box
still reaches 0.02 m below its own underside, which encloses the dust lying on
the top face, while nothing touches the keyboard and shoves it out of reach.
"""


def turned(quat_wxyz, radians):
    """Rotate an orientation about the world z axis."""
    current = Rotation.from_quat(np.asarray(quat_wxyz)[[1, 2, 3, 0]]).as_matrix()
    turn = Rotation.from_euler("z", radians).as_matrix()
    return Rotation.from_matrix(turn @ current).as_quat()[[3, 0, 1, 2]]


def signed_angle(source, target):
    """Angle between planar unit vectors, folded into +-90 degrees.

    The rod is symmetric, so pointing it either way gives the same swath;
    folding avoids a pointless 180 degree wrist turn.
    """
    angle = math.atan2(float(np.cross(source, target)), float(np.dot(source, target)))
    if angle > math.pi / 2:
        angle -= math.pi
    if angle < -math.pi / 2:
        angle += math.pi
    return angle


RESULT = {"held": HELD, "swept": False, "waypoints": 0, "passes": 0}

if not HELD:
    print("no verified grasp, so nothing to sweep with")
else:
    dock_near(KEYBOARD_HOME[:2], LEVEL, get_observation())
    save_current_observation("docked_at_keyboard")

    # Re-detect from the new stance so the sweep is planned in freshly observed
    # coordinates rather than through the drift accumulated while driving.
    eef = get_current_eef_pose(1)[0]
    POINTS = world_points(get_observation())
    AGAIN = find_keyboard(POINTS, LEVEL, KEYBOARD_HOME)
    if AGAIN is not None:
        KEYBOARD_HOME = AGAIN["centre"].copy()
        KEYBOARD_AXIS = AGAIN["axis"].copy()
        KEYBOARD_TOP = float(AGAIN["top"])
        KEYBOARD_SPAN = float(AGAIN["long"])
        print("keyboard re-detected at %s span %.3f top %.3f"
              % (np.round(KEYBOARD_HOME, 3), KEYBOARD_SPAN, KEYBOARD_TOP))
    else:
        print("could not re-detect the keyboard; using the first fix")

    ACROSS = np.array([-KEYBOARD_AXIS[1], KEYBOARD_AXIS[0]])
    eef_position, eef_quat = get_current_eef_pose(1)
    held_now = tool_near(get_observation(), eef_position[:2], radius=.32)
    if held_now is not None:
        delta = signed_angle(held_now["axis"], ACROSS)
        print("turning the wrist %.0f degrees to lay the rod across the keyboard"
              % math.degrees(delta))
        move_hand((eef_position, turned(eef_quat, delta)), 1)

    eef_position, eef_quat = get_current_eef_pose(1)
    held_now = tool_near(get_observation(), eef_position[:2], radius=.32)
    OFFSET = np.zeros(3)
    if held_now is not None:
        OFFSET = held_now["centre"] - eef_position
        print("hand-to-tool offset", np.round(OFFSET, 3),
              "| rod axis", np.round(held_now["axis"], 2))
    else:
        print("could not re-measure the rod in hand; sweeping on the hand alone")

    SWEEP_Z = KEYBOARD_TOP + .02
    REACH = KEYBOARD_SPAN / 2 + .09
    for direction in (1, -1):
        targets = []
        for offset in np.linspace(-REACH, REACH, 7)[::direction]:
            spot = KEYBOARD_HOME[:2] + KEYBOARD_AXIS * offset
            targets.append(np.array([spot[0], spot[1], SWEEP_Z]))
        # Come in from above so the rod does not clip the keyboard edge.
        move_hand((targets[0] - OFFSET + np.array([0, 0, .10]), eef_quat), 1)
        reached = 0
        for target in targets:
            if move_hand((target - OFFSET, eef_quat), 1, max_joint_step=.008):
                reached += 1
            TRACE["waypoints"] += 1
        RESULT["waypoints"] += reached
        RESULT["passes"] += 1
        print("  pass %d: %d of 7 waypoints reached" % (RESULT["passes"], reached))
        save_current_observation("after_pass_%d" % RESULT["passes"])
        if reached == 0:
            break
    RESULT["swept"] = RESULT["waypoints"] > 0

print("RESULT", RESULT, "TRACE", TRACE)
