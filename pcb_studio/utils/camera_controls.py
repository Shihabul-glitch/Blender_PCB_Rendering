"""Non-animated product-camera controls for PCB Studio."""

from __future__ import annotations

from math import asin, atan2, cos, pi, sin

import bpy
from mathutils import Matrix, Quaternion, Vector

from ..constants import (
    CAMERA_FLYOVER_ROOT_NAME,
    CAMERA_NAME,
    CAMERA_ORBIT_ROOT_NAME,
    CAMERA_TARGET_NAME,
    PROP_SCENE_ATTR,
)
from .camera import (
    ensure_managed_target_constraint,
    get_managed_target_constraint,
    get_or_create_camera_target,
)
from .composition import (
    _compute_object_world_bounds,
    _get_pcb_bounds,
    get_single_selected_pcb_mesh,
)
from .geometry import (
    BoundingBox,
    board_direction,
    camera_field_of_view,
    required_camera_distance,
)


_STEP_FACTORS = {"FINE": 0.015, "NORMAL": 0.05, "COARSE": 0.12}
_BATCH_KEY = "pcbstudio_camera_batch_update"


def camera_animation_block_reason() -> str:
    """Return a clear reason when an animation rig owns the camera."""
    active = []
    if bpy.data.objects.get(CAMERA_ORBIT_ROOT_NAME) is not None:
        active.append("Camera Orbit")
    if bpy.data.objects.get(CAMERA_FLYOVER_ROOT_NAME) is not None:
        active.append("Cinematic Flyover")
    if not active:
        return ""
    return (
        f"Still-camera controls are locked while {' / '.join(active)} animation is active. "
        "Use Reset Animation first."
    )


def _props(scene: bpy.types.Scene):
    return getattr(scene, PROP_SCENE_ATTR, None)


def _camera_and_target() -> tuple[bpy.types.Object | None, bpy.types.Object | None, str]:
    camera = bpy.data.objects.get(CAMERA_NAME)
    if camera is None or camera.type != "CAMERA":
        return None, None, "Managed camera not found. Run Prepare Scene first."
    target = get_or_create_camera_target()
    return camera, target, ""


def _world_location(obj: bpy.types.Object) -> Vector:
    return obj.matrix_world.translation.copy()


def _set_world_location(obj: bpy.types.Object, location: Vector) -> None:
    matrix = obj.matrix_world.copy()
    matrix.translation = location
    obj.matrix_world = matrix


def _set_property_values(scene: bpy.types.Scene, **values) -> None:
    props = _props(scene)
    if props is None:
        return
    scene[_BATCH_KEY] = True
    try:
        for name, value in values.items():
            setattr(props, name, value)
    finally:
        scene[_BATCH_KEY] = False


def _look_at(
    camera: bpy.types.Object,
    target_location: Vector,
    roll: float = 0.0,
) -> None:
    location = _world_location(camera)
    direction = target_location - location
    if direction.length < 1e-9:
        return
    rotation = direction.normalized().to_track_quat("-Z", "Y")
    if abs(roll) > 1e-9:
        rotation = rotation @ Quaternion((0.0, 0.0, 1.0), roll)
    camera.matrix_world = Matrix.LocRotScale(
        location,
        rotation,
        camera.matrix_world.to_scale(),
    )


def _set_targeting_for_mode(
    scene: bpy.types.Scene,
    camera: bpy.types.Object,
    target: bpy.types.Object,
) -> None:
    props = _props(scene)
    enabled = props is None or props.camera_control_mode == "AUTO_TARGET"
    ensure_managed_target_constraint(camera, target, enabled=enabled)


def sync_camera_properties(scene: bpy.types.Scene) -> None:
    """Synchronize product-position and target-offset UI values from the scene."""
    props = _props(scene)
    camera = bpy.data.objects.get(CAMERA_NAME)
    target = bpy.data.objects.get(CAMERA_TARGET_NAME)
    if props is None or camera is None or target is None:
        return
    offset = _world_location(camera) - _world_location(target)
    distance = max(offset.length, 0.0001)
    elevation = asin(max(-1.0, min(1.0, offset.z / distance)))
    azimuth = atan2(offset.x, -offset.y)
    bounds = _get_pcb_bounds()
    target_offset = (
        _world_location(target) - bounds.center
        if bounds is not None
        else _world_location(target)
    )
    _set_property_values(
        scene,
        camera_azimuth=azimuth,
        camera_elevation=elevation,
        camera_distance=distance,
        camera_focal_length=float(camera.data.lens),
        camera_target_offset_x=target_offset.x,
        camera_target_offset_y=target_offset.y,
        camera_target_offset_z=target_offset.z,
    )


