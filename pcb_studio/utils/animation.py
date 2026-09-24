"""PCB turntable and camera-orbit animation utilities."""

from __future__ import annotations

from math import radians

import bpy
from mathutils import Matrix, Vector

from ..constants import (
    CAMERA_NAME,
    CAMERA_FLYOVER_ROOT_NAME,
    CAMERA_ORBIT_MOUNT_NAME,
    CAMERA_ORBIT_ROOT_NAME,
    CAMERA_TARGET_NAME,
    COLLECTION_NAME,
    PROP_SCENE_ATTR,
    RENDER_SETUP_COLLECTION,
    ROOT_EMPTY_NAME,
)
from .geometry import BoundingBox, compute_pcb_bounds
from .camera import ensure_managed_target_constraint

_ORIGINAL_CAMERA_MATRIX = "pcbstudio_original_camera_matrix"
_ORIGINAL_CAMERA_PARENT = "pcbstudio_original_camera_parent"
_ORIGINAL_CAMERA_PARENT_INVERSE = "pcbstudio_original_camera_parent_inverse"
_ORIGINAL_CAMERA_PARENT_TYPE = "pcbstudio_original_camera_parent_type"
_ORIGINAL_CAMERA_PARENT_BONE = "pcbstudio_original_camera_parent_bone"
_ORIGINAL_TARGET_MATRIX = "pcbstudio_original_target_matrix"
_ORBIT_TRACK_CONSTRAINT = "PCB Studio Camera Orbit Track"
_ORBIT_TRACK_CREATED = "pcbstudio_orbit_track_created"
_FLYOVER_TRACK_CONSTRAINT = "PCB Studio Cinematic Flyover Track"
_FLYOVER_TRACK_CREATED = "pcbstudio_flyover_track_created"
_ORIGINAL_CAMERA_LENS = "pcbstudio_original_camera_lens"
_ORIGINAL_FRAME_START = "pcbstudio_original_frame_start"
_ORIGINAL_FRAME_END = "pcbstudio_original_frame_end"
_ORIGINAL_FRAME_CURRENT = "pcbstudio_original_frame_current"


def _object_action_fcurves(obj: bpy.types.Object):
    """Return the assigned slot's F-Curves on Blender 4.5 through 5.2+."""
    animation_data = obj.animation_data
    if animation_data is None or animation_data.action is None:
        return None
    action = animation_data.action
    legacy_fcurves = getattr(action, "fcurves", None)
    if legacy_fcurves is not None:
        return legacy_fcurves
    from bpy_extras.anim_utils import animdata_get_channelbag_for_assigned_slot

    channelbag = animdata_get_channelbag_for_assigned_slot(animation_data)
    return channelbag.fcurves if channelbag is not None else None


def _get_root() -> bpy.types.Object | None:
    """Return PCB_MODEL_ROOT or None."""
    return bpy.data.objects.get(ROOT_EMPTY_NAME)


def _clear_z_rotation_keyframes(obj: bpy.types.Object) -> None:
    """Remove only Z-rotation keyframes from *obj*."""
    if obj.animation_data is None or obj.animation_data.action is None:
        return
    fcurves = _object_action_fcurves(obj)
    if fcurves is None:
        return
    fcurve = fcurves.find("rotation_euler", index=2)
    if fcurve is not None:
        fcurves.remove(fcurve)
    if len(fcurves) == 0:
        obj.animation_data_clear()


def _matrix_to_list(matrix: Matrix) -> list[float]:
    """Flatten a 4x4 matrix for storage as a Blender custom property."""
    return [float(matrix[row][column]) for row in range(4) for column in range(4)]


def _list_to_matrix(values: object) -> Matrix | None:
    """Rebuild a 4x4 matrix stored by :func:`_matrix_to_list`."""
    if values is None or len(values) != 16:
        return None
    return Matrix(
        tuple(
            tuple(values[row * 4 + column] for column in range(4))
            for row in range(4)
        ),
    )


def _get_pcb_bounds() -> BoundingBox | None:
    """Return the current world-space PCB bounds."""
    collection = bpy.data.collections.get(COLLECTION_NAME)
    if collection is None:
        return None
    bounds = compute_pcb_bounds(collection)
    return bounds if bounds.is_valid else None


