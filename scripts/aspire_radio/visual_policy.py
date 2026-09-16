"""Adapted from ASPIRE's R1ProRadioCodeEnv.ORACLE_CODE (pickup, not toggle)."""

import numpy as np

# Code block 1
save_current_observation("initial")
assert find_object_base_rotate("red radio"), "Radio not visible after base scan"
radio_pos, radio_quat, _, radio_points, radio_box = get_object_pose("red radio")
table_pos, table_quat, _, table_points, table_box = get_object_pose("table")
goal = get_navigation_pose(table_points, radio_points)
assert navigate_to_pose(goal), "Visual approach did not converge"
save_current_observation("pregrasp")

# Code block 2
# The ASPIRE pickup example supplies this sequence; reference RGB supports right-hand holding.
pregrasps, grasps = sample_grasp_pose("red radio")
held = False
for pregrasp, grasp in zip(pregrasps, grasps):
    if grasp_object(pregrasp, grasp, "red radio", arm=1) and check_object_in_hand(arm=1):
        held = True
        break
assert held, "Observed radio did not rise with the hand"
save_current_observation("after_grasp")

# Code block 3
# The free left hand operates the front control; never chase it with the holding hand.
obs = get_observation()
radios = segment_sam3_text_prompt(obs["rgb"], "red radio")
buttons = segment_sam3_text_prompt(obs["rgb"], "power button on the red radio")
assert radios and buttons, "Power button needs visual grounding; do not substitute a simulator marker"
candidates = []
for button in buttons:
    if button["score"] < 0.1:
        continue
    ys, xs = np.where(button["mask"])
    if len(xs) == 0:
        continue
    x, y = int(np.median(xs)), int(np.median(ys))
    for radio in radios:
        x1, y1, x2, y2 = radio["box"]
        if radio["score"] >= 0.1 and x1 <= x <= x2 and y1 <= y <= y2:
            candidates.append((button["score"] + radio["score"], x, y))
assert candidates, "No confident button detection falls within a detected radio"
_, button_x, button_y = max(candidates)
pressed = press_at_pixel(button_x, button_y, arm=0)
assert pressed, "Press motion did not reach the observed target"

RESULT = {"grasp_observed": held, "press_motion_completed": pressed}
