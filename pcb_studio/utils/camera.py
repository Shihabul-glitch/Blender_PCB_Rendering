"""Camera creation, framing, and look-at utilities."""

from __future__ import annotations

from math import atan, tan

import bpy
from mathutils import Vector

from ..constants import (
    CAMERA_NAME,
    CAMERA_TARGET_NAME,
    RENDER_SETUP_COLLECTION,
)
from .geometry import BoundingBox


def get_or_create_render_setup_collection() -> bpy.types.Collection:
    """Return the PCB_RENDER_SETUP collection, creating it if necessary."""
    coll = bpy.data.collections.get(RENDER_SETUP_COLLECTION)
    if coll is None:
        coll = bpy.data.collections.new(RENDER_SETUP_COLLECTION)
        bpy.context.scene.collection.children.link(coll)
    return coll


def _remove_track_constraints(camera: bpy.types.Object) -> None:
    """Remove all Damped Track constraints from the camera."""
    for constraint in camera.constraints:
        if constraint.type == "DAMPED_TRACK":
            camera.constraints.remove(constraint)


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
    """Create or update the PCB render camera and target.

    Positions the camera in a three-quarter product-view direction,
    frames the complete PCB with a margin, and aims at a target
    Empty at the PCB center using a Damped Track constraint.

    Args:
        bounds: The combined PCB bounding box.

    Returns:
        A status message describing the result.
    """
    scene = bpy.context.scene
    setup_coll = get_or_create_render_setup_collection()

    # --- Camera target ---
    target = bpy.data.objects.get(CAMERA_TARGET_NAME)
    if target is None:
        target = bpy.data.objects.new(CAMERA_TARGET_NAME, None)
        target.empty_display_type = "PLAIN_AXES"
        setup_coll.objects.link(target)
    target.location = bounds.center

    # --- Camera ---
    camera_obj = bpy.data.objects.get(CAMERA_NAME)
    if camera_obj is None:
        cam_data = bpy.data.cameras.new(CAMERA_NAME)
        cam_data.type = "PERSP"
        cam_data.lens = 50.0  # mm
        camera_obj = bpy.data.objects.new(CAMERA_NAME, cam_data)
        setup_coll.objects.link(camera_obj)

    cam_data = camera_obj.data
    cam_data.lens = 50.0

    # Sensor dimensions (Blender defaults).
    sensor_width = cam_data.sensor_width
    sensor_height = cam_data.sensor_height

    # Three-quarter view direction.
    direction = Vector((1.0, -1.0, 1.0)).normalized()

    # Compute distance and position.
    distance = _compute_camera_distance(
        bounds.dimensions, sensor_width, sensor_height, cam_data.lens,
    )
    camera_obj.location = bounds.center + direction * distance

    # --- Damped Track constraint ---
    _remove_track_constraints(camera_obj)
    track = camera_obj.constraints.new(type="DAMPED_TRACK")
    track.target = target
    track.track_axis = "TRACK_NEGATIVE_Z"

    # Set as active camera.
    scene.camera = camera_obj

    return f"Camera framed at distance {distance:.1f} units."