# Code block 1
"""Pick a book off the desk and put it in a bookcase cubby.

`re_shelving_library_books` wants every book `inside` a bookcase, and
`Inside` is satisfied when the book's AABB centre lands in the bookcase's
`openfillable` volume. Unlike the radio's 11 mm toggle sphere that volume is
roughly 0.29 x 0.31 x 0.26 m, so the hard part here is the grasp, not the aim.

Grounding deliberately uses no colour or shape prior for the objects. The
support surface is found as the dominant horizontal plane in a reachable
height band, and anything sitting a few centimetres proud of it inside its
footprint is a candidate object. That is the same primitive most of the
`ontop`/`inside` tasks need, so it is written to be reusable rather than
tuned to books.

Only RGB-D, proprioception, the official relative camera calibration, static
URDF finger geometry and body-velocity odometry are used. No object poses,
registry entries, contacts or demonstrations are read; task success is
reported by the evaluator afterwards and is never an input.
"""

import numpy as np
from scipy.spatial.transform import Rotation

TRACE = {"grasp_attempts": 0, "grasp_verified": 0, "objects_seen": 0}
SUPPORT_BAND = (.45, 1.15)          # plausible table/desk/shelf heights
OBJECT_BAND = (.012, .20)           # how far proud of the surface an object sits
PIXEL_BUDGET = 150000


def components(mask, min_pixels=30):
    height, width = mask.shape
    seen = np.zeros(mask.shape, dtype=bool)
    found = []
    budget = PIXEL_BUDGET
    ys, xs = np.nonzero(mask)
    for start_y, start_x in zip(ys, xs):
        if seen[start_y, start_x]:
            continue
        if budget <= 0 or len(found) >= 300:
            break
        stack = [(int(start_y), int(start_x))]
        seen[start_y, start_x] = True
        pixels = []
        while stack:
            py, px = stack.pop()
            pixels.append((py, px))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = py + dy, px + dx
                    if (0 <= ny < height and 0 <= nx < width
                            and mask[ny, nx] and not seen[ny, nx]):
                        seen[ny, nx] = True
                        stack.append((ny, nx))
        budget -= len(pixels)
        if len(pixels) >= min_pixels:
            found.append(np.asarray(pixels, dtype=int))
    return found


def world_of(observation):
    depth = observation["depth"]
    valid = np.isfinite(depth) & (depth > 0) & (depth < 6)
    points = mask_to_world_points(valid, depth, observation["intrinsics"],
                                  observation["world_from_camera"])
    ys, xs = np.nonzero(valid)
    return valid, ys, xs, points


def support_surface(observation):
    """Dominant horizontal plane in the reachable band, as (height, xy bounds)."""
    valid, ys, xs, points = world_of(observation)
    if len(points) < 500:
        return None
    band = (points[:, 2] > SUPPORT_BAND[0]) & (points[:, 2] < SUPPORT_BAND[1])
    if int(band.sum()) < 400:
        return None
    heights = points[band, 2]
    edges = np.arange(SUPPORT_BAND[0], SUPPORT_BAND[1] + .01, .01)
    counts, _ = np.histogram(heights, bins=edges)
    if counts.max() < 300:
        return None
    level = float(edges[int(np.argmax(counts))] + .005)
    on_plane = band & (np.abs(points[:, 2] - level) < .02)
    if int(on_plane.sum()) < 300:
        return None
    plane_xy = points[on_plane][:, :2]
    lo = np.percentile(plane_xy, 2, axis=0)
    hi = np.percentile(plane_xy, 98, axis=0)
    return level, lo, hi, plane_xy


def objects_on(observation, surface):
    """Clusters standing proud of the support surface, inside its footprint."""
    level, lo, hi, _ = surface
    valid, ys, xs, points = world_of(observation)
    above = ((points[:, 2] > level + OBJECT_BAND[0])
             & (points[:, 2] < level + OBJECT_BAND[1])
             & (points[:, 0] > lo[0] - .04) & (points[:, 0] < hi[0] + .04)
             & (points[:, 1] > lo[1] - .04) & (points[:, 1] < hi[1] + .04))
    if int(above.sum()) < 30:
        return []
    mask = np.zeros(valid.shape, dtype=bool)
    mask[ys[above], xs[above]] = True
    index = np.full(valid.shape, -1, dtype=int)
    index[ys, xs] = np.arange(len(points))
    found = []
    for pixels in components(mask, 30):
        ids = index[pixels[:, 0], pixels[:, 1]]
        ids = ids[ids >= 0]
        if len(ids) < 20:
            continue
        cluster = points[ids]
        extent = np.percentile(cluster, 97, axis=0) - np.percentile(cluster, 3, axis=0)
        if max(float(extent[0]), float(extent[1])) > .45:
            continue                      # a wall or a big fixture, not a movable
        if float(extent[2]) > .35:
            continue
        span = max(float(extent[0]), float(extent[1]))
        # A parallel jaw opens about 0.127 m, and two books 0.13 m apart merge
        # into one cluster whose centre is the gap between them.  Prefer
        # clusters that are plausibly a single graspable item.
        graspable = .05 <= span <= .32 and float(extent[2]) <= .14
        found.append({"points": cluster,
                      "center": np.median(cluster, axis=0),
                      "extent": extent,
                      "span": span,
                      "graspable": graspable,
                      "pixels": len(ids)})
    return sorted(found, key=lambda item: (not item["graspable"], -item["pixels"]))