def _ensure_camera_tracks_target(
    camera: bpy.types.Object,
    target: bpy.types.Object,
) -> bool:
    """Ensure the orbit camera aims down its local -Z axis at *target*.

    Returns True only when a temporary constraint was created and must later
    be removed by the orbit cleanup path.
    """
    ensure_managed_target_constraint(camera, target, enabled=True)
    return False


def _restore_still_camera_targeting(
    camera: bpy.types.Object | None,
    target: bpy.types.Object | None,
) -> None:
    """Restore the still-camera constraint mode after an animation rig."""
    if camera is None or target is None:
        return
    props = getattr(bpy.context.scene, PROP_SCENE_ATTR, None)
    enabled = props is None or props.camera_control_mode == "AUTO_TARGET"
    ensure_managed_target_constraint(camera, target, enabled=enabled)


def calculate_flyover_positions(
    bounds: BoundingBox,
    style: str,
    height_preset: str,
) -> tuple[Vector, Vector, Vector]:
    """Return dimension-scaled start, midpoint, and end camera positions."""
    center = bounds.center
    width = max(bounds.dimensions.x, bounds.max_dimension * 0.05)
    length = max(bounds.dimensions.y, bounds.max_dimension * 0.05)
    base_size = max(width, length)
    height_factor = {"LOW": 0.45, "MEDIUM": 0.70, "HIGH": 1.05}.get(
        height_preset, 0.70,
    )
    z = bounds.max.z + base_size * height_factor
    mid_z = bounds.max.z + base_size * height_factor * 0.88

    if style == "SIDE_SWEEP":
        x_span = max(width * 0.95, base_size * 0.75)
        y = center.y - max(length * 1.15, base_size * 0.65)
        return (
            Vector((center.x - x_span, y, z)),
            Vector((center.x, y, mid_z)),
            Vector((center.x + x_span, y, z)),
        )
    if style == "FRONT_TO_BACK":
        y_span = max(length * 0.95, base_size * 0.75)
        x = center.x + width * 0.18
        return (
            Vector((x, center.y - y_span, z)),
            Vector((center.x, center.y, mid_z)),
            Vector((x, center.y + y_span, z)),
        )

    # Diagonal Reveal is intentionally asymmetric at the midpoint so the
    # move feels less mechanical while the target remains the true PCB center.
    x_span = max(width * 0.90, base_size * 0.65)
    y_span = max(length * 0.90, base_size * 0.65)
    return (
        Vector((center.x - x_span, center.y - y_span, z)),
        Vector((center.x, center.y - length * 0.12, mid_z)),
        Vector((center.x + x_span, center.y + y_span, z)),
    )


def _remove_camera_flyover() -> bool:
    """Remove the managed flyover rig and restore its captured camera state."""
    rig = bpy.data.objects.get(CAMERA_FLYOVER_ROOT_NAME)
    if rig is None:
        return False
    camera = bpy.data.objects.get(CAMERA_NAME)
    target = bpy.data.objects.get(CAMERA_TARGET_NAME)

    if target is not None:
        target_matrix = _list_to_matrix(rig.get(_ORIGINAL_TARGET_MATRIX))
        if target_matrix is not None:
            target.matrix_world = target_matrix

    if camera is not None:
        if rig.get(_FLYOVER_TRACK_CREATED, False):
            constraint = camera.constraints.get(_FLYOVER_TRACK_CONSTRAINT)
            if constraint is not None:
                camera.constraints.remove(constraint)
        original_parent_name = rig.get(_ORIGINAL_CAMERA_PARENT, "")
        original_parent = bpy.data.objects.get(original_parent_name) if original_parent_name else None
        camera.parent = original_parent
        if original_parent is not None:
            camera.parent_type = rig.get(_ORIGINAL_CAMERA_PARENT_TYPE, "OBJECT")
            camera.parent_bone = rig.get(_ORIGINAL_CAMERA_PARENT_BONE, "")
        parent_inverse = _list_to_matrix(rig.get(_ORIGINAL_CAMERA_PARENT_INVERSE))
        if parent_inverse is not None:
            camera.matrix_parent_inverse = parent_inverse
        original_matrix = _list_to_matrix(rig.get(_ORIGINAL_CAMERA_MATRIX))
        if original_matrix is not None:
            camera.matrix_world = original_matrix
        if camera.type == "CAMERA" and _ORIGINAL_CAMERA_LENS in rig:
            camera.data.lens = float(rig[_ORIGINAL_CAMERA_LENS])
        _restore_still_camera_targeting(camera, target)

    scene = bpy.context.scene
    scene.frame_start = int(rig.get(_ORIGINAL_FRAME_START, scene.frame_start))
    scene.frame_end = int(rig.get(_ORIGINAL_FRAME_END, scene.frame_end))
    original_frame = int(rig.get(_ORIGINAL_FRAME_CURRENT, scene.frame_start))
    bpy.data.objects.remove(rig, do_unlink=True)
    scene.frame_set(original_frame)
    return True


