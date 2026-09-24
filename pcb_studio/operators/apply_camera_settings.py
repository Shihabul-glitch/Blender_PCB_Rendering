"""Operators for camera settings, zoom-to-fit, and reflection plane."""

from __future__ import annotations

import traceback

import bpy

from ..constants import (
    OPERATOR_ID_ALIGN_CAMERA_TO_VIEW,
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
from ..utils.camera_controls import camera_animation_block_reason


def _get_3d_view_context(context: bpy.types.Context) -> dict | None:
    """Return a 3D View override context that can run view operators."""
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type != "VIEW_3D":
                continue
            for region in area.regions:
                if region.type == "WINDOW":
                    return {
                        "window": window,
                        "screen": window.screen,
                        "area": area,
                        "region": region,
                        "scene": context.scene,
                        "active_object": context.active_object,
                    }
    return None


class PCBSTUDIO_OT_align_camera_to_view(bpy.types.Operator):
    """Align the active camera to the current viewport orientation."""

    bl_idname: str = OPERATOR_ID_ALIGN_CAMERA_TO_VIEW
    bl_label: str = "Align Active Camera to View"
    bl_description: str = "Match the visible 3D viewport to the active camera"
    bl_options: set[str] = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context | None) -> set[str]:
        try:
            return self._execute_impl(context)
        except Exception:
            traceback.print_exc()
            self.report({"ERROR"}, "Unexpected error. See system console.")
            return {"CANCELLED"}

    def _execute_impl(self, context: bpy.types.Context | None) -> set[str]:
        if context is None:
            self.report({"ERROR"}, "No active Blender context.")
            return {"CANCELLED"}

        blocked = camera_animation_block_reason()
        if blocked:
            self.report({"ERROR"}, blocked)
            return {"CANCELLED"}

        camera = context.scene.camera
        if camera is None:
            camera = context.active_object
            if camera is not None and camera.type == "CAMERA":
                context.scene.camera = camera
            else:
                self.report({"ERROR"}, "No active camera. Set a camera as the scene camera first.")
                return {"CANCELLED"}

        override = _get_3d_view_context(context)
        if override is None:
            self.report({"ERROR"}, "No 3D View is available to align the camera from.")
            return {"CANCELLED"}

        with context.temp_override(**override):
            result = bpy.ops.view3d.camera_to_view()

        if result not in ({"FINISHED"}, {"RUNNING_MODAL"}):
            self.report({"ERROR"}, f"Camera alignment failed: {result}")
            return {"CANCELLED"}

        props = getattr(context.scene, PROP_SCENE_ATTR, None)
        if props is not None:
            props.camera_status = "Camera aligned to current viewport."
        self.report({"INFO"}, "Camera aligned to current viewport.")
        return {"FINISHED"}


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
        success = result.startswith("Camera settings applied.")
        self.report({"INFO"} if success else {"ERROR"}, result)
        return {"FINISHED"} if success else {"CANCELLED"}


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

        result = zoom_to_fit(1.0 + props.camera_fit_margin)
        props.camera_status = result
        success = result.startswith("Fit PCB")
        self.report({"INFO"} if success else {"ERROR"}, result)
        return {"FINISHED"} if success else {"CANCELLED"}


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
        try:
            from ..utils.studio import refresh_studio_values
            refresh_studio_values(context.scene, props)
        except Exception:
            # Geometry was still updated; the explicit Update Studio button
            # reports any detailed material refresh failure.
            pass
        props.camera_status = result
        self.report({"INFO"}, result)
        return {"FINISHED"}
