"""Three-point lighting rig utilities."""

from __future__ import annotations

import bpy
from mathutils import Vector

from ..constants import (
    FILL_LIGHT_NAME,
    KEY_LIGHT_NAME,
    RIM_LIGHT_NAME,
    RENDER_SETUP_COLLECTION,
)
from .geometry import BoundingBox


def _get_or_create_area_light(
    name: str,
    collection: bpy.types.Collection,
) -> bpy.types.Object:
    """Return an existing Area light by name, or create a new one."""
    obj = bpy.data.objects.get(name)
    if obj is None:
        light_data = bpy.data.lights.new(name, "AREA")
        obj = bpy.data.objects.new(name, light_data)
        collection.objects.link(obj)
    # Ensure the data is still an Area light.
    if obj.data.type != "AREA":
        new_data = bpy.data.lights.new(name, "AREA")
        obj.data = new_data
    return obj


def _aim_light_at(
    light: bpy.types.Object,
    target: Vector,
    track_axis: str = "TRACK_NEGATIVE_Z",
) -> None:
    """Point a light toward *target* using a Damped Track constraint."""
    # Remove existing track constraints.
    for c in light.constraints:
        if c.type == "DAMPED_TRACK":
            light.constraints.remove(c)

    # Use a temporary empty as track target.
    track_target = bpy.data.objects.new(
        f"{light.name}_track_target", None,
    )
    track_target.location = target
    # Link to the same collection as the light (won't show in renders).
    for coll in light.users_collection:
        coll.objects.link(track_target)
        break

    track = light.constraints.new(type="DAMPED_TRACK")
    track.target = track_target
    track.track_axis = track_axis


def setup_lights(bounds: BoundingBox) -> str:
    """Create or update the three-point lighting rig.

    Lights are sized and positioned relative to the PCB dimensions.
    All three use Area lights for soft illumination.

    Args:
        bounds: The combined PCB bounding box.

    Returns:
        A status message.
    """
    center = bounds.center
    max_dim = bounds.max_dimension

    if max_dim <= 0:
        return "Skipped lights: invalid bounding box."

    from .camera import get_or_create_render_setup_collection
    setup_coll = get_or_create_render_setup_collection()

    light_size = max_dim * 1.5
    light_distance = max_dim * 2.0

    # --- Key light: above and to the side ---
    key = _get_or_create_area_light(KEY_LIGHT_NAME, setup_coll)
    key.data.energy = 500.0 * max_dim
    key.data.size = light_size
    key.location = center + Vector((light_distance, -light_distance, light_distance))
    _aim_light_at(key, center)

    # --- Fill light: opposite side, lower energy ---
    fill = _get_or_create_area_light(FILL_LIGHT_NAME, setup_coll)
    fill.data.energy = 200.0 * max_dim
    fill.data.size = light_size
    fill.location = center + Vector((-light_distance, light_distance, light_distance * 0.5))
    _aim_light_at(fill, center)

    # --- Rim light: behind, moderate energy ---
    rim = _get_or_create_area_light(RIM_LIGHT_NAME, setup_coll)
    rim.data.energy = 300.0 * max_dim
    rim.data.size = light_size * 0.8
    rim.location = center + Vector((0.0, light_distance, light_distance * 0.7))
    _aim_light_at(rim, center)

    return "Three-point lighting rig created."