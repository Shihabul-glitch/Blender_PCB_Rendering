"""Operator that applies a background preset."""

from __future__ import annotations

import traceback

import bpy

from ..constants import (
    OPERATOR_ID_APPLY_BACKGROUND,
    PROP_SCENE_ATTR,
)
from ..utils.environment import apply_background_preset


class PCBSTUDIO_OT_apply_background(bpy.types.Operator):
    """Apply the selected background preset."""

    bl_idname: str = OPERATOR_ID_APPLY_BACKGROUND
    bl_label: str = "Apply Background"
    bl_description: str = "Apply the selected background preset"
    bl_options: set[str] = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context | None) -> set[str]:
        try:
            return self._execute_impl(context)
        except Exception:
            traceback.print_exc()
            self.report({"ERROR"}, "Unexpected error. See system console.")
            return {"CANCELLED"}

    def _execute_impl(self, context: bpy.types.Context | None) -> set[str]:
        props = getattr(context.scene, PROP_SCENE_ATTR, None)
        if props is None:
            self.report({"ERROR"}, "Extension state not available.")
            return {"CANCELLED"}

        result = apply_background_preset(props.background_preset)
        props.environment_status = result
        self.report({"INFO"}, result)
        return {"FINISHED"}