"""Operator that switches 3D Viewports to Material Preview shading."""

from __future__ import annotations

import traceback

import bpy

from ..constants import OPERATOR_ID_PREVIEW_MATERIALS


class PCBSTUDIO_OT_preview_materials(bpy.types.Operator):
    """Switch 3D Viewports to Material Preview mode for inspecting materials."""

    bl_idname: str = OPERATOR_ID_PREVIEW_MATERIALS
    bl_label: str = "Preview Materials"
    bl_description: str = (
        "Switch 3D Viewports to Material Preview shading. "
        "You can also press Z and select Material Preview."
    )
    bl_options: set[str] = {"REGISTER"}

    def execute(self, context: bpy.types.Context | None) -> set[str]:
        """Attempt to switch viewport shading to Material Preview."""
        try:
            return self._execute_impl(context)
        except Exception:
            traceback.print_exc()
            self.report(
                {"ERROR"},
                "Could not switch to Material Preview. "
                "Check the system console for details.",
            )
            return {"CANCELLED"}

    def _execute_impl(self, context: bpy.types.Context | None) -> set[str]:
        """Core preview logic."""
        switched = 0

        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type != "VIEW_3D":
                    continue
                try:
                    area.spaces.active.shading.type = "MATERIAL"
                    switched += 1
                except Exception:
                    pass

        if switched > 0:
            msg = (
                f"Switched {switched} 3D Viewport(s) to Material Preview."
            )
            self.report({"INFO"}, msg)
        else:
            self.report(
                {"WARNING"},
                "No 3D Viewport found. "
                "Press Z in the 3D View and select Material Preview.",
            )

        return {"FINISHED"}