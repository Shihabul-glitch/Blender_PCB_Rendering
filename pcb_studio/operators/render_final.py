"""Operator that renders and saves a final PNG image."""

from __future__ import annotations

import traceback
from pathlib import Path

import bpy

from ..constants import (
    CAMERA_NAME,
    COLLECTION_NAME,
    EXTENSION_NAME,
    EXTENSION_VERSION,
    OPERATOR_ID_RENDER_FINAL,
    PROP_SCENE_ATTR,
)
from ..utils.output import validate_output_path


def _configure_quality_preset(preset: str) -> str:
    """Apply resolution and EEVEE quality settings for *preset*.

    Returns a status message.
    """
    scene = bpy.context.scene

    presets = {
        "LOW_POWER": (1280, 720, 32),
        "STANDARD": (1920, 1080, 64),
        "HIGH": (2560, 1440, 128),
    }

    res_x, res_y, samples = presets.get(preset, (1280, 720, 32))

    scene.render.resolution_x = res_x
    scene.render.resolution_y = res_y
    scene.render.resolution_percentage = 100

    if hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = samples

    return f"Quality: {res_x}×{res_y}, {samples} samples."


class PCBSTUDIO_OT_render_final(bpy.types.Operator):
    """Render and save a final PNG image of the PCB."""

    bl_idname: str = OPERATOR_ID_RENDER_FINAL
    bl_label: str = "Render Final PNG"
    bl_description: str = "Render and save a final PNG image to disk"
    bl_options: set[str] = {"REGISTER"}

    def execute(self, context: bpy.types.Context | None) -> set[str]:
        """Validate, render, and save."""
        try:
            return self._execute_impl(context)
        except Exception:
            traceback.print_exc()
            self.report(
                {"ERROR"},
                "An unexpected error occurred during final render. "
                "Check the system console for details.",
            )
            return {"CANCELLED"}

    def _execute_impl(self, context: bpy.types.Context | None) -> set[str]:
        """Core final render logic."""
        props = getattr(context.scene, PROP_SCENE_ATTR, None)
        if props is None:
            self.report({"ERROR"}, "Extension state not available.")
            return {"CANCELLED"}

        # --- Validate PCB_MODEL ---
        pcb_coll = bpy.data.collections.get(COLLECTION_NAME)
        if pcb_coll is None or len(pcb_coll.all_objects) == 0:
            self.report({"ERROR"}, "No PCB imported. Import a PCB first.")
            props.final_render_status = "No PCB imported."
            return {"CANCELLED"}

        # --- Validate camera ---
        camera_obj = bpy.data.objects.get(CAMERA_NAME)
        if camera_obj is None:
            self.report(
                {"ERROR"},
                "PCB_RENDER_CAMERA not found. Run Prepare Scene first.",
            )
            props.final_render_status = "Camera not found."
            return {"CANCELLED"}

        context.scene.camera = camera_obj

        # --- Validate output path ---
        try:
            output_path = validate_output_path(
                props.final_output_directory,
                props.final_filename,
            )
        except ValueError as exc:
            self.report({"ERROR"}, str(exc))
            props.final_render_status = str(exc)
            return {"CANCELLED"}

        # --- Overwrite check ---
        if output_path.exists() and not props.overwrite_existing:
            self.report(
                {"ERROR"},
                f"File already exists: {output_path}. "
                "Enable 'Overwrite Existing File' to replace it.",
            )
            props.final_render_status = (
                f"File exists: {output_path.name}"
            )
            return {"CANCELLED"}

        # --- Configure quality ---
        quality_msg = _configure_quality_preset(props.final_render_quality)

        # --- Set output ---
        scene = context.scene
        scene.render.filepath = str(output_path)
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode = "RGB"

        # --- Render ---
        props.final_render_status = (
            f"Rendering {quality_msg}..."
        )
        print(
            f"{EXTENSION_NAME} v{EXTENSION_VERSION}: "
            f"Final render starting — {quality_msg} → {output_path}",
        )

        try:
            result = bpy.ops.render.render(write_still=True)
        except Exception:
            traceback.print_exc()
            self.report(
                {"ERROR"},
                "Render operator failed. Check the system console.",
            )
            props.final_render_status = "Render failed."
            return {"CANCELLED"}

        if result == {"CANCELLED"}:
            self.report({"ERROR"}, "Render was cancelled.")
            props.final_render_status = "Render cancelled."
            return {"CANCELLED"}

        # --- Success ---
        props.last_render_filepath = str(output_path)
        props.final_render_status = (
            f"Saved: {output_path.name}"
        )

        self.report({"INFO"}, f"Final render saved to {output_path}")
        print(
            f"{EXTENSION_NAME} v{EXTENSION_VERSION}: "
            f"Final render saved to {output_path}",
        )

        return {"FINISHED"}