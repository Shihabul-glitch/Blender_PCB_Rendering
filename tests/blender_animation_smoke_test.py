"""Headless Blender acceptance test for PCB Studio animation modes."""

from __future__ import annotations

import sys
from math import radians
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pcb_studio
from pcb_studio.constants import (
    BACKGROUND_NAME,
    CAMERA_NAME,
    CAMERA_FLYOVER_ROOT_NAME,
    CAMERA_ORBIT_MOUNT_NAME,
    CAMERA_ORBIT_ROOT_NAME,
    CAMERA_TARGET_NAME,
    COLLECTION_NAME,
    DOF_TARGET_NAME,
    FILL_LIGHT_NAME,
    KEY_LIGHT_NAME,
    PROP_SCENE_ATTR,
    REFLECTION_PLANE_NAME,
    RIM_LIGHT_2_NAME,
    RIM_LIGHT_NAME,
    ROOT_EMPTY_NAME,
    TOP_LIGHT_NAME,
)
from pcb_studio.utils.geometry import compute_pcb_bounds


def _action_fcurves(obj: bpy.types.Object):
    action = obj.animation_data.action
    legacy = getattr(action, "fcurves", None)
    if legacy is not None:
        return legacy
    from bpy_extras.anim_utils import animdata_get_channelbag_for_assigned_slot

    channelbag = animdata_get_channelbag_for_assigned_slot(obj.animation_data)
    assert channelbag is not None
    return channelbag.fcurves


def _create_mock_pcb() -> None:
    collection = bpy.data.collections.new(COLLECTION_NAME)
    bpy.context.scene.collection.children.link(collection)

    mesh = bpy.data.meshes.new("SmokeTestPCBMesh")
    mesh.from_pydata(
        [
            (-2.0, -1.0, -0.1),
            (2.0, -1.0, -0.1),
            (2.0, 1.0, -0.1),
            (-2.0, 1.0, -0.1),
            (-2.0, -1.0, 0.1),
            (2.0, -1.0, 0.1),
            (2.0, 1.0, 0.1),
            (-2.0, 1.0, 0.1),
        ],
        [],
        [
            (0, 1, 2, 3),
            (4, 7, 6, 5),
            (0, 4, 5, 1),
            (1, 5, 6, 2),
            (2, 6, 7, 3),
            (4, 0, 3, 7),
        ],
    )
    mesh.update()
    collection.objects.link(bpy.data.objects.new("SmokeTestPCB", mesh))


def _assert_matrix_close(
    left: Matrix,
    right: Matrix,
    tolerance: float = 1e-5,
) -> None:
    for row in range(4):
        for column in range(4):
            assert abs(left[row][column] - right[row][column]) <= tolerance


def _camera_position(camera: bpy.types.Object, frame: int) -> Vector:
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    return camera.matrix_world.translation.copy()


def _assert_camera_aims_at(
    camera: bpy.types.Object,
    center: Vector,
    tolerance: float = 0.999,
) -> None:
    forward = camera.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))
    desired = (center - camera.matrix_world.translation).normalized()
    assert forward.normalized().dot(desired) >= tolerance


def _configure_animation(props, animation_type: str, rotation: str = "360") -> None:
    props.animation_type = animation_type
    props.turntable_duration = 2.0
    props.turntable_fps = "24"
    props.turntable_rotation_degrees = rotation
    props.turntable_direction = "CLOCKWISE"
    props.turntable_motion_style = "CONSTANT"
    props.turntable_start_angle = 0.0


def _setup_camera_orbit(props, rotation: str = "360") -> None:
    _configure_animation(props, "CAMERA_ORBIT", rotation)
    assert bpy.ops.pcbstudio.setup_turntable() == {"FINISHED"}


