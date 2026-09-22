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
* the task rescales the pipe cleaner (model yccyjo) to 0.40 x 0.10 x 0.10 m
  (`task_custom_lists.json`): a thin cyan handle that fits the 0.044 m jaw
  span, and bristles 0.10 m across. With its 0.02 m margin the removal box is
  0.44 x 0.14 x 0.14 m, so one or two strokes cover the 0.48 x 0.18 m keyboard.
  (An earlier version assumed the library's unscaled 0.037 m thickness; the
  bristles then dug 2 cm into the keys and shoved or flung the keyboard.)

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
KEYBOARD_RISE_MIN = .015            # a slab 4 mm proud of the desk was a mat edge, not the keyboard
DOCK_SEARCH = 1.0                   # desk surface considered when choosing a dock
FINGER_MARGIN = .006                # finger opening that separates held from empty
GRASP_REACH = .80                   # base-to-tool distance: grasps worked at 0.69-0.94 m, failed at 0.45-0.53 m
PLAN_NEAR = .72                     # planned dock: this close to the tool
PLAN_FAR = .90                      # to this far
PLAN_CELL = .05                     # occupancy grid resolution
PLAN_RANGE = 3.2                    # grid half-width around the robot
PLAN_INFLATE = .28                  # base clearance from anything solid; .34 sealed the tool's desk off entirely
PLAN_INNER = .08                    # plan to [PLAN_NEAR, PLAN_NEAR + this]
PLAN_SLACK = .06                    # but accept arriving this far outside [PLAN_NEAR, PLAN_FAR]
PLAN_BLIND = .55                    # floor around the base the head never sees
PLAN_LEG = 1.5                      # longest straight leg before looking again
PLAN_OBSTACLE_LOW = .06             # lowest point height counted as an obstacle
SWEEP_REACH = .65                   # base-to-keyboard-centre distance while re-detecting it
LANES = (0., -.05, .05)             # across-keyboard offsets of the sweep lanes
BASE_CLEAR = .34                    # chairs, cabinets and other base-height obstacles
DESK_CLEAR = .30                    # the desk-top edge; the torso leans over it
TORSO_CLEAR = .22                   # anything standing above the desk top
BLIND_RADIUS = .70                  # floor the head camera cannot see around the base
REFIND_RADIUS = 2.5                 # accept the cyan tool this far from the robot
ROD_CLEARANCE = .058                # rod axis above the keyboard top while sweeping. The bristles are 0.10 m
                                    # across: at +.05 they just clear the keys; above +.066 the removal box
                                    # (bristles +0.02 m) no longer reaches the dust on the key tops
STANCE_DESK_CLEAR = .25             # base-to-desk-edge clearance at the sweeping stance
PASSES = (0., -.17, .17)            # rod-centre offsets along the keyboard; covers it whichever end the bristles are
RADIAL = (.13, .02, -.10)           # rod-centre offsets across the keyboard, near edge to past the far edge;
                                    # -.045 left the far 5 mm of the 0.18 m keyboard unswept (instance 301)
TILTS = (0., .45, .85)              # forward hand pitch tried in turn to extend reach
KEYBOARD_SEARCH_TURNS = 7           # views tried when re-finding the keyboard at its dock
GRASP_TILTS = (.35, .60)            # tip the grasp about the rod this far when straight-down is out of reach
PREGRASP_BACKOFF = .15              # pre-grasp distance back along the approach
STANCE_FIXED = .68                  # base distance from the keyboard centre while sweeping
TOUCH_FROM = .08                    # start the touch descent this far above the seen keyboard top. Every held
                                    # move costs ~150 steps (the loaded wrist sags past the harness's 0.01 rad
                                    # settle test, so each move waits out all 120 settle steps); from .12 the
                                    # probe alone used ~1400 of the 5814 (instance 302)
TOUCH_STEP = .01                    # descend in steps of this
TOUCH_STEPS = 16                    # at most this many
TOUCH_BLOCKED = .006                # hand this far above its target means the rod is resting on the keys
TOUCH_LIFT = .010                   # sweep with the rod's lowest point this far above the keys. At .012 (+tilt)
                                    # it rode 1.5-2 cm high and half the dust stayed; at .005 it dug 1.2 cm in
                                    # and shoved the keyboard 0.18 m (both instance 301)
FALLBACK_RING = .50                 # looser ring for the stance fallback, after more driving
RING_TOLERANCE = .35                # keyboard must lie this close to the scan's tool-keyboard distance
KEYBOARD_COMPLETE = (.42, .54)      # a view of the whole 0.477 m keyboard; shorter clusters are partial
KEYBOARD_GATE = .80                 # re-detected keyboard must be this close to where it was expected
LEVEL_MIN = .03                     # below this the rod is level enough
LEVEL_MAX = .60                     # above this the fit is not trusted
FAST_STEP = .025                    # joint step for lifts and approaches; .03 with a loaded arm tipped the robot
CLOSE_ENOUGH = .04                  # a sweep point this close counts as swept
CROSS_RADIAL = (.14, .07, 0.)       # cross-mode hand offsets toward the robot from the keyboard's centre line.
                                    # Held, the tool's box centre is 0.12 m from the hand along the rod
                                    # (evaluator debug log): the box reaches ~0.10 m past the hand on the
                                    # grip side and ~0.34 m on the brush side. At .14 it covers the whole
                                    # keyboard if the brush points away; at 0 the far edge either way
CROSS_ALONG = (-.28, -.14, 0., .14, .28)
SWEEP_STEP = .008                   # joint step while the rod is on the keyboard; .015 missed the 2.5 cm tolerance
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


def masked_points(observation, mask, nearest=.15):
    depth = observation["depth"]
    keep = np.asarray(mask, dtype=bool) & np.isfinite(depth) & (depth > nearest) & (depth < 4.5)
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
                and KEYBOARD_RISE_MIN <= candidate["top"] - level <= KEYBOARD_RISE):
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


HOME = get_current_joint_positions()
MAP = []


def turned(quat_wxyz, radians):
    current = Rotation.from_quat(np.asarray(quat_wxyz)[[1, 2, 3, 0]]).as_matrix()
    turn = Rotation.from_euler("z", radians).as_matrix()
    return Rotation.from_matrix(turn @ current).as_quat()[[3, 0, 1, 2]]


def rod_axis(quat_wxyz):
    axis = Rotation.from_quat(np.asarray(quat_wxyz)[[1, 2, 3, 0]]).as_matrix()[:2, 0]
    return axis / (np.linalg.norm(axis) + 1e-9)


def signed_angle(source, target):
    """Planar angle folded into +-90 degrees; the rod is symmetric."""
    angle = math.atan2(float(source[0] * target[1] - source[1] * target[0]),
                       float(np.dot(source, target)))
    if angle > math.pi / 2:
        angle -= math.pi
    if angle < -math.pi / 2:
        angle += math.pi
    return angle


def go_to(pose):
    """navigate_to_pose, split into legs under its three-metre limit.

    A bare call raised on instance 306 when a dock lay 3.1 m away.
    """
    pose = np.asarray(pose, dtype=float)
    here = get_robot_position()[0][:2]
    offset = pose[:2] - here
    distance = float(np.linalg.norm(offset))
    if distance > 2.8:
        direction = offset / distance
        waypoint = here + (distance - 2.5) * direction
        if not navigate_to_pose(np.array([waypoint[0], waypoint[1], math.atan2(direction[1], direction[0])])):
            return False
    return bool(navigate_to_pose(pose))


def remember(observation):
    """Keep a coarse odometry-frame point map, so later docking does not
    depend on whatever the head happens to see after the arm has moved."""
    MAP.append(world_points(observation, stride=4))
    if len(MAP) > 40:
        del MAP[0]


def map_points(recent=6):
    """Points from the most recent views; older ones carry more yaw drift."""
    return np.concatenate(MAP[-recent:]) if MAP else np.zeros((0, 3))


def go_home_unsafe():
    """Tuck the arm and restore the start trunk.

    In that posture the head camera points 22.8 degrees down and nothing of
    the robot is in view. After a reach, the trunk has swung the head and the
    arm occludes the desk, so any perception without this first is unreliable.
    """
    return move_to_posture(arm=1, arm_joints=HOME[17:24], trunk_joints=HOME[6:10],
                           max_joint_step=.03)


def go_home():
    try:
        return go_home_unsafe()
    except ValueError:
        print("  could not return home; continuing")
        return False