def dock_at(target_xy, radius, keep_clear=None):
    base = get_robot_position()[0]
    bearing = np.arctan2(base[1] - target_xy[1], base[0] - target_xy[0])
    spot = target_xy + radius * np.array([np.cos(bearing), np.sin(bearing)])
    if keep_clear is not None and len(keep_clear) > 20:
        for _ in range(4):
            gap = np.min(np.linalg.norm(keep_clear - spot, axis=1))
            if gap > .28:
                break
            radius += .10
            spot = target_xy + radius * np.array([np.cos(bearing), np.sin(bearing)])
    step = spot - base[:2]
    if np.linalg.norm(step) > 2.5:
        spot = base[:2] + step / np.linalg.norm(step) * 2.4
    goal = np.array([spot[0], spot[1],
                     np.arctan2(target_xy[1] - spot[1], target_xy[0] - spot[0])])
    return navigate_to_pose(goal)


def survey():
    for camera in ("head",):
        observation = get_observation(camera)
        surface = support_surface(observation)
        if surface is None:
            continue
        items = objects_on(observation, surface)
        if items:
            return observation, surface, items
    return None


# ------------------------------------------------------------- find work ----
scene = None
for step in range(12):
    scene = survey()
    if scene is not None:
        save_current_observation("survey_" + str(step))
        print("survey hit at step", step, "surface_z",
              round(scene[1][0], 3), "objects", len(scene[2]),
              [np.round(o["extent"], 3).tolist() for o in scene[2][:4]])
        break
    rotate_base(np.pi / 6)
assert scene is not None, "No support surface with objects on it was found"
observation, surface, items = scene
TRACE["objects_seen"] = len(items)
graspables = [o for o in items if o["graspable"]]
assert graspables, "Support surface found but nothing on it looks graspable"
target = graspables[0]["center"]

for approach in range(3):
    dock_at(target[:2], .62, surface[3])
    again = survey()
    if again is None:
        continue
    observation, surface, items = again
    graspables = [o for o in items if o["graspable"]]
    near = [o for o in graspables if np.linalg.norm(o["center"][:2] - target[:2]) < .55]
    if near:
        target = near[0]["center"]
    elif graspables:
        target = graspables[0]["center"]
save_current_observation("after_dock")
print("docked; surface_z", round(surface[0], 3), "target",
      np.round(target, 3).tolist(), "objects", len(items))

# Code block 2
# ------------------------------------------------------------------ pick ----
def cluster_near(point, tolerance=.30):
    look = survey()
    if look is None:
        return None, None
    obs, surf, found = look
    close = [o for o in found
             if np.linalg.norm(o["center"] - point) < tolerance and o["graspable"]]
    return (close[0] if close else None), obs


def held_after_lift(before_center, arm):
    """Did something follow the hand up? Purely visual, no object state."""
    hand, _ = get_current_eef_pose(arm)
    observation = get_observation("head")
    surface = support_surface(observation)
    still_there = False
    if surface is not None:
        for item in objects_on(observation, surface):
            if np.linalg.norm(item["center"][:2] - before_center[:2]) < .12 \
                    and abs(float(item["center"][2] - before_center[2])) < .06:
                still_there = True
    valid, ys, xs, points = world_of(observation)
    near_hand = np.linalg.norm(points - hand, axis=1) < .22
    lifted = int(near_hand.sum()) > 60 and float(
        np.median(points[near_hand][:, 2])) > before_center[2] + .04
    print("  verify: still_on_surface", still_there, "mass_near_hand",
          int(near_hand.sum()), "lifted", lifted)
    return bool(lifted and not still_there)

picked = False
pick_arm = 1
for attempt in range(4):
    item, obs = cluster_near(target, .45)
    if item is None:
        if not dock_at(target[:2], .60, surface[3]):
            break
        continue
    target = item["center"]
    save_current_observation("pick_target_" + str(attempt))
    base, _, yaw = get_robot_position()
    lateral = (-np.sin(yaw) * (target[0] - base[0]) + np.cos(yaw) * (target[1] - base[1]))
    for arm in ((0, 1) if lateral > 0 else (1, 0)):
        try:
            pregrasps, grasps = sample_grasp_pose_from_points(item["points"], arm=arm)
        except (ValueError, RuntimeError):
            continue
        for index in range(len(grasps)):
            TRACE["grasp_attempts"] += 1
            try:
                moved = execute_grasp(pregrasps[index], grasps[index], arm=arm, lift=.12)
            except (ValueError, RuntimeError):
                continue
            if not moved:
                open_gripper(arm)
                continue
            save_current_observation("after_lift_" + str(TRACE["grasp_attempts"]))
            if held_after_lift(target, arm):
                picked = True
                pick_arm = arm
                TRACE["grasp_verified"] += 1
                break
            open_gripper(arm)
        if picked:
            break
    if picked:
        break

save_current_observation("after_pick")
print("pick", picked, "attempts", TRACE["grasp_attempts"],
      "verified", TRACE["grasp_verified"], "objects_seen", TRACE["objects_seen"])
RESULT = {"picked": bool(picked), "grasp_attempts": TRACE["grasp_attempts"],
          "grasp_verified": TRACE["grasp_verified"],
          "objects_seen": TRACE["objects_seen"],
          "grounding": "support-plane segmentation, no colour or shape prior"}
