"""Operator that applies a studio lighting preset."""

from __future__ import annotations

import traceback

import bpy

from ..constants import (
    OPERATOR_ID_APPLY_LIGHTING,
    PROP_SCENE_ATTR,
)
from ..utils.environment import apply_lighting_preset


class PCBSTUDIO_OT_apply_lighting_preset(bpy.types.Operator):
    """Apply the selected studio lighting preset to managed lights."""

    bl_idname: str = OPERATOR_ID_APPLY_LIGHTING
    bl_label: str = "Apply Lighting Preset"
    bl_description: str = "Apply the selected studio lighting preset"
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

        result = apply_lighting_preset(
            props.studio_lighting_preset,
            intensity=props.lighting_intensity,
            shadow_softness=props.shadow_softness,
        )

        props.environment_status = result
        self.report({"INFO"}, result)
        return {"FINISHED"}