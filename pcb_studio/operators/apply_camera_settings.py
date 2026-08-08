"""Operators for camera settings, zoom-to-fit, and reflection plane."""

from __future__ import annotations

import traceback

import bpy

from ..constants import (
    OPERATOR_ID_APPLY_CAMERA_SETTINGS,
    OPERATOR_ID_APPLY_REFLECTION,
    OPERATOR_ID_ZOOM_TO_FIT,
    PROP_SCENE_ATTR,
)
from ..utils.composition import (
    apply_camera_settings,
    apply_reflection_plane,
    zoom_to_fit,
)


class PCBSTUDIO_OT_apply_camera_settings(bpy.types.Operator):
    """Apply focal length, DOF, and re-frame the camera."""

    bl_idname: str = OPERATOR_ID_APPLY_CAMERA_SETTINGS
    bl_label: str = "Apply Camera Settings"
    bl_description: str = "Apply focal length, depth of field, and re-frame"
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

        result = apply_camera_settings(
            props.camera_focal_length,
            props.use_depth_of_field,
            props.focus_target_mode,
            props.camera_fstop,
            context=context,
        )

        props.camera_status = result
        self.report({"INFO"}, result)
        return {"FINISHED"}


class PCBSTUDIO_OT_zoom_to_fit(bpy.types.Operator):
    """Zoom the camera to fit the entire PCB while preserving direction."""

    bl_idname: str = OPERATOR_ID_ZOOM_TO_FIT
    bl_label: str = "Zoom to Fit PCB"
    bl_description: str = "Move camera to frame the entire PCB"
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

        result = zoom_to_fit()
        props.camera_status = result
        self.report({"INFO"}, result)
        return {"FINISHED"}


class PCBSTUDIO_OT_apply_reflection_plane(bpy.types.Operator):
    """Apply the selected reflection surface preset."""

    bl_idname: str = OPERATOR_ID_APPLY_REFLECTION
    bl_label: str = "Apply Reflection Plane"
    bl_description: str = "Apply the selected reflection surface"
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

        result = apply_reflection_plane(props.reflection_surface)
        props.camera_status = result
        self.report({"INFO"}, result)
        return {"FINISHED"}