def restore_trunk():
    """Head back to its start pitch while the arm keeps whatever it holds.

    After a loaded grasp one arm encoder can read a hair past its limit, and
    the harness then rejects the whole command (instance 301 crashed here).
    The start posture is inside the limits and the limits are a box, so
    blending the arm slightly toward it lands back inside.
    """
    arm = get_current_joint_positions()[17:24]
    for blend in (0., .03, .10, .30):
        try:
            return move_to_posture(arm=1, arm_joints=(1 - blend) * arm + blend * HOME[17:24],
                                   trunk_joints=HOME[6:10], max_joint_step=.03)
        except ValueError:
            continue
    print("  could not restore the trunk; continuing with the current view")
    return False


def look_around(turns=12):
    """Turn until the tool and keyboard are both in view, and stop there.

    Rotation odometry is poor: a static tool's odometry-frame bearing drifted
    about 4.5 degrees per 30 degree turn (~15%), so a full 360 degree scan
    accumulated 55-70 degrees of error and scrambled every position in it.
    Stopping at the first good view keeps the error to a few turns' worth.
    """
    tool_only = None
    for _ in range(turns):
        view = get_observation()
        remember(view)
        found = survey(view)
        if found is not None:
            return found
        if tool_only is None:
            tool = find_tool(view)
            if tool is not None:
                level = desk_level(world_points(view), tool["centre"])
                if level is not None:
                    tool_only = (level, None, tool)
        rotate_base(math.pi / 6)
    # The keyboard can sit 2-2.5 m from the tool (instances 312, 314, 317),
    # too far apart to share one view; take the tool now and look for the
    # keyboard once the tool is in hand.
    return tool_only


save_current_observation("start")
SCENE = look_around()
assert SCENE is not None, "Never saw the cyan pipe cleaner on a desk"
LEVEL, KEYBOARD, TOOL = SCENE
TOOL_HOME = TOOL["centre"].copy()
TOOL_SCAN = TOOL_HOME.copy()
KEYBOARD_KNOWN = KEYBOARD is not None
if not KEYBOARD_KNOWN:
    # Placeholder until the keyboard is found; block 3 searches for it.
    KEYBOARD = {"centre": TOOL_HOME.copy(), "axis": np.array([1., 0.]), "top": LEVEL + .032,
                "long": .477, "short": .181}
KEYBOARD_HOME = KEYBOARD["centre"].copy()
KEYBOARD_AXIS = KEYBOARD["axis"].copy()
KEYBOARD_TOP = float(KEYBOARD["top"])
KEYBOARD_SPAN = float(KEYBOARD["long"])
# The tool-to-keyboard distance, measured within one view, survives odometry
# drift; absolute positions do not.
SCAN_GAP = float(np.linalg.norm(TOOL_SCAN[:2] - KEYBOARD_HOME[:2])) if KEYBOARD_KNOWN else None
print("keyboard in the first view:", KEYBOARD_KNOWN, "| tool-keyboard gap", SCAN_GAP)
print("desk %.3f | tool %s %.2fx%.2f | keyboard %s %.2fx%.2f top %.3f | gap %.3f"
      % (LEVEL, np.round(TOOL_HOME, 3), TOOL["long"], TOOL["short"],
         np.round(KEYBOARD_HOME, 3), KEYBOARD_SPAN, KEYBOARD["short"], KEYBOARD_TOP,
         float(np.linalg.norm(TOOL_HOME[:2] - KEYBOARD_HOME[:2]))))
save_current_observation("scene")

# Code block 2
"""Dock beside the pipe cleaner and pick it up.

Four things this block does differently from the version that scored 1/20:

* docking uses the remembered map, not the current head view;
* the robot closes in to within reach after docking - the edge-based dock
  alone left the tool 0.9-1.0 m away, past the arm's reach at desk height;
* the tool is always re-found after driving. Grasping at coordinates measured
  before the drive closed the fingers on bare desk (instance 302);
* the grasp is re-aimed from the wrist camera at the pre-grasp pose. There
  the wrist camera sees the handle with thousands of points, while the head
  camera, swung by the reaching trunk, often sees nothing.

It always uses the grasp that closes the jaws *across* the rod. The helper's
second candidate closes them along its 0.15 m length, which cannot fit a
0.044 m jaw span; the old loop alternated and wasted every other attempt.
"""


VISITED = []


def dock_candidates(target_xy, level, standoffs=(.55, .65, .75, .85)):
    """Standing spots around a target, checked against the remembered map.

    get_navigation_pose picks a desk edge by geometry alone. With the whole
    desk in the map it chose the far side on instance 301, and the straight
    drive there went into the desk and wedged the robot for the rest of the
    episode. Here every spot must be clear of chairs and cabinets, of the desk
    edge, and of anything the leaning torso could hit; must stand on floor
    that was seen, or that the robot itself has occupied (the head camera
    never sees the floor right around the base); and must be reachable by a
    straight drive that does not cross the desk.
    """
    target_xy = np.asarray(target_xy, dtype=float)[:2]
    here = get_robot_position()[0][:2]
    points = map_points()
    near = points[np.linalg.norm(points[:, :2] - (target_xy + here) / 2, axis=1)
                  < .5 * np.linalg.norm(target_xy - here) + 2.0]
    desk = near[np.abs(near[:, 2] - level) < .03]
    low = near[(near[:, 2] > .06) & (near[:, 2] < level - .03)]
    high = near[(near[:, 2] >= level + .05) & (near[:, 2] < 1.8)]
    floor = near[near[:, 2] < .04]
    solid = np.concatenate([low, desk]) if len(desk) else low
    occupied = [here] + [np.asarray(v)[:2] for v in VISITED]
    found = []
    for standoff in standoffs:
        for step in range(36):
            bearing = step * math.pi / 18
            spot = target_xy + standoff * np.array([math.cos(bearing), math.sin(bearing)])
            if len(low) and np.min(np.linalg.norm(low[:, :2] - spot, axis=1)) < BASE_CLEAR:
                continue
            if len(desk) and np.min(np.linalg.norm(desk[:, :2] - spot, axis=1)) < DESK_CLEAR:
                continue
            if len(high) and np.min(np.linalg.norm(high[:, :2] - spot, axis=1)) < TORSO_CLEAR:
                continue
            seen_floor = len(floor) > 0 and int((np.linalg.norm(floor[:, :2] - spot, axis=1) < .25).sum()) >= 15
            been_there = any(np.linalg.norm(spot - place) < BLIND_RADIUS for place in occupied)
            if not (seen_floor or been_there):
                continue
            travel = spot - here
            length = float(np.linalg.norm(travel))
            blocked = 0
            if length > .05 and len(solid):
                along = (solid[:, :2] - here) @ (travel / length)
                across = np.abs((solid[:, :2] - here) @ np.array([-travel[1], travel[0]]) / length)
                blocked = int(((along > .30) & (along < length - .05) & (across < .30)).sum())
            if blocked > 15:
                continue
            found.append((length + .8 * standoff, spot))
    found.sort(key=lambda item: item[0])
    return [spot for _, spot in found]


def face(target_xy):
    here = get_robot_position()[0][:2]
    offset = np.asarray(target_xy)[:2] - here
    go_to(np.array([here[0], here[1], math.atan2(offset[1], offset[0])]))


def dock_near(target_xy, level, tries=2, holding=False):
    """Drive to a clear standing spot facing a target.

    Turn toward the target first and look, so the map covers the place the
    robot is heading - the recent-views map otherwise only held the area it
    had just left, and on instance 301 that left zero candidate spots beside
    the keyboard. If no candidate works, fall back to the desk-edge dock.
    """
    target_xy = np.asarray(target_xy, dtype=float)[:2]
    face(target_xy)
    if not holding:
        # With the tool in hand, restoring the trunk swings the arm with it:
        # on instance 320 that put the rod at z 0.39, under the desk edge,
        # and every later motion failed against the desk.
        restore_trunk()
    remember(get_observation())
    spots = dock_candidates(target_xy, level)
    print("  %d dock candidates around %s" % (len(spots), np.round(target_xy, 2)))
    for spot in spots[:tries]:
        here = get_robot_position()[0][:2]
        if np.linalg.norm(spot - here) > 2.9:
            direction = (spot - here) / np.linalg.norm(spot - here)
            waypoint = here + 2.4 * direction
            go_to(np.array([waypoint[0], waypoint[1], math.atan2(direction[1], direction[0])]))
        heading = math.atan2(target_xy[1] - spot[1], target_xy[0] - spot[0])
        ok = bool(go_to(np.array([spot[0], spot[1], heading])))
        VISITED.append(get_robot_position()[0][:2].copy())
        print("    dock at %s -> %s" % (np.round(spot, 2), "ok" if ok else "stalled"))
        if ok:
            return True
    points = map_points()
    desk = points[(np.abs(points[:, 2] - level) < .012)
                  & (np.linalg.norm(points[:, :2] - target_xy, axis=1) < DOCK_SEARCH)]
    if len(desk) >= 40:
        try:
            pose = np.asarray(get_navigation_pose(desk, np.array([[target_xy[0], target_xy[1], level]])),
                              dtype=float)
            ok = bool(go_to(pose))
            VISITED.append(get_robot_position()[0][:2].copy())
            print("    desk-edge dock at %s -> %s" % (np.round(pose[:2], 2), "ok" if ok else "stalled"))
            return ok
        except Exception as error:
            print("    desk-edge dock failed:", str(error)[:80])
    return False


