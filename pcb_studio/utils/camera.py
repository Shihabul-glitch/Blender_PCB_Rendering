"""Camera creation, framing, and managed-target utilities."""

from __future__ import annotations

from math import atan, radians, tan

import bpy
from mathutils import Vector

from ..constants import (
    CAMERA_NAME,
    CAMERA_TARGET_CONSTRAINT_NAME,
    CAMERA_TARGET_NAME,
    PROP_SCENE_ATTR,
    RENDER_SETUP_COLLECTION,
)
from .geometry import BoundingBox, board_direction


def get_or_create_render_setup_collection() -> bpy.types.Collection:
    """Return the PCB_RENDER_SETUP collection, creating it if necessary."""
    coll = bpy.data.collections.get(RENDER_SETUP_COLLECTION)
    if coll is None:
        coll = bpy.data.collections.new(RENDER_SETUP_COLLECTION)
        bpy.context.scene.collection.children.link(coll)
    return coll


def get_or_create_camera_target() -> bpy.types.Object:
    """Return PCB Studio's camera target without affecting other empties."""
    target = bpy.data.objects.get(CAMERA_TARGET_NAME)
    if target is None:
        target = bpy.data.objects.new(CAMERA_TARGET_NAME, None)
        target.empty_display_type = "PLAIN_AXES"
        get_or_create_render_setup_collection().objects.link(target)
    return target


def get_managed_target_constraint(
    camera: bpy.types.Object,
) -> bpy.types.Constraint | None:
    """Return only the targeting constraint owned by PCB Studio.

    Older PCB Studio scenes used Blender's default constraint name. A legacy
    constraint is adopted only when it already targets PCB_CAMERA_TARGET;
    unrelated user constraints are never removed or modified.
    """
    for constraint in camera.constraints:
        if (
            constraint.type == "DAMPED_TRACK"
            and (
                constraint.name == CAMERA_TARGET_CONSTRAINT_NAME
                or constraint.name.startswith(f"{CAMERA_TARGET_CONSTRAINT_NAME}.")
            )
        ):
            return constraint
    target = bpy.data.objects.get(CAMERA_TARGET_NAME)
    if target is not None:
        for constraint in camera.constraints:
            if (
                constraint.type == "DAMPED_TRACK"
                and constraint.target == target
                and constraint.name.startswith("Damped Track")
            ):
                constraint.name = CAMERA_TARGET_CONSTRAINT_NAME
                return constraint
    return None


def ensure_managed_target_constraint(
    camera: bpy.types.Object,
    target: bpy.types.Object | None = None,
    *,
    enabled: bool = True,
) -> bpy.types.Constraint:
    """Create/update PCB Studio's one managed camera-target constraint."""
    target = target or get_or_create_camera_target()
    track = get_managed_target_constraint(camera)
    if track is None:
        track = camera.constraints.new(type="DAMPED_TRACK")
        track.name = CAMERA_TARGET_CONSTRAINT_NAME
    track.target = target
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.mute = not enabled
    track.influence = 1.0
    return track


def set_managed_targeting(camera: bpy.types.Object, enabled: bool) -> None:
    """Enable or mute only PCB Studio's targeting constraint."""
    ensure_managed_target_constraint(camera, enabled=enabled)


def _compute_camera_distance(
    dimensions: Vector,
    sensor_width: float,
    sensor_height: float,
    focal_length: float,
    margin: float = 1.15,
) -> float:
    """Return the distance required to fit *dimensions* in the camera frame.

    Args:
        dimensions: Bounding box dimensions (width, depth, height).
        sensor_width: Camera sensor width in mm.
        sensor_height: Camera sensor height in mm.
        focal_length: Focal length in mm.
        margin: Framing margin multiplier (1.15 = 15%).
    """
    hfov = 2.0 * atan(sensor_width / (2.0 * focal_length))
    vfov = 2.0 * atan(sensor_height / (2.0 * focal_length))

    dist_h = (dimensions.x * margin / 2.0) / tan(hfov / 2.0) if tan(hfov / 2.0) else 1e6
    dist_v = (dimensions.y * margin / 2.0) / tan(vfov / 2.0) if tan(vfov / 2.0) else 1e6

    return max(dist_h, dist_v)


def setup_camera(bounds: BoundingBox) -> str:
    """Create/update the managed camera in the default Top view of the board face."""
    scene = bpy.context.scene
    setup_coll = get_or_create_render_setup_collection()

    # --- Camera target ---
    target = get_or_create_camera_target()
    target.location = bounds.center

    # --- Camera ---
    camera_obj = bpy.data.objects.get(CAMERA_NAME)
    if camera_obj is None:
        cam_data = bpy.data.cameras.new(CAMERA_NAME)
        cam_data.type = "PERSP"
        camera_obj = bpy.data.objects.new(CAMERA_NAME, cam_data)
        setup_coll.objects.link(camera_obj)

    cam_data = camera_obj.data
    cam_data.lens = 75.0
    distance = _compute_camera_distance(
        bounds.dimensions,
        cam_data.sensor_width,
        cam_data.sensor_height,
        cam_data.lens,
        1.10,
    )
    # The board does not always lie flat in XY, so start on its face normal
    # rather than hardcoding "straight above".
    camera_obj.location = bounds.center + board_direction(bounds, Vector((0.0, 0.0, 1.0))) * distance
    ensure_managed_target_constraint(camera_obj, target, enabled=True)
    scene.camera = camera_obj
    bpy.context.view_layer.update()
    props = getattr(scene, PROP_SCENE_ATTR, None)
    if props is not None:
        scene["pcbstudio_camera_batch_update"] = True
        try:
            props.camera_preset = "TOP"
            props.camera_focal_length = 75.0
            props.camera_control_mode = "AUTO_TARGET"
            props.camera_azimuth = 0.0
            props.camera_elevation = radians(90.0)
            props.camera_distance = max(0.0001, distance)
            props.camera_roll = 0.0
            props.camera_target_offset_x = 0.0
            props.camera_target_offset_y = 0.0
            props.camera_target_offset_z = 0.0
        finally:
            scene["pcbstudio_camera_batch_update"] = False
    return f"Top camera framed at distance {distance:.1f} units."
