"""ASPIRE-style radio policy composed from the annotated local skill library."""

# Code block 1
print(f"Reference navigation success: {execute_reference_skill('move to')}")

# Code block 2
print(f"Reference pickup success: {execute_reference_skill('pick up from')}")
pressed = execute_reference_skill("press")
if not pressed:
    pressed = execute_reference_skill("press")
print(f"Reference press success: {pressed}")
RESULT = {"success": pressed}
