"""World-space bounding box utility for PCB geometry."""

from __future__ import annotations

from dataclasses import dataclass
from math import atan, isinf, tan

import bpy
from mathutils import Vector

from .board_orientation import declared_board_frame


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


def compute_world_bounds(objects) -> BoundingBox:
    """Calculate combined evaluated world bounds for an object iterable."""
    depsgraph = bpy.context.evaluated_depsgraph_get()

    min_corner = Vector((float("inf"), float("inf"), float("inf")))
    max_corner = Vector((float("-inf"), float("-inf"), float("-inf")))
    found_any = False

    for obj in objects:
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

    if not found_any or isinf(min_corner.x) or isinf(max_corner.x):
        return BoundingBox(
            min=Vector((0, 0, 0)), max=Vector((0, 0, 0)),
            center=Vector((0, 0, 0)), dimensions=Vector((0, 0, 0)),
            max_dimension=0.0, is_valid=False,
        )

    dimensions = max_corner - min_corner
    center = (min_corner + max_corner) / 2.0
    max_dim = max(dimensions.x, dimensions.y, dimensions.z)
    return BoundingBox(
        min=min_corner, max=max_corner, center=center,
        dimensions=dimensions, max_dimension=max_dim,
        is_valid=max_dim > 0.0,
    )


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
    return compute_world_bounds(o for o in pcb_collection.all_objects
                                if not o.get("pcbstudio_environment_role") and not o.get("pcbstudio_managed"))


#: A board is only treated as facing a non-default axis when its thinnest
#: dimension is clearly thinner than the next one.  A near-cubic bounding box is
#: ambiguous, so it falls back to the flat-board convention (+Z).
_BOARD_AXIS_MARGIN: float = 0.7


def board_normal_axis(bounds: BoundingBox) -> Vector:
    """Unit vector along the PCB's thinnest dimension: the board's face normal.

    Altium exports do not agree on which way a board lies.  A board flat in XY
    faces +Z, which every camera preset used to assume; a board standing in XZ
    faces Y, and a top-down preset then looks along its edge.  The thinnest axis
    of the product bounds identifies the face reliably, because a PCB is always
    far thinner than it is wide even with connectors on it.

    The sign is the side a face-on camera sits on: +Z above a flat board, and
    the negative axis otherwise, matching Blender's front and left views.
    """
    dimensions = bounds.dimensions
    ordered = sorted(
        (
            (abs(dimensions.x), Vector((-1.0, 0.0, 0.0))),
            (abs(dimensions.y), Vector((0.0, -1.0, 0.0))),
            (abs(dimensions.z), Vector((0.0, 0.0, 1.0))),
        ),
        key=lambda item: item[0],
    )
    thinnest, axis = ordered[0]
    next_thinnest = ordered[1][0]
    if next_thinnest <= 0.0 or thinnest > next_thinnest * _BOARD_AXIS_MARGIN:
        return Vector((0.0, 0.0, 1.0))
    return axis


def board_basis(
    bounds: BoundingBox,
    scene: bpy.types.Scene | None = None,
) -> tuple[Vector, Vector, Vector]:
    """Right / up / normal frame that camera presets are authored in.

    Presets are written for a board lying flat and facing +Z, where canonical Y
    points away from the viewer and canonical Z is the board's face normal.  For
    a flat board this frame is the world axes, so existing scenes are unchanged.

    A board orientation the user has declared wins over the bounds-based guess:
    the declared top face becomes the normal and the declared front edge becomes
    canonical -Y, which is the only way the roll and the left/right side of an
    angled preset can be known rather than assumed.
    """
    declared = declared_board_frame(scene)
    if declared is not None:
        normal, front = declared
        normal = normal.normalized()
        # Canonical +Y points away from a viewer standing at the front edge.
        up = -front
        up = up - normal * up.dot(normal)
        if up.length < 1e-9:
            return _guessed_board_basis(bounds)
        up.normalize()
        return up.cross(normal), up, normal
    return _guessed_board_basis(bounds)


def _guessed_board_basis(bounds: BoundingBox) -> tuple[Vector, Vector, Vector]:
    """The historic frame, inferred from the thinnest bounding-box dimension."""
    normal = board_normal_axis(bounds)
    # A standing board keeps world +Z as "up" in frame, which means canonical
    # -Y (authored as "toward the viewer") has to become elevation.
    up = Vector((0.0, 1.0, 0.0)) if abs(normal.z) >= 0.9 else Vector((0.0, 0.0, -1.0))
    return up.cross(normal), up, normal


def board_direction(
    bounds: BoundingBox,
    authored: Vector,
    scene: bpy.types.Scene | None = None,
) -> Vector:
    """Map a preset direction from the canonical board frame into world space."""
    right, up, normal = board_basis(bounds, scene)
    mapped = right * authored.x + up * authored.y + normal * authored.z
    return mapped.normalized() if mapped.length > 1e-9 else Vector((0.0, 0.0, 1.0))


def bounds_corners(bounds: BoundingBox) -> list[Vector]:
    """The eight world-space corners of *bounds*."""
    return [
        Vector((x, y, z))
        for x in (bounds.min.x, bounds.max.x)
        for y in (bounds.min.y, bounds.max.y)
        for z in (bounds.min.z, bounds.max.z)
    ]


def camera_field_of_view(
    camera_data: bpy.types.Camera,
    scene: bpy.types.Scene,
) -> tuple[float, float]:
    """Horizontal and vertical field of view for the scene's output aspect.

    ``Camera.angle_x`` and ``angle_y`` describe the sensor alone, so on any
    output that is not the sensor's own shape they frame the wrong axis.  The
    rendered frame is what has to contain the board, so the fitting axis is
    taken from ``sensor_fit`` and the other is derived from the render aspect.
    """
    render = scene.render
    width = render.resolution_x * render.pixel_aspect_x
    height = render.resolution_y * render.pixel_aspect_y
    aspect = (width / height) if height else 1.0
    fit = camera_data.sensor_fit
    if fit == "HORIZONTAL" or (fit == "AUTO" and aspect >= 1.0):
        angle_x = float(camera_data.angle_x if fit == "HORIZONTAL" else camera_data.angle)
        return angle_x, 2.0 * atan(tan(angle_x / 2.0) / aspect)
    angle_y = float(camera_data.angle_y if fit == "VERTICAL" else camera_data.angle)
    return 2.0 * atan(tan(angle_y / 2.0) * aspect), angle_y


def required_camera_distance(
    bounds: BoundingBox,
    back: Vector,
    right: Vector,
    up: Vector,
    angle_x: float,
    angle_y: float,
    margin: float = 1.10,
) -> float:
    """Distance along *back* that fits *bounds* for a camera with this basis.

    Every corner is projected onto the camera's own axes, so an edge-on view of
    a thin board frames on its real width and height rather than on the world X
    and Y extents of the bounding box.

    Args:
        bounds: What has to fit in frame.
        back: Unit vector from the target toward the camera.
        right: Camera right axis.
        up: Camera up axis.
        angle_x: Horizontal field of view in radians.
        angle_y: Vertical field of view in radians.
        margin: Framing margin multiplier (1.10 = 10% of extra space).
    """
    tan_x = max(tan(max(angle_x, 1e-6) / 2.0), 1e-6)
    tan_y = max(tan(max(angle_y, 1e-6) / 2.0), 1e-6)
    required = 0.0001
    for corner in bounds_corners(bounds):
        offset = corner - bounds.center
        depth = offset.dot(back)
        required = max(
            required,
            depth + abs(offset.dot(right)) * margin / tan_x,
            depth + abs(offset.dot(up)) * margin / tan_y,
        )
    return required