def reach_with_yaw(pose, max_joint_step=.015):
    """move_hand, retrying from base yaws of +-20 degrees when planning fails.

    Reach depends on where the target sits relative to the right shoulder,
    not only on distance: the tool was reached at 0.94 m on one instance and
    missed at 0.77 m on another.
    """
    if move_hand(pose, 1, max_joint_step=max_joint_step):
        return True
    here, _, yaw = get_robot_position()
    for turn in (-.35, .35):
        go_to(np.array([here[0], here[1], yaw + turn]))
        if move_hand(pose, 1, max_joint_step=max_joint_step):
            return True
    go_to(np.array([here[0], here[1], yaw]))
    return False


def close_in(target_xy, reach):
    """Drive straight at a target until it is within `reach`, facing it.

    Stalling against the desk edge is fine: that is as close as the base gets.
    """
    here = get_robot_position()[0][:2]
    offset = np.asarray(target_xy)[:2] - here
    distance = float(np.linalg.norm(offset))
    heading = math.atan2(offset[1], offset[0])
    if distance <= reach + .03:
        go_to(np.array([here[0], here[1], heading]))
        return distance
    spot = here + offset / distance * (distance - reach)
    go_to(np.array([spot[0], spot[1], heading]))
    return float(np.linalg.norm(np.asarray(target_xy)[:2] - get_robot_position()[0][:2]))


def stand_at(target_xy, distance):
    """Put the base `distance` from a target on the current line, facing it.

    Too close is as bad as too far. Across the runs so far, grasps succeeded
    with the tool 0.69-0.94 m from the base and failed at 0.45-0.53 m, where
    a straight-down hand needs a folded elbow the planner cannot find; the
    sweep likewise failed from 0.23 m. So this backs up as well as closing in.
    """
    target_xy = np.asarray(target_xy, dtype=float)[:2]
    here = get_robot_position()[0][:2]
    offset = here - target_xy
    length = float(np.linalg.norm(offset))
    if length < 1e-6:
        offset, length = np.array([1., 0.]), 1.
    spot = target_xy + offset / length * distance
    go_to(np.array([spot[0], spot[1], math.atan2(-offset[1], -offset[0])]))
    return float(np.linalg.norm(get_robot_position()[0][:2] - target_xy))


def tool_near(observation, centre_xy, radius=.30, nearest=.15):
    """A cyan blob within `radius` of a point, at any height."""
    mask = teal_mask(observation["rgb"])
    if int(mask.sum()) < 25:
        return None
    points = masked_points(observation, mask, nearest=nearest)
    if len(points) < 12:
        return None
    points = points[np.linalg.norm(points[:, :2] - centre_xy, axis=1) < radius]
    blobs = clusters(points, tolerance=.04, minimum=12)
    return entry_for(max(blobs, key=len)) if blobs else None


def keyboard_near(points, level, expected_xy, here_xy):
    """The keyboard-shaped slab nearest where the keyboard is expected.

    Taking the largest slab near the robot picked a different, 2.2 m distant
    slab on instance 306 and the whole sweep went there. Prefer the candidate
    closest to the expected position within KEYBOARD_GATE; only when nothing
    is that close fall back to the one nearest the robot.
    """
    near = points[np.linalg.norm(points[:, :2] - np.asarray(here_xy)[:2], axis=1) < SCENE_SEARCH]
    slab = near[(near[:, 2] > level + ON_SURFACE[0]) & (near[:, 2] < level + ON_SURFACE[1])]
    candidates = []
    for cluster in clusters(slab):
        candidate = entry_for(cluster)
        if (KEYBOARD_LONG[0] <= candidate["long"] <= KEYBOARD_LONG[1]
                and KEYBOARD_SHORT[0] <= candidate["short"] <= KEYBOARD_SHORT[1]
                and KEYBOARD_RISE_MIN <= candidate["top"] - level <= KEYBOARD_RISE):
            candidates.append(candidate)
    if not candidates:
        return None
    expected = np.asarray(expected_xy)[:2]
    close = [c for c in candidates if np.linalg.norm(c["centre"][:2] - expected) < KEYBOARD_GATE]
    if close:
        return min(close, key=lambda c: float(np.linalg.norm(c["centre"][:2] - expected)))
    # Nothing near where the keyboard should be: keep the old fix rather than
    # adopt some other slab (instance 304 swept a slab 1.1 m from the keyboard).
    return None


def keyboard_on_ring(points, level, anchor_xy, gap, here_xy):
    """A keyboard-shaped slab lying `gap` from where the tool was picked up.

    After the drive to the tool, the scan's keyboard position had drifted
    3.5 m on instance 320 and every sweep target was out of reach. The
    tool-keyboard distance does not drift, and the grasp spot was measured
    fresh, so the keyboard lies on that ring whatever the rotation error.
    """
    near = points[np.linalg.norm(points[:, :2] - np.asarray(here_xy)[:2], axis=1) < SCENE_SEARCH]
    slab = near[(near[:, 2] > level + ON_SURFACE[0]) & (near[:, 2] < level + ON_SURFACE[1])]
    best = None
    for cluster in clusters(slab):
        candidate = entry_for(cluster)
        if not (KEYBOARD_LONG[0] <= candidate["long"] <= KEYBOARD_LONG[1]
                and KEYBOARD_SHORT[0] <= candidate["short"] <= KEYBOARD_SHORT[1]
                and KEYBOARD_RISE_MIN <= candidate["top"] - level <= KEYBOARD_RISE):
            continue
        miss = abs(float(np.linalg.norm(candidate["centre"][:2] - np.asarray(anchor_xy)[:2])) - gap)
        if miss < RING_TOLERANCE and (best is None or miss < best[0]):
            best = (miss, candidate)
    return None if best is None else best[1]


def keyboard_nearest(points, level, here_xy, reach=2.0):
    """The keyboard-shaped slab nearest the robot, wherever the old fix was."""
    near = points[np.linalg.norm(points[:, :2] - np.asarray(here_xy)[:2], axis=1) < reach]
    slab = near[(near[:, 2] > level + ON_SURFACE[0]) & (near[:, 2] < level + ON_SURFACE[1])]
    best = None
    for cluster in clusters(slab):
        candidate = entry_for(cluster)
        if (KEYBOARD_LONG[0] <= candidate["long"] <= KEYBOARD_LONG[1]
                and KEYBOARD_SHORT[0] <= candidate["short"] <= KEYBOARD_SHORT[1]
                and KEYBOARD_RISE_MIN <= candidate["top"] - level <= KEYBOARD_RISE):
            gap = float(np.linalg.norm(candidate["centre"][:2] - np.asarray(here_xy)[:2]))
            if best is None or gap < best[0]:
                best = (gap, candidate)
    return None if best is None else best[1]


def refind_tool(target_xy, radius=REFIND_RADIUS):
    """Find the tool again from the home posture, turning a full circle if needed.

    Rotation odometry drifts by roughly 15% of every turn, so after docking
    the robot can face a wall while believing it faces the tool (instance
    310). The tool is the only saturated cyan object, so accept it wherever
    it appears within reach of a short drive; its position is then measured
    in the current, not the drifted, frame.
    """
    go_home()
    for index in range(12):
        if index:
            rotate_base(math.pi / 6)
        view = get_observation()
        remember(view)
        found = find_tool(view)
        if found is not None:
            here = get_robot_position()[0][:2]
            if np.linalg.norm(found["centre"][:2] - here) < radius:
                if index:
                    print("    re-found after %d turns, %.2f m from the old fix"
                          % (index, float(np.linalg.norm(found["centre"][:2] - target_xy))))
                return found
        TRACE["refind_misses"] = TRACE.get("refind_misses", 0) + 1
        if TRACE["refind_misses"] <= 3:
            save_current_observation("refind_miss_%d" % TRACE["refind_misses"])
    return None


