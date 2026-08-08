"""Operators for previewing, test-rendering, and rendering turntable animations."""

from __future__ import annotations

import traceback

import bpy

from ..constants import (
    CAMERA_NAME,
    COLLECTION_NAME,
    EXTENSION_NAME,
    EXTENSION_VERSION,
    OPERATOR_ID_PREVIEW_TURNTABLE,
    OPERATOR_ID_RENDER_TEST_FRAME,
    OPERATOR_ID_RENDER_TURNTABLE,
    PROP_SCENE_ATTR,
)
from ..utils.animation import get_turntable_frame_count
from ..utils.video_output import (
    apply_resolution_preset,
    configure_mp4_output,
    configure_png_sequence_output,
    validate_animation_output,
)


class PCBSTUDIO_OT_preview_turntable(bpy.types.Operator):
    """Preview the turntable animation in the viewport."""

    bl_idname: str = OPERATOR_ID_PREVIEW_TURNTABLE
    bl_label: str = "Preview Turntable"
    bl_description: str = "Start viewport animation playback to preview the turntable"
    bl_options: set[str] = {"REGISTER"}

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

        pcb_coll = bpy.data.collections.get(COLLECTION_NAME)
        if pcb_coll is None:
            self.report({"ERROR"}, "PCB_MODEL not found. Import a PCB first.")
            return {"CANCELLED"}

        camera = bpy.data.objects.get(CAMERA_NAME)
        if camera is None:
            self.report({"ERROR"}, "Camera not found. Run Prepare Scene first.")
            return {"CANCELLED"}

        context.scene.camera = camera
        context.scene.frame_set(1)

        # Try to start viewport playback.
        try:
            bpy.ops.screen.animation_play()
        except Exception:
            # Playback cannot be started from some contexts.
            self.report(
                {"INFO"},
                "Turntable configured. Press Spacebar to preview animation.",
            )
            props.turntable_status = "Ready for preview."
            return {"FINISHED"}

        props.turntable_status = "Preview playback started."
        self.report({"INFO"}, "Turntable preview started.")
        return {"FINISHED"}


class PCBSTUDIO_OT_render_test_frame(bpy.types.Operator):
    """Render a single test frame of the turntable animation."""

    bl_idname: str = OPERATOR_ID_RENDER_TEST_FRAME
    bl_label: str = "Render Test Frame"
    bl_description: str = "Render one frame to check lighting and composition"
    bl_options: set[str] = {"REGISTER"}

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

        pcb_coll = bpy.data.collections.get(COLLECTION_NAME)
        if pcb_coll is None:
            self.report({"ERROR"}, "PCB_MODEL not found.")
            return {"CANCELLED"}

        camera = bpy.data.objects.get(CAMERA_NAME)
        if camera is None:
            self.report({"ERROR"}, "Camera not found.")
            return {"CANCELLED"}

        context.scene.camera = camera

        # Apply resolution preset.
        res_msg = apply_resolution_preset(props.turntable_resolution)

        # Render current frame.
        scene = context.scene
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode = "RGB"

        props.turntable_status = (
            f"Rendering test frame at frame {scene.frame_current}..."
        )
        print(
            f"{EXTENSION_NAME} v{EXTENSION_VERSION}: "
            f"Test frame rendering — {res_msg}",
        )

        try:
            result = bpy.ops.render.render(write_still=False)
        except Exception:
            traceback.print_exc()
            self.report({"ERROR"}, "Render failed. Check system console.")
            props.turntable_status = "Test frame render failed."
            return {"CANCELLED"}

        if result == {"CANCELLED"}:
            props.turntable_status = "Test frame cancelled."
            return {"CANCELLED"}

        props.turntable_status = "Test frame rendered."
        self.report({"INFO"}, f"Test frame rendered. {res_msg}")
        return {"FINISHED"}


class PCBSTUDIO_OT_render_turntable(bpy.types.Operator):
    """Render the complete turntable animation to video or PNG sequence."""

    bl_idname: str = OPERATOR_ID_RENDER_TURNTABLE
    bl_label: str = "Render Turntable Video"
    bl_description: str = "Render the turntable animation to MP4 or PNG sequence"
    bl_options: set[str] = {"REGISTER"}

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

        # Validate PCB.
        pcb_coll = bpy.data.collections.get(COLLECTION_NAME)
        if pcb_coll is None or len(pcb_coll.all_objects) == 0:
            self.report({"ERROR"}, "No PCB imported.")
            props.turntable_status = "No PCB imported."
            return {"CANCELLED"}

        # Validate camera.
        camera = bpy.data.objects.get(CAMERA_NAME)
        if camera is None:
            self.report({"ERROR"}, "Camera not found. Run Prepare Scene first.")
            props.turntable_status = "Camera not found."
            return {"CANCELLED"}

        context.scene.camera = camera

        # Validate output path.
        output_fmt = props.animation_output_format
        try:
            err_msg, full_path = validate_animation_output(
                props.animation_output_directory,
                props.animation_filename,
                output_fmt,
                props.animation_overwrite,
            )
        except ValueError as exc:
            self.report({"ERROR"}, str(exc))
            props.turntable_status = str(exc)
            return {"CANCELLED"}

        if err_msg:
            self.report({"ERROR"}, err_msg)
            props.turntable_status = err_msg
            return {"CANCELLED"}

        # Apply resolution preset.
        res_msg = apply_resolution_preset(props.turntable_resolution)

        # Configure output.
        if output_fmt == "MP4":
            out_msg = configure_mp4_output(full_path)
        else:
            out_msg = configure_png_sequence_output(full_path)

        # Ensure EEVEE engine.
        scene = context.scene
        try:
            scene.render.engine = "BLENDER_EEVEE_NEXT"
        except TypeError:
            scene.render.engine = "BLENDER_EEVEE"

        # Apply FPS from properties.
        scene.render.fps = int(props.turntable_fps)

        # Calculate frame count for display.
        fps = int(props.turntable_fps)
        total_frames = get_turntable_frame_count(props.turntable_duration, fps)

        # Summary.
        summary = (
            f"PCB Studio Turntable Render\n"
            f"Resolution: {scene.render.resolution_x}×{scene.render.resolution_y}\n"
            f"FPS: {fps}\n"
            f"Duration: {props.turntable_duration}s\n"
            f"Frames: {total_frames}\n"
            f"Output: {full_path}"
        )
        print(f"{EXTENSION_NAME} v{EXTENSION_VERSION}:\n{summary}")

        props.turntable_status = "Rendering..."
        self.report({"INFO"}, "Turntable animation rendering started.")

        # Render animation.
        try:
            result = bpy.ops.render.render(animation=True, write_still=False)
        except Exception:
            traceback.print_exc()
            self.report({"ERROR"}, "Animation render failed. Check system console.")
            props.turntable_status = "Render failed."
            return {"CANCELLED"}

        if result == {"CANCELLED"}:
            props.turntable_status = "Render cancelled."
            return {"CANCELLED"}

        props.turntable_status = f"Completed: {total_frames} frames"
        props.last_animation_output = full_path
        self.report({"INFO"}, f"Turntable animation saved to {full_path}")
        print(
            f"{EXTENSION_NAME} v{EXTENSION_VERSION}: "
            f"Turntable animation saved to {full_path}",
        )
        return {"FINISHED"}