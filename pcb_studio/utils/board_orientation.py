"""The board's declared top face and front edge.

``AUTO`` mode keeps the historic behaviour: the board's facing axis is guessed
from the thinnest dimension of the product bounds.  That finds a face but never
a front edge, so the roll and the left/right side of an angled preset are
arbitrary, and a board with tall connectors can defeat the guess entirely.  In
``MANUAL`` mode the user states which world axis each of those points along and
every board-relative camera preset is aimed in that frame instead.

Nothing here moves geometry -- a declaration only changes where the camera goes.
"""

from __future__ import annotations

import bpy
from mathutils import Vector

from ..constants import BOARD_AXIS_ITEMS, PROP_SCENE_ATTR

#: World direction for each key in ``BOARD_AXIS_ITEMS``.
AXIS_VECTORS: dict[str, Vector] = {
    "POS_X": Vector((1.0, 0.0, 0.0)),
    "NEG_X": Vector((-1.0, 0.0, 0.0)),
    "POS_Y": Vector((0.0, 1.0, 0.0)),
    "NEG_Y": Vector((0.0, -1.0, 0.0)),
    "POS_Z": Vector((0.0, 0.0, 1.0)),
    "NEG_Z": Vector((0.0, 0.0, -1.0)),
}

#: Display label for each axis key, for status messages.
_AXIS_LABELS: dict[str, str] = {key: name for key, name, _ in BOARD_AXIS_ITEMS}

#: Fallback order used when a chosen front edge collides with the top face.
_FRONT_FALLBACKS: tuple[str, ...] = ("NEG_Y", "POS_X", "NEG_Z", "POS_Y", "NEG_X", "POS_Z")

#: Two axes count as the same line when their directions are this aligned.
_PARALLEL_TOLERANCE: float = 0.5


def axis_vector(key: str) -> Vector:
    """Return the world direction for an axis key, defaulting to +Z."""
    return AXIS_VECTORS.get(key, AXIS_VECTORS["POS_Z"]).copy()


def is_perpendicular(top_key: str, front_key: str) -> bool:
    """True when the two axis keys describe perpendicular world directions."""
    return abs(axis_vector(top_key).dot(axis_vector(front_key))) < _PARALLEL_TOLERANCE


def perpendicular_front(top_key: str, front_key: str) -> str:
    """Return *front_key*, or the first fallback axis perpendicular to the top.

    The property update callback uses this so the stored pair can never be
    degenerate, which would otherwise collapse the camera basis.
    """
    if is_perpendicular(top_key, front_key):
        return front_key
    for candidate in _FRONT_FALLBACKS:
        if is_perpendicular(top_key, candidate):
            return candidate
    return "NEG_Y"


def nearest_world_axis(direction: Vector) -> str:
    """Return the axis key whose direction most closely matches *direction*.

    Used by the pick-from-view buttons: whatever the user has orbited to, the
    board is declared on the nearest of the six world axes.
    """
    if direction.length < 1e-9:
        return "POS_Z"
    normalized = direction.normalized()
    return max(AXIS_VECTORS, key=lambda key: normalized.dot(AXIS_VECTORS[key]))


def _props(scene: bpy.types.Scene | None):
    scene = scene if scene is not None else getattr(bpy.context, "scene", None)
    return getattr(scene, PROP_SCENE_ATTR, None) if scene is not None else None


def declared_board_frame(
    scene: bpy.types.Scene | None = None,
) -> tuple[Vector, Vector] | None:
    """Return the declared ``(top, front)`` world axes, or ``None`` for AUTO.

    ``None`` also covers an unregistered scene and a stored pair that is no
    longer perpendicular, so callers fall back to the bounds-based guess rather
    than to a degenerate frame.
    """
    props = _props(scene)
    if props is None or getattr(props, "board_orientation_mode", "AUTO") != "MANUAL":
        return None
    top_key = props.board_top_axis
    front_key = props.board_front_axis
    if not is_perpendicular(top_key, front_key):
        return None
    return axis_vector(top_key), axis_vector(front_key)


def set_board_axis_from_view(
    scene: bpy.types.Scene,
    view_direction: Vector,
    which: str,
) -> str:
    """Declare the top face or front edge from a viewport direction.

    *view_direction* points from the board toward the viewer, so the axis the
    user is looking at is simply the nearest world axis to it.  Switches the
    scene into MANUAL mode, since picking a face is a declaration.
    """
    props = _props(scene)
    if props is None:
        return "Cannot declare the board orientation: extension state not available."
    axis = nearest_world_axis(view_direction)
    label = _AXIS_LABELS.get(axis, axis)
    if which == "TOP":
        props.board_orientation_mode = "MANUAL"
        props.board_top_axis = axis
        # The setter below re-runs the perpendicular guard against the new top.
        props.board_front_axis = perpendicular_front(axis, props.board_front_axis)
        return f"Board top face declared as {label}."
    if not is_perpendicular(props.board_top_axis, axis):
        return (
            "Cannot use this view as the front edge: it points along the declared "
            "top face. Orbit to a side of the board, not its top."
        )
    props.board_orientation_mode = "MANUAL"
    props.board_front_axis = axis
    return f"Board front edge declared as {label}."
