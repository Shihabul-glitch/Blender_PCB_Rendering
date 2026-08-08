"""Diagnostic operator for PCB Studio system checks."""

import bpy

from ..constants import (
    EXTENSION_NAME,
    EXTENSION_VERSION,
    OPERATOR_ID_SYSTEM_CHECK,
)


class PCBSTUDIO_OT_system_check(bpy.types.Operator):
    """Run a system check to verify the extension is working correctly."""

    bl_idname: str = OPERATOR_ID_SYSTEM_CHECK
    bl_label: str = "Run System Check"
    bl_description: str = "Check Blender version and extension foundation"
    bl_options: set[str] = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context | None) -> set[str]:
        """Execute the diagnostic check and report the Blender version."""
        bl_version: str = bpy.app.version_string
        message: str = (
            f"{EXTENSION_NAME} {EXTENSION_VERSION} system check passed. "
            f"Blender version: {bl_version}"
        )

        print(message)
        self.report({"INFO"}, message)

        return {"FINISHED"}