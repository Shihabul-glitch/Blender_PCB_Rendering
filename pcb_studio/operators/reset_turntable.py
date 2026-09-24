"""Operator that resets the turntable animation."""

from __future__ import annotations

import traceback

import bpy

from ..constants import (
    OPERATOR_ID_RESET_TURNTABLE,
    PROP_SCENE_ATTR,
)
from ..utils.animation import reset_animation


class PCBSTUDIO_OT_reset_turntable(bpy.types.Operator):
    """Remove managed animation and restore the PCB and camera."""

    bl_idname: str = OPERATOR_ID_RESET_TURNTABLE
    bl_label: str = "Reset Animation"
    bl_description: str = "Remove managed keyframes and restore PCB and camera"
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

        if context.screen is not None and context.screen.is_animation_playing:
            try:
                bpy.ops.screen.animation_cancel(restore_frame=False)
            except RuntimeError:
                pass
        result = reset_animation()
        props.turntable_status = result
        props.turntable_enabled = False
        self.report({"INFO"}, result)
        return {"FINISHED"}
