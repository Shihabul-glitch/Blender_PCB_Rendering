"""Operator that declares a board face from the current viewport angle."""

from __future__ import annotations

import traceback

import bpy
from mathutils import Vector

from ..constants import (
    OPERATOR_ID_SET_BOARD_AXIS_FROM_VIEW,
    PROP_SCENE_ATTR,
)
from ..utils.board_orientation import set_board_axis_from_view

_AXIS_ITEMS = [
    ("TOP", "Top Face", "Declare the face you are looking at as the component side"),
    ("FRONT", "Front Edge", "Declare the edge you are looking at as the front"),
]


def _view_direction(context: bpy.types.Context) -> Vector | None:
    """Direction from the board toward the viewer, from the active 3D view.

    The viewport's own area is preferred so the button reads the view the user
    is actually looking through; any other open 3D view is the fallback.
    """
    areas = []
    if context.area is not None and context.area.type == "VIEW_3D":
        areas.append(context.area)
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D" and area not in areas:
                areas.append(area)
    for area in areas:
        region_3d = getattr(area.spaces.active, "region_3d", None)
        if region_3d is not None:
            return region_3d.view_rotation @ Vector((0.0, 0.0, 1.0))
    return None


class PCBSTUDIO_OT_set_board_axis_from_view(bpy.types.Operator):
    """Declare the board's top face or front edge from the current view."""

    bl_idname: str = OPERATOR_ID_SET_BOARD_AXIS_FROM_VIEW
    bl_label: str = "Set From View"
    bl_description: str = (
        "Orbit until you are looking straight at the face, then declare it"
    )
    bl_options: set[str] = {"REGISTER", "UNDO"}

    axis: bpy.props.EnumProperty(name="Face", items=_AXIS_ITEMS, default="TOP")

    def execute(self, context: bpy.types.Context | None) -> set[str]:
        try:
            return self._execute_impl(context)
        except Exception:
            traceback.print_exc()
            self.report({"ERROR"}, "Unexpected error. See system console.")
            return {"CANCELLED"}

    def _execute_impl(self, context: bpy.types.Context | None) -> set[str]:
        if context is None:
            self.report({"ERROR"}, "No active Blender context.")
            return {"CANCELLED"}
        props = getattr(context.scene, PROP_SCENE_ATTR, None)
        if props is None:
            self.report({"ERROR"}, "Extension state not available.")
            return {"CANCELLED"}

        direction = _view_direction(context)
        if direction is None:
            self.report({"ERROR"}, "No 3D View is available to read the angle from.")
            return {"CANCELLED"}

        result = set_board_axis_from_view(context.scene, direction, self.axis)
        props.camera_status = result
        success = not result.startswith("Cannot")
        self.report({"INFO"} if success else {"ERROR"}, result)
        return {"FINISHED"} if success else {"CANCELLED"}
