"""Organized 3D View sidebar panels for PCB Studio."""

import bpy

from ..constants import (
    BACKGROUND_LIGHT_NAME,
    CAMERA_NAME,
    COLLECTION_NAME,
    EXTENSION_NAME,
    EXTENSION_VERSION,
    FILL_LIGHT_NAME,
    KEY_LIGHT_NAME,
    OPERATOR_ID_ALIGN_CAMERA_TO_VIEW,
    OPERATOR_ID_ADD_CUSTOM_LIGHT,
    OPERATOR_ID_ADD_LIGHT_CARD,
    OPERATOR_ID_APPLY_CUSTOM_LIGHT_PRESET,
    OPERATOR_ID_APPLY_FLOOR_PRESET,
    OPERATOR_ID_FLOOR_ACTION,
    OPERATOR_ID_AIM_CAMERA_PCB,
    OPERATOR_ID_AIM_CAMERA_SELECTED,
    OPERATOR_ID_APPLY_BACKGROUND,
    OPERATOR_ID_APPLY_CAMERA_PRESET,
    OPERATOR_ID_SET_BOARD_AXIS_FROM_VIEW,
    OPERATOR_ID_APPLY_CAMERA_SETTINGS,
    OPERATOR_ID_APPLY_HDRI,
    OPERATOR_ID_APPLY_LIGHTING,
    OPERATOR_ID_APPLY_MICRO_BEVEL,
    OPERATOR_ID_APPLY_REFLECTION,
    OPERATOR_ID_ASSIGN_MATERIAL,
    OPERATOR_ID_ASSIGN_ACTIVE_MATERIAL,
    OPERATOR_ID_CREATE_MATERIAL,
    OPERATOR_ID_MAKE_MATERIAL_UNIQUE,
    OPERATOR_ID_PICK_ACTIVE_MATERIAL,
    OPERATOR_ID_PICK_MATERIAL_PRESET,
    OPERATOR_ID_RESET_MATERIAL_VALUES,
    OPERATOR_ID_SELECT_SAME_MATERIAL,
    OPERATOR_ID_UPDATE_ACTIVE_MATERIAL,
    OPERATOR_ID_CAMERA_NUDGE,
    OPERATOR_ID_CREATE_PCB_SURFACE,
    OPERATOR_ID_DELETE_CUSTOM_LIGHT,
    OPERATOR_ID_IMPORT_OBJ,
    OPERATOR_ID_FIT_CAMERA_SELECTED,
    OPERATOR_ID_LOAD_HDRI,
    OPERATOR_ID_PREPARE_SCENE,
    OPERATOR_ID_PREVIEW_MATERIALS,
    OPERATOR_ID_PREVIEW_TURNTABLE,
    OPERATOR_ID_REMOVE_HDRI,
    OPERATOR_ID_REMOVE_LIGHT_CARD,
    OPERATOR_ID_REMOVE_MICRO_BEVEL,
    OPERATOR_ID_RENDER_FINAL,
    OPERATOR_ID_RENDER_LIGHTING_PREVIEW,
    OPERATOR_ID_RENDER_PREVIEW,
    OPERATOR_ID_RENDER_PROFESSIONAL,
    OPERATOR_ID_REFRESH_CYCLES_DEVICES,
    OPERATOR_ID_RENDER_TEST_FRAME,
    OPERATOR_ID_RENDER_TURNTABLE,
    OPERATOR_ID_RESET_STUDIO,
    OPERATOR_ID_RESET_CAMERA,
    OPERATOR_ID_RESET_CAMERA_TARGET,
    OPERATOR_ID_RESET_TURNTABLE,
    OPERATOR_ID_RESTORE_LIGHTS,
    OPERATOR_ID_RESTORE_CAMERA_VIEW,
    OPERATOR_ID_SAVE_CAMERA_VIEW,
    OPERATOR_ID_SET_CAMERA_MODE,
    OPERATOR_ID_SETUP_PCB_UV,
    OPERATOR_ID_SETUP_TURNTABLE,
    OPERATOR_ID_SMOOTH_ALL,
    OPERATOR_ID_SMOOTH_SELECTED,
    OPERATOR_ID_SOLO_LIGHT,
    OPERATOR_ID_STUDIO_HELPER,
    OPERATOR_ID_SYSTEM_CHECK,
    OPERATOR_ID_UPDATE_STUDIO,
    OPERATOR_ID_ZOOM_TO_FIT,
    PANEL_ID,
    PANEL_LABEL,
    PROP_SCENE_ATTR,
    RIM_LIGHT_2_NAME,
    RIM_LIGHT_NAME,
    SIDEBAR_CATEGORY,
    TOP_LIGHT_NAME,
    FRONT_LIGHT_LEFT_NAME,
    FRONT_LIGHT_RIGHT_NAME,
)

from ..utils.animation import get_turntable_frame_count
from ..utils.composition import describe_detected_board_axis
from ..utils.camera_controls import camera_animation_block_reason
from ..utils.cycles_devices import cycles_devices_from_json
from ..utils import material_compat as compat
from ..utils.materials import PRESET_DATA


def _props(context):
    return getattr(context.scene, PROP_SCENE_ATTR, None)


def _selected_pcb_count(context) -> int:
    """Count selected PCB meshes without scanning the whole collection."""
    collection = bpy.data.collections.get(COLLECTION_NAME)
    if collection is None:
        return 0
    members = collection.all_objects
    return sum(
        1 for obj in context.selected_objects
        if obj.type == "MESH" and members.get(obj.name) is not None
    )


def _disclosure(box, props, property_name: str, label: str):
    open_state = getattr(props, property_name)
    row = box.row(align=True)
    row.prop(
        props, property_name, text=label,
        icon="TRIA_DOWN" if open_state else "TRIA_RIGHT", emboss=False,
    )
    return open_state


def _solo_button(layout, light_name: str):
    operator = layout.operator(OPERATOR_ID_SOLO_LIGHT, text="Solo", icon="HIDE_OFF")
    operator.light_name = light_name


class _PCBStudioPanel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = SIDEBAR_CATEGORY


class PCBSTUDIO_UL_custom_lights(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index=0, flt_flag=0):
        row = layout.row(align=True)
        row.label(text=item.display_name or item.object_name, icon="LIGHT")
        row.label(text=item.light_type.replace("_", " ").title())
        row.prop(item, "enabled", text="", icon="HIDE_OFF" if item.enabled else "HIDE_ON")


class PCBSTUDIO_UL_light_cards(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index=0, flt_flag=0):
        row = layout.row(align=True)
        row.label(text=item.display_name or item.object_name, icon="MESH_PLANE")
        row.label(text=item.card_type.title())