def wrist_tool(centre_xy, radius=.20):
    """The handle as seen by the wrist camera from just above it."""
    view = get_observation("right_wrist")
    return tool_near(view, centre_xy, radius=radius, nearest=.04)


def occupancy(points, here, level):
    """Inflated obstacle grid and seen-floor grid centred on the robot."""
    size = int(2 * PLAN_RANGE / PLAN_CELL)
    origin = np.asarray(here, dtype=float)[:2] - PLAN_RANGE
    cells = np.floor((points[:, :2] - origin) / PLAN_CELL).astype(np.int64)
    inside = (cells[:, 0] >= 0) & (cells[:, 1] >= 0) & (cells[:, 0] < size) & (cells[:, 1] < size)
    cells, heights = cells[inside], points[inside, 2]
    solid = np.zeros((size, size), dtype=bool)
    floor = np.zeros((size, size), dtype=bool)
    tall = (heights > PLAN_OBSTACLE_LOW) & (heights < 1.8)
    solid[cells[tall, 0], cells[tall, 1]] = True
    low = heights < .04
    floor[cells[low, 0], cells[low, 1]] = True
    radius = int(math.ceil(PLAN_STATE["inflate"] / PLAN_CELL))
    blocked = np.zeros_like(solid)
    padded = np.pad(solid, radius)
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            if dx * dx + dy * dy <= radius * radius:
                blocked |= padded[radius + dx:radius + dx + size, radius + dy:radius + dy + size]
    # The robot stands on the floor around itself even though the head never
    # sees it; clear that disc.
    centre = int(PLAN_RANGE / PLAN_CELL)
    blind = int(PLAN_BLIND / PLAN_CELL)
    ys, xs = np.mgrid[-blind:blind + 1, -blind:blind + 1]
    disc = xs * xs + ys * ys <= blind * blind
    blocked[centre - blind:centre + blind + 1, centre - blind:centre + blind + 1][disc] = False
    return blocked, floor, origin


def plan_to(target_xy, near, far, level, points, here):
    """Waypoints to the closest free cell whose distance to the target is in [near, far]."""
    blocked, floor, origin = occupancy(points, here, level)
    size = blocked.shape[0]
    start = (int(PLAN_RANGE / PLAN_CELL), int(PLAN_RANGE / PLAN_CELL))
    target = np.asarray(target_xy, dtype=float)[:2]
    cost = np.full((size, size), 1e9)
    parent = {}
    cost[start] = 0
    buckets = [[start]]
    goal = None
    steps = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
    level_index = 0
    while level_index < len(buckets) and goal is None:
        bucket = buckets[level_index]
        for cell in bucket:
            if cost[cell] < level_index:
                continue
            world = origin + (np.array(cell) + .5) * PLAN_CELL
            gap = float(np.linalg.norm(world - target))
            if near <= gap <= far:
                goal = cell
                break
            for dx, dy in steps:
                nx, ny = cell[0] + dx, cell[1] + dy
                if nx < 0 or ny < 0 or nx >= size or ny >= size or blocked[nx, ny]:
                    continue
                step = (3 if dx and dy else 2) * (1 if floor[nx, ny] else 2)
                new = level_index + step
                if new < cost[nx, ny]:
                    cost[nx, ny] = new
                    parent[(nx, ny)] = cell
                    while len(buckets) <= new:
                        buckets.append([])
                    buckets[new].append((nx, ny))
        level_index += 1
    if goal is None:
        return None
    path = [goal]
    while path[-1] != start:
        path.append(parent[path[-1]])
    path = path[::-1]

    def clear(a, b):
        n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) + 1
        for t in np.linspace(0, 1, n + 1):
            x = int(round(a[0] + (b[0] - a[0]) * t))
            y = int(round(a[1] + (b[1] - a[1]) * t))
            if blocked[x, y]:
                return False
        return True

    waypoints = []
    anchor = 0
    while anchor < len(path) - 1:
        reach = len(path) - 1
        while reach > anchor + 1 and not clear(path[anchor], path[reach]):
            reach -= 1
        waypoints.append(origin + (np.array(path[reach]) + .5) * PLAN_CELL)
        anchor = reach
    return waypoints


PLAN_STATE = {"inflate": PLAN_INFLATE}


def plan_dock(target_xy, near, far, legs=4):
    """Reach a spot near..far from a target along a planned, collision-free path.

    The straight-line dock stalled against desks and chairs on 11 of 20
    instances, leaving the tool 1.3-2.1 m away. This plans on an occupancy
    grid built from the single current view - older views are rotated by
    odometry drift and smeared the grid into a solid block - drives one leg,
    then looks again and re-plans.
    """
    target_xy = np.asarray(target_xy, dtype=float)[:2]
    for leg in range(legs):
        face(target_xy)
        restore_trunk()
        view = get_observation()
        remember(view)
        here = get_robot_position()[0][:2]
        gap = float(np.linalg.norm(here - target_xy))
        if near - PLAN_SLACK <= gap <= far + PLAN_SLACK:
            return True
        # Aim for the inner part of the band: the planner stops at the first
        # band cell it reaches, and the base parks up to 0.11 m short of a
        # goal, which left it just outside the band and re-planning the same
        # leg over and over (instances 302, 308, 310).
        # The view after turning to face the target can be walled in by a
        # chair beside the base (instance 301 found no path from it, but did
        # from the scan view taken on the same spot), so also use the view
        # from before the turn, then relax the band and the clearance.
        # Adding views only ever adds obstacles, so the union of the facing
        # view and the scan view found no path on instances 303 and 319 while
        # the scan view alone did. Try each recent view alone, then the union,
        # relaxing the band and the clearance step by step.
        sources = [MAP[-1]] + ([MAP[-2]] if len(MAP) >= 2 else [])
        if len(MAP) >= 2:
            sources.append(np.concatenate(MAP[-2:]))
        waypoints = None
        for lo, hi, inflate in ((near, near + PLAN_INNER, PLAN_INFLATE), (near, far, PLAN_INFLATE),
                                (near, far + .05, PLAN_INFLATE - .06), (near, far + .20, PLAN_INFLATE - .10)):
            PLAN_STATE["inflate"] = inflate
            for points in sources:
                waypoints = plan_to(target_xy, lo, hi, LEVEL, points, here)
                if waypoints:
                    break
            if waypoints:
                break
        PLAN_STATE["inflate"] = PLAN_INFLATE
        if not waypoints:
            print("    plan leg %d: no path from %s (%.2f m away)" % (leg, np.round(here, 2), gap))
            return False
        step = waypoints[0]
        if np.linalg.norm(step - here) > PLAN_LEG:
            step = here + (step - here) / np.linalg.norm(step - here) * PLAN_LEG
        ahead = waypoints[1] if len(waypoints) > 1 and np.linalg.norm(step - waypoints[0]) < .05 else target_xy
        ok = go_to(np.array([step[0], step[1], math.atan2(ahead[1] - step[1], ahead[0] - step[0])]))
        VISITED.append(get_robot_position()[0][:2].copy())
        print("    plan leg %d: %d waypoints, drove to %s -> %s" % (leg, len(waypoints), np.round(step, 2),
                                                                 "ok" if ok else "stalled"))
    here = get_robot_position()[0][:2]
    return near - PLAN_SLACK <= float(np.linalg.norm(here - target_xy)) <= far + PLAN_SLACK


def calibrate_fingers():
    """Which joints are the right-hand fingers, and their empty-closed opening.

    Measured, not assumed: open, close on nothing, and the joints that moved
    are the fingers. Closing on the 0.02-0.04 m handle stops them partway.
    """
    open_gripper(1)
    opened = get_current_joint_positions()
    close_gripper(1)
    shut = get_current_joint_positions()
    fingers = [index for index in range(len(opened)) if abs(opened[index] - shut[index]) > .005]
    open_gripper(1)
    return (fingers, float(sum(shut[index] for index in fingers)),
            float(sum(opened[index] for index in fingers)))


def finger_opening(fingers):
    joints = get_current_joint_positions()
    return float(sum(joints[index] for index in fingers))


