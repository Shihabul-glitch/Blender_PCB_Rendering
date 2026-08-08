"""Operator that applies a camera preset."""

from __future__ import annotations

import traceback

import bpy

from ..constants import (
    OPERATOR_ID_APPLY_CAMERA_PRESET,
    PROP_SCENE_ATTR,
)
from ..utils.composition import apply_camera_preset


class PCBSTUDIO_OT_apply_camera_preset(bpy.types.Operator):
    """Apply the selected camera preset."""

    bl_idname: str = OPERATOR_ID_APPLY_CAMERA_PRESET
    bl_label: str = "Apply Camera Preset"
    bl_description: str = "Apply the selected camera preset"
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

        result = apply_camera_preset(
            props.camera_preset,
            focal_length=props.camera_focal_length,
            context=context,
        )

        props.camera_status = result
        self.report(
            {"INFO"} if "applied" in result else {"ERROR"}, result,
        )
        return {"FINISHED"}