class PCBSTUDIO_PT_main_panel(_PCBStudioPanel, bpy.types.Panel):
    bl_idname = PANEL_ID
    bl_label = PANEL_LABEL

    def draw(self, context):
        layout = self.layout
        props = _props(context)
        head = layout.row(align=True)
        head.label(text=f"{EXTENSION_NAME} {EXTENSION_VERSION}", icon="SCENE_DATA")
        head.operator(OPERATOR_ID_SYSTEM_CHECK, text="Check", icon="SYSTEM")
        if props is None:
            return
        status = layout.column(align=True)
        status.scale_y = 0.85
        row = status.row(align=True)
        row.label(text="PCB: " + ("Ready" if props.pcb_imported else "Not imported"))
        row.label(text=f"Selected: {_selected_pcb_count(context)}")
        row = status.row(align=True)
        row.label(text="Studio: " + ("Ready" if props.scene_setup_ready else "Not set up"))
        row.label(text="Camera: " + ("Ready" if props.camera_ready else "Not set up"))


class PCBSTUDIO_PT_import_prepare(_PCBStudioPanel, bpy.types.Panel):
    bl_idname = "PCBSTUDIO_PT_import_prepare"
    bl_label = "1. Import & Setup"
    bl_order = 1
    bl_parent_id = PANEL_ID

    def draw(self, context):
        layout = self.layout
        props = _props(context)
        layout.operator(OPERATOR_ID_IMPORT_OBJ, text="Select and Import OBJ", icon="IMPORT")
        if props is None:
            return
        if props.import_status:
            layout.label(text=props.import_status, icon="INFO")
        row = layout.row()
        row.enabled = props.pcb_imported
        row.operator_context = "INVOKE_DEFAULT"
        row.operator(OPERATOR_ID_PREPARE_SCENE, text="Prepare Scene...", icon="SETTINGS")
        if props.scene_setup_status:
            layout.label(text=props.scene_setup_status, icon="SCENE")


class PCBSTUDIO_PT_materials(_PCBStudioPanel, bpy.types.Panel):
    bl_idname = "PCBSTUDIO_PT_materials"
    bl_label = "2. Materials"
    bl_order = 2
    bl_parent_id = PANEL_ID
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        props = _props(context)
        if props is None:
            return
        if not props.pcb_imported:
            layout.label(text="Import a PCB first.", icon="INFO")
            return

        selected = _selected_pcb_count(context)
        current = bpy.data.materials.get(props.current_material_name)
        info = layout.row(align=True)
        info.label(text=f"Selected: {selected}", icon="RESTRICT_SELECT_OFF")
        if current is not None:
            info.label(text=f"{current.name} ({current.users} users)")

        active = context.active_object
        active_material = active.active_material if active is not None else None
        if compat.is_shared(active_material):
            shared_count = compat.count_material_objects(active_material)
            shared = layout.box()
            where = f"{shared_count} objects" if shared_count > 1 else "several objects"
            shared.label(text=f"'{active_material.name}' is on {where}.", icon="INFO")
            shared.label(text="Make it unique to edit it here.")
            shared.operator(OPERATOR_ID_MAKE_MATERIAL_UNIQUE, icon="DUPLICATE")

        picker = layout.box()
        picker.label(text="Material Presets")
        width = context.region.width if context.region else 0
        ui_scale = context.preferences.system.ui_scale or 1.0
        grid = picker.grid_flow(row_major=True, columns=3 if width / ui_scale >= 480 else 2,
                                even_columns=True, even_rows=True, align=True)
        first = ("BLACK_IC_PLASTIC", "PLASTIC_BLACK")
        for key in (*first, *(key for key in PRESET_DATA if key not in first)):
            preset = PRESET_DATA[key]
            op = grid.operator(OPERATOR_ID_PICK_MATERIAL_PRESET, text=preset.display_name,
                               depress=props.material_preset == key)
            op.preset = key
        if props.material_preset == "CUSTOM":
            picker.prop(props, "custom_material_name", text="Name")

        values = layout.column(align=True)
        values.prop(props, "material_base_color", text="Color")
        values.prop(props, "material_metallic", slider=True)
        values.prop(props, "material_roughness", slider=True)
        values.prop(props, "material_coat_weight", slider=True)
        if props.material_coat_weight > 0.0:
            values.prop(props, "material_coat_roughness", slider=True)
        if props.material_transmission_weight > 0.0:
            values.prop(props, "material_transmission_weight", slider=True)
            values.prop(props, "material_ior")

        actions = layout.column(align=True)
        actions.scale_y = 1.15
        actions.operator(
            OPERATOR_ID_CREATE_MATERIAL,
            text="Create or Update Material",
            icon="NODE_MATERIAL",
        )
        row = actions.row(align=True)
        assign = row.row(align=True)
        assign.enabled = selected > 0
        assign.operator(OPERATOR_ID_ASSIGN_MATERIAL, text="Assign to Selected", icon="PASTEDOWN")
        row.operator(OPERATOR_ID_RESET_MATERIAL_VALUES, text="Reset", icon="LOOP_BACK")
        row = layout.row(align=True)
        live = row.row(align=True)
        live.enabled = current is not None
        live.prop(props, "material_live_preview", toggle=True, icon="SHADING_RENDERED")
        row.operator(OPERATOR_ID_PREVIEW_MATERIALS, text="Preview Shading", icon="SHADING_TEXTURE")
        advanced = layout.box()
        if _disclosure(advanced, props, "show_material_advanced", "Advanced"):
            col = advanced.column(align=True)
            col.prop(props, "material_ior")
            col.prop(props, "material_specular", slider=True)
            col.prop(props, "material_coat_roughness", slider=True)
            col.prop(props, "material_anisotropic", slider=True)
            col.prop(props, "material_anisotropic_rotation", slider=True)
            col.prop(props, "material_transmission_weight", slider=True)
            col.prop(props, "material_emission_color", text="Emission")
            col.prop(props, "material_emission_strength")
            col.prop(props, "material_alpha", slider=True)
            col.prop(props, "material_normal_strength")
            col.prop(props, "material_bump_strength", slider=True)

        surface = layout.box()
        if _disclosure(surface, props, "show_material_surface", "Surface Detail"):
            surface.prop(props, "material_micro_detail", text="")
            if props.material_micro_detail != "OFF":
                row = surface.row(align=True)
                row.prop(props, "material_micro_amount", slider=True)
                row.prop(props, "material_micro_scale")
                surface.label(text="Applied by Create or Update.", icon="INFO")

        maps = layout.box()
        if _disclosure(maps, props, "show_material_maps", "Texture Maps"):
            col = maps.column(align=True)
            col.prop(props, "material_map_base_color", text="Color")
            col.prop(props, "material_map_roughness", text="Roughness")
            col.prop(props, "material_map_metallic", text="Metallic")
            col.prop(props, "material_map_normal", text="Normal")
            col.prop(props, "material_map_bump", text="Bump")
            col.prop(props, "material_map_emission", text="Emission")
            maps.label(text="Clear a path to remove that map again.", icon="INFO")

        tools = layout.box()
        if _disclosure(tools, props, "show_material_tools", "Material Tools"):
            active = context.active_object
            mat = active.active_material if active is not None else None
            if mat is None:
                tools.label(text="The active object has no material.", icon="INFO")
            else:
                used = compat.count_material_objects(mat)
                tools.label(text=f"{mat.name}: used by {used} PCB object(s)", icon="MATERIAL")
                if used > 1:
                    warning = tools.row()
                    warning.alert = True
                    warning.label(text="Editing changes all of them.", icon="ERROR")
            col = tools.column(align=True)
            col.enabled = mat is not None
            col.operator(OPERATOR_ID_PICK_ACTIVE_MATERIAL, icon="EYEDROPPER")
            col.operator(OPERATOR_ID_UPDATE_ACTIVE_MATERIAL, icon="FILE_REFRESH")
            col.operator(
                OPERATOR_ID_ASSIGN_ACTIVE_MATERIAL, text="Assign Active to Selected",
                icon="PASTEDOWN",
            )
            col.operator(OPERATOR_ID_SELECT_SAME_MATERIAL, icon="RESTRICT_SELECT_OFF")
            col.operator(OPERATOR_ID_MAKE_MATERIAL_UNIQUE, icon="DUPLICATE")
        if props.material_status:
            layout.label(text=props.material_status, icon="INFO")


