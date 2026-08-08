"""Main sidebar panel for PCB Studio in the 3D Viewport."""

import bpy

from ..constants import (
    CAMERA_NAME,
    COLLECTION_NAME,
    EXTENSION_NAME,
    EXTENSION_VERSION,
    OPERATOR_ID_APPLY_BACKGROUND,
    OPERATOR_ID_APPLY_CAMERA_PRESET,
    OPERATOR_ID_APPLY_CAMERA_SETTINGS,
    OPERATOR_ID_APPLY_HDRI,
    OPERATOR_ID_APPLY_LIGHTING,
    OPERATOR_ID_APPLY_REFLECTION,
    OPERATOR_ID_ASSIGN_MATERIAL,
    OPERATOR_ID_IMPORT_OBJ,
    OPERATOR_ID_LOAD_HDRI,
    OPERATOR_ID_PREPARE_SCENE,
    OPERATOR_ID_PREVIEW_MATERIALS,
    OPERATOR_ID_PREVIEW_TURNTABLE,
    OPERATOR_ID_REMOVE_HDRI,
    OPERATOR_ID_RENDER_FINAL,
    OPERATOR_ID_RENDER_PREVIEW,
    OPERATOR_ID_RENDER_TEST_FRAME,
    OPERATOR_ID_RENDER_TURNTABLE,
    OPERATOR_ID_RESET_TURNTABLE,
    OPERATOR_ID_SETUP_TURNTABLE,
    OPERATOR_ID_SYSTEM_CHECK,
    OPERATOR_ID_ZOOM_TO_FIT,
    PANEL_ID,
    PANEL_LABEL,
    PROP_SCENE_ATTR,
    SIDEBAR_CATEGORY,
)
from ..utils.animation import get_turntable_frame_count


def _count_selected_pcb_objects(context: bpy.types.Context) -> int:
    pcb_coll = bpy.data.collections.get(COLLECTION_NAME)
    if pcb_coll is None:
        return 0
    pcb_names = {o.name for o in pcb_coll.all_objects}
    return sum(
        1 for o in context.selected_objects
        if o.type == "MESH" and o.name in pcb_names
    )


def _get_active_object_name(context: bpy.types.Context) -> str:
    obj = context.active_object
    return obj.name if obj is not None else "(none)"