def run() -> None:
    pcb_studio.register()
    try:
        _create_mock_pcb()
        props = getattr(bpy.context.scene, PROP_SCENE_ATTR)
        props.pcb_imported = True

        assert bpy.ops.pcbstudio.prepare_scene() == {"FINISHED"}

        # Focused regression checks for the scene features Camera Orbit uses.
        props.camera_preset = "ISOMETRIC"
        assert bpy.ops.pcbstudio.apply_camera_preset() == {"FINISHED"}
        assert bpy.ops.pcbstudio.zoom_to_fit() == {"FINISHED"}
        props.use_depth_of_field = True
        props.focus_target_mode = "PCB_CENTER"
        assert bpy.ops.pcbstudio.apply_camera_settings() == {"FINISHED"}
        props.reflection_surface = "SUBTLE"
        assert bpy.ops.pcbstudio.apply_reflection_plane() == {"FINISHED"}
        props.studio_lighting_preset = "PCB_SHOWCASE"
        assert bpy.ops.pcbstudio.apply_lighting_preset() == {"FINISHED"}

        camera = bpy.data.objects[CAMERA_NAME]
        target = bpy.data.objects[CAMERA_TARGET_NAME]
        root = bpy.data.objects[ROOT_EMPTY_NAME]
        pcb_bounds = compute_pcb_bounds(bpy.data.collections[COLLECTION_NAME])
        center = pcb_bounds.center.copy()

        original_camera_matrix = camera.matrix_world.copy()
        original_camera_parent = camera.parent
        original_target_matrix = target.matrix_world.copy()
        root_matrix = root.matrix_world.copy()
        studio_names = (
            KEY_LIGHT_NAME,
            FILL_LIGHT_NAME,
            RIM_LIGHT_NAME,
            RIM_LIGHT_2_NAME,
            TOP_LIGHT_NAME,
            BACKGROUND_NAME,
            REFLECTION_PLANE_NAME,
            DOF_TARGET_NAME,
        )
        studio_matrices = {
            name: bpy.data.objects[name].matrix_world.copy()
            for name in studio_names
        }

        # True camera translation at quarter points of a circular 360-degree orbit.
        _setup_camera_orbit(props)
        pivot = bpy.data.objects[CAMERA_ORBIT_ROOT_NAME]
        mount = bpy.data.objects[CAMERA_ORBIT_MOUNT_NAME]
        assert mount.parent == pivot
        assert camera.parent == mount
        assert root.animation_data is None
        assert (pivot.matrix_world.translation - center).length <= 1e-6

        frames = (1, 13, 25, 37, 49)
        positions = [_camera_position(camera, frame) for frame in frames]
        for position in positions[1:4]:
            assert (position - positions[0]).length > 0.1

        radii = [(position - center).xy.length for position in positions]
        heights = [position.z - center.z for position in positions]
        for radius in radii[1:]:
            assert abs(radius - radii[0]) <= 1e-5
        for height in heights[1:]:
            assert abs(height - heights[0]) <= 1e-5
        assert (positions[-1] - positions[0]).length <= 1e-5

        for frame in frames[:4]:
            _camera_position(camera, frame)
            _assert_camera_aims_at(camera, center)
            _assert_matrix_close(root.matrix_world, root_matrix)
            for name, original_matrix in studio_matrices.items():
                _assert_matrix_close(
                    bpy.data.objects[name].matrix_world,
                    original_matrix,
                )

        # Direction reverses positional travel.
        clockwise_quarter = positions[1] - center
        assert bpy.ops.pcbstudio.reset_turntable() == {"FINISHED"}
        _configure_animation(props, "CAMERA_ORBIT")
        props.turntable_direction = "COUNTER_CLOCKWISE"
        assert bpy.ops.pcbstudio.setup_turntable() == {"FINISHED"}
        counter_quarter = _camera_position(camera, 13) - center
        assert (clockwise_quarter.xy + counter_quarter.xy).length <= 1e-5

        # 180 degrees produces a half orbit; 720 produces two full orbits.
        assert bpy.ops.pcbstudio.reset_turntable() == {"FINISHED"}
        _setup_camera_orbit(props, "180")
        half_start = _camera_position(camera, 1) - center
        half_end = _camera_position(camera, 49) - center
        assert (half_start.xy + half_end.xy).length <= 1e-5
        assert abs(half_start.z - half_end.z) <= 1e-5

        assert bpy.ops.pcbstudio.reset_turntable() == {"FINISHED"}
        _setup_camera_orbit(props, "720")
        double_start = _camera_position(camera, 1)
        double_middle = _camera_position(camera, 25)
        double_end = _camera_position(camera, 49)
        assert (double_middle - double_start).length <= 1e-5
        assert (double_end - double_start).length <= 1e-5

        # Start Angle offsets camera position, not camera Euler orientation.
        assert bpy.ops.pcbstudio.reset_turntable() == {"FINISHED"}
        _configure_animation(props, "CAMERA_ORBIT")
        props.turntable_start_angle = radians(90.0)
        assert bpy.ops.pcbstudio.setup_turntable() == {"FINISHED"}
        start_offset = _camera_position(camera, 1) - center
        original_offset = original_camera_matrix.translation - center
        expected_offset = Vector((-original_offset.y, original_offset.x, original_offset.z))
        assert (start_offset - expected_offset).length <= 1e-5

        # Motion style controls only angular timing; the orbit remains circular.
        assert bpy.ops.pcbstudio.reset_turntable() == {"FINISHED"}
        _configure_animation(props, "CAMERA_ORBIT")
        props.turntable_motion_style = "EASE_IN_OUT"
        assert bpy.ops.pcbstudio.setup_turntable() == {"FINISHED"}
        orbit = bpy.data.objects[CAMERA_ORBIT_ROOT_NAME]
        orbit_curve = _action_fcurves(orbit).find("rotation_euler", index=2)
        assert orbit_curve is not None
        assert all(
            keyframe.interpolation == "BEZIER"
            for keyframe in orbit_curve.keyframe_points
        )

        # Three repeated setups retain one rig and do not drift.
        assert bpy.ops.pcbstudio.reset_turntable() == {"FINISHED"}
        _configure_animation(props, "CAMERA_ORBIT")
        for _ in range(3):
            assert bpy.ops.pcbstudio.setup_turntable() == {"FINISHED"}
            assert len([
                obj for obj in bpy.data.objects
                if obj.name == CAMERA_ORBIT_ROOT_NAME
            ]) == 1
            assert len([
                obj for obj in bpy.data.objects
                if obj.name == CAMERA_ORBIT_MOUNT_NAME
            ]) == 1
            assert (
                _camera_position(camera, 1) - original_camera_matrix.translation
            ).length <= 1e-5

        # Switching modes clears the inactive system and remains reversible.
        _configure_animation(props, "PCB_TURNTABLE")
        assert bpy.ops.pcbstudio.setup_turntable() == {"FINISHED"}
        assert bpy.data.objects.get(CAMERA_ORBIT_ROOT_NAME) is None
        assert bpy.data.objects.get(CAMERA_ORBIT_MOUNT_NAME) is None
        assert camera.parent == original_camera_parent
        assert root.animation_data is not None

        _setup_camera_orbit(props)
        assert root.animation_data is None
        assert camera.parent == bpy.data.objects[CAMERA_ORBIT_MOUNT_NAME]

        # Reset restores exact camera, parent, target, PCB, and timeline state.
        assert bpy.ops.pcbstudio.reset_turntable() == {"FINISHED"}
        assert bpy.data.objects.get(CAMERA_ORBIT_ROOT_NAME) is None
        assert bpy.data.objects.get(CAMERA_ORBIT_MOUNT_NAME) is None
        assert camera.parent == original_camera_parent
        _assert_matrix_close(camera.matrix_world, original_camera_matrix)
        _assert_matrix_close(target.matrix_world, original_target_matrix)
        _assert_matrix_close(root.matrix_world, root_matrix)
        assert bpy.context.scene.frame_start == 1
        assert bpy.context.scene.frame_end == 250

        # Cinematic Flyover physically translates the camera while every
        # non-camera studio element and PCB_MODEL_ROOT remains stationary.
        original_camera_matrix = camera.matrix_world.copy()
        original_camera_parent = camera.parent
        original_target_matrix = target.matrix_world.copy()
        props.animation_type = "CINEMATIC_FLYOVER"
        props.flyover_style = "DIAGONAL_REVEAL"
        props.flyover_height = "MEDIUM"
        props.turntable_duration = 2.0
        props.turntable_fps = "24"
        props.turntable_motion_style = "EASE_IN_OUT"
        assert bpy.ops.pcbstudio.setup_turntable() == {"FINISHED"}
        flyover = bpy.data.objects[CAMERA_FLYOVER_ROOT_NAME]
        assert camera.parent == flyover
        assert root.animation_data is None
        flyover_frames = (1, 13, 24, 36, 48)
        flyover_positions = [_camera_position(camera, frame) for frame in flyover_frames]
        print("Flyover camera world positions:", [tuple(round(v, 4) for v in p) for p in flyover_positions])
        assert all(
            (flyover_positions[index] - flyover_positions[index - 1]).length > 0.05
            for index in range(1, len(flyover_positions))
        )
        for frame in flyover_frames:
            _camera_position(camera, frame)
            _assert_camera_aims_at(camera, center)
            _assert_matrix_close(root.matrix_world, root_matrix)
            for name, original_matrix in studio_matrices.items():
                _assert_matrix_close(bpy.data.objects[name].matrix_world, original_matrix)

        flyover_action = flyover.animation_data.action
        location_curves = [curve for curve in _action_fcurves(flyover) if curve.data_path == "location"]
        assert len(location_curves) == 3
        assert all(
            point.interpolation == "BEZIER"
            for curve in location_curves for point in curve.keyframe_points
        )

        # Styles and normalized heights produce distinct paths and elevations.
        style_positions = {}
        height_values = {}
        for style in ("SIDE_SWEEP", "DIAGONAL_REVEAL"):
            props.flyover_style = style
            assert bpy.ops.pcbstudio.setup_turntable() == {"FINISHED"}
            style_positions[style] = (
                _camera_position(camera, 1), _camera_position(camera, 48),
            )
        assert abs(style_positions["SIDE_SWEEP"][0].y - style_positions["SIDE_SWEEP"][1].y) <= 1e-5
        assert abs(style_positions["DIAGONAL_REVEAL"][0].y - style_positions["DIAGONAL_REVEAL"][1].y) > 0.1
        for height in ("LOW", "MEDIUM", "HIGH"):
            props.flyover_height = height
            assert bpy.ops.pcbstudio.setup_turntable() == {"FINISHED"}
            height_values[height] = _camera_position(camera, 1).z
        assert height_values["LOW"] < height_values["MEDIUM"] < height_values["HIGH"]

        # Repeated setup remains singular, and switching clears the old rig.
        for _ in range(3):
            assert bpy.ops.pcbstudio.setup_turntable() == {"FINISHED"}
            assert len([o for o in bpy.data.objects if o.name == CAMERA_FLYOVER_ROOT_NAME]) == 1
        _configure_animation(props, "CAMERA_ORBIT")
        assert bpy.ops.pcbstudio.setup_turntable() == {"FINISHED"}
        assert bpy.data.objects.get(CAMERA_FLYOVER_ROOT_NAME) is None
        props.animation_type = "CINEMATIC_FLYOVER"
        props.flyover_style = "DIAGONAL_REVEAL"
        props.flyover_height = "MEDIUM"
        assert bpy.ops.pcbstudio.setup_turntable() == {"FINISHED"}
        assert bpy.data.objects.get(CAMERA_ORBIT_ROOT_NAME) is None

        assert bpy.ops.pcbstudio.reset_turntable() == {"FINISHED"}
        assert bpy.data.objects.get(CAMERA_FLYOVER_ROOT_NAME) is None
        assert camera.parent == original_camera_parent
        _assert_matrix_close(camera.matrix_world, original_camera_matrix)
        _assert_matrix_close(target.matrix_world, original_target_matrix)
        _assert_matrix_close(root.matrix_world, root_matrix)

        print("PCB Studio orbit and cinematic-flyover acceptance tests passed.")
    finally:
        pcb_studio.unregister()


if __name__ == "__main__":
    run()