class PCBSTUDIO_PT_studio(_PCBStudioPanel, bpy.types.Panel):
    bl_idname = "PCBSTUDIO_PT_studio"
    bl_label = "4. Studio & Background"
    bl_order = 4
    bl_parent_id = PANEL_ID
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        props = _props(context)
        if props is None or not props.scene_setup_ready:
            layout.label(text="Prepare the scene first.")
            return

        from .studio_environment import draw as draw_environment
        if draw_environment(layout, context, props):
            return

        background = layout.box()
        if _disclosure(background, props, "show_studio_background", "Background / Walls"):
            background.prop(props, "backdrop_type")
            background.prop(props, "background_preset", text="Wall Preset")
            background.prop(props, "wall_color")
            background.prop(props, "floor_color", text="Backdrop Floor Color")
            background.prop(props, "wall_roughness")
            background.prop(props, "backdrop_grain", slider=True)
            if props.backdrop_grain > 0.0:
                background.prop(props, "backdrop_grain_scale")
            background.prop(props, "background_brightness")
            for name in ("wall_distance", "wall_height", "cyclorama_radius", "studio_width", "studio_depth"):
                background.prop(props, name)
            if props.backdrop_type == "GRADIENT_CYCLORAMA" or "GRADIENT" in props.background_preset:
                background.prop(props, "background_color_2", text="Gradient Color")
                background.prop(props, "background_gradient_intensity")
                background.prop(props, "background_gradient_strength")
            background.operator(OPERATOR_ID_APPLY_BACKGROUND, text="Apply Background", icon="CHECKMARK")

        floor = layout.box()
        if _disclosure(floor, props, "show_studio_floor", "Floor"):
            floor.prop(props, "floor_mode", text="Floor Mode")
            floor.prop(props, "floor_ui_mode", expand=True)
            if props.floor_mode == "SHADOW_CATCHER" and context.scene.render.engine != "CYCLES":
                floor.label(text="Native shadow catching requires Cycles.", icon="INFO")

            if props.floor_mode == "NONE":
                floor.label(text="Product floats in the studio environment.", icon="INFO")
                op = floor.operator(OPERATOR_ID_FLOOR_ACTION, text="Enable Standard Floor", icon="ADD")
                op.action = "ENABLE"
            else:
                if props.floor_ui_mode == "SIMPLE":
                    floor.prop(props, "floor_studio_preset", text="Floor Preset")
                    op = floor.operator(OPERATOR_ID_FLOOR_ACTION, text="Apply Preset", icon="CHECKMARK")
                    op.action = "STUDIO_PRESET"
                    floor.prop(props, "floor_color", text="Floor Color")
                    floor.prop(props, "floor_roughness")
                    floor.prop(props, "floor_reflection_strength", text="Reflection", slider=True)
                    row = floor.row(align=True)
                    op = row.operator(OPERATOR_ID_FLOOR_ACTION, text="Ground Product")
                    op.action = "GROUND"
                    op = row.operator(OPERATOR_ID_FLOOR_ACTION, text="Fit Floor")
                    op.action = "FIT"
                else:
                    presets = floor.box()
                    if _disclosure(presets, props, "show_floor_presets", "Presets"):
                        presets.prop(props, "floor_studio_preset", text="Studio Floor")
                        op = presets.operator(OPERATOR_ID_FLOOR_ACTION, text="Apply Studio Preset", icon="CHECKMARK")
                        op.action = "STUDIO_PRESET"
                        if props.floor_mode == "INFINITE":
                            presets.prop(props, "infinite_studio_preset")
                            op = presets.operator(OPERATOR_ID_FLOOR_ACTION, text="Apply Infinity Preset")
                            op.action = "INFINITE_PRESET"

                    transform = floor.box()
                    if _disclosure(transform, props, "show_floor_transform", "Transform"):
                        if props.floor_mode == "CUSTOM":
                            transform.prop(props, "floor_custom_object")
                        elif props.floor_mode == "INFINITE":
                            for name in ("infinite_width", "infinite_depth", "infinite_height", "infinite_curve_radius", "floor_height", "infinite_smoothness"):
                                transform.prop(props, name)
                        else:
                            for name in ("floor_size", "floor_height", "floor_offset_x", "floor_offset_y", "floor_rotation", "floor_thickness"):
                                transform.prop(props, name)
                        row = transform.row(align=True)
                        op = row.operator(OPERATOR_ID_FLOOR_ACTION, text="Center Floor")
                        op.action = "CENTER"
                        op = row.operator(OPERATOR_ID_FLOOR_ACTION, text="Fit to Product")
                        op.action = "FIT"

                    material = floor.box()
                    if _disclosure(material, props, "show_floor_material", "Material"):
                        material.prop(props, "floor_material")
                        op = material.operator(OPERATOR_ID_FLOOR_ACTION, text="Apply Material", icon="MATERIAL")
                        op.action = "MATERIAL"
                        for name in ("floor_color", "floor_roughness", "floor_specular", "floor_metallic", "floor_bump_strength", "floor_bump_scale"):
                            material.prop(props, name)

                    reflections = floor.box()
                    if _disclosure(reflections, props, "show_floor_reflections", "Reflections"):
                        reflections.prop(props, "floor_reflection_preset")
                        op = reflections.operator(OPERATOR_ID_FLOOR_ACTION, text="Apply Reflection Preset")
                        op.action = "REFLECTION"
                        for name in ("floor_reflection_enabled", "floor_reflection_strength", "floor_reflection_roughness", "floor_reflection_blur", "floor_fresnel_strength"):
                            reflections.prop(props, name)

                    grounding = floor.box()
                    if _disclosure(grounding, props, "show_floor_grounding", "Shadows / Grounding"):
                        if props.floor_mode == "SHADOW_CATCHER":
                            grounding.prop(props, "shadow_strength")
                            grounding.prop(props, "shadow_softness")
                            grounding.prop(props, "shadow_catcher_transparent")
                            if context.scene.render.engine != "CYCLES":
                                grounding.label(text="Native shadow catching requires Cycles.", icon="INFO")
                        for name in ("floor_gap", "auto_ground_product"):
                            grounding.prop(props, name)
                        row = grounding.row(align=True)
                        op = row.operator(OPERATOR_ID_FLOOR_ACTION, text="Ground Product")
                        op.action = "GROUND"
                        op = row.operator(OPERATOR_ID_FLOOR_ACTION, text="Reset Ground")
                        op.action = "RESET_GROUND"

                    advanced = floor.box()
                    if _disclosure(advanced, props, "show_floor_advanced", "Advanced"):
                        advanced.prop(props, "floor_receive_shadows")
                        advanced.prop(props, "floor_visible_camera")
                        advanced.prop(props, "floor_brightness")
                        row = advanced.row(align=True)
                        op = row.operator(OPERATOR_ID_FLOOR_ACTION, text="Reset Floor")
                        op.action = "RESET"
                        op = row.operator(OPERATOR_ID_FLOOR_ACTION, text="Hide Floor")
                        op.action = "HIDE"

        pedestal = layout.box()
        if _disclosure(pedestal, props, "show_studio_pedestal", "Pedestal"):
            pedestal.prop(props, "stage_type", text="Enable / Mode")
            if props.stage_type in {"ROUNDED_PEDESTAL", "RAISED_PLATFORM"}:
                pedestal.prop(props, "pedestal_shape")
                for name in ("pedestal_width", "pedestal_depth", "pedestal_height", "pedestal_corner_radius", "pedestal_color", "pedestal_roughness", "pedestal_metallic"):
                    pedestal.prop(props, name)

        shadows = layout.box()
        if _disclosure(shadows, props, "show_studio_shadows", "Product Shadows"):
            shadows.prop(props, "shadow_strength", slider=True)
            shadows.prop(props, "shadow_softness", slider=True)
            shadows.prop(props, "contact_shadow")
            shadows.prop(props, "shadow_catcher_style")
            shadows.prop(props, "disable_floor_shadow")

        cards = layout.box()
        if _disclosure(cards, props, "show_light_cards", "Reflection Cards"):
            row = cards.row(align=True)
            row.prop(props, "light_card_type", text="")
            row.operator(OPERATOR_ID_ADD_LIGHT_CARD, text="Add", icon="ADD")
            cards.template_list("PCBSTUDIO_UL_light_cards", "", props, "light_cards", props, "light_card_index", rows=2)
            if props.light_cards:
                index = min(props.light_card_index, len(props.light_cards) - 1)
                card = props.light_cards[index]
                cards.prop(card, "display_name")
                cards.prop(card, "card_type")
                cards.prop(card, "position")
                cards.prop(card, "rotation")
                cards.prop(card, "scale")
                cards.prop(card, "visible_render")
                cards.operator(OPERATOR_ID_REMOVE_LIGHT_CARD, icon="TRASH")

        helpers = layout.box()
        helpers.label(text="Composition Helpers")
        row = helpers.row(align=True)
        op = row.operator(OPERATOR_ID_STUDIO_HELPER, text="Auto Center")
        op.action = "AUTO_CENTER"
        op = row.operator(OPERATOR_ID_STUDIO_HELPER, text="Fit to PCB")
        op.action = "FIT"
        row = helpers.row(align=True)
        op = row.operator(OPERATOR_ID_STUDIO_HELPER, text="Hide")
        op.action = "HIDE"
        op = row.operator(OPERATOR_ID_STUDIO_HELPER, text="Show")
        op.action = "SHOW"
        op = row.operator(OPERATOR_ID_STUDIO_HELPER, text="Lock")
        op.action = "LOCK"
        helpers.operator(OPERATOR_ID_UPDATE_STUDIO, text="Update Studio", icon="FILE_REFRESH")
        op = helpers.operator(OPERATOR_ID_STUDIO_HELPER, text="Reset Studio", icon="TRASH")
        op.action = "RESET"
        if props.environment_status:
            layout.label(text=props.environment_status, icon="INFO")


