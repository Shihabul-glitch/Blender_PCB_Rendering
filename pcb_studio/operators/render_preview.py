"""Operator that renders a single preview still image."""

from __future__ import annotations

import traceback

import bpy

from ..constants import (
    CAMERA_NAME,
    COLLECTION_NAME,
    EXTENSION_NAME,
    EXTENSION_VERSION,
    OPERATOR_ID_RENDER_PREVIEW,
    PROP_SCENE_ATTR,
)


class PCBSTUDIO_OT_render_preview(bpy.types.Operator):
    """Render a single still image of the PCB using the studio camera."""

    bl_idname: str = OPERATOR_ID_RENDER_PREVIEW
    bl_label: str = "Render Preview"
    bl_description: str = "Render one preview image using EEVEE"
    bl_options: set[str] = {"REGISTER"}

    def execute(self, context: bpy.types.Context | None) -> set[str]:
        """Validate preconditions and render."""
        try:
            return self._execute_impl(context)
        except Exception:
            traceback.print_exc()
            self.report(
                {"ERROR"},
                "An unexpected error occurred during rendering. "
                "Check the system console for details.",
            )
            return {"CANCELLED"}

    def _execute_impl(self, context: bpy.types.Context | None) -> set[str]:
        """Core render logic."""
        props = getattr(context.scene, PROP_SCENE_ATTR, None)
        if props is None:
            self.report({"ERROR"}, "Extension state not available.")
            return {"CANCELLED"}

        # --- Validate PCB_MODEL ---
        pcb_coll = bpy.data.collections.get(COLLECTION_NAME)
        if pcb_coll is None:
            self.report(
                {"ERROR"},
                "PCB_MODEL collection not found. Import a PCB first.",
            )
            props.render_status = "No PCB imported."
            props.last_render_successful = False
            return {"CANCELLED"}

        if len(pcb_coll.all_objects) == 0:
            self.report(
                {"ERROR"},
                "PCB_MODEL collection is empty. Import a PCB first.",
            )
            props.render_status = "PCB_MODEL is empty."
            props.last_render_successful = False
            return {"CANCELLED"}

        # --- Validate camera ---
        camera_obj = bpy.data.objects.get(CAMERA_NAME)
        if camera_obj is None:
            self.report(
                {"ERROR"},
                "PCB_RENDER_CAMERA not found. Run Prepare Scene first.",
            )
            props.render_status = "Camera not found."
            props.last_render_successful = False
            return {"CANCELLED"}

        if context.scene.camera != camera_obj:
            self.report(
                {"WARNING"},
                "Scene camera is not PCB_RENDER_CAMERA. Setting it now.",
            )
            context.scene.camera = camera_obj

        # --- Confirm scene preparation ---
        if not props.scene_setup_ready:
            self.report(
                {"WARNING"},
                "Scene has not been prepared. Run Prepare Scene first for best results.",
            )

        # --- Render ---
        try:
            result = bpy.ops.render.render(write_still=True)
        except Exception:
            traceback.print_exc()
            self.report(
                {"ERROR"},
                "Render operator failed. Check the system console for details.",
            )
            props.render_status = "Render failed."
            props.last_render_successful = False
            return {"CANCELLED"}

        if result == {"CANCELLED"}:
            self.report({"ERROR"}, "Render was cancelled.")
            props.render_status = "Render cancelled."
            props.last_render_successful = False
            return {"CANCELLED"}

        # --- Attempt to show Render Result ---
        try:
            # Try to find an Image Editor area and set it to the render result.
            for window in context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type == "IMAGE_EDITOR":
                        area.spaces.active.image = bpy.data.images.get(
                            "Render Result",
                        )
                        break
        except Exception:
            # Displaying is best-effort; render already completed.
            pass

        # --- Success ---
        props.render_status = "Render completed successfully."
        props.last_render_successful = True

        self.report({"INFO"}, "Preview render completed.")
        print(
            f"{EXTENSION_NAME} v{EXTENSION_VERSION}: "
            f"Preview render completed successfully.",
        )

        return {"FINISHED"}