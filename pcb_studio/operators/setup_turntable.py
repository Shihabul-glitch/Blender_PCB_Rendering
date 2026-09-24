"""Operator that sets up the turntable animation."""

from __future__ import annotations

import traceback
from math import degrees

import bpy

from ..constants import (
    OPERATOR_ID_SETUP_TURNTABLE,
    PROP_SCENE_ATTR,
)
from ..utils.animation import setup_animation


class PCBSTUDIO_OT_setup_turntable(bpy.types.Operator):
    """Configure keyframes for the selected animation type."""

    bl_idname: str = OPERATOR_ID_SETUP_TURNTABLE
    bl_label: str = "Setup Animation"
    bl_description: str = "Create the selected PCB Studio animation"
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

        result = setup_animation(
            animation_type=props.animation_type,
            duration=props.turntable_duration,
            fps=int(props.turntable_fps),
            rotation_degrees=float(props.turntable_rotation_degrees),
            direction=props.turntable_direction,
            start_angle_degrees=degrees(props.turntable_start_angle),
            motion_style=props.turntable_motion_style,
            flyover_style=props.flyover_style,
            flyover_height=props.flyover_height,
        )

        props.turntable_status = result
        success = result.startswith((
            "PCB turntable set up", "Camera orbit set up", "Cinematic flyover set up",
        ))
        self.report({"INFO"} if success else {"ERROR"}, result)
        return {"FINISHED"} if success else {"CANCELLED"}