class PCBSTUDIO_PT_professional_studio(_PCBStudioPanel, bpy.types.Panel):
    bl_idname = "PCBSTUDIO_PT_professional_studio"
    bl_label = "5. Lighting"
    bl_order = 5
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = PANEL_ID

    def _draw_product_light(self, box, props, prefix: str, light_name: str):
        row = box.row(align=True)
        row.prop(props, f"{prefix}_enabled", text="Enable")
        _solo_button(row, light_name)
        box.prop(props, f"{prefix}_power")
        box.prop(props, f"{prefix}_color")
        box.prop(props, f"{prefix}_size")
        if prefix == "fill":
            box.prop(props, "fill_strength", slider=True)
        box.prop(props, f"{prefix}_azimuth")
        box.prop(props, f"{prefix}_elevation")
        box.prop(props, f"{prefix}_distance")
        box.prop(props, f"{prefix}_horizontal_offset")
        box.prop(props, f"{prefix}_vertical_offset")

    def draw(self, context):
        layout = self.layout
        props = _props(context)
        if props is None or not props.scene_setup_ready:
            layout.label(text="Prepare the scene first.")
            return
        presets = layout.box()
        if _disclosure(presets, props, "show_lighting_presets", "Lighting Presets"):
            presets.prop(props, "studio_lighting_preset", text="")
            presets.operator(OPERATOR_ID_APPLY_LIGHTING, text="Apply Complete Preset", icon="LIGHT_AREA")
        layout.prop(props, "studio_lighting_enabled")
        layout.prop(props, "master_product_brightness", slider=True)
        layout.prop(props, "lighting_contrast", slider=True)
        layout.prop(props, "shadow_softness", slider=True)

        environment = layout.box()
        if _disclosure(environment, props, "show_hdri", "HDRI Environment"):
            environment.prop(props, "hdri_mode", text="Mode")
            environment.operator(OPERATOR_ID_LOAD_HDRI, text="Load HDRI (.hdr / .exr)", icon="FILE_FOLDER")
            if props.hdri_filepath:
                environment.label(text=props.hdri_filepath, icon="FILE_IMAGE")
            else:
                environment.label(text="Free HDRIs: polyhaven.com/hdris", icon="INFO")
            environment.prop(props, "hdri_rotation")
            environment.prop(props, "hdri_brightness")
            environment.prop(props, "world_background_color")
            row = environment.row(align=True)
            row.operator(OPERATOR_ID_APPLY_HDRI, text="Apply")
            row.operator(OPERATOR_ID_REMOVE_HDRI, text="Remove", icon="X")

        product = layout.box()
        if _disclosure(product, props, "show_existing_lights", "Existing Managed Lights"):
            section = product.box()
            if _disclosure(section, props, "show_key_light", "Key Light"):
                row = section.row(align=True)
                row.prop(props, "key_enabled", text="Enable")
                _solo_button(row, KEY_LIGHT_NAME)
                section.prop(props, "key_power")
                section.prop(props, "key_use_temperature")
                section.prop(props, "key_temperature" if props.key_use_temperature else "key_color")
                for name in ("key_size", "key_azimuth", "key_elevation", "key_distance", "key_horizontal_offset", "key_vertical_offset"):
                    section.prop(props, name)
            section = product.box()
            if _disclosure(section, props, "show_fill_light", "Fill Light"):
                self._draw_product_light(section, props, "fill", FILL_LIGHT_NAME)
            section = product.box()
            if _disclosure(section, props, "show_left_rim", "Left Rim"):
                self._draw_product_light(section, props, "left_rim", RIM_LIGHT_NAME)
            section = product.box()
            if _disclosure(section, props, "show_right_rim", "Right Rim"):
                self._draw_product_light(section, props, "right_rim", RIM_LIGHT_2_NAME)
            section = product.box()
            if _disclosure(section, props, "show_top_light", "Top Strip"):
                row = section.row(align=True)
                row.prop(props, "top_light_enabled", text="Enable")
                _solo_button(row, TOP_LIGHT_NAME)
                for name in ("top_light_power", "top_light_color", "top_light_width", "top_light_length", "top_light_height", "top_light_front_back", "top_light_rotation", "highlight_position"):
                    section.prop(props, name)
            section = product.box()
            if _disclosure(section, props, "show_front_fill", "Front Fill Lights"):
                # Front-Left light
                subleft = section.box()
                subleft.label(text="Front-Left", icon="LIGHT")
                row = subleft.row(align=True)
                row.prop(props, "front_left_enabled", text="Enable")
                _solo_button(row, FRONT_LIGHT_LEFT_NAME)
                subleft.prop(props, "front_left_power")
                subleft.prop(props, "front_left_use_temperature")
                subleft.prop(props, "front_left_temperature" if props.front_left_use_temperature else "front_left_color")
                for name in ("front_left_size", "front_left_azimuth", "front_left_elevation", "front_left_distance"):
                    subleft.prop(props, name)
                # Front-Right light
                subright = section.box()
                subright.label(text="Front-Right", icon="LIGHT")
                row = subright.row(align=True)
                row.prop(props, "front_right_enabled", text="Enable")
                _solo_button(row, FRONT_LIGHT_RIGHT_NAME)
                subright.prop(props, "front_right_power")
                subright.prop(props, "front_right_use_temperature")
                subright.prop(props, "front_right_temperature" if props.front_right_use_temperature else "front_right_color")
                for name in ("front_right_size", "front_right_azimuth", "front_right_elevation", "front_right_distance"):
                    subright.prop(props, name)

        custom = layout.box()
        if _disclosure(custom, props, "show_custom_lights", "Custom Studio Lights"):
            custom.prop(props, "custom_light_preset", text="Starting Preset")
            row = custom.row(align=True)
            row.operator(OPERATOR_ID_ADD_CUSTOM_LIGHT, text="Add Light", icon="ADD")
            row.operator(OPERATOR_ID_DELETE_CUSTOM_LIGHT, text="Delete Selected", icon="TRASH")
            grid = custom.grid_flow(row_major=True, columns=2, even_columns=True, align=True)
            for preset_id, label in (
                ("LARGE_SOFTBOX", "Large Softbox"), ("SIDE_STRIP", "Side Strip"),
                ("TOP_STRIP", "Top Strip"), ("EDGE_RIM", "Edge Rim"),
                ("OVERHEAD", "Overhead"), ("ACCENT_SPOT", "Accent Spot"),
            ):
                op = grid.operator(OPERATOR_ID_APPLY_CUSTOM_LIGHT_PRESET, text=label)
                op.preset = preset_id
            custom.template_list("PCBSTUDIO_UL_custom_lights", "", props, "custom_lights", props, "custom_light_index", rows=3)
            if props.custom_lights:
                index = min(props.custom_light_index, len(props.custom_lights) - 1)
                light = props.custom_lights[index]
                custom.prop(light, "display_name")
                custom.prop(light, "light_type")
                custom.prop(light, "enabled")
                custom.prop(light, "power")
                custom.prop(light, "use_temperature")
                custom.prop(light, "temperature" if light.use_temperature else "color")
                custom.prop(light, "size")
                if light.light_type in {"STRIP", "RIM", "TOP"}:
                    custom.prop(light, "length")
                custom.prop(light, "position")
                custom.prop(light, "auto_aim")
                custom.prop(light, "rotation")
                if light.light_type == "SPOT":
                    custom.prop(light, "spot_size")
                    custom.prop(light, "spot_softness")
        background = layout.box()
        if _disclosure(background, props, "show_background_lighting", "Background Lighting"):
            background.prop(props, "background_glow_enabled")
            background.prop(props, "background_light_mode")
            if props.background_light_mode == "DUAL_GLOW":
                background.prop(props, "background_left_color")
                background.prop(props, "background_left_strength")
                background.prop(props, "background_right_color")
                background.prop(props, "background_right_strength")
            else:
                background.prop(props, "background_glow_color")
                background.prop(props, "background_glow_strength")
            for name in ("background_glow_size", "background_glow_horizontal", "background_glow_vertical", "background_glow_spread"):
                background.prop(props, name)
            _solo_button(background, BACKGROUND_LIGHT_NAME)

        row = layout.row(align=True)
        row.operator(OPERATOR_ID_UPDATE_STUDIO, text="Update Studio", icon="FILE_REFRESH")
        row.operator(OPERATOR_ID_RESTORE_LIGHTS, text="Restore Lights")
        layout.operator(OPERATOR_ID_RESET_STUDIO, icon="TRASH")
        if props.environment_status:
            layout.label(text=props.environment_status, icon="INFO")