def set_camera_control_mode(scene: bpy.types.Scene, mode: str) -> str:
    """Switch between target-constrained and free manual camera rotation."""
    camera, target, error = _camera_and_target()
    if error:
        return error
    blocked = camera_animation_block_reason()
    if blocked:
        current = get_managed_target_constraint(camera)
        actual_mode = "MANUAL" if current is not None and current.mute else "AUTO_TARGET"
        _set_property_values(scene, camera_control_mode=actual_mode)
        return blocked
    props = _props(scene)
    roll = props.camera_roll if props is not None else 0.0
    _look_at(camera, _world_location(target), roll)
    ensure_managed_target_constraint(camera, target, enabled=mode == "AUTO_TARGET")
    return "Auto Target enabled." if mode == "AUTO_TARGET" else "Manual camera rotation unlocked."


def apply_product_parameters(scene: bpy.types.Scene) -> str:
    """Apply live azimuth, elevation, distance, and roll values."""
    blocked = camera_animation_block_reason()
    if blocked:
        return blocked
    camera, target, error = _camera_and_target()
    props = _props(scene)
    if error or props is None:
        return error or "Extension state not available."
    distance = max(0.0001, props.camera_distance)
    elevation = max(-pi / 2.0, min(pi / 2.0, props.camera_elevation))
    azimuth = props.camera_azimuth
    horizontal = distance * cos(elevation)
    offset = Vector((
        horizontal * sin(azimuth),
        -horizontal * cos(azimuth),
        distance * sin(elevation),
    ))
    _set_world_location(camera, _world_location(target) + offset)
    _look_at(camera, _world_location(target), props.camera_roll)
    _set_targeting_for_mode(scene, camera, target)
    scene.camera = camera
    return "Camera product view updated."


def apply_target_offsets(scene: bpy.types.Scene) -> str:
    """Apply live target offsets relative to the PCB center."""
    blocked = camera_animation_block_reason()
    if blocked:
        return blocked
    camera, target, error = _camera_and_target()
    props = _props(scene)
    bounds = _get_pcb_bounds()
    if error or props is None:
        return error or "Extension state not available."
    if bounds is None:
        return "No PCB geometry found."
    location = bounds.center + Vector((
        props.camera_target_offset_x,
        props.camera_target_offset_y,
        props.camera_target_offset_z,
    ))
    _set_world_location(target, location)
    _look_at(camera, location, props.camera_roll)
    _set_targeting_for_mode(scene, camera, target)
    return "Camera target offsets updated."


def _movement_step(scene: bpy.types.Scene) -> float:
    bounds = _get_pcb_bounds()
    base = bounds.max_dimension if bounds is not None else 1.0
    props = _props(scene)
    mode = props.camera_move_step_mode if props is not None else "NORMAL"
    return max(base * _STEP_FACTORS.get(mode, 0.05), 0.0001)


def _camera_axes(camera: bpy.types.Object) -> tuple[Vector, Vector, Vector]:
    bpy.context.view_layer.update()
    rotation = camera.matrix_world.to_quaternion()
    right = (rotation @ Vector((1.0, 0.0, 0.0))).normalized()
    up = (rotation @ Vector((0.0, 1.0, 0.0))).normalized()
    forward = (rotation @ Vector((0.0, 0.0, -1.0))).normalized()
    return right, up, forward


def orbit_camera(scene: bpy.types.Scene, horizontal: float, vertical: float) -> str:
    """Orbit the still camera around its target without changing distance."""
    camera, target, error = _camera_and_target()
    props = _props(scene)
    if error or props is None:
        return error or "Extension state not available."
    sync_camera_properties(scene)
    azimuth = props.camera_azimuth + horizontal
    elevation = max(-pi / 2.0, min(pi / 2.0, props.camera_elevation + vertical))
    if azimuth > pi:
        azimuth -= 2.0 * pi
    elif azimuth < -pi:
        azimuth += 2.0 * pi
    _set_property_values(scene, camera_azimuth=azimuth, camera_elevation=elevation)
    return apply_product_parameters(scene)


