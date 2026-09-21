# Code block 1
"""Look-only probe: does a toggleable object other than the radio render its
``ToggledOn`` marker visibly?

The radio policy grounds the control by finding the marker cap in RGB.  That
works because the radio's cap protrudes 3.6 mm proud of its collision face,
through the speaker recess.  The scanner's sits 1.8 mm *below* its lid surface,
so it may not render at all.  This probe drives nothing and presses nothing: it
rotates in place, saves every view, and reports what small round blobs of any
colour it can find, so the question can be answered from the images.
"""

import numpy as np

SPAN_MIN, SPAN_MAX = .002, .060


def components(mask, limit=40000):
    height, width = mask.shape
    seen = np.zeros(mask.shape, dtype=bool)
    out = []
    budget = limit
    ys, xs = np.nonzero(mask)
    for sy, sx in zip(ys, xs):
        if seen[sy, sx] or budget <= 0 or len(out) > 300:
            continue
        stack = [(int(sy), int(sx))]
        seen[sy, sx] = True
        pix = []
        while stack:
            py, px = stack.pop()
            pix.append((py, px))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = py + dy, px + dx
                    if (0 <= ny < height and 0 <= nx < width
                            and mask[ny, nx] and not seen[ny, nx]):
                        seen[ny, nx] = True
                        stack.append((ny, nx))
        budget -= len(pix)
        out.append(np.asarray(pix, dtype=int))
    return out


def saturated(image, channel):
    others = [c for c in (0, 1, 2) if c != channel]
    return ((image[..., channel] > 110)
            & (image[..., channel] > 1.7 * image[..., others[0]])
            & (image[..., channel] > 1.7 * image[..., others[1]]))


def report(tag):
    observation = get_observation("head")
    image = observation["rgb"].astype(float)
    depth = observation["depth"]
    finite = np.isfinite(depth) & (depth > 0) & (depth < 6)
    for name, channel in (("red", 0), ("green", 1)):
        mask = saturated(image, channel) & finite
        if int(mask.sum()) < 6:
            continue
        for pixels in components(mask):
            if len(pixels) < 8:
                continue
            rows, cols = pixels[:, 0], pixels[:, 1]
            height = int(rows.max() - rows.min() + 1)
            width = int(cols.max() - cols.min() + 1)
            blob = np.zeros(mask.shape, dtype=bool)
            blob[rows, cols] = True
            world = mask_to_world_points(blob, depth, observation["intrinsics"],
                                         observation["world_from_camera"])
            if len(world) < 6:
                continue
            span = float(np.max(np.percentile(world, 90, axis=0)
                                - np.percentile(world, 10, axis=0)))
            point = np.median(world, axis=0)
            if SPAN_MIN <= span <= SPAN_MAX and max(height, width) < 140:
                print(tag, name, "blob px", len(pixels), "hw", height, width,
                      "span_mm", round(span * 1000, 1),
                      "world", np.round(point, 3).tolist())


for step in range(12):
    save_current_observation("look_" + str(step))
    report("look_" + str(step))
    rotate_base(np.pi / 6)
print("probe complete")
RESULT = {"probe": "look-only, no motion beyond base rotation"}