class PCBSTUDIO_PT_pcb_realism(_PCBStudioPanel, bpy.types.Panel):
    bl_idname = "PCBSTUDIO_PT_pcb_realism"
    bl_label = "3. PCB Realism"
    bl_order = 3
    bl_parent_id = PANEL_ID
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        props = _props(context)
        if props is None or not props.pcb_imported:
            layout.label(text="Import a PCB first.")
            return
        layout.label(text=f"Selected PCB objects: {_selected_pcb_count(context)}")
        layout.prop(props, "smooth_angle")
        row = layout.row(align=True)
        row.operator(OPERATOR_ID_SMOOTH_SELECTED)
        row.operator(OPERATOR_ID_SMOOTH_ALL)
        layout.prop(props, "micro_bevel_preset")
        if props.micro_bevel_preset == "CUSTOM":
            layout.prop(props, "micro_bevel_width")
        layout.prop(props, "micro_bevel_segments")
        layout.prop(props, "micro_bevel_angle_limit")
        layout.prop(props, "realism_apply_all")
        row = layout.row(align=True)
        row.operator(OPERATOR_ID_APPLY_MICRO_BEVEL)
        row.operator(OPERATOR_ID_REMOVE_MICRO_BEVEL)

        surface = layout.box()
        if _disclosure(surface, props, "show_pcb_surface", "PCB Surface & Layers"):
            for name in ("pcb_color_preset", "pcb_solder_mask_color", "pcb_solder_mask_roughness", "pcb_solder_mask_coat", "pcb_copper_color", "pcb_copper_roughness", "pcb_copper_metallic", "pcb_silkscreen_color", "pcb_silkscreen_roughness", "pcb_silkscreen_relief", "pcb_edge_color", "pcb_edge_roughness"):
                surface.prop(props, name)
            for name in ("front_copper_mask", "front_solder_mask", "front_silkscreen_mask", "back_copper_mask", "back_solder_mask", "back_silkscreen_mask"):
                surface.prop(props, name)
            surface.label(text="Shared UV Alignment")
            for name in ("pcb_uv_rotation", "pcb_uv_scale", "pcb_uv_offset_x", "pcb_uv_offset_y"):
                surface.prop(props, name)
            surface.operator(OPERATOR_ID_SETUP_PCB_UV)
            surface.prop(props, "trace_relief_enabled")
            if props.trace_relief_enabled:
                surface.prop(props, "trace_relief_strength")
                surface.prop(props, "trace_relief_distance")
                surface.prop(props, "trace_relief_invert")
            surface.prop(props, "surface_imperfections")
            surface.operator(OPERATOR_ID_CREATE_PCB_SURFACE, icon="NODE_MATERIAL")
        if props.realism_status:
            layout.label(text=props.realism_status, icon="INFO")


