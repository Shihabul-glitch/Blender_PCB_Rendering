"""Turntable animation setup and reset utilities."""

from __future__ import annotations

from math import radians

import bpy

from ..constants import ROOT_EMPTY_NAME


def _get_root() -> bpy.types.Object | None:
    """Return PCB_MODEL_ROOT or None."""
    return bpy.data.objects.get(ROOT_EMPTY_NAME)


def _clear_turntable_keyframes(root: bpy.types.Object) -> None:
    """Remove only Z-rotation keyframes from *root*."""
    if root.animation_data is None or root.animation_data.action is None:
        return
    action = root.animation_data.action
    fcurve = action.fcurves.find("rotation_euler", index=2)
    if fcurve is not None:
        action.fcurves.remove(fcurve)
    # If no fcurves remain, clear animation data.
    if len(action.fcurves) == 0:
        root.animation_data_clear()


def get_turntable_frame_count(duration: float, fps: int) -> int:
    """Calculate total rendered frames for a turntable.

    Args:
        duration: Animation duration in seconds.
        fps: Frames per second.

    Returns:
        Integer frame count.
    """
    return max(1, int(round(duration * fps)))


def setup_turntable(
    duration: float,
    fps: int,
    rotation_degrees: float,
    direction: str,
    start_angle_degrees: float,
    motion_style: str,
) -> str:
    """Create turntable keyframes on PCB_MODEL_ROOT.

    Rotates around local Z axis.  The first frame is 1; the last
    rendered frame is ``total_frames``.  A keyframe at frame
    ``total_frames + 1`` creates the final orientation for seamless
    looping without rendering a duplicate frame.

    Args:
        duration: Animation duration in seconds.
        fps: Frames per second.
        rotation_degrees: Total rotation (180, 360, or 720).
        direction: "CLOCKWISE" or "COUNTER_CLOCKWISE".
        start_angle_degrees: Starting angle offset.
        motion_style: "CONSTANT" or "EASE_IN_OUT".

    Returns:
        A status message.
    """
    root = _get_root()
    if root is None:
        return "PCB_MODEL_ROOT not found. Run Prepare Scene first."

    total_frames = get_turntable_frame_count(duration, fps)

    # Determine sign and total rotation.
    sign = -1.0 if direction == "CLOCKWISE" else 1.0
    total_radians = radians(rotation_degrees) * sign
    start_radians = radians(start_angle_degrees % 360.0)

    # Clear previous turntable keyframes.
    _clear_turntable_keyframes(root)

    # Ensure animation data exists.
    if root.animation_data is None:
        root.animation_data_create()

    # First keyframe.
    root.rotation_euler.z = start_radians
    root.keyframe_insert(data_path="rotation_euler", index=2, frame=1)

    # Final keyframe (one frame past render end for seamless loop).
    root.rotation_euler.z = start_radians + total_radians
    root.keyframe_insert(
        data_path="rotation_euler", index=2, frame=total_frames + 1,
    )

    # Set interpolation on all new keyframes.
    if root.animation_data and root.animation_data.action:
        for fcurve in root.animation_data.action.fcurves:
            if fcurve.data_path == "rotation_euler" and fcurve.array_index == 2:
                for kf in fcurve.keyframe_points:
                    if motion_style == "CONSTANT":
                        kf.interpolation = "LINEAR"
                    else:
                        kf.interpolation = "BEZIER"

    # Configure scene timeline.
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = total_frames
    scene.frame_set(1)
    scene.render.fps = fps

    interp = "linear" if motion_style == "CONSTANT" else "bezier ease"
    return (
        f"Turntable set up: {total_frames} frames, "
        f"{rotation_degrees}°, {interp}."
    )


def reset_turntable() -> str:
    """Remove turntable keyframes and restore the PCB to its original
    orientation (rotation_euler Z = 0).

    Returns:
        A status message.
    """
    root = _get_root()
    if root is None:
        return "PCB_MODEL_ROOT not found."

    _clear_turntable_keyframes(root)

    # Restore default rotation.
    root.rotation_euler.z = 0.0

    # Reset timeline.
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 250
    scene.frame_set(1)

    return "Turntable reset. PCB restored to original orientation."