def level_rod(points):
    """Rotate the hand so the held rod lies level; returns the correction.

    The rod can be carried off level - up to ~35 degrees was seen (instance
    306) - and then its low end digs into the keys. Rotating about the
    horizontal axis perpendicular to the rod, through the grip, levels it
    without changing its heading. The fit uses the handle points seen before
    the grasp; the touch-calibrated sweep height covers what this misses.
    """
    global GRASP_OFFSET
    centred = points - points.mean(axis=0)
    if len(centred) < 20:
        return 0.
    _, _, basis = np.linalg.svd(centred, full_matrices=False)
    direction = basis[0] / (np.linalg.norm(basis[0]) + 1e-9)
    flat = np.array([direction[0], direction[1], 0.])
    if np.linalg.norm(flat) < 1e-6:
        return 0.
    flat = flat / np.linalg.norm(flat)
    angle = math.acos(float(np.clip(np.dot(direction, flat), -1., 1.)))
    if angle < LEVEL_MIN or angle > LEVEL_MAX:
        return 0.
    axis = np.cross(direction, flat)
    axis = axis / (np.linalg.norm(axis) + 1e-9)
    position, quat = get_current_eef_pose(1)
    for fraction in (1., .6):
        turn = Rotation.from_rotvec(axis * angle * fraction)
        target = (turn * Rotation.from_quat(np.asarray(quat)[[1, 2, 3, 0]])).as_quat()[[3, 0, 1, 2]]
        if move_hand((position, target), 1, max_joint_step=.01):
            GRASP_OFFSET = turn.apply(GRASP_OFFSET)
            return angle * fraction
    return 0.


def tilted_grasp(grasp_pose, tilt, toward_xy):
    """A top-down grasp tipped about the rod so the hand comes in from the
    robot's side. The jaws still close across the rod, and the pre-grasp,
    backed off along the tilted approach, is nearer the robot: on instances
    303 and 305 the base stalled 0.86-1.0 m from the tool and no straight-down
    pre-grasp could be reached from there.
    """
    position, quat = grasp_pose
    rotation = Rotation.from_quat(np.asarray(quat)[[1, 2, 3, 0]])
    rod = rotation.as_matrix()[:, 0]
    for sign in (1., -1.):
        candidate = Rotation.from_rotvec(rod * sign * tilt) * rotation
        approach = candidate.as_matrix()[:, 2]
        if float(np.dot(approach[:2], toward_xy)) >= 0:
            return candidate.as_quat()[[3, 0, 1, 2]], approach
    return np.asarray(quat), rotation.as_matrix()[:, 2]


FINGERS, EMPTY_SHUT, FULL_OPEN = calibrate_fingers()
print("fingers %s | empty-closed %.4f | fully open %.4f" % (FINGERS, EMPTY_SHUT, FULL_OPEN))

HELD = False
for attempt in range(4):
    if attempt == 0 or attempt == 2:
        if not plan_dock(TOOL_HOME[:2], PLAN_NEAR, PLAN_FAR):
            # The desk-edge fallback picked the far side of the desk on
            # instance 301 and drove into it; approach straight instead.
            stand_at(TOOL_HOME[:2], GRASP_REACH)
    distance = float(np.linalg.norm(TOOL_HOME[:2] - get_robot_position()[0][:2]))
    if not PLAN_NEAR - .05 <= distance <= PLAN_FAR + .05:
        distance = stand_at(TOOL_HOME[:2], GRASP_REACH)
    found = refind_tool(TOOL_HOME[:2])
    if found is None:
        print("  attempt %d: tool not re-found near %s" % (attempt, np.round(TOOL_HOME[:2], 2)))
        continue
    TOOL, TOOL_HOME = found, found["centre"].copy()
    distance = float(np.linalg.norm(TOOL_HOME[:2] - get_robot_position()[0][:2]))
    if abs(distance - GRASP_REACH) > .15:
        # Fresh fix, but not at a good reach: reposition and look once more.
        stand_at(TOOL_HOME[:2], GRASP_REACH)
        again = refind_tool(TOOL_HOME[:2])
        if again is not None:
            TOOL, TOOL_HOME = again, again["centre"].copy()
        distance = float(np.linalg.norm(TOOL_HOME[:2] - get_robot_position()[0][:2]))
    save_current_observation("before_grasp_%d" % attempt)
    TRACE["grasp_attempts"] += 1
    pregrasps, grasps = sample_grasp_pose_from_points(TOOL["points"])
    open_gripper(1)
    # A parallel gripper is symmetric, so the same grasp turned 180 degrees
    # about the vertical is equally good; the helper never offers it, and on
    # instance 310 the offered one needed a wrist angle past its limit.
    FLIP = 0.
    TILT = 0.
    toward = TOOL_HOME[:2] - get_robot_position()[0][:2]
    toward = toward / (np.linalg.norm(toward) + 1e-9)
    above = reach_with_yaw(pregrasps[0])
    if not above:
        flipped = (pregrasps[0][0], turned(pregrasps[0][1], math.pi))
        above = reach_with_yaw(flipped)
        FLIP = math.pi if above else 0.
    if not above:
        for tilt in GRASP_TILTS:
            for flip in (0., math.pi):
                quat, approach = tilted_grasp((grasps[0][0], turned(grasps[0][1], flip)), tilt, toward)
                if move_hand((grasps[0][0] - approach * PREGRASP_BACKOFF, quat), 1):
                    above, FLIP, TILT = True, flip, tilt
                    break
            if above:
                break
    refined = wrist_tool(TOOL_HOME[:2])
    ROD_POINTS = TOOL["points"]
    if refined is not None and len(refined["points"]) >= 40:
        ROD_POINTS = refined["points"]
        shift = float(np.linalg.norm(refined["centre"][:2] - TOOL_HOME[:2]))
        pregrasps, grasps = sample_grasp_pose_from_points(refined["points"])
        if TILT:
            quat, approach = tilted_grasp((grasps[0][0], turned(grasps[0][1], FLIP)), TILT, toward)
            above = bool(move_hand((grasps[0][0] - approach * PREGRASP_BACKOFF, quat), 1))
        else:
            above = bool(move_hand((pregrasps[0][0], turned(pregrasps[0][1], FLIP)), 1))
        TOOL_HOME = refined["centre"].copy()
    else:
        shift = -1.
    grasps = [(grasps[0][0], turned(grasps[0][1], FLIP))] + list(grasps[1:])
    if TILT:
        grasps = [(grasps[0][0], tilted_grasp(grasps[0], TILT, toward)[0])] + list(grasps[1:])
    down = bool(move_hand(grasps[0], 1, max_joint_step=.005))
    # The rod sits where it lay, relative to where the hand closed on it. The
    # finger-link origins are 0.02 m above the pads, so they are not a guide.
    GRASP_OFFSET = TOOL_HOME - get_current_eef_pose(1)[0]
    if np.linalg.norm(GRASP_OFFSET[:2]) > .08 or abs(GRASP_OFFSET[2]) > .05:
        # The hand did not end up on the tool; use the typical measured value.
        GRASP_OFFSET = np.array([0., 0., -.007])
    close_gripper(1)
    lift_arm(1, distance=.12)
    opening = finger_opening(FINGERS)
    # Held only if the hand actually got down to the tool: on instance 302
    # the fingers read 0.085 after a grasp whose descent had failed.
    HELD = bool(down) and EMPTY_SHUT + FINGER_MARGIN < opening < FULL_OPEN - FINGER_MARGIN
    print("  attempt %d: base-tool %.2f m | above %s | wrist refine shift %.3f | down %s | fingers %.4f -> %s"
          % (attempt, distance, above, shift, down, opening, "HELD" if HELD else "empty"))
    save_current_observation("after_grasp_%d" % attempt)
    if HELD:
        TRACE["grasp_verified"] += 1
        GRASP_SPOT = TOOL_HOME.copy()
        LEVELLED = level_rod(ROD_POINTS)
        print("    rod levelled by %.1f deg" % math.degrees(LEVELLED))
        break
    open_gripper(1)

print("held", HELD, "attempts", TRACE["grasp_attempts"])

# Code block 3
"""Carry the tool to the keyboard and sweep it across in lanes.

The rod's direction comes from proprioception, not vision: a top-down grasp
closes across the rod, so the rod lies along the gripper's x axis, and turning
the wrist turns it. The rod's centre sits at the finger centre.

Heights: the bristle end is about 0.05 m across and the handle about 0.035 m.
With the rod's axis 0.033 m above the keyboard top, the removal box (the
object's AABB grown by 0.02 m) reaches below the top face on both parts, so it
encloses the dust, while the rod barely touches the keys.

Lanes: the handle is held near its middle, and the bristles extend 0.12 m to
one side, unknown which. Three lanes 0.05 m apart cover the keyboard's 0.18 m
width with margin whichever way the bristles point.
"""