class PCBSTUDIO_PT_camera(_PCBStudioPanel, bpy.types.Panel):
    bl_idname = "PCBSTUDIO_PT_camera"
    bl_label = "6. Camera Options"
    bl_order = 6
    bl_parent_id = PANEL_ID
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        props = _props(context)
        if props is None or not props.scene_setup_ready:
            layout.label(text="Prepare the scene first.")
            return
        blocked = camera_animation_block_reason()
        if blocked:
            warning = layout.box()
            warning.alert = True
            warning.label(text="Still camera locked by animation.", icon="LOCKED")
            warning.label(text="Use Reset Animation to restore still controls.")

        body = layout.column()
        body.enabled = not bool(blocked)

        body.prop(context.scene, "camera", text="Camera")
        body.prop(props, "camera_focal_length", text="Lens")
        body.operator(OPERATOR_ID_APPLY_CAMERA_SETTINGS)
        body.operator(OPERATOR_ID_ALIGN_CAMERA_TO_VIEW, text="Align Camera to Active View", icon="VIEW_CAMERA")
        body.operator("view3d.view_camera", text="View Through Camera", icon="CAMERA_DATA")

        orientation = body.box()
        orientation.label(text="Board Orientation")
        row = orientation.row(align=True)
        row.prop_enum(props, "board_orientation_mode", "AUTO", text="Automatic")
        row.prop_enum(props, "board_orientation_mode", "MANUAL", text="Declare Faces")
        if props.board_orientation_mode == "MANUAL":
            row = orientation.row(align=True)
            row.prop(props, "board_top_axis", text="Top Face")
            row.operator(
                OPERATOR_ID_SET_BOARD_AXIS_FROM_VIEW, text="From View", icon="AXIS_TOP",
            ).axis = "TOP"
            row = orientation.row(align=True)
            row.prop(props, "board_front_axis", text="Front Edge")
            row.operator(
                OPERATOR_ID_SET_BOARD_AXIS_FROM_VIEW, text="From View", icon="AXIS_FRONT",
            ).axis = "FRONT"
        else:
            orientation.label(text=describe_detected_board_axis(), icon="INFO")

        preset = body.box()
        preset.label(text="Composition Preset")
        preset.prop(props, "camera_preset", text="")
        preset.operator(OPERATOR_ID_APPLY_CAMERA_PRESET, icon="CAMERA_DATA")

        framing = body.box()
        framing.label(text="Framing & Aim")
        row = framing.row(align=True)
        row.operator(OPERATOR_ID_ZOOM_TO_FIT, text="Fit PCB", icon="VIEWZOOM")
        row.operator(OPERATOR_ID_FIT_CAMERA_SELECTED, text="Fit Selected", icon="FULLSCREEN_ENTER")
        row = framing.row(align=True)
        row.operator(OPERATOR_ID_AIM_CAMERA_PCB, text="Aim at PCB", icon="PIVOT_BOUNDBOX")
        row.operator(OPERATOR_ID_AIM_CAMERA_SELECTED, text="Aim at Selected", icon="PIVOT_ACTIVE")

        controls = body.box()
        controls.label(text="Still Camera Controls")
        row = controls.row(align=True)
        row.prop_enum(props, "camera_control_mode", "AUTO_TARGET", text="Auto Target", icon="LOCKED")
        row.prop_enum(props, "camera_control_mode", "MANUAL", text="Manual", icon="UNLOCKED")
        controls.prop(props, "camera_move_step_mode", text="Step")
        row = controls.row(align=True)
        op = row.operator(OPERATOR_ID_SET_CAMERA_MODE, text="Unlock Manual Camera", icon="UNLOCKED")
        op.mode = "MANUAL"
        op = row.operator(OPERATOR_ID_SET_CAMERA_MODE, text="Re-enable PCB Targeting", icon="LOCKED")
        op.mode = "AUTO_TARGET"

        controls.label(text="Dolly / Depth")
        row = controls.row(align=True)
        op = row.operator(OPERATOR_ID_CAMERA_NUDGE, text="Dolly In", icon="ADD")
        op.action = "DOLLY_IN"
        op = row.operator(OPERATOR_ID_CAMERA_NUDGE, text="Dolly Out", icon="REMOVE")
        op.action = "DOLLY_OUT"
        row = controls.row(align=True)
        op = row.operator(OPERATOR_ID_CAMERA_NUDGE, text="Forward")
        op.action = "FORWARD"
        op = row.operator(OPERATOR_ID_CAMERA_NUDGE, text="Back")
        op.action = "BACK"

        if _disclosure(controls, props, "show_camera_nudge", "Move, Pan and Orbit"):
            steps = controls.column(align=True)
            steps.label(text="Move Camera")
            row = steps.row(align=True)
            op = row.operator(OPERATOR_ID_CAMERA_NUDGE, text="Left", icon="TRIA_LEFT")
            op.action = "LEFT"
            op = row.operator(OPERATOR_ID_CAMERA_NUDGE, text="Right", icon="TRIA_RIGHT")
            op.action = "RIGHT"
            row = steps.row(align=True)
            op = row.operator(OPERATOR_ID_CAMERA_NUDGE, text="Up", icon="TRIA_UP")
            op.action = "UP"
            op = row.operator(OPERATOR_ID_CAMERA_NUDGE, text="Down", icon="TRIA_DOWN")
            op.action = "DOWN"

            steps.label(text="Pan (Camera + Target)")
            row = steps.row(align=True)
            op = row.operator(OPERATOR_ID_CAMERA_NUDGE, text="Left", icon="TRIA_LEFT")
            op.action = "PAN_LEFT"
            op = row.operator(OPERATOR_ID_CAMERA_NUDGE, text="Right", icon="TRIA_RIGHT")
            op.action = "PAN_RIGHT"
            row = steps.row(align=True)
            op = row.operator(OPERATOR_ID_CAMERA_NUDGE, text="Up", icon="TRIA_UP")
            op.action = "PAN_UP"
            op = row.operator(OPERATOR_ID_CAMERA_NUDGE, text="Down", icon="TRIA_DOWN")
            op.action = "PAN_DOWN"

            steps.label(text="Still Orbit (No Keyframes)")
            row = steps.row(align=True)
            op = row.operator(OPERATOR_ID_CAMERA_NUDGE, text="Orbit Left", icon="TRIA_LEFT")
            op.action = "ORBIT_LEFT"
            op = row.operator(OPERATOR_ID_CAMERA_NUDGE, text="Orbit Right", icon="TRIA_RIGHT")
            op.action = "ORBIT_RIGHT"
            row = steps.row(align=True)
            op = row.operator(OPERATOR_ID_CAMERA_NUDGE, text="Orbit Up", icon="TRIA_UP")
            op.action = "ORBIT_UP"
            op = row.operator(OPERATOR_ID_CAMERA_NUDGE, text="Orbit Down", icon="TRIA_DOWN")
            op.action = "ORBIT_DOWN"

        body.operator(OPERATOR_ID_RESET_CAMERA, icon="LOOP_BACK")

        advanced = body.box()
        row = advanced.row()
        row.prop(
            props,
            "show_camera_advanced",
            text="Advanced Camera Controls",
            icon="TRIA_DOWN" if props.show_camera_advanced else "TRIA_RIGHT",
            emboss=False,
        )
        if props.show_camera_advanced:
            advanced.label(text="Product Position (Live)")
            advanced.prop(props, "camera_azimuth")
            advanced.prop(props, "camera_elevation")
            advanced.prop(props, "camera_distance")
            advanced.prop(props, "camera_roll")
            advanced.prop(props, "camera_orbit_step")
            row = advanced.row(align=True)
            op = row.operator(OPERATOR_ID_CAMERA_NUDGE, text="Roll Left")
            op.action = "ROLL_LEFT"
            op = row.operator(OPERATOR_ID_CAMERA_NUDGE, text="Reset Roll")
            op.action = "ROLL_RESET"
            op = row.operator(OPERATOR_ID_CAMERA_NUDGE, text="Roll Right")
            op.action = "ROLL_RIGHT"

            advanced.label(text="Target Offset (Live)")
            advanced.prop(props, "camera_target_offset_x", text="X")
            advanced.prop(props, "camera_target_offset_y", text="Y")
            advanced.prop(props, "camera_target_offset_z", text="Z")
            advanced.operator(OPERATOR_ID_RESET_CAMERA_TARGET, icon="PIVOT_CURSOR")
            advanced.prop(props, "camera_fit_margin")

            row = advanced.row(align=True)
            row.operator(OPERATOR_ID_SAVE_CAMERA_VIEW, icon="BOOKMARKS")
            restore = row.row(align=True)
            restore.enabled = props.camera_has_saved_view
            restore.operator(OPERATOR_ID_RESTORE_CAMERA_VIEW, icon="RECOVER_LAST")

        camera = bpy.data.objects.get(CAMERA_NAME)
        if camera is not None:
            layout.label(
                text=(
                    f"{props.camera_control_mode.replace('_', ' ').title()} | "
                    f"{camera.data.lens:.0f} mm | DOF: "
                    f"{'On' if camera.data.dof.use_dof else 'Off'}"
                ),
                icon="CAMERA_DATA",
            )
        if props.camera_status:
            layout.label(text=props.camera_status, icon="INFO")


