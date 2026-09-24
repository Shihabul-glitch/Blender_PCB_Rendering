"""Fast lighting-preview and professional Cycles still operators."""

from __future__ import annotations

import traceback

import bpy

from ..constants import (
    CAMERA_NAME,
    COLLECTION_NAME,
    OPERATOR_ID_RENDER_LIGHTING_PREVIEW,
    OPERATOR_ID_RENDER_PROFESSIONAL,
    PROP_SCENE_ATTR,
)
from ..utils.output import validate_output_path
from ..utils.cycles_devices import (
    configure_requested_cycles_device,
    format_cycles_render_status,
    restore_cycles_device_state,
    save_cycles_device_state,
)
from ..utils.professional_render import (
    configure_cycles_final,
    configure_eevee_preview,
    configure_managed_finishing,
    restore_render_settings,
    snapshot_render_settings,
)
from ..utils.studio import update_professional_studio


def _validate_scene(context, props) -> str | None:
    collection = bpy.data.collections.get(COLLECTION_NAME)
    if collection is None or not any(obj.type == "MESH" for obj in collection.all_objects):
        return "No PCB geometry found. Import a PCB first."
    camera = bpy.data.objects.get(CAMERA_NAME)
    if camera is None:
        return "PCB_RENDER_CAMERA not found. Run Prepare Scene first."
    context.scene.camera = camera
    result = update_professional_studio(context.scene, props)
    # Failure is signalled by the message prefix, never by whitelisting one
    # success sentence: update_professional_studio has several success strings
    # (the adaptive studio returns its own) and whitelisting rejected them all.
    if result.startswith(("Cannot", "No ", "Unknown")):
        return result
    return None


def _render_still() -> None:
    """Invoke Blender's still render (kept separate for failure-path testing)."""
    bpy.ops.render.render(write_still=True)


class PCBSTUDIO_OT_render_lighting_preview(bpy.types.Operator):
    bl_idname = OPERATOR_ID_RENDER_LIGHTING_PREVIEW
    bl_label = "Render Lighting Preview"
    bl_description = "Render a reduced-resolution EEVEE lighting preview"
    bl_options = {"REGISTER"}

    def execute(self, context):
        props = getattr(context.scene, PROP_SCENE_ATTR, None)
        if props is None:
            return {"CANCELLED"}
        snapshot = snapshot_render_settings(context.scene)
        try:
            error = _validate_scene(context, props)
            if error:
                self.report({"ERROR"}, error)
                return {"CANCELLED"}
            message = configure_eevee_preview(context.scene, props)
            configure_managed_finishing(context.scene, props)
            bpy.ops.render.render(write_still=False)
            props.professional_render_status = message
            self.report({"INFO"}, message)
            return {"FINISHED"}
        except Exception:
            traceback.print_exc()
            props.professional_render_status = "Lighting preview failed."
            self.report({"ERROR"}, "Lighting preview failed. See system console.")
            return {"CANCELLED"}
        finally:
            restore_render_settings(context.scene, snapshot)


class PCBSTUDIO_OT_render_professional_still(bpy.types.Operator):
    bl_idname = OPERATOR_ID_RENDER_PROFESSIONAL
    bl_label = "Render Professional Still"
    bl_description = "Render and save an adaptive, denoised Cycles product still"
    bl_options = {"REGISTER"}

    def execute(self, context):
        props = getattr(context.scene, PROP_SCENE_ATTR, None)
        if props is None:
            return {"CANCELLED"}
        snapshot = snapshot_render_settings(context.scene)
        device_snapshot = None
        try:
            error = _validate_scene(context, props)
            if error:
                self.report({"ERROR"}, error)
                return {"CANCELLED"}
            output_path = validate_output_path(
                props.final_output_directory, props.final_filename,
            )
            if output_path.exists() and not props.overwrite_existing:
                message = f"File already exists: {output_path}"
                props.professional_render_status = message
                self.report({"ERROR"}, message)
                return {"CANCELLED"}
            device_snapshot = save_cycles_device_state(context.scene, context)
            quality = configure_cycles_final(context.scene, props)
            device = configure_requested_cycles_device(
                context.scene,
                props.cycles_render_device,
                props.cycles_gpu_backend,
                props.cycles_fallback_to_cpu,
                context,
            )
            render_status = format_cycles_render_status(device, props)
            props.cycles_device_status = device.message
            props.professional_render_status = render_status
            print(f"PCB Studio Professional Still: {render_status}")
            self.report({"INFO"}, device.message)
            finishing = configure_managed_finishing(context.scene, props)
            context.scene.render.filepath = str(output_path)
            context.scene.render.image_settings.file_format = "PNG"
            context.scene.render.image_settings.color_mode = "RGB"
            _render_still()
            props.last_render_filepath = str(output_path)
            props.final_render_status = f"Saved: {output_path}"
            props.professional_render_status = (
                f"{render_status} | {quality} {finishing} Saved: {output_path}"
            )
            self.report({"INFO"}, f"Professional still saved: {output_path}")
            return {"FINISHED"}
        except ValueError as exc:
            props.professional_render_status = str(exc)
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        except RuntimeError as exc:
            message = f"Professional still failed: {exc}"
            props.professional_render_status = message
            self.report({"ERROR"}, message)
            return {"CANCELLED"}
        except Exception:
            traceback.print_exc()
            props.professional_render_status = "Professional still failed."
            self.report({"ERROR"}, "Professional still failed. See system console.")
            return {"CANCELLED"}
        finally:
            if device_snapshot is not None:
                warnings = restore_cycles_device_state(
                    context.scene, device_snapshot, context,
                )
                for warning in warnings:
                    print(f"PCB Studio Cycles restore warning: {warning}")
            restore_render_settings(context.scene, snapshot)