def nudge_camera(scene: bpy.types.Scene, action: str) -> str:
    """Apply one scale-aware still-camera movement, pan, orbit, or roll step."""
    blocked = camera_animation_block_reason()
    if blocked:
        return blocked
    camera, target, error = _camera_and_target()
    props = _props(scene)
    if error or props is None:
        return error or "Extension state not available."
    step = _movement_step(scene)
    angle = props.camera_orbit_step
    right, up, forward = _camera_axes(camera)
    translations = {
        "LEFT": -right,
        "RIGHT": right,
        "UP": up,
        "DOWN": -up,
        "FORWARD": forward,
        "BACK": -forward,
        "DOLLY_IN": forward,
        "DOLLY_OUT": -forward,
    }
    pans = {
        "PAN_LEFT": -right,
        "PAN_RIGHT": right,
        "PAN_UP": up,
        "PAN_DOWN": -up,
    }
    if action in translations:
        _set_world_location(camera, _world_location(camera) + translations[action] * step)
        sync_camera_properties(scene)
        return f"Camera moved {action.replace('_', ' ').title()}."
    if action in pans:
        delta = pans[action] * step
        _set_world_location(camera, _world_location(camera) + delta)
        _set_world_location(target, _world_location(target) + delta)
        sync_camera_properties(scene)
        return f"Camera panned {action[4:].replace('_', ' ').title()}."
    if action == "ORBIT_LEFT":
        return orbit_camera(scene, -angle, 0.0)
    if action == "ORBIT_RIGHT":
        return orbit_camera(scene, angle, 0.0)
    if action == "ORBIT_UP":
        return orbit_camera(scene, 0.0, angle)
    if action == "ORBIT_DOWN":
        return orbit_camera(scene, 0.0, -angle)
    if action in {"ROLL_LEFT", "ROLL_RIGHT", "ROLL_RESET"}:
        roll = 0.0 if action == "ROLL_RESET" else props.camera_roll
        if action == "ROLL_LEFT":
            roll -= angle
        elif action == "ROLL_RIGHT":
            roll += angle
        roll = (roll + pi) % (2.0 * pi) - pi
        _set_property_values(scene, camera_roll=roll)
        _look_at(camera, _world_location(target), roll)
        _set_targeting_for_mode(scene, camera, target)
        return "Camera roll reset." if action == "ROLL_RESET" else "Camera roll adjusted."
    return f"Unknown camera movement: {action}"


def aim_camera_at_bounds(scene: bpy.types.Scene, bounds: BoundingBox, label: str) -> str:
    camera, target, error = _camera_and_target()
    props = _props(scene)
    if error:
        return error
    _set_world_location(target, bounds.center)
    _look_at(camera, bounds.center, props.camera_roll if props is not None else 0.0)
    _set_targeting_for_mode(scene, camera, target)
    sync_camera_properties(scene)
    return f"Camera aimed at {label}."


def aim_camera_at_pcb(scene: bpy.types.Scene) -> str:
    blocked = camera_animation_block_reason()
    if blocked:
        return blocked
    bounds = _get_pcb_bounds()
    return aim_camera_at_bounds(scene, bounds, "PCB center") if bounds else "No PCB geometry found."


def aim_camera_at_selected(scene: bpy.types.Scene, context: bpy.types.Context) -> str:
    blocked = camera_animation_block_reason()
    if blocked:
        return blocked
    selected, error = get_single_selected_pcb_mesh(context)
    if selected is None:
        return error
    bounds = _compute_object_world_bounds(selected)
    return aim_camera_at_bounds(scene, bounds, f"selected component '{selected.name}'") if bounds else "Selected object has invalid bounds."


