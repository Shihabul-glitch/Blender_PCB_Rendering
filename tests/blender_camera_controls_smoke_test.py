"""Headless acceptance test for PCB Studio's still-camera controls."""

from __future__ import annotations

import sys
from math import isclose, radians
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pcb_studio
from pcb_studio.constants import (
    CAMERA_NAME,
    CAMERA_ORBIT_ROOT_NAME,
    CAMERA_TARGET_CONSTRAINT_NAME,
    CAMERA_TARGET_NAME,
    COLLECTION_NAME,
)
from pcb_studio.utils.camera import setup_camera
from pcb_studio.utils.geometry import compute_pcb_bounds


def _create_mock_pcb() -> bpy.types.Object:
    collection = bpy.data.collections.new(COLLECTION_NAME)
    bpy.context.scene.collection.children.link(collection)
    mesh = bpy.data.meshes.new("CameraTestPCBMesh")
    mesh.from_pydata(
        [
            (-4.0, -2.0, -0.1), (4.0, -2.0, -0.1),
            (4.0, 2.0, -0.1), (-4.0, 2.0, -0.1),
            (-4.0, -2.0, 0.1), (4.0, -2.0, 0.1),
            (4.0, 2.0, 0.1), (-4.0, 2.0, 0.1),
        ],
        [],
        [
            (0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
            (1, 5, 6, 2), (2, 6, 7, 3), (4, 0, 3, 7),
        ],
    )
    mesh.update()
    obj = bpy.data.objects.new("CameraTestPCB", mesh)
    collection.objects.link(obj)
    return obj


def _close(left: Vector, right: Vector, tolerance: float = 1e-5) -> bool:
    return (left - right).length <= tolerance


def run() -> None:
    pcb_studio.register()
    try:
        scene = bpy.context.scene
        props = scene.pcb_studio_import
        pcb = _create_mock_pcb()
        bounds = compute_pcb_bounds(bpy.data.collections[COLLECTION_NAME])
        assert bounds.is_valid
        setup_camera(bounds)
        props.scene_setup_ready = True

        camera = bpy.data.objects[CAMERA_NAME]
        target = bpy.data.objects[CAMERA_TARGET_NAME]
        constraint = camera.constraints[CAMERA_TARGET_CONSTRAINT_NAME]
        assert props.camera_preset == "TOP"
        assert props.camera_control_mode == "AUTO_TARGET"
        assert isclose(camera.data.lens, 75.0)
        assert _close(target.matrix_world.translation, bounds.center)
        assert isclose(camera.matrix_world.translation.x, bounds.center.x, abs_tol=1e-6)
        assert isclose(camera.matrix_world.translation.y, bounds.center.y, abs_tol=1e-6)
        assert camera.matrix_world.translation.z > bounds.center.z
        assert not constraint.mute

        # A user-authored target constraint must survive every setup refresh.
        user_target = bpy.data.objects.new("UserCameraTarget", None)
        scene.collection.objects.link(user_target)
        user_track = camera.constraints.new(type="DAMPED_TRACK")
        user_track.name = "User Camera Track"
        user_track.target = user_target
        user_track.influence = 0.25
        setup_camera(bounds)
        assert camera.constraints.get("User Camera Track") == user_track
        assert isclose(user_track.influence, 0.25)

        assert bpy.ops.pcbstudio.set_camera_control_mode(mode="MANUAL") == {"FINISHED"}
        assert constraint.mute
        before_camera = camera.matrix_world.translation.copy()
        before_target = target.matrix_world.translation.copy()
        assert bpy.ops.pcbstudio.camera_nudge(action="LEFT") == {"FINISHED"}
        assert not _close(camera.matrix_world.translation, before_camera)
        assert _close(target.matrix_world.translation, before_target)

        camera_before_pan = camera.matrix_world.translation.copy()
        target_before_pan = target.matrix_world.translation.copy()
        assert bpy.ops.pcbstudio.camera_nudge(action="PAN_UP") == {"FINISHED"}
        camera_delta = camera.matrix_world.translation - camera_before_pan
        target_delta = target.matrix_world.translation - target_before_pan
        assert _close(camera_delta, target_delta)

        distance = (camera.matrix_world.translation - target.matrix_world.translation).length
        assert bpy.ops.pcbstudio.camera_nudge(action="ORBIT_DOWN") == {"FINISHED"}
        assert isclose(
            (camera.matrix_world.translation - target.matrix_world.translation).length,
            distance,
            rel_tol=1e-5,
        )
        assert bpy.ops.pcbstudio.camera_nudge(action="ROLL_RIGHT") == {"FINISHED"}
        assert isclose(props.camera_roll, radians(5.0), abs_tol=1e-5)

        assert bpy.ops.pcbstudio.set_camera_control_mode(mode="AUTO_TARGET") == {"FINISHED"}
        assert not constraint.mute
        props.camera_target_offset_x = 0.5
        props.camera_target_offset_y = -0.25
        assert isclose(target.matrix_world.translation.x, bounds.center.x + 0.5, abs_tol=1e-5)
        assert isclose(target.matrix_world.translation.y, bounds.center.y - 0.25, abs_tol=1e-5)

        bpy.context.view_layer.objects.active = pcb
        pcb.select_set(True)
        assert bpy.ops.pcbstudio.aim_camera_at_selected() == {"FINISHED"}
        assert bpy.ops.pcbstudio.fit_camera_selected() == {"FINISHED"}
        assert bpy.ops.pcbstudio.zoom_to_fit() == {"FINISHED"}

        assert bpy.ops.pcbstudio.save_camera_view() == {"FINISHED"}
        saved_location = camera.matrix_world.translation.copy()
        saved_target = target.matrix_world.translation.copy()
        saved_lens = camera.data.lens
        assert bpy.ops.pcbstudio.camera_nudge(action="DOLLY_OUT") == {"FINISHED"}
        camera.data.lens = 35.0
        assert bpy.ops.pcbstudio.restore_camera_view() == {"FINISHED"}
        assert _close(camera.matrix_world.translation, saved_location)
        assert _close(target.matrix_world.translation, saved_target)
        assert isclose(camera.data.lens, saved_lens)

        assert bpy.ops.pcbstudio.reset_camera() == {"FINISHED"}
        assert props.camera_preset == "TOP"
        assert props.camera_control_mode == "AUTO_TARGET"
        assert isclose(camera.data.lens, 75.0)

        # Still controls must refuse to alter an animation-owned camera.
        rig = bpy.data.objects.new(CAMERA_ORBIT_ROOT_NAME, None)
        scene.collection.objects.link(rig)
        locked_location = camera.matrix_world.translation.copy()
        try:
            locked_result = bpy.ops.pcbstudio.camera_nudge(action="RIGHT")
        except RuntimeError as exc:
            assert "controls are locked" in str(exc)
        else:
            assert locked_result == {"CANCELLED"}
        assert _close(camera.matrix_world.translation, locked_location)
        bpy.data.objects.remove(rig, do_unlink=True)

        # These controls are deliberately non-animated, even with auto-key on.
        scene.tool_settings.use_keyframe_insert_auto = True
        assert bpy.ops.pcbstudio.camera_nudge(action="DOWN") == {"FINISHED"}
        assert camera.animation_data is None or camera.animation_data.action is None
        assert target.animation_data is None or target.animation_data.action is None
        assert camera.constraints.get("User Camera Track") == user_track
        scene.tool_settings.use_keyframe_insert_auto = False

        # --- Declared board orientation ---
        # Manual mode with the default axes describes exactly the flat board the
        # automatic guess finds, so it must not move the camera at all.
        assert bpy.ops.pcbstudio.apply_camera_preset() == {"FINISHED"}
        auto_top = camera.matrix_world.translation.copy()
        props.board_orientation_mode = "MANUAL"
        props.board_top_axis = "POS_Z"
        props.board_front_axis = "NEG_Y"
        assert bpy.ops.pcbstudio.apply_camera_preset() == {"FINISHED"}
        assert _close(camera.matrix_world.translation, auto_top)

        # A front edge along the declared top face collapses the camera basis,
        # so the property must refuse it rather than store it.
        props.board_front_axis = "POS_Z"
        assert props.board_front_axis != "POS_Z"
        assert props.board_front_axis == "NEG_Y"

        # Declare the board as standing upright: top faces +Y, front faces +Z.
        props.board_top_axis = "POS_Y"
        props.board_front_axis = "POS_Z"
        target_location = target.matrix_world.translation.copy()
        assert bpy.ops.pcbstudio.apply_camera_preset() == {"FINISHED"}
        offset = camera.matrix_world.translation - target_location
        assert offset.y > 0.0 and abs(offset.x) < 1e-4 and abs(offset.z) < 1e-4, tuple(offset)
        # The declared front edge sits at the bottom of a Top view.  Roll is read
        # off rotation_euler because this camera also carries the user-authored
        # track constraint added above, which owns the evaluated world matrix.
        assert (camera.rotation_euler.to_quaternion() @ Vector((0.0, 1.0, 0.0))).z < -0.9

        # Front Flat is now an elevation of the declared front edge, not the face.
        props.camera_preset = "FRONT_FLAT"
        assert bpy.ops.pcbstudio.apply_camera_preset() == {"FINISHED"}
        offset = camera.matrix_world.translation - target_location
        assert offset.z > 0.0 and abs(offset.x) < 1e-4 and abs(offset.y) < 1e-4, tuple(offset)
        # The board's top face points up in frame for an elevation view.
        assert (camera.rotation_euler.to_quaternion() @ Vector((0.0, 1.0, 0.0))).y > 0.9

        # Left and Right are the remaining declared axis, one each way.
        props.camera_preset = "RIGHT"
        assert bpy.ops.pcbstudio.apply_camera_preset() == {"FINISHED"}
        right_offset = camera.matrix_world.translation - target_location
        props.camera_preset = "LEFT"
        assert bpy.ops.pcbstudio.apply_camera_preset() == {"FINISHED"}
        left_offset = camera.matrix_world.translation - target_location
        assert right_offset.x * left_offset.x < 0.0, (tuple(right_offset), tuple(left_offset))
        assert abs(right_offset.y) < 1e-4 and abs(right_offset.z) < 1e-4

        props.board_orientation_mode = "AUTO"
    finally:
        pcb_studio.unregister()

    print("PCB Studio still-camera controls smoke test passed.")


if __name__ == "__main__":
    run()
