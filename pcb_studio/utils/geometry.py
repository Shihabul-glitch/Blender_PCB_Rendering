"""World-space bounding box utility for PCB geometry."""

from __future__ import annotations

from dataclasses import dataclass
from math import isinf

import bpy
from mathutils import Vector


@dataclass
class BoundingBox:
    """Axis-aligned world-space bounding box."""

    min: Vector
    """Minimum corner in world space."""

    max: Vector
    """Maximum corner in world space."""

    center: Vector
    """Geometric center in world space."""

    dimensions: Vector
    """Size along each axis (max - min)."""

    max_dimension: float
    """Largest single-axis dimension."""

    is_valid: bool
    """True if the bounding box contains meaningful geometry."""


def compute_pcb_bounds(pcb_collection: bpy.types.Collection) -> BoundingBox:
    """Calculate the combined world-space bounding box of all mesh
    objects in *pcb_collection*.

    Uses each object's evaluated ``bound_box`` transformed by its
    ``matrix_world``.  Camera, light, and empty objects are ignored.

    Args:
        pcb_collection: The ``PCB_MODEL`` collection.

    Returns:
        A :class:`BoundingBox`.  ``is_valid`` is ``False`` when no
        mesh geometry is found.
    """
    depsgraph = bpy.context.evaluated_depsgraph_get()

    min_corner = Vector((float("inf"), float("inf"), float("inf")))
    max_corner = Vector((float("-inf"), float("-inf"), float("-inf")))

    found_any = False

    for obj in pcb_collection.all_objects:
        if obj.type != "MESH":
            continue

        evaluated = obj.evaluated_get(depsgraph)
        world_mat = obj.matrix_world

        for corner_local in evaluated.bound_box:
            world_corner = world_mat @ Vector(corner_local)
            min_corner.x = min(min_corner.x, world_corner.x)
            min_corner.y = min(min_corner.y, world_corner.y)
            min_corner.z = min(min_corner.z, world_corner.z)
            max_corner.x = max(max_corner.x, world_corner.x)
            max_corner.y = max(max_corner.y, world_corner.y)
            max_corner.z = max(max_corner.z, world_corner.z)
            found_any = True

    if not found_any:
        return BoundingBox(
            min=Vector((0, 0, 0)),
            max=Vector((0, 0, 0)),
            center=Vector((0, 0, 0)),
            dimensions=Vector((0, 0, 0)),
            max_dimension=0.0,
            is_valid=False,
        )

    # Guard against an infinitely large box (should never happen).
    if isinf(min_corner.x) or isinf(max_corner.x):
        return BoundingBox(
            min=Vector((0, 0, 0)),
            max=Vector((0, 0, 0)),
            center=Vector((0, 0, 0)),
            dimensions=Vector((0, 0, 0)),
            max_dimension=0.0,
            is_valid=False,
        )

    dimensions = max_corner - min_corner
    center = (min_corner + max_corner) / 2.0
    max_dim = max(dimensions.x, dimensions.y, dimensions.z)

    if max_dim <= 0.0:
        return BoundingBox(
            min=min_corner,
            max=max_corner,
            center=center,
            dimensions=dimensions,
            max_dimension=0.0,
            is_valid=False,
        )

    return BoundingBox(
        min=min_corner,
        max=max_corner,
        center=center,
        dimensions=dimensions,
        max_dimension=max_dim,
        is_valid=True,
    )