def fit_camera_to_bounds(scene: bpy.types.Scene, bounds: BoundingBox, label: str) -> str:
    """Frame bounds while retaining the current target-to-camera direction."""
    camera, target, error = _camera_and_target()
    props = _props(scene)
    if error:
        return error
    camera_location = _world_location(camera)
    old_target = _world_location(target)
    back = camera_location - old_target
    if back.length < 1e-9:
        back = Vector((0.0, 0.0, 1.0))
    back.normalize()
    _set_world_location(target, bounds.center)
    _set_world_location(camera, bounds.center + back * max((camera_location - old_target).length, 1.0))
    roll = props.camera_roll if props is not None else 0.0
    _look_at(camera, bounds.center, roll)
    right, up, _forward = _camera_axes(camera)
    margin = 1.0 + (props.camera_fit_margin if props is not None else 0.10)
    angle_x, angle_y = camera_field_of_view(camera.data, scene)
    required = required_camera_distance(bounds, back, right, up, angle_x, angle_y, margin)
    _set_world_location(camera, bounds.center + back * required)
    _look_at(camera, bounds.center, roll)
    _set_targeting_for_mode(scene, camera, target)
    sync_camera_properties(scene)
    return f"Fit {label} in camera (distance {required:.1f})."


def fit_camera_to_pcb(scene: bpy.types.Scene) -> str:
    blocked = camera_animation_block_reason()
    if blocked:
        return blocked
    bounds = _get_pcb_bounds()
    return fit_camera_to_bounds(scene, bounds, "PCB") if bounds else "No PCB geometry found."


def fit_camera_to_selected(scene: bpy.types.Scene, context: bpy.types.Context) -> str:
    blocked = camera_animation_block_reason()
    if blocked:
        return blocked
    selected, error = get_single_selected_pcb_mesh(context)
    if selected is None:
        return error
    bounds = _compute_object_world_bounds(selected)
    return fit_camera_to_bounds(scene, bounds, f"selected component '{selected.name}'") if bounds else "Selected object has invalid bounds."


def save_camera_view(scene: bpy.types.Scene) -> str:
    blocked = camera_animation_block_reason()
    if blocked:
        return blocked
    camera, target, error = _camera_and_target()
    props = _props(scene)
    if error or props is None:
        return error or "Extension state not available."
    matrix = camera.matrix_world.copy()
    props.camera_saved_view = tuple(matrix[row][col] for row in range(4) for col in range(4))
    props.camera_saved_target = tuple(_world_location(target))
    props.camera_saved_lens = float(camera.data.lens)
    props.camera_saved_mode = props.camera_control_mode
    props.camera_has_saved_view = True
    return "Camera view saved."


def restore_camera_view(scene: bpy.types.Scene) -> str:
    blocked = camera_animation_block_reason()
    if blocked:
        return blocked
    camera, target, error = _camera_and_target()
    props = _props(scene)
    if error or props is None:
        return error or "Extension state not available."
    if not props.camera_has_saved_view:
        return "No saved camera view is available."
    values = list(props.camera_saved_view)
    camera.matrix_world = Matrix((values[0:4], values[4:8], values[8:12], values[12:16]))
    _set_world_location(target, Vector(props.camera_saved_target))
    camera.data.lens = props.camera_saved_lens
    mode = props.camera_saved_mode if props.camera_saved_mode in {"AUTO_TARGET", "MANUAL"} else "AUTO_TARGET"
    _set_property_values(scene, camera_control_mode=mode)
    ensure_managed_target_constraint(camera, target, enabled=mode == "AUTO_TARGET")
    sync_camera_properties(scene)
    return "Camera view restored."


def reset_camera(scene: bpy.types.Scene) -> str:
    """Restore the 75 mm Top view of the board face and fit the complete PCB."""
    blocked = camera_animation_block_reason()
    if blocked:
        return blocked
    camera, target, error = _camera_and_target()
    bounds = _get_pcb_bounds()
    if error:
        return error
    if bounds is None:
        return "No PCB geometry found."
    _set_property_values(
        scene,
        camera_preset="TOP",
        camera_control_mode="AUTO_TARGET",
        camera_focal_length=75.0,
        camera_azimuth=0.0,
        camera_elevation=pi / 2.0,
        camera_roll=0.0,
        camera_target_offset_x=0.0,
        camera_target_offset_y=0.0,
        camera_target_offset_z=0.0,
    )
    camera.data.lens = 75.0
    _set_world_location(target, bounds.center)
    face = board_direction(bounds, Vector((0.0, 0.0, 1.0)), scene)
    _set_world_location(camera, bounds.center + face * max(bounds.max_dimension, 1.0))
    _look_at(camera, bounds.center, 0.0)
    ensure_managed_target_constraint(camera, target, enabled=True)
    fit_camera_to_bounds(scene, bounds, "PCB")
    return "Camera reset to Top (75 mm) and fit to PCB."
