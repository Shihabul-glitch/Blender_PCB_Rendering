"""Operator that applies a background preset."""

from __future__ import annotations

import traceback

import bpy

from ..constants import (
    OPERATOR_ID_APPLY_BACKGROUND,
    PROP_SCENE_ATTR,
)
from ..utils.environment import apply_background_preset
from ..utils.studio import update_professional_studio


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

        material_result = apply_background_preset(props.background_preset)
        studio_result = update_professional_studio(context.scene, props)
        failed = studio_result.startswith(("Cannot", "No ", "Unknown"))
        result = studio_result if failed else f"{material_result}. {studio_result}"
        props.environment_status = result
        self.report({"ERROR"} if failed else {"INFO"}, result)
        return {"CANCELLED"} if failed else {"FINISHED"}
