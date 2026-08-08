"""Operators for loading and removing HDRI environments."""

from __future__ import annotations

import traceback

import bpy

from ..constants import (
    OPERATOR_ID_APPLY_HDRI,
    OPERATOR_ID_LOAD_HDRI,
    OPERATOR_ID_REMOVE_HDRI,
    PROP_SCENE_ATTR,
)
from ..utils.environment import remove_hdri_from_world, setup_hdri_world


class PCBSTUDIO_OT_load_hdri(bpy.types.Operator):
    """Load an HDRI environment file (.hdr, .exr)."""

    bl_idname: str = OPERATOR_ID_LOAD_HDRI
    bl_label: str = "Load HDRI"
    bl_description: str = "Select and load an HDRI environment file"
    bl_options: set[str] = {"REGISTER", "UNDO"}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")  # type: ignore[valid-type]

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

        if not self.filepath:
            self.report({"ERROR"}, "No file selected.")
            return {"CANCELLED"}

        result = setup_hdri_world(
            self.filepath,
            rotation_degrees=props.hdri_rotation,
            brightness=props.hdri_brightness,
        )

        if "HDRI loaded" in result:
            props.hdri_filepath = self.filepath
            # Hide studio lights when HDRI is active.
            from ..utils.environment import set_light_visibility
            set_light_visibility(False)

        props.environment_status = result
        self.report(
            {"INFO"} if "loaded" in result else {"ERROR"}, result,
        )
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context | None, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


class PCBSTUDIO_OT_apply_hdri(bpy.types.Operator):
    """Re-apply the loaded HDRI with current rotation and brightness values."""

    bl_idname: str = OPERATOR_ID_APPLY_HDRI
    bl_label: str = "Apply HDRI"
    bl_description: str = "Apply current rotation and brightness to the loaded HDRI"
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

        if not props.hdri_filepath:
            self.report({"ERROR"}, "No HDRI loaded. Use Load HDRI first.")
            return {"CANCELLED"}

        result = setup_hdri_world(
            props.hdri_filepath,
            rotation_degrees=props.hdri_rotation,
            brightness=props.hdri_brightness,
        )

        props.environment_status = result
        self.report({"INFO"}, result)
        return {"FINISHED"}


class PCBSTUDIO_OT_remove_hdri(bpy.types.Operator):
    """Remove the HDRI environment and restore a neutral world."""

    bl_idname: str = OPERATOR_ID_REMOVE_HDRI
    bl_label: str = "Remove HDRI"
    bl_description: str = "Remove the HDRI and restore a neutral world"
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

        result = remove_hdri_from_world()
        props.hdri_filepath = ""
        props.environment_status = result
        self.report({"INFO"}, result)
        return {"FINISHED"}