def sweep_lane(lane, direction, quat, offset, targets_along):
    reached = []
    first = None
    for along in targets_along[::direction]:
        spot = KEYBOARD_HOME[:2] + KEYBOARD_AXIS * along + ACROSS * lane
        target = np.array([spot[0], spot[1], SWEEP_Z]) - offset
        if first is None:
            first = target
            reach_with_yaw((target + np.array([0, 0, .08]), quat))
        ok = bool(move_hand((target, quat), 1, max_joint_step=.008))
        reached.append(ok)
        TRACE["waypoints"] += 1
        if len(reached) >= 2 and not reached[-1] and not reached[-2]:
            break  # out of reach from here; each further miss costs ~200 steps
    move_hand((get_current_eef_pose(1)[0] + np.array([0, 0, .06]), quat), 1)
    return reached


RESULT = {"held": HELD, "lanes": 0, "reached": 0, "total": 0}
if not HELD:
    print("no verified grasp, so nothing to sweep with")
else:
    ACROSS = np.array([-KEYBOARD_AXIS[1], KEYBOARD_AXIS[0]])
    # Carry the tool high and close to the body before driving, and lay the
    # rod along the keyboard now, while the arm has room to turn.
    # No carry pose: holding the tool with the arm extended at 1.06 m tipped
    # the robot over while it drove (instance 320). The grasp's own lift is
    # what the successful run drove with.
    # Pull the held tool in, low and close, before the base drives. Left
    # extended ~0.85 m over the desk, it swung into objects while the base
    # turned and the arm ended 0.49 m off target (instance 313). This pose is
    # lower and nearer than the carry pose that tipped the robot over.
    # No tuck either: moving the loaded arm before driving tipped the robot
    # again (instance 303 under v19, camera view rolled onto the floor). Drive
    # with the hand where the grasp's lift left it, as the successful runs did.
    carried = True
    quat = get_current_eef_pose(1)[1]
    delta = signed_angle(rod_axis(quat), KEYBOARD_AXIS)
    for turn in (delta, delta - math.pi if delta > 0 else delta + math.pi):
        if move_hand((get_current_eef_pose(1)[0], turned(quat, turn)), 1):
            break
    print("carried %s | rod turned toward the keyboard axis: %s"
          % (carried, np.round(rod_axis(get_current_eef_pose(1)[1]), 2)))
    # Face the keyboard and look, rather than running a dock search: the
    # search spent ~1500 steps on instance 303 and the step limit is 5814.
    face(KEYBOARD_HOME[:2])
    again = None
    for index in range(12):
        if index:
            # Headings 0, +30, -30, +60, -60, ... then onward round the circle.
            rotate_base((1 if index % 2 else -1) * index * math.pi / 6 if index < 7 else math.pi / 6)
        view = get_observation()
        remember(view)
        here = get_robot_position()[0][:2]
        if SCAN_GAP is not None:
            again = keyboard_on_ring(world_points(view), LEVEL, GRASP_SPOT[:2], SCAN_GAP, here)
        else:
            again = keyboard_near(world_points(view), LEVEL, KEYBOARD_HOME[:2], here)
        if again is not None:
            break
    if again is not None:
        KEYBOARD_HOME = again["centre"].copy()
        KEYBOARD_AXIS = again["axis"].copy()
        KEYBOARD_TOP = float(again["top"])
        ACROSS = np.array([-KEYBOARD_AXIS[1], KEYBOARD_AXIS[0]])
        save_current_observation("redetected")
        print("keyboard re-detected at %s top %.3f (%.2f x %.2f)"
              % (np.round(KEYBOARD_HOME, 3), KEYBOARD_TOP, again["long"], again["short"]))
    else:
        print("keyboard not re-detected; using the scan's fix")
    assert again is not None or KEYBOARD_KNOWN, "Holding the tool but never found the keyboard"
    save_current_observation("at_keyboard")

    PARTIAL_VIEW = [False]

    def refresh_keyboard(gate=.35):
        """Re-detect the keyboard from here and keep its axis sign.

        Moving the base sideways between passes turns it through ~180
        degrees, and rotation odometry drifts ~15%, so the keyboard's
        odometry-frame pose goes stale; side passes then missed it.
        """
        global KEYBOARD_HOME, KEYBOARD_AXIS, KEYBOARD_TOP
        view = get_observation()
        remember(view)
        seen = find_keyboard(world_points(view), LEVEL, KEYBOARD_HOME)
        if seen is None or np.linalg.norm(seen["centre"][:2] - KEYBOARD_HOME[:2]) > gate:
            return False
        axis = seen["axis"] if float(np.dot(seen["axis"], KEYBOARD_AXIS)) >= 0 else -seen["axis"]
        PARTIAL_VIEW[0] = not (KEYBOARD_COMPLETE[0] <= seen["long"] <= KEYBOARD_COMPLETE[1])
        if not PARTIAL_VIEW[0]:
            KEYBOARD_HOME, KEYBOARD_AXIS, KEYBOARD_TOP = seen["centre"].copy(), axis, float(seen["top"])
            return True
        # A partial view - the held tool and arm hide part of the keyboard -
        # still fixes its heading and where it lies across its width, which is
        # what the across-keyboard strokes need. Its centre along the length is
        # biased toward the visible end, so keep the old along-position. Taking
        # partial centroids whole put strokes beside the keyboard (instance 307).
        offset = KEYBOARD_HOME[:2] - seen["centre"][:2]
        centre = seen["centre"][:2] + axis * float(np.dot(offset, axis))
        KEYBOARD_HOME = np.array([centre[0], centre[1], seen["centre"][2]])
        KEYBOARD_AXIS, KEYBOARD_TOP = axis, float(seen["top"])
        return True

    # Stand straight out from the keyboard's long side, as close as the desk
    # edge allows, facing it.
    points = map_points()
    desk_points = points[np.abs(points[:, 2] - LEVEL) < .03]
    here = get_robot_position()[0][:2]

    def desk_near(spot):
        if len(desk_points) == 0:
            return 0
        return int((np.linalg.norm(desk_points[:, :2] - spot, axis=1) < STANCE_DESK_CLEAR).sum())

    sides = []
    for sign in (1., -1.):
        out = ACROSS * sign
        for standoff in (.68, .72, .76, .80):
            if desk_near(KEYBOARD_HOME[:2] + out * standoff) == 0:
                break
        sides.append((desk_near(KEYBOARD_HOME[:2] + out * standoff), standoff,
                      float(np.linalg.norm(KEYBOARD_HOME[:2] + out * standoff - here)), sign))
    sides.sort()
    OUT = ACROSS * sides[0][3]
    # Use the standoff that worked, not the smallest "desk-clear" one: the
    # map-dependent pick drifted to 0.80 m, where the tipped hand clipped and
    # shoved the keyboard 0.22 m (instance 301). If the desk is closer than
    # the map suggests, the drive simply stops at it.
    STANDOFF = STANCE_FIXED
    stance = KEYBOARD_HOME[:2] + OUT * STANDOFF
    go_to(np.array([stance[0], stance[1], math.atan2(-OUT[1], -OUT[0])]))
    stand_at(KEYBOARD_HOME[:2], STANDOFF)
    refreshed = refresh_keyboard()
    if not refreshed:
        # The held tool hangs in front of the head camera; lift it out of the
        # way, then glance either side. Sweeping the stale scan fix instead put
        # every stroke of instance 307 somewhere else.
        position, quat = get_current_eef_pose(1)
        move_hand((position + np.array([0., 0., .15]), quat), 1, max_joint_step=FAST_STEP)
        refreshed = refresh_keyboard(gate=.60)
        for turn in (.35, -.70):
            if refreshed:
                break
            rotate_base(turn)
            refreshed = refresh_keyboard(gate=.60)
        # Still nothing: every stroke swept from a stale fix removed no dust
        # (15 held runs of v35, one success). Look all the way round before
        # sweeping; a slab near the old fix beats sweeping empty desk.
        fallback = None
        for index in range(11):
            if refreshed:
                break
            rotate_base(math.pi / 6)
            view = get_observation()
            remember(view)
            view_points = world_points(view)
            again = keyboard_near(view_points, LEVEL, KEYBOARD_HOME[:2], get_robot_position()[0][:2])
            if again is None and fallback is None:
                candidate = keyboard_nearest(view_points, LEVEL, get_robot_position()[0][:2])
                # Same distance from the grasp spot as the scan measured, or
                # it is some other slab (v39 swept the wrong one on 304, 314, 317).
                if candidate is not None and (SCAN_GAP is None or abs(float(np.linalg.norm(
                        candidate["centre"][:2] - GRASP_SPOT[:2])) - SCAN_GAP) < FALLBACK_RING):
                    fallback = candidate
                    save_current_observation("fallback_slab")
            if again is None and index == 10 and fallback is not None:
                # Nothing near the fix all the way round: the fix itself was
                # wrong (the post-grasp ring search can latch onto another
                # slab; instances 302 and 304). Take the nearest keyboard-shaped
                # slab rather than sweep empty desk.
                again = fallback
                print("keyboard fix abandoned; nearest keyboard-shaped slab instead")
            if again is not None:
                axis = again["axis"] if float(np.dot(again["axis"], KEYBOARD_AXIS)) >= 0 else -again["axis"]
                KEYBOARD_HOME, KEYBOARD_AXIS, KEYBOARD_TOP = again["centre"].copy(), axis, float(again["top"])
                save_current_observation("stance_search_found")
                print("keyboard found on the stance search at %s (%.2f x %.2f, rise %.3f)"
                      % (np.round(KEYBOARD_HOME, 3), again["long"], again["short"], again["top"] - LEVEL))
                refreshed = True
        if refreshed:
            ACROSS = np.array([-KEYBOARD_AXIS[1], KEYBOARD_AXIS[0]])
            OUT = ACROSS * (1. if float(np.dot(ACROSS, get_robot_position()[0][:2] - KEYBOARD_HOME[:2])) >= 0 else -1.)
            stance = KEYBOARD_HOME[:2] + OUT * STANDOFF
            go_to(np.array([stance[0], stance[1], math.atan2(-OUT[1], -OUT[0])]))
            stand_at(KEYBOARD_HOME[:2], STANDOFF)
            refresh_keyboard(gate=.35)
    if refreshed and PARTIAL_VIEW[0]:
        # Only part of the keyboard was in view, usually at the image edge:
        # face what was seen and look again for the whole of it.
        face(KEYBOARD_HOME[:2])
        refresh_keyboard(gate=.35)
    save_current_observation("stance")
    print("keyboard refreshed at the stance:", refreshed, "| partial view:", PARTIAL_VIEW[0])
    print("stance %.2f m out on the %s side; now %.2f m from the keyboard centre"
          % (STANDOFF, "+" if sides[0][3] > 0 else "-",
             float(np.linalg.norm(get_robot_position()[0][:2] - KEYBOARD_HOME[:2]))))

    # Lay the rod along the keyboard. Swept toward and away from the robot,
    # the hand can then pitch forward about the rod's own axis: the rod stays
    # level and aligned while the fingers reach about 0.1 m further than a
    # straight-down hand, which topped out near 0.6 m (instance 313).
    eef_position, eef_quat = get_current_eef_pose(1)
    delta = signed_angle(rod_axis(eef_quat), KEYBOARD_AXIS)
    for turn in (delta, delta - math.pi if delta > 0 else delta + math.pi):
        if abs(turn) < .05 or move_hand((eef_position, turned(eef_quat, turn)), 1):
            delta = turn
            break
    eef_position, eef_quat = get_current_eef_pose(1)
    OFFSET = np.array([*(Rotation.from_euler("z", delta).as_matrix()[:2, :2] @ GRASP_OFFSET[:2]),
                       GRASP_OFFSET[2]])
    print("wrist turned %.0f deg | rod axis %s | keyboard axis %s | hand-to-rod %s"
          % (math.degrees(delta), np.round(rod_axis(eef_quat), 2), np.round(KEYBOARD_AXIS, 2),
             np.round(OFFSET, 3)))

    TILT_AXIS = np.array([-OUT[1], OUT[0], 0.])
    TILT_AXIS = TILT_AXIS / (np.linalg.norm(TILT_AXIS) + 1e-9)

    def pitched(quat, radians):
        """Tip the fingers away from the robot, about the rod's axis."""
        current = Rotation.from_quat(np.asarray(quat)[[1, 2, 3, 0]])
        return (Rotation.from_rotvec(TILT_AXIS * radians) * current).as_quat()[[3, 0, 1, 2]]

    # Start with the configuration the arm is in right now, after the wrist
    # turn: instance 307 jammed before any stroke had set one, and with
    # nothing to fall back to every later plan failed.
    SAFE = {"joints": get_current_joint_positions()}

    def lift_clear(height=.12):
        """Lift straight up, or escape in joint space if the arm is jammed.

        Driven into the keyboard, the loaded arm reached a state from which
        every IK plan failed, even a 9 cm lift (instance 301 under v17), and
        all remaining passes were lost. move_to_joints needs no IK, so fall
        back to the last configuration that held the rod safely above the keys.
        """
        position, quat = get_current_eef_pose(1)
        if move_hand((position + np.array([0, 0, height]), quat), 1, max_joint_step=FAST_STEP):
            return True
        if get_current_eef_pose(1)[0][2] > position[2] + height / 2:
            return True
        if SAFE["joints"] is not None:
            try:
                move_to_joints(SAFE["joints"], max_joint_step=FAST_STEP)
                TRACE["escapes"] = TRACE.get("escapes", 0) + 1
                return True
            except ValueError:
                pass
        return False

    def place_rod(point, step=SWEEP_STEP):
        """Put the rod's centre at a point, tilting the hand if it must."""
        for tilt in TILTS:
            target = point - OFFSET
            if move_hand((target, pitched(eef_quat, tilt)), 1, max_joint_step=step):
                return tilt
            # move_hand demands 2.5 cm; a hand a few centimetres off still
            # drags the rod across the keys, and lifting it here would not.
            if np.linalg.norm(get_current_eef_pose(1)[0] - target) < CLOSE_ENOUGH:
                return tilt
        # One lift after all tilts failed, not one per tilt: a stroke whose
        # every point failed that way used ~3000 steps (instances 307, 309).
        lift_clear()
        return None

    SWEEP_Z = KEYBOARD_TOP + ROD_CLEARANCE

    def touch_height(spot=None):
        """Sweep height from touch: step down over the keyboard centre until
        the hand stops following, i.e. the rod's lowest point is on the keys.

        The removal box is the tool's axis-aligned box grown by 0.02 m, so
        its floor sits 0.02 m under the tool's lowest point across the whole
        footprint: whatever the rod's tilt, it covers every key once that
        lowest point skims the keys. The rod is often carried tilted (up to
        ~35 degrees), and a fixed height either dug its low end in - shoving
        the keyboard - or left the box floor above the dust. Touch also
        absorbs the camera's ~1 cm height bias.
        """
        above = (KEYBOARD_HOME[:2] if spot is None else spot) - OFFSET[:2]
        position = np.array([above[0], above[1], KEYBOARD_TOP + TOUCH_FROM - OFFSET[2]])
        if not move_hand((position, eef_quat), 1, max_joint_step=FAST_STEP):
            if np.linalg.norm(get_current_eef_pose(1)[0] - position) > CLOSE_ENOUGH:
                return None
        start = float(get_current_eef_pose(1)[0][2])
        stuck = 0
        for _ in range(TOUCH_STEPS):
            before = float(get_current_eef_pose(1)[0][2])
            target = get_current_eef_pose(1)[0] - np.array([0., 0., TOUCH_STEP])
            move_hand((target, eef_quat), 1, max_joint_step=.004)
            actual = get_current_eef_pose(1)[0]
            # Give up after two steps with no descent: when the hand simply
            # cannot go there, each attempt still costs ~100 steps, and one
            # failed probe used ~1800 of the 5814 (instance 304).
            stuck = stuck + 1 if before - actual[2] < TOUCH_STEP / 3 else 0
            if stuck >= 2 and start - actual[2] < TOUCH_STEP / 2:
                return None
            if actual[2] - target[2] > TOUCH_BLOCKED:
                # Only a stop after real descent, at a height where a rod up
                # to ~35 degrees off level could be resting on the keys, is a
                # touch; a hand that never moved down is a planning failure.
                axis = float(actual[2]) + OFFSET[2]
                if start - actual[2] > TOUCH_STEP / 2 and KEYBOARD_TOP - .01 <= axis <= KEYBOARD_TOP + .17:
                    return float(actual[2])
                return None
        return None

    contact = touch_height()
    if contact is not None:
        SWEEP_Z = contact + TOUCH_LIFT + OFFSET[2]
    lift_clear(.08)
    print("touch height: contact eef z %s -> rod target %.3f (keyboard top seen at %.3f)"
          % ("none" if contact is None else "%.3f" % contact, SWEEP_Z, KEYBOARD_TOP))
    # Keep sweeping until the episode ends: success terminates it at once, so
    # extra passes cost nothing, and a full 9/9 sweep on instance 311 still
    # left 1 of 20 particles. Later rounds interleave along the keyboard and
    # run the other way across it.
    # Few stances, several strokes each. Base moves cost ~300 steps apiece
    # and most near misses ran out of the 5814-step budget, so each stance
    # now sweeps a zig-zag of strokes 0.10 m apart along the keyboard instead
    # of one. Leftover dust clustered at one end of the keyboard's long axis
    # (the arm holding the tool hides part of the keyboard, biasing its
    # observed centre), so the strokes reach +-0.33 m, well past its ends.
    # One stance: the 0.44 m removal box covers most of the keyboard's length
    # per stroke, so strokes a few centimetres apart suffice, and base moves
    # - ~300 steps each - are what ran the near misses out of time.
    ROUNDS = (((0.,), (-.08, .08)),
              ((0.,), (-.16, 0., .16)),
              ((0.,), (-.04, .04, -.12, .12)))
    def cross_sweep():
        """Sweep with the rod pointing away from the robot, along the keyboard.

        Laid along the keyboard, the rod's far strokes need the hand 0.10 m
        past the keyboard's centre; where the desk edge stops the base short,
        every stroke was out of reach (5 of 18 fresh-seed runs of v35). Turned
        to point outward, the tool's box spans the keyboard's whole width from
        a hand held nearer the robot, and one stroke along the length covers it.
        """
        global eef_quat, OFFSET, SWEEP_Z, OUT
        lift_clear(.15)
        position, quat = get_current_eef_pose(1)
        delta = signed_angle(rod_axis(quat), OUT)
        choice = None
        for turn in sorted((delta, delta - math.pi if delta > 0 else delta + math.pi), key=abs):
            if abs(turn) < .05 or move_hand((position, turned(quat, turn)), 1, max_joint_step=.01):
                choice = turn
                break
        if choice is None:
            print("cross sweep: could not turn the rod outward")
            return
        eef_quat = get_current_eef_pose(1)[1]
        OFFSET = np.array([*(Rotation.from_euler("z", choice).as_matrix()[:2, :2] @ OFFSET[:2]), OFFSET[2]])
        SAFE["joints"] = get_current_joint_positions()
        touch = touch_height(KEYBOARD_HOME[:2] + OUT * CROSS_RADIAL[0])
        if touch is not None:
            SWEEP_Z = touch + TOUCH_LIFT + OFFSET[2]
        lift_clear(.08)
        print("cross sweep: rod axis %s | out %s | touch %s -> rod target %.3f"
              % (np.round(rod_axis(eef_quat), 2), np.round(OUT, 2),
                 "none" if touch is None else "%.3f" % touch, SWEEP_Z))
        count = 0
        for sweep_round in range(4):
            if sweep_round and count == 0:
                break  # not one stroke reachable in a whole round
            for k, radial in enumerate(CROSS_RADIAL):
                alongs = CROSS_ALONG if (k + sweep_round) % 2 == 0 else CROSS_ALONG[::-1]
                if refresh_keyboard(gate=.30):
                    perpendicular = np.array([-KEYBOARD_AXIS[1], KEYBOARD_AXIS[0]])
                    OUT = perpendicular if float(np.dot(perpendicular, OUT)) >= 0 else -perpendicular
                start = KEYBOARD_HOME[:2] + KEYBOARD_AXIS * alongs[0] + OUT * radial
                above = np.array([start[0], start[1], SWEEP_Z + .10]) - OFFSET
                if not move_hand((above, eef_quat), 1, max_joint_step=FAST_STEP) and \
                        np.linalg.norm(get_current_eef_pose(1)[0] - above) > CLOSE_ENOUGH:
                    print("  cross %+.2f: approach unreachable, skipped" % radial)
                    lift_clear()
                    continue
                SAFE["joints"] = get_current_joint_positions()
                reached = []
                for along in alongs:
                    point = KEYBOARD_HOME[:2] + KEYBOARD_AXIS * along + OUT * radial
                    target = np.array([point[0], point[1], SWEEP_Z]) - OFFSET
                    ok = move_hand((target, eef_quat), 1, max_joint_step=SWEEP_STEP)
                    reached.append(bool(ok) or np.linalg.norm(get_current_eef_pose(1)[0] - target) < CLOSE_ENOUGH)
                    TRACE["waypoints"] += 1
                    if len(reached) >= 3 and not any(reached[-3:]):
                        break
                RESULT["lanes"] += 1
                RESULT["reached"] += sum(reached)
                RESULT["total"] += len(reached)
                print("  cross %+.2f: %s" % (radial, "".join("x" if ok else "." for ok in reached)))
                lifted = get_current_eef_pose(1)
                move_hand((lifted[0] + np.array([0, 0, .07]), lifted[1]), 1)
                save_current_observation("after_cross_%d" % count)
                count += 1

    index = 0
    unreachable = 0
    for stances, offsets in ROUNDS:
        if unreachable >= 2:
            break
        for stance_along in stances:
            lift_clear(.15)
            spot = KEYBOARD_HOME[:2] + KEYBOARD_AXIS * stance_along + OUT * STANDOFF
            go_to(np.array([spot[0], spot[1], math.atan2(-OUT[1], -OUT[0])]))
            if refresh_keyboard():
                perpendicular = np.array([-KEYBOARD_AXIS[1], KEYBOARD_AXIS[0]])
                OUT = perpendicular if float(np.dot(perpendicular, OUT)) >= 0 else -perpendicular
                TILT_AXIS = np.array([-OUT[1], OUT[0], 0.])
                if contact is None:
                    SWEEP_Z = KEYBOARD_TOP + ROD_CLEARANCE
            for stroke, offset in enumerate(offsets):
                along = stance_along + offset
                radial_path = RADIAL if stroke % 2 == 0 else RADIAL[::-1]
                # Re-find the keyboard before every stroke: the rod nudges it,
                # and on instance 301 it slid 0.18 m and the last particles
                # sat 1-7 cm outside every later stroke. Looking costs no steps.
                if refresh_keyboard(gate=.30):
                    perpendicular = np.array([-KEYBOARD_AXIS[1], KEYBOARD_AXIS[0]])
                    OUT = perpendicular if float(np.dot(perpendicular, OUT)) >= 0 else -perpendicular
                    TILT_AXIS = np.array([-OUT[1], OUT[0], 0.])
                start_point = KEYBOARD_HOME[:2] + KEYBOARD_AXIS * along + OUT * radial_path[0]
                started = place_rod(np.array([start_point[0], start_point[1], SWEEP_Z + .10]), FAST_STEP)
                if started is None and radial_path[0] < radial_path[-1]:
                    # Every other stroke starts at the far edge; when only
                    # that end is out of reach, sweep it from the near end.
                    radial_path = radial_path[::-1]
                    start_point = KEYBOARD_HOME[:2] + KEYBOARD_AXIS * along + OUT * radial_path[0]
                    started = place_rod(np.array([start_point[0], start_point[1], SWEEP_Z + .10]), FAST_STEP)
                if started is None:
                    # Cannot even get above the start: skip the stroke rather
                    # than spend hundreds of steps on each of its points.
                    print("  pass %+.2f: approach unreachable, skipped" % along)
                    index += 1
                    unreachable += 1
                    if unreachable >= 2:
                        break
                    continue
                SAFE["joints"] = get_current_joint_positions()
                tilts = []
                for radial in radial_path:
                    point = KEYBOARD_HOME[:2] + KEYBOARD_AXIS * along + OUT * radial
                    tilts.append(place_rod(np.array([point[0], point[1], SWEEP_Z])))
                    TRACE["waypoints"] += 1
                reached = [tilt is not None for tilt in tilts]
                # Two poor strokes in a row: the lengthwise rod is out of
                # reach here, so turn it outward instead.
                unreachable = unreachable + 1 if sum(reached) < 2 else 0
                RESULT["lanes"] += 1
                RESULT["reached"] += sum(reached)
                RESULT["total"] += len(reached)
                print("  pass %+.2f: %s (tilts %s)" % (along, "".join("x" if ok else "." for ok in reached),
                                                     [None if t is None else round(t, 2) for t in tilts]))
                lifted = get_current_eef_pose(1)
                move_hand((lifted[0] + np.array([0, 0, .07]), lifted[1]), 1)
                save_current_observation("after_pass_%d" % index)
                index += 1
                if unreachable >= 2:
                    break

    if unreachable >= 2:
        cross_sweep()

print("RESULT", RESULT, "TRACE", TRACE)