class PCBSTUDIO_PT_depth_of_field(_PCBStudioPanel, bpy.types.Panel):
    bl_idname = "PCBSTUDIO_PT_depth_of_field"
    bl_label = "Depth of Field"
    bl_parent_id = "PCBSTUDIO_PT_camera"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        props = _props(context)
        if props is None or not props.scene_setup_ready:
            layout.label(text="Prepare the scene first.")
            return
        layout.prop(props, "dof_preset")
        layout.prop(props, "use_depth_of_field")
        if props.use_depth_of_field:
            layout.prop(props, "focus_target_mode")
            layout.prop(props, "camera_fstop")
        layout.operator(OPERATOR_ID_APPLY_CAMERA_SETTINGS, text="Apply Depth of Field")


class PCBSTUDIO_PT_render(_PCBStudioPanel, bpy.types.Panel):
    bl_idname = "PCBSTUDIO_PT_render"
    bl_label = "8. Render"
    bl_order = 8
    bl_parent_id = PANEL_ID

    def draw(self, context):
        layout = self.layout
        props = _props(context)
        if props is None or not props.scene_setup_ready:
            layout.label(text="Prepare the scene first.")
            return
        layout.prop(props, "professional_render_engine")
        layout.prop(props, "still_format")
        if props.still_format == "CUSTOM":
            row = layout.row(align=True)
            row.prop(props, "still_custom_width")
            row.prop(props, "still_custom_height")
        layout.prop(props, "color_look")
        layout.prop(props, "color_exposure")
        if props.professional_render_engine == "PROFESSIONAL_FINAL":
            layout.prop(props, "cycles_quality")

        # The device is chosen before the render buttons, not after them.
        device_box = layout.box()
        if _disclosure(device_box, props, "show_render_device", "Render Device (GPU / CPU)"):
            device_box.prop(props, "cycles_render_device")
            if props.cycles_render_device == "GPU":
                device_box.prop(props, "cycles_gpu_backend")
                device_box.prop(props, "cycles_fallback_to_cpu")
            if props.professional_render_engine != "PROFESSIONAL_FINAL":
                device_box.label(
                    text="Device choice only affects Final Quality renders.",
                    icon="INFO",
                )
            device_box.operator(OPERATOR_ID_REFRESH_CYCLES_DEVICES, icon="FILE_REFRESH")
            detected = cycles_devices_from_json(props.cycles_detected_devices)
            if detected:
                for device in detected:
                    row = device_box.row(align=True)
                    row.label(text=device.name, icon="CHECKMARK")
                    row.label(text=f"{device.backend} / Available")
            else:
                device_box.label(text="Click Detect / Refresh Devices.", icon="INFO")
            if props.cycles_device_status:
                device_box.label(text=props.cycles_device_status, icon="INFO")

        test = layout.box()
        test.label(text="Quick Test Render", icon="RENDER_STILL")
        test.prop(props, "lighting_preview_resolution")
        test.operator(OPERATOR_ID_RENDER_LIGHTING_PREVIEW, icon="RENDER_STILL")

        final = layout.box()
        final.label(text="Final Render", icon="RENDER_RESULT")
        final.prop(props, "final_output_directory", text="Output")
        final.prop(props, "final_filename")
        final.prop(props, "overwrite_existing")
        final.operator(OPERATOR_ID_RENDER_PROFESSIONAL, icon="RENDER_RESULT")

        finishing = layout.box()
        if _disclosure(finishing, props, "show_render_finishing", "Optional Finishing"):
            finishing.prop(props, "compositor_glow")
            finishing.prop(props, "compositor_contrast")
            finishing.prop(props, "compositor_saturation")

        legacy = layout.box()
        if _disclosure(legacy, props, "show_render_legacy", "Legacy EEVEE Renders"):
            legacy.operator(OPERATOR_ID_RENDER_PREVIEW)
            legacy.prop(props, "final_render_quality")
            legacy.operator(OPERATOR_ID_RENDER_FINAL)
        if props.professional_render_status:
            layout.label(text=props.professional_render_status, icon="INFO")