class PCBSTUDIO_PT_main_panel(bpy.types.Panel):
    """PCB Studio main panel in the 3D Viewport sidebar."""

    bl_idname: str = PANEL_ID
    bl_label: str = PANEL_LABEL
    bl_space_type: str = "VIEW_3D"
    bl_region_type: str = "UI"
    bl_category: str = SIDEBAR_CATEGORY

    def draw(self, context: bpy.types.Context | None) -> None:
        layout = self.layout
        props = getattr(context.scene, PROP_SCENE_ATTR, None)

        # --- Header ---
        layout.label(text=f"{EXTENSION_NAME}")
        layout.label(text=f"Version {EXTENSION_VERSION}")
        layout.separator()
        layout.label(text="Extension foundation is active.")
        layout.separator()
        layout.operator(OPERATOR_ID_SYSTEM_CHECK, text="Run System Check", icon="SYSTEM")

        # --- Import PCB ---
        layout.separator(factor=1.5)
        box = layout.box()
        box.label(text="Import PCB", icon="IMPORT")
        if props is not None:
            if props.obj_filepath:
                box.label(text=f"OBJ: {props.obj_filepath}", icon="FILE_3D")
            else:
                box.label(text="OBJ: (none selected)", icon="FILE_3D")
            if props.mtl_filepath:
                box.label(text=f"MTL: {props.mtl_filepath}", icon="MATERIAL")
            else:
                box.label(text="MTL: (not detected)", icon="MATERIAL")
            if props.import_status:
                box.separator()
                box.label(text=f"Status: {props.import_status}")
            if props.pcb_imported:
                box.separator()
                row = box.row(align=True)
                row.label(text=f"Objects: {props.imported_object_count}")
                row.label(text=f"Materials: {props.imported_material_count}")
        box.separator()
        box.operator(OPERATOR_ID_IMPORT_OBJ, text="Select and Import OBJ", icon="IMPORT")

        # --- Studio Setup ---
        layout.separator(factor=1.5)
        box2 = layout.box()
        box2.label(text="Studio Setup", icon="SCENE")
        if props is not None:
            if props.scene_setup_status:
                box2.label(text=f"Setup: {props.scene_setup_status}", icon="INFO")
            elif not props.pcb_imported:
                box2.label(text="Setup: Import a PCB first", icon="ERROR")
            if props.camera_ready:
                box2.label(text="Camera: Active", icon="CAMERA_DATA")
            else:
                box2.label(text="Camera: Not set", icon="CAMERA_DATA")
            if props.last_render_successful:
                box2.label(text="Render: Successful", icon="RENDER_RESULT")
            elif props.render_status:
                box2.label(text=f"Render: {props.render_status}", icon="RENDER_RESULT")
            else:
                box2.label(text="Render: Not run", icon="RENDER_RESULT")
        box2.separator()
        if props is not None and props.pcb_imported:
            box2.operator(OPERATOR_ID_PREPARE_SCENE, text="Prepare Scene", icon="SETTINGS")
        else:
            row = box2.row()
            row.enabled = False
            row.operator(OPERATOR_ID_PREPARE_SCENE, text="Prepare Scene", icon="SETTINGS")
        if props is not None and props.scene_setup_ready:
            box2.operator(OPERATOR_ID_RENDER_PREVIEW, text="Render Preview", icon="RENDER_STILL")
        else:
            row = box2.row()
            row.enabled = False
            row.operator(OPERATOR_ID_RENDER_PREVIEW, text="Render Preview", icon="RENDER_STILL")

        # --- Materials ---
        layout.separator(factor=1.5)
        box3 = layout.box()
        box3.label(text="Materials", icon="MATERIAL")
        if props is not None and props.pcb_imported:
            selected_count = _count_selected_pcb_objects(context)
            box3.label(text=f"Active object: {_get_active_object_name(context)}")
            box3.label(text=f"Selected PCB objects: {selected_count}")
            box3.separator()
            box3.prop(props, "material_preset", text="Preset")
            box3.prop(props, "material_base_color", text="")
            box3.prop(props, "material_metallic", slider=True)
            box3.prop(props, "material_roughness", slider=True)
            box3.prop(props, "material_coat_weight", slider=True)
            if props.material_preset == "CUSTOM":
                box3.prop(props, "custom_material_name", text="Name")
            box3.separator()
            box3.operator("pcbstudio.create_or_update_material", text="Create or Update Material", icon="NODE_MATERIAL")
            box3.operator(OPERATOR_ID_ASSIGN_MATERIAL, text="Assign to Selected Objects", icon="PASTEDOWN")
            box3.operator(OPERATOR_ID_PREVIEW_MATERIALS, text="Preview Materials", icon="SHADING_RENDERED")
            if props.material_status:
                box3.separator()
                box3.label(text=f"Status: {props.material_status}")
            if props.current_material_name:
                box3.label(text=f"Material: {props.current_material_name}")
        else:
            box3.label(text="Import a PCB to use materials.")

        # --- Final Render ---
        layout.separator(factor=1.5)
        box4 = layout.box()
        box4.label(text="Final Render", icon="RENDER_ANIMATION")
        if props is not None and props.scene_setup_ready:
            box4.prop(props, "final_render_quality", text="Quality")
            box4.prop(props, "final_output_directory", text="Output")
            box4.prop(props, "final_filename", text="Filename")
            box4.prop(props, "overwrite_existing")
            box4.separator()
            box4.operator(OPERATOR_ID_RENDER_FINAL, text="Render Final PNG", icon="RENDER_STILL")
            if props.final_render_status:
                box4.separator()
                box4.label(text=f"Status: {props.final_render_status}")
            if props.last_render_filepath:
                box4.label(text=f"Saved: {props.last_render_filepath}")
        else:
            box4.label(text="Prepare the scene first.")

        # --- Lighting & Environment ---
        layout.separator(factor=1.5)
        box5 = layout.box()
        box5.label(text="Lighting & Environment", icon="LIGHT_AREA")
        if props is not None and props.scene_setup_ready:
            box5.prop(props, "lighting_mode", text="Mode")
            if props.lighting_mode == "STUDIO":
                box5.separator()
                box5.prop(props, "studio_lighting_preset", text="Studio Preset")
                box5.prop(props, "lighting_intensity", slider=True)
                box5.prop(props, "shadow_softness", slider=True)
                box5.operator(OPERATOR_ID_APPLY_LIGHTING, text="Apply Lighting Preset", icon="LIGHT_AREA")
                box5.separator()
                box5.label(text="Background", icon="IMAGE_PLANE")
                box5.prop(props, "background_preset", text="Preset")
                box5.operator(OPERATOR_ID_APPLY_BACKGROUND, text="Apply Background", icon="CHECKMARK")
            elif props.lighting_mode == "HDRI":
                box5.separator()
                box5.label(text="HDRI Environment", icon="WORLD")
                if props.hdri_filepath:
                    box5.label(text=f"File: {props.hdri_filepath}", icon="FILE_IMAGE")
                else:
                    box5.label(text="No HDRI loaded", icon="FILE_IMAGE")
                box5.operator(OPERATOR_ID_LOAD_HDRI, text="Load HDRI", icon="FILE_FOLDER")
                box5.prop(props, "hdri_rotation", text="Rotation")
                box5.prop(props, "hdri_brightness", text="Brightness")
                box5.operator(OPERATOR_ID_APPLY_HDRI, text="Apply HDRI", icon="CHECKMARK")
                box5.operator(OPERATOR_ID_REMOVE_HDRI, text="Remove HDRI", icon="X")
            if props.environment_status:
                box5.separator()
                box5.label(text=f"Status: {props.environment_status}")
        else:
            box5.label(text="Prepare the scene first.")

        # --- Camera & Composition ---
        layout.separator(factor=1.5)
        box6 = layout.box()
        box6.label(text="Camera & Composition", icon="CAMERA_DATA")
        if props is not None and props.scene_setup_ready:
            box6.prop(props, "camera_preset", text="Preset")
            box6.operator(OPERATOR_ID_APPLY_CAMERA_PRESET, text="Apply Camera Preset", icon="CHECKMARK")
            box6.operator(OPERATOR_ID_ZOOM_TO_FIT, text="Zoom to Fit PCB", icon="VIEWZOOM")

            box6.separator()
            box6.prop(props, "camera_focal_length", text="Focal Length")
            box6.prop(props, "use_depth_of_field", text="Depth of Field")
            if props.use_depth_of_field:
                box6.prop(props, "focus_target_mode", text="Focus")
                box6.prop(props, "camera_fstop", text="F-Stop")
            box6.operator(OPERATOR_ID_APPLY_CAMERA_SETTINGS, text="Apply Camera Settings", icon="CHECKMARK")

            box6.separator()
            box6.label(text="Reflection Surface", icon="MESH_PLANE")
            box6.prop(props, "reflection_surface", text="")
            box6.operator(OPERATOR_ID_APPLY_REFLECTION, text="Apply Reflection Plane", icon="CHECKMARK")

            # Camera status (read-only, computed locally).
            camera = bpy.data.objects.get(CAMERA_NAME)
            if camera is not None:
                lens = camera.data.lens
                dof_on = camera.data.dof.use_dof
                box6.separator()
                box6.label(text=f"Lens: {lens:.0f} mm")
                box6.label(text=f"DOF: {'On' if dof_on else 'Off'}")
            if props.camera_status:
                box6.label(text=f"Status: {props.camera_status}")
        else:
            box6.label(text="Prepare the scene first.")

        # --- Animation & Video ---
        layout.separator(factor=1.5)
        box7 = layout.box()
        box7.label(text="Animation & Video", icon="RENDER_ANIMATION")
        if props is not None and props.scene_setup_ready:
            box7.prop(props, "turntable_enabled", text="Enable Turntable")
            if props.turntable_enabled:
                box7.prop(props, "turntable_direction", text="Direction")
                box7.prop(props, "turntable_rotation_degrees", text="Rotation")
                box7.prop(props, "turntable_duration", text="Duration")
                box7.prop(props, "turntable_fps", text="Frame Rate")
                box7.prop(props, "turntable_resolution", text="Video Quality")
                box7.prop(props, "turntable_motion_style", text="Motion")
                box7.prop(props, "turntable_start_angle", text="Start Angle")

                # Calculated frame count (local, no Scene write).
                fps = int(props.turntable_fps)
                frame_count = get_turntable_frame_count(
                    props.turntable_duration, fps,
                )

                box7.separator()
                box7.prop(props, "animation_output_format", text="Output Format")
                box7.prop(props, "animation_output_directory", text="Output")
                box7.prop(props, "animation_filename", text="Filename")
                box7.prop(props, "animation_overwrite")

                box7.separator()
                box7.operator(OPERATOR_ID_SETUP_TURNTABLE, text="Setup Turntable", icon="KEYINGSET")
                box7.operator(OPERATOR_ID_PREVIEW_TURNTABLE, text="Preview Turntable", icon="PLAY")
                box7.operator(OPERATOR_ID_RENDER_TEST_FRAME, text="Render Test Frame", icon="RENDER_STILL")
                box7.operator(OPERATOR_ID_RENDER_TURNTABLE, text="Render Turntable Video", icon="RENDER_ANIMATION")
                box7.operator(OPERATOR_ID_RESET_TURNTABLE, text="Reset Turntable", icon="LOOP_BACK")

                box7.separator()
                box7.label(text=f"Estimated Frames: {frame_count}")
                if props.turntable_status:
                    box7.label(text=f"Status: {props.turntable_status}")
                if props.last_animation_output:
                    box7.label(text=f"Output: {props.last_animation_output}")
        else:
            box7.label(text="Prepare the scene first.")