def _setup_camera_flyover(
    bounds: BoundingBox,
    total_frames: int,
    motion_style: str,
    style: str,
    height_preset: str,
) -> str:
    camera = bpy.data.objects.get(CAMERA_NAME)
    target = bpy.data.objects.get(CAMERA_TARGET_NAME)
    setup_collection = bpy.data.collections.get(RENDER_SETUP_COLLECTION)
    if camera is None or target is None or setup_collection is None:
        return "Run Prepare Scene before setting up Cinematic Flyover."

    scene = bpy.context.scene
    original_world = camera.matrix_world.copy()
    rig = bpy.data.objects.new(CAMERA_FLYOVER_ROOT_NAME, None)
    rig.empty_display_type = "PLAIN_AXES"
    rig.empty_display_size = max(bounds.max_dimension * 0.04, 0.01)
    setup_collection.objects.link(rig)
    rig[_ORIGINAL_CAMERA_MATRIX] = _matrix_to_list(original_world)
    rig[_ORIGINAL_CAMERA_PARENT] = camera.parent.name if camera.parent else ""
    rig[_ORIGINAL_CAMERA_PARENT_INVERSE] = _matrix_to_list(camera.matrix_parent_inverse)
    rig[_ORIGINAL_CAMERA_PARENT_TYPE] = camera.parent_type
    rig[_ORIGINAL_CAMERA_PARENT_BONE] = camera.parent_bone
    rig[_ORIGINAL_CAMERA_LENS] = float(camera.data.lens)
    rig[_ORIGINAL_TARGET_MATRIX] = _matrix_to_list(target.matrix_world)
    rig[_ORIGINAL_FRAME_START] = scene.frame_start
    rig[_ORIGINAL_FRAME_END] = scene.frame_end
    rig[_ORIGINAL_FRAME_CURRENT] = scene.frame_current

    target_world = target.matrix_world.copy()
    target_world.translation = bounds.center
    target.matrix_world = target_world
    created_track = _ensure_camera_tracks_target(camera, target)
    if created_track:
        constraint = camera.constraints[-1]
        constraint.name = _FLYOVER_TRACK_CONSTRAINT
    rig[_FLYOVER_TRACK_CREATED] = created_track

    start, middle, end = calculate_flyover_positions(bounds, style, height_preset)
    camera.parent = rig
    camera.matrix_parent_inverse = Matrix.Identity(4)
    camera.location = (0.0, 0.0, 0.0)
    rig.rotation_euler = (0.0, 0.0, 0.0)
    rig.scale = (1.0, 1.0, 1.0)

    middle_frame = max(2, (total_frames + 1) // 2)
    for frame, position in ((1, start), (middle_frame, middle), (total_frames, end)):
        rig.location = position
        rig.keyframe_insert(data_path="location", frame=frame)

    action = rig.animation_data.action if rig.animation_data else None
    if action is not None:
        for fcurve in _object_action_fcurves(rig) or ():
            if fcurve.data_path != "location":
                continue
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = "LINEAR" if motion_style == "CONSTANT" else "BEZIER"
                if motion_style != "CONSTANT":
                    keyframe.handle_left_type = "AUTO_CLAMPED"
                    keyframe.handle_right_type = "AUTO_CLAMPED"

    interpolation = "linear" if motion_style == "CONSTANT" else "bezier ease"
    return f"Cinematic flyover set up: {total_frames} frames, {style}, {height_preset}, {interpolation}."


def _remove_camera_orbit() -> bool:
    """Remove the orbit pivot and restore the pre-orbit camera transform."""
    pivot = bpy.data.objects.get(CAMERA_ORBIT_ROOT_NAME)
    mount = bpy.data.objects.get(CAMERA_ORBIT_MOUNT_NAME)
    if pivot is None and mount is None:
        return False

    camera = bpy.data.objects.get(CAMERA_NAME)
    target = bpy.data.objects.get(CAMERA_TARGET_NAME)

    if target is not None and pivot is not None:
        original_target = _list_to_matrix(pivot.get(_ORIGINAL_TARGET_MATRIX))
        if original_target is not None:
            target.matrix_world = original_target

    if camera is not None:
        if pivot is not None and pivot.get(_ORBIT_TRACK_CREATED, False):
            constraint = camera.constraints.get(_ORBIT_TRACK_CONSTRAINT)
            if constraint is not None:
                camera.constraints.remove(constraint)

        current_world = camera.matrix_world.copy()
        original_world = (
            _list_to_matrix(pivot.get(_ORIGINAL_CAMERA_MATRIX))
            if pivot is not None
            else None
        )
        original_parent_name = (
            pivot.get(_ORIGINAL_CAMERA_PARENT, "") if pivot is not None else ""
        )
        original_parent = (
            bpy.data.objects.get(original_parent_name)
            if original_parent_name
            else None
        )

        if camera.parent in {pivot, mount}:
            camera.parent = original_parent
            if original_parent is not None and pivot is not None:
                camera.parent_type = pivot.get(
                    _ORIGINAL_CAMERA_PARENT_TYPE,
                    "OBJECT",
                )
                camera.parent_bone = pivot.get(_ORIGINAL_CAMERA_PARENT_BONE, "")

            if pivot is not None:
                original_parent_inverse = _list_to_matrix(
                    pivot.get(_ORIGINAL_CAMERA_PARENT_INVERSE),
                )
                if original_parent_inverse is not None:
                    camera.matrix_parent_inverse = original_parent_inverse

            camera.matrix_world = (
                original_world if original_world is not None else current_world
            )
        _restore_still_camera_targeting(camera, target)

    if mount is not None:
        bpy.data.objects.remove(mount, do_unlink=True)
    if pivot is not None:
        _clear_z_rotation_keyframes(pivot)
        bpy.data.objects.remove(pivot, do_unlink=True)
    return True


def _keyframe_z_rotation(
    obj: bpy.types.Object,
    total_frames: int,
    rotation_degrees: float,
    direction: str,
    start_angle_degrees: float,
    motion_style: str,
) -> str:
    """Create a managed Z rotation with a non-rendered loop endpoint."""
    sign = -1.0 if direction == "CLOCKWISE" else 1.0
    total_radians = radians(rotation_degrees) * sign
    start_radians = radians(start_angle_degrees % 360.0)

    _clear_z_rotation_keyframes(obj)
    obj.rotation_mode = "XYZ"
    obj.rotation_euler.z = start_radians
    obj.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
    obj.rotation_euler.z = start_radians + total_radians
    obj.keyframe_insert(
        data_path="rotation_euler",
        index=2,
        frame=total_frames + 1,
    )

    if obj.animation_data and obj.animation_data.action:
        fcurves = _object_action_fcurves(obj)
        fcurve = fcurves.find(
            "rotation_euler",
            index=2,
        ) if fcurves is not None else None
        if fcurve is not None:
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = (
                    "LINEAR" if motion_style == "CONSTANT" else "BEZIER"
                )

    return "linear" if motion_style == "CONSTANT" else "bezier ease"


def get_turntable_frame_count(duration: float, fps: int) -> int:
    """Calculate the rendered frame count for either animation type."""
    return max(1, int(round(duration * fps)))


def has_managed_animation(animation_type: str) -> bool:
    """Return whether the selected managed animation has a Z-rotation curve."""
    if animation_type == "CINEMATIC_FLYOVER":
        obj = bpy.data.objects.get(CAMERA_FLYOVER_ROOT_NAME)
        if obj is None or obj.animation_data is None or obj.animation_data.action is None:
            return False
        return any(curve.data_path == "location" for curve in (_object_action_fcurves(obj) or ()))
    object_name = CAMERA_ORBIT_ROOT_NAME if animation_type == "CAMERA_ORBIT" else ROOT_EMPTY_NAME
    obj = bpy.data.objects.get(object_name)
    if obj is None or obj.animation_data is None:
        return False
    fcurves = _object_action_fcurves(obj)
    return fcurves is not None and fcurves.find("rotation_euler", index=2) is not None


def setup_animation(
    animation_type: str,
    duration: float,
    fps: int,
    rotation_degrees: float,
    direction: str,
    start_angle_degrees: float,
    motion_style: str,
    flyover_style: str = "DIAGONAL_REVEAL",
    flyover_height: str = "MEDIUM",
) -> str:
    """Create either PCB-turntable or camera-orbit keyframes.

    Both modes rotate around the PCB centre on the Z axis. The endpoint is
    placed one frame beyond the render range so a 360-degree animation loops
    without rendering a duplicate frame.
    """
    if _product_presentation_active():
        return "Clear product animation/previews and Reset Orientation before using legacy camera/PCB animation tools."
    total_frames = get_turntable_frame_count(duration, fps)

    if animation_type == "CINEMATIC_FLYOVER":
        root = _get_root()
        if root is None:
            return "PCB_MODEL_ROOT not found. Run Prepare Scene first."
        _clear_z_rotation_keyframes(root)
        root.rotation_euler.z = 0.0
        _remove_camera_orbit()
        _remove_camera_flyover()
        bpy.context.view_layer.update()
        bounds = _get_pcb_bounds()
        if bounds is None:
            return "Cannot set up Cinematic Flyover: PCB bounds could not be calculated."
        mode_result = _setup_camera_flyover(
            bounds, total_frames, motion_style, flyover_style, flyover_height,
        )
        if not mode_result.startswith("Cinematic flyover set up"):
            return mode_result
        mode_message = mode_result
    elif animation_type == "CAMERA_ORBIT":
        root = _get_root()
        if root is None:
            return "PCB_MODEL_ROOT not found. Run Prepare Scene first."

        # Only one PCB Studio animation may be active. Restore any previous
        # orbit before capturing the camera's starting composition.
        _clear_z_rotation_keyframes(root)
        root.rotation_euler.z = 0.0
        _remove_camera_flyover()
        _remove_camera_orbit()
        bpy.context.view_layer.update()

        camera = bpy.data.objects.get(CAMERA_NAME)
        target = bpy.data.objects.get(CAMERA_TARGET_NAME)
        setup_collection = bpy.data.collections.get(RENDER_SETUP_COLLECTION)
        if camera is None or target is None or setup_collection is None:
            return "Run Prepare Scene before setting up Camera Orbit."

        bounds = _get_pcb_bounds()
        if bounds is None:
            return "Cannot set up Camera Orbit: PCB center could not be calculated."

        original_world = camera.matrix_world.copy()
        original_position = original_world.translation.copy()
        orbit_offset = original_position - bounds.center
        horizontal_radius = orbit_offset.xy.length
        minimum_radius = max(bounds.max_dimension * 0.001, 1e-5)
        if horizontal_radius <= minimum_radius:
            return (
                "Camera is directly above the PCB center. Apply Isometric or "
                "45 Degree before setting up Camera Orbit."
            )

        pivot = bpy.data.objects.new(CAMERA_ORBIT_ROOT_NAME, None)
        pivot.empty_display_type = "PLAIN_AXES"
        pivot.location = bounds.center
        pivot.rotation_mode = "XYZ"
        pivot.rotation_euler = (0.0, 0.0, 0.0)
        pivot.scale = (1.0, 1.0, 1.0)
        setup_collection.objects.link(pivot)

        # Keep enough state on the managed pivot to survive save/reload and
        # restore the user's exact pre-orbit camera composition.
        pivot[_ORIGINAL_CAMERA_MATRIX] = _matrix_to_list(original_world)
        pivot[_ORIGINAL_CAMERA_PARENT] = (
            camera.parent.name if camera.parent is not None else ""
        )
        pivot[_ORIGINAL_CAMERA_PARENT_INVERSE] = _matrix_to_list(
            camera.matrix_parent_inverse,
        )
        pivot[_ORIGINAL_CAMERA_PARENT_TYPE] = camera.parent_type
        pivot[_ORIGINAL_CAMERA_PARENT_BONE] = camera.parent_bone
        pivot[_ORIGINAL_TARGET_MATRIX] = _matrix_to_list(target.matrix_world)

        # The mount's local offset is the current camera vector relative to
        # the true PCB center. Rotating the unit-scale pivot therefore changes
        # camera XYZ along a mathematically circular path at constant height.
        mount = bpy.data.objects.new(CAMERA_ORBIT_MOUNT_NAME, None)
        mount.empty_display_type = "CUBE"
        mount.empty_display_size = max(bounds.max_dimension * 0.03, 0.01)
        setup_collection.objects.link(mount)
        mount.parent = pivot
        mount.matrix_parent_inverse = Matrix.Identity(4)
        mount.location = orbit_offset
        mount.rotation_euler = (0.0, 0.0, 0.0)
        mount.scale = (1.0, 1.0, 1.0)

        camera.parent = mount
        camera.matrix_parent_inverse = Matrix.Identity(4)
        camera.location = (0.0, 0.0, 0.0)

        # Camera position comes from the orbit mount; its existing Damped
        # Track keeps local -Z aimed at the stationary PCB target.
        target_world = target.matrix_world.copy()
        target_world.translation = bounds.center
        target.matrix_world = target_world
        pivot[_ORBIT_TRACK_CREATED] = _ensure_camera_tracks_target(camera, target)

        interpolation = _keyframe_z_rotation(
            pivot,
            total_frames,
            rotation_degrees,
            direction,
            start_angle_degrees,
            motion_style,
        )
        mode_message = "Camera orbit"
    else:
        root = _get_root()
        if root is None:
            return "PCB_MODEL_ROOT not found. Run Prepare Scene first."

        _remove_camera_flyover()
        _remove_camera_orbit()
        interpolation = _keyframe_z_rotation(
            root,
            total_frames,
            rotation_degrees,
            direction,
            start_angle_degrees,
            motion_style,
        )
        mode_message = "PCB turntable"

    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = total_frames
    scene.frame_set(1)
    scene.render.fps = fps

    if animation_type == "CINEMATIC_FLYOVER":
        return mode_message
    return (
        f"{mode_message} set up: {total_frames} frames, "
        f"{rotation_degrees} degrees, {interpolation}."
    )


def setup_turntable(
    duration: float,
    fps: int,
    rotation_degrees: float,
    direction: str,
    start_angle_degrees: float,
    motion_style: str,
) -> str:
    """Compatibility wrapper for the original PCB-turntable API."""
    return setup_animation(
        animation_type="PCB_TURNTABLE",
        duration=duration,
        fps=fps,
        rotation_degrees=rotation_degrees,
        direction=direction,
        start_angle_degrees=start_angle_degrees,
        motion_style=motion_style,
    )


def reset_animation() -> str:
    """Remove managed animation and restore the PCB and camera transforms."""
    if _product_presentation_active():
        return "Reset Product Orientation first; product presentation was preserved."
    root = _get_root()
    reset_pcb = False
    if root is not None:
        _clear_z_rotation_keyframes(root)
        root.rotation_euler.z = 0.0
        reset_pcb = True

    reset_camera = _remove_camera_orbit()
    reset_flyover = _remove_camera_flyover()
    reset_camera = reset_flyover or reset_camera

    scene = bpy.context.scene
    if not reset_flyover:
        scene.frame_start = 1
        scene.frame_end = 250
        scene.frame_set(1)

    if not reset_pcb and not reset_camera:
        return "No managed animation found."
    return "Animation reset. PCB and camera restored."


def reset_turntable() -> str:
    """Compatibility wrapper for the original reset API."""
    return reset_animation()


def _product_presentation_active() -> bool:
    """Do not let legacy cleanup delete actions owned by product presentation."""
    scene = bpy.context.scene
    if any("pcbstudio_product_snapshot" in obj for obj in scene.objects):
        return True
    props = getattr(scene, "pcb_studio_product", None)
    return props is not None and any(abs(v) > 1e-8 for v in props.orientation)