class PCBSTUDIO_PT_animation(_PCBStudioPanel, bpy.types.Panel):
    bl_idname = "PCBSTUDIO_PT_animation"
    bl_label = "9. Animation"
    bl_order = 9
    bl_parent_id = PANEL_ID
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        props = _props(context)
        if props is None or not props.scene_setup_ready:
            layout.label(text="Prepare the scene first.")
            return
        layout.prop(props, "turntable_enabled", text="Enable Animation")
        if not props.turntable_enabled:
            return
        layout.prop(props, "animation_type", text="Type")
        if props.animation_type == "CINEMATIC_FLYOVER":
            layout.prop(props, "flyover_style")
            layout.prop(props, "flyover_height")
        else:
            layout.prop(props, "turntable_direction")
            layout.prop(props, "turntable_rotation_degrees")
            layout.prop(props, "turntable_start_angle")
        layout.prop(props, "turntable_duration")
        layout.prop(props, "turntable_fps")
        layout.prop(props, "turntable_resolution")
        layout.prop(props, "turntable_motion_style")
        layout.prop(props, "animation_output_format")
        layout.prop(props, "animation_output_directory", text="Output")
        layout.prop(props, "animation_filename")
        layout.prop(props, "animation_overwrite")
        layout.operator(OPERATOR_ID_SETUP_TURNTABLE, text="Setup Animation", icon="KEYINGSET")
        layout.operator(OPERATOR_ID_PREVIEW_TURNTABLE, text="Preview Animation", icon="PLAY")
        layout.operator(OPERATOR_ID_RENDER_TEST_FRAME)
        layout.operator(OPERATOR_ID_RENDER_TURNTABLE, text="Render Animation", icon="RENDER_ANIMATION")
        layout.operator(OPERATOR_ID_RESET_TURNTABLE, text="Reset Animation", icon="LOOP_BACK")
        frames = get_turntable_frame_count(props.turntable_duration, int(props.turntable_fps))
        layout.label(text=f"Estimated Frames: {frames}")
        if props.turntable_status:
            layout.label(text=props.turntable_status, icon="INFO")


PANEL_CLASSES = (
    PCBSTUDIO_UL_custom_lights,
    PCBSTUDIO_UL_light_cards,
    PCBSTUDIO_PT_main_panel,
    PCBSTUDIO_PT_import_prepare,
    PCBSTUDIO_PT_materials,
    PCBSTUDIO_PT_pcb_realism,
    PCBSTUDIO_PT_studio,
    PCBSTUDIO_PT_professional_studio,
    PCBSTUDIO_PT_camera,
    PCBSTUDIO_PT_depth_of_field,
    PCBSTUDIO_PT_animation,
    PCBSTUDIO_PT_render,
)
