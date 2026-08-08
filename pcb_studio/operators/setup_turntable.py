"""Operator that sets up the turntable animation."""

from __future__ import annotations

import traceback

import bpy

from ..constants import (
    OPERATOR_ID_SETUP_TURNTABLE,
    PROP_SCENE_ATTR,
)
from ..utils.animation import setup_turntable


class PCBSTUDIO_OT_setup_turntable(bpy.types.Operator):
    """Configure keyframes for a PCB turntable animation."""

    bl_idname: str = OPERATOR_ID_SETUP_TURNTABLE
    bl_label: str = "Setup Turntable"
    bl_description: str = "Create turntable keyframes on the PCB root"
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

        result = setup_turntable(
            duration=props.turntable_duration,
            fps=int(props.turntable_fps),
            rotation_degrees=float(props.turntable_rotation_degrees),
            direction=props.turntable_direction,
            start_angle_degrees=props.turntable_start_angle,
            motion_style=props.turntable_motion_style,
        )

        props.turntable_status = result
        self.report({"INFO"}, result)
        return {"FINISHED"}