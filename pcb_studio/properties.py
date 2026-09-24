"""PropertyGroup for PCB Studio import state."""

import bpy
from math import radians

from .constants import (
    ANIMATION_TYPE_ITEMS,
    ANIMATION_FORMAT_ITEMS,
    BACKGROUND_PRESET_ITEMS,
    BACKDROP_TYPE_ITEMS,
    BACKGROUND_LIGHT_MODE_ITEMS,
    BOARD_AXIS_ITEMS,
    BOARD_ORIENTATION_MODE_ITEMS,
    CAMERA_CONTROL_MODE_ITEMS,
    CAMERA_MOVE_STEP_ITEMS,
    CAMERA_PRESET_ITEMS,
    COLOR_LOOK_ITEMS,
    CUSTOM_LIGHT_PRESET_ITEMS,
    CUSTOM_LIGHT_TYPE_ITEMS,
    CYCLES_GPU_BACKEND_ITEMS,
    CYCLES_QUALITY_ITEMS,
    CYCLES_RENDER_DEVICE_ITEMS,
    DEFAULT_ANIMATION_FILENAME,
    DEFAULT_OUTPUT_FILENAME,
    FOCUS_TARGET_ITEMS,
    DOF_PRESET_ITEMS,
    FLYOVER_HEIGHT_ITEMS,
    FLYOVER_STYLE_ITEMS,
    FLOOR_PRESET_ITEMS,
    FLOOR_MODE_ITEMS,
    FLOOR_MATERIAL_ITEMS,
    FLOOR_STUDIO_PRESET_ITEMS,
    FLOOR_REFLECTION_PRESET_ITEMS,
    INFINITE_STUDIO_PRESET_ITEMS,
    LIGHTING_MODE_ITEMS,
    LIGHT_CARD_TYPE_ITEMS,
    MATERIAL_MICRO_DETAIL_ITEMS,
    PROP_GROUP_ID,
    HDRI_MODE_ITEMS,
    MICRO_BEVEL_PRESET_ITEMS,
    PCB_COLOR_PRESET_ITEMS,
    PEDESTAL_SHAPE_ITEMS,
    PREVIEW_RESOLUTION_ITEMS,
    PROFESSIONAL_RENDER_ENGINE_ITEMS,
    REFLECTION_SURFACE_ITEMS,
    RENDER_QUALITY_ITEMS,
    STUDIO_PRESET_ITEMS,
    STAGE_TYPE_ITEMS,
    STILL_FORMAT_ITEMS,
    SURFACE_IMPERFECTION_ITEMS,
    TURNTABLE_DIRECTION_ITEMS,
    TURNTABLE_FPS_ITEMS,
    TURNTABLE_MOTION_ITEMS,
    TURNTABLE_RESOLUTION_ITEMS,
    TURNTABLE_ROTATION_ITEMS,
)
from .utils.materials import (
    MATERIAL_PRESET_ITEMS,
    PRESET_DATA,
    apply_preset_to_props,
    apply_props_to_material,
    live_preview_target,
)

#: True while a preset writes many values at once, so live preview runs once.
_MATERIAL_SYNCING: bool = False


def _on_material_value_update(self, context: bpy.types.Context | None) -> None:
    """Push a changed value into the active object's own material.

    Only Principled socket default values are written; the shader graph is never
    rebuilt while a slider moves.  Does nothing unless Live Preview is on.

    The target is resolved from the selection rather than from a scene-global
    name, so dragging a value can never recolour a component the user did not
    select.  This callback deliberately creates no datablocks: when the material
    is shared, ``live_preview_target`` returns None and the write is skipped,
    leaving the split to the Make Unique operator that the panel offers.
    """
    global _MATERIAL_SYNCING
    if _MATERIAL_SYNCING or not self.material_live_preview:
        return
    mat = live_preview_target(context, self)
    if mat is None:
        return
    apply_props_to_material(mat, self)
    if mat.name != self.current_material_name:
        _MATERIAL_SYNCING = True
        try:
            self.current_material_name = mat.name
        finally:
            _MATERIAL_SYNCING = False


def _on_material_preset_update(self, context: bpy.types.Context | None) -> None:
    """Sync material UI values from the selected preset."""
    global _MATERIAL_SYNCING
    if _MATERIAL_SYNCING or self.material_preset == "CUSTOM":
        return
    if PRESET_DATA.get(self.material_preset) is None:
        return
    _MATERIAL_SYNCING = True
    try:
        apply_preset_to_props(self, self.material_preset)
    finally:
        _MATERIAL_SYNCING = False
    _on_material_value_update(self, context)


def _on_quick_studio_update(self, context: bpy.types.Context | None) -> None:
    """Refresh cheap studio values without rebuilding managed geometry."""
    if context is None or not self.scene_setup_ready:
        return
    if context.scene.get("pcbstudio_batch_update", False):
        return
    try:
        from .utils.environment import refresh_studio_values
        refresh_studio_values(context.scene, self)
    except Exception:
        # Slider callbacks must never make Blender's UI unusable. The explicit
        # Update Studio operator reports detailed failures for the same data.
        pass


def _on_environment_surface_update(self, context):
    if context is None or context.scene.get("pcbstudio_batch_update", False):
        return
    from .utils import studio_environment
    if studio_environment.enabled(context.scene):
        try:
            self.environment_status = studio_environment.update(context.scene, self)
        except (ValueError, RuntimeError) as exc:
            self.environment_status = str(exc)
    else:
        _on_quick_studio_update(self, context)


def _on_floor_update(self, context: bpy.types.Context | None) -> None:
    if context is None or not self.scene_setup_ready or context.scene.get("pcbstudio_batch_update", False):
        return
    from .utils import studio_environment
    if studio_environment.enabled(context.scene):
        _on_environment_surface_update(self, context)
        return
    try:
        from .utils.floor import update_floor_system
        update_floor_system(context.scene, self)
        if self.auto_ground_product:
            from .utils.floor import ground_product
            ground_product(context.scene, self)
    except Exception:
        pass


def _on_floor_material_update(self, context: bpy.types.Context | None) -> None:
    if context is None or not self.scene_setup_ready or context.scene.get("pcbstudio_batch_update", False):
        return
    from .utils import studio_environment
    if studio_environment.enabled(context.scene):
        _on_environment_surface_update(self, context)
        return
    try:
        from .utils.floor import update_floor_material
        update_floor_material(context.scene, self)
    except Exception:
        pass


def _on_auto_ground_update(self, context: bpy.types.Context | None) -> None:
    if not self.auto_ground_product or context is None or not self.scene_setup_ready:
        return
    try:
        from .utils.floor import ground_product
        ground_product(context.scene, self)
    except Exception:
        pass


def _on_micro_bevel_preset(self, context: bpy.types.Context | None) -> None:
    values = {
        "OFF": (0.0, 1),
        "SUBTLE": (0.0005, 2),
        "REALISTIC": (0.0012, 3),
        "STRONG": (0.0025, 4),
    }.get(self.micro_bevel_preset)
    if values is not None:
        self.micro_bevel_width = values[0]
        self.micro_bevel_segments = values[1]


def _on_pcb_color_preset(self, context: bpy.types.Context | None) -> None:
    color = {
        "GREEN": (0.025, 0.22, 0.055, 1.0),
        "BLACK": (0.012, 0.014, 0.018, 1.0),
        "BLUE": (0.018, 0.055, 0.30, 1.0),
        "RED": (0.34, 0.025, 0.02, 1.0),
        "PURPLE": (0.18, 0.025, 0.28, 1.0),
        "WHITE": (0.78, 0.80, 0.76, 1.0),
    }.get(self.pcb_color_preset)
    if color is not None:
        self.pcb_solder_mask_color = color


def _on_dof_preset(self, context: bpy.types.Context | None) -> None:
    values = {
        "OFF": (False, 8.0),
        "PRODUCT_SHARP": (True, 8.0),
        "SUBTLE": (True, 5.6),
        "MACRO": (True, 2.8),
    }.get(self.dof_preset)
    if values is not None:
        self.use_depth_of_field, self.camera_fstop = values


def _camera_callback_is_blocked(context: bpy.types.Context | None) -> bool:
    return bool(
        context is None
        or context.scene.get("pcbstudio_camera_batch_update", False)
    )


def _on_board_top_axis(self, context: bpy.types.Context | None) -> None:
    """Keep the declared front edge perpendicular to a newly chosen top face."""
    from .utils.board_orientation import perpendicular_front

    corrected = perpendicular_front(self.board_top_axis, self.board_front_axis)
    if corrected != self.board_front_axis:
        self.board_front_axis = corrected


def _on_board_front_axis(self, context: bpy.types.Context | None) -> None:
    """Reject a front edge that lies along the top face, rather than storing it.

    A parallel pair collapses the camera basis, so the nearest perpendicular
    axis is stored instead.
    """
    from .utils.board_orientation import is_perpendicular, perpendicular_front

    if not is_perpendicular(self.board_top_axis, self.board_front_axis):
        self.board_front_axis = perpendicular_front(
            self.board_top_axis, self.board_front_axis,
        )


def _on_camera_control_mode(self, context: bpy.types.Context | None) -> None:
    """Enable or mute only PCB Studio's managed camera targeting."""
    if _camera_callback_is_blocked(context):
        return
    try:
        from .utils.camera_controls import set_camera_control_mode

        self.camera_status = set_camera_control_mode(context.scene, self.camera_control_mode)
    except Exception:
        self.camera_status = "Could not change camera control mode."


def _on_camera_product_parameter(self, context: bpy.types.Context | None) -> None:
    """Apply azimuth, elevation, distance, and roll as live controls."""
    if _camera_callback_is_blocked(context):
        return
    try:
        from .utils.camera_controls import apply_product_parameters

        self.camera_status = apply_product_parameters(context.scene)
    except Exception:
        self.camera_status = "Could not update camera position."


def _on_camera_target_offset(self, context: bpy.types.Context | None) -> None:
    """Move the managed target from the PCB center using live offsets."""
    if _camera_callback_is_blocked(context):
        return
    try:
        from .utils.camera_controls import apply_target_offsets

        self.camera_status = apply_target_offsets(context.scene)
    except Exception:
        self.camera_status = "Could not update camera target."


def _on_custom_light_update(self, context: bpy.types.Context | None) -> None:
    if not self.object_name or context is None:
        return
    try:
        from .utils.studio import sync_custom_light_slot

        sync_custom_light_slot(context.scene, self)
    except Exception:
        pass


def _on_light_card_update(self, context: bpy.types.Context | None) -> None:
    if not self.object_name or context is None:
        return
    try:
        from .utils.studio import sync_light_card_slot

        sync_light_card_slot(context.scene, self)
    except Exception:
        pass


class PCBSTUDIO_PG_custom_light(bpy.types.PropertyGroup):
    object_name: bpy.props.StringProperty(default="", options={"HIDDEN"})
    display_name: bpy.props.StringProperty(name="Name", default="Studio Light", update=_on_custom_light_update)
    light_type: bpy.props.EnumProperty(name="Type", items=CUSTOM_LIGHT_TYPE_ITEMS, default="AREA", update=_on_custom_light_update)
    enabled: bpy.props.BoolProperty(name="Enabled", default=True, update=_on_custom_light_update)
    power: bpy.props.FloatProperty(name="Power", default=500.0, min=0.0, max=10000.0, update=_on_custom_light_update)
    color: bpy.props.FloatVectorProperty(name="Color", subtype="COLOR", size=3, min=0.0, max=1.0, default=(1.0, 0.95, 0.88), update=_on_custom_light_update)
    use_temperature: bpy.props.BoolProperty(name="Use Temperature", default=False, update=_on_custom_light_update)
    temperature: bpy.props.FloatProperty(name="Temperature", default=5600.0, min=1000.0, max=12000.0, update=_on_custom_light_update)
    size: bpy.props.FloatProperty(name="Size", default=1.0, min=0.01, max=20.0, update=_on_custom_light_update)
    length: bpy.props.FloatProperty(name="Length", default=2.0, min=0.01, max=30.0, update=_on_custom_light_update)
    position: bpy.props.FloatVectorProperty(name="Position", subtype="TRANSLATION", size=3, update=_on_custom_light_update)
    rotation: bpy.props.FloatVectorProperty(name="Rotation", subtype="EULER", size=3, update=_on_custom_light_update)
    auto_aim: bpy.props.BoolProperty(name="Aim at PCB Center", default=True, update=_on_custom_light_update)
    spot_size: bpy.props.FloatProperty(name="Spot Size", subtype="ANGLE", default=radians(45.0), min=radians(1.0), max=radians(179.0), update=_on_custom_light_update)
    spot_softness: bpy.props.FloatProperty(name="Spot Softness", default=0.35, min=0.0, max=1.0, update=_on_custom_light_update)


class PCBSTUDIO_PG_light_card(bpy.types.PropertyGroup):
    object_name: bpy.props.StringProperty(default="", options={"HIDDEN"})
    display_name: bpy.props.StringProperty(name="Name", default="Reflection Card", update=_on_light_card_update)
    card_type: bpy.props.EnumProperty(name="Type", items=LIGHT_CARD_TYPE_ITEMS, default="WHITE", update=_on_light_card_update)
    position: bpy.props.FloatVectorProperty(name="Position", subtype="TRANSLATION", size=3, update=_on_light_card_update)
    rotation: bpy.props.FloatVectorProperty(name="Rotation", subtype="EULER", size=3, update=_on_light_card_update)
    scale: bpy.props.FloatVectorProperty(name="Scale", subtype="XYZ", size=3, min=0.000001, default=(1.0, 1.0, 1.0), update=_on_light_card_update)
    visible_render: bpy.props.BoolProperty(name="Visible in Render", default=True, update=_on_light_card_update)
    visible_camera: bpy.props.BoolProperty(name="Visible to Camera", default=True, update=_on_light_card_update)
    color: bpy.props.FloatVectorProperty(name="White Card Color", size=4, subtype="COLOR", min=0, max=1, default=(.92,.92,.92,1), update=_on_light_card_update)
    brightness: bpy.props.FloatProperty(name="White Card Brightness", default=1, min=0, max=1, update=_on_light_card_update)


class PCBSTUDIO_PG_import_state(bpy.types.PropertyGroup):
    """Persistent UI state for PCB Studio."""

    bl_idname: str = PROP_GROUP_ID

    # --- Import properties ---
    obj_filepath: bpy.props.StringProperty(subtype="FILE_PATH", default="")
    mtl_filepath: bpy.props.StringProperty(subtype="FILE_PATH", default="")
    import_status: bpy.props.StringProperty(default="")
    imported_object_count: bpy.props.IntProperty(default=0)
    imported_material_count: bpy.props.IntProperty(default=0)
    pcb_imported: bpy.props.BoolProperty(default=False)

    # --- Scene setup properties ---
    scene_setup_ready: bpy.props.BoolProperty(default=False)
    scene_setup_status: bpy.props.StringProperty(default="")
    camera_ready: bpy.props.BoolProperty(default=False)

    # --- Render preview properties ---
    render_status: bpy.props.StringProperty(default="")
    last_render_successful: bpy.props.BoolProperty(default=False)

    # --- Material properties ---
    material_preset: bpy.props.EnumProperty(
        name="Preset", items=MATERIAL_PRESET_ITEMS, default="SOLDER_MASK_GREEN",
        description="Realistic starting values for a common PCB material",
        update=_on_material_preset_update,
    )
    material_live_preview: bpy.props.BoolProperty(
        name="Live Preview", default=False,
        description=(
            "Update the current material while you drag a slider. Only values "
            "change, the shader graph is never rebuilt"
        ),
    )
    custom_material_name: bpy.props.StringProperty(
        name="Name", default="",
        description="Material name to use with the Custom preset",
    )
    material_base_color: bpy.props.FloatVectorProperty(
        name="Base Color", subtype="COLOR", size=4, min=0.0, max=1.0,
        default=(0.043, 0.175, 0.075, 1.0),
        description="Main surface colour",
        update=_on_material_value_update,
    )
    material_metallic: bpy.props.FloatProperty(
        name="Metallic", default=0.0, min=0.0, max=1.0,
        description="0 for plastic, mask and ceramic. 1 for bare metal",
        update=_on_material_value_update,
    )
    material_roughness: bpy.props.FloatProperty(
        name="Roughness", default=0.42, min=0.0, max=1.0,
        description="0 is a mirror, 1 is completely matte",
        update=_on_material_value_update,
    )
    material_coat_weight: bpy.props.FloatProperty(
        name="Coat", default=0.0, min=0.0, max=1.0,
        description="Thin clear lacquer over the surface, as on solder mask",
        update=_on_material_value_update,
    )
    material_coat_roughness: bpy.props.FloatProperty(
        name="Coat Roughness", default=0.06, min=0.0, max=1.0,
        description="How sharp the clear coat reflections are",
        update=_on_material_value_update,
    )
    material_ior: bpy.props.FloatProperty(
        name="IOR", default=1.5, min=1.0, max=3.0,
        description="Index of refraction: 1.45 plastic, 1.52 glass, 1.9 ceramic",
        update=_on_material_value_update,
    )
    material_specular: bpy.props.FloatProperty(
        name="Specular Level", default=0.5, min=0.0, max=1.0,
        description="Strength of the basic reflection on non-metals",
        update=_on_material_value_update,
    )
    material_anisotropic: bpy.props.FloatProperty(
        name="Anisotropy", default=0.0, min=0.0, max=1.0,
        description="Stretches highlights in one direction, as on brushed metal",
        update=_on_material_value_update,
    )
    material_anisotropic_rotation: bpy.props.FloatProperty(
        name="Anisotropy Rotation", default=0.0, min=0.0, max=1.0,
        description="Direction of the brushed streaks",
        update=_on_material_value_update,
    )
    material_transmission_weight: bpy.props.FloatProperty(
        name="Transmission", default=0.0, min=0.0, max=1.0,
        description="How much light passes through, for glass and lenses",
        update=_on_material_value_update,
    )
    material_emission_color: bpy.props.FloatVectorProperty(
        name="Emission Color", subtype="COLOR", size=4, min=0.0, max=1.0,
        default=(0.0, 0.0, 0.0, 1.0),
        description="Colour of light given off, for lit LEDs and displays",
        update=_on_material_value_update,
    )
    material_emission_strength: bpy.props.FloatProperty(
        name="Emission Strength", default=0.0, min=0.0, max=50.0, soft_max=10.0,
        description="Brightness of the emitted light. 0 disables it",
        update=_on_material_value_update,
    )
    material_alpha: bpy.props.FloatProperty(
        name="Alpha", default=1.0, min=0.0, max=1.0,
        description="Surface opacity. Below 1 enables blending on this material",
        update=_on_material_value_update,
    )
    material_normal_strength: bpy.props.FloatProperty(
        name="Normal Strength", default=1.0, min=0.0, max=4.0,
        description="Strength of the normal map, applied on Create or Update",
    )
    material_bump_strength: bpy.props.FloatProperty(
        name="Bump Strength", default=0.0, min=0.0, max=1.0,
        description="Strength of the bump map, applied on Create or Update",
    )
    material_micro_detail: bpy.props.EnumProperty(
        name="Micro Detail", items=MATERIAL_MICRO_DETAIL_ITEMS, default="OFF",
        description=(
            "Very subtle procedural surface texture, added on Create or Update. "
            "Stops parts looking like flat plastic in close-ups"
        ),
    )
    material_micro_amount: bpy.props.FloatProperty(
        name="Amount", default=0.35, min=0.0, max=1.0,
        description="Strength of the micro detail. Small values are realistic",
    )
    material_micro_scale: bpy.props.FloatProperty(
        name="Scale", default=1.0, min=0.1, max=5.0,
        description="Higher values make the grain coarser",
    )
    material_map_base_color: bpy.props.StringProperty(
        name="Base Color Map", subtype="FILE_PATH", default="",
        description="Optional colour image. Leave empty to remove it",
    )
    material_map_roughness: bpy.props.StringProperty(
        name="Roughness Map", subtype="FILE_PATH", default="",
        description="Optional roughness image, loaded as Non-Color data",
    )
    material_map_metallic: bpy.props.StringProperty(
        name="Metallic Map", subtype="FILE_PATH", default="",
        description="Optional metallic image, loaded as Non-Color data",
    )
    material_map_normal: bpy.props.StringProperty(
        name="Normal Map", subtype="FILE_PATH", default="",
        description="Optional tangent space normal map",
    )
    material_map_bump: bpy.props.StringProperty(
        name="Bump Map", subtype="FILE_PATH", default="",
        description="Optional height map. Needs Bump Strength above 0",
    )
    material_map_emission: bpy.props.StringProperty(
        name="Emission Map", subtype="FILE_PATH", default="",
        description="Optional emission colour image",
    )
    show_material_advanced: bpy.props.BoolProperty(name="Advanced", default=False)
    show_material_surface: bpy.props.BoolProperty(name="Surface Detail", default=False)
    show_material_maps: bpy.props.BoolProperty(name="Texture Maps", default=False)
    show_material_tools: bpy.props.BoolProperty(name="Material Tools", default=False)
    current_material_name: bpy.props.StringProperty(default="")
    material_status: bpy.props.StringProperty(default="")

    # --- Final render properties ---
    final_render_quality: bpy.props.EnumProperty(
        items=RENDER_QUALITY_ITEMS, default="LOW_POWER",
    )
    final_output_directory: bpy.props.StringProperty(subtype="DIR_PATH", default="")
    final_filename: bpy.props.StringProperty(default=DEFAULT_OUTPUT_FILENAME)
    overwrite_existing: bpy.props.BoolProperty(default=False)
    final_render_status: bpy.props.StringProperty(default="")
    last_render_filepath: bpy.props.StringProperty(subtype="FILE_PATH", default="")

    # --- Lighting & Environment properties ---
    lighting_mode: bpy.props.EnumProperty(
        name="Lighting Mode",
        items=LIGHTING_MODE_ITEMS,
        default="STUDIO",
        update=lambda self, ctx: _on_lighting_mode_update(self, ctx),
    )
    studio_lighting_preset: bpy.props.EnumProperty(
        name="Studio Preset",
        items=STUDIO_PRESET_ITEMS,
        default="PREMIUM_DARK",
    )
    lighting_intensity: bpy.props.FloatProperty(
        name="Lighting Intensity",
        default=1.0, min=0.0, max=5.0,
        update=_on_quick_studio_update,
    )
    custom_light_preset: bpy.props.EnumProperty(name="Light Preset", items=CUSTOM_LIGHT_PRESET_ITEMS, default="LARGE_SOFTBOX")
    custom_lights: bpy.props.CollectionProperty(type=PCBSTUDIO_PG_custom_light)
    custom_light_index: bpy.props.IntProperty(default=0, min=0)
    light_card_type: bpy.props.EnumProperty(name="Card Type", items=LIGHT_CARD_TYPE_ITEMS, default="WHITE")
    light_cards: bpy.props.CollectionProperty(type=PCBSTUDIO_PG_light_card)
    light_card_index: bpy.props.IntProperty(default=0, min=0)
    shadow_softness: bpy.props.FloatProperty(
        name="Shadow Softness",
        default=1.0, min=0.25, max=3.0,
        update=_on_quick_studio_update,
    )
    background_preset: bpy.props.EnumProperty(
        name="Background Preset",
        items=BACKGROUND_PRESET_ITEMS,
        default="DARK_GRAY",
    )
    backdrop_type: bpy.props.EnumProperty(name="Backdrop Type", items=BACKDROP_TYPE_ITEMS, default="INFINITY_CYCLORAMA", update=_on_quick_studio_update)
    wall_color: bpy.props.FloatVectorProperty(name="Wall Color", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.03, 0.035, 0.045, 1.0), update=_on_environment_surface_update)
    wall_roughness: bpy.props.FloatProperty(name="Wall Roughness", default=0.72, min=0.0, max=1.0, update=_on_environment_surface_update)
    backdrop_grain: bpy.props.FloatProperty(
        name="Backdrop Grain", default=0.15, min=0.0, max=1.0, subtype="FACTOR",
        description="Fine surface tooth on the backdrop, like real seamless paper",
        update=_on_environment_surface_update,
    )
    backdrop_grain_scale: bpy.props.FloatProperty(
        name="Grain Scale", default=320.0, min=1.0, max=2000.0,
        description="Higher is a finer grain",
        update=_on_environment_surface_update,
    )
    background_brightness: bpy.props.FloatProperty(name="Background Brightness", default=1.0, min=0.0, max=5.0, update=_on_quick_studio_update)
    wall_distance: bpy.props.FloatProperty(name="Wall Distance", default=2.5, min=0.5, max=10.0, update=_on_quick_studio_update)
    wall_height: bpy.props.FloatProperty(name="Wall Height", default=4.0, min=1.0, max=12.0, update=_on_quick_studio_update)
    cyclorama_radius: bpy.props.FloatProperty(name="Curve Radius", default=1.25, min=0.1, max=5.0, update=_on_quick_studio_update)
    studio_width: bpy.props.FloatProperty(name="Studio Width", default=5.0, min=1.0, max=15.0, update=_on_quick_studio_update)
    studio_depth: bpy.props.FloatProperty(name="Studio Depth", default=4.0, min=1.0, max=15.0, update=_on_quick_studio_update)
    background_gradient_intensity: bpy.props.FloatProperty(name="Gradient Intensity", default=1.0, min=0.0, max=3.0, update=_on_quick_studio_update)
    hdri_filepath: bpy.props.StringProperty(
        name="HDRI File",
        subtype="FILE_PATH",
        default="",
    )
    hdri_rotation: bpy.props.FloatProperty(
        name="HDRI Rotation",
        default=0.0, min=radians(-180.0), max=radians(180.0),
        subtype="ANGLE",
        update=_on_quick_studio_update,
    )
    hdri_brightness: bpy.props.FloatProperty(
        name="Environment Lighting Strength",
        default=1.0, min=0.0, max=5.0,
        update=_on_quick_studio_update,
    )
    environment_status: bpy.props.StringProperty(
        name="Environment Status",
        default="",
    )

    # --- Professional Studio master controls ---
    studio_lighting_enabled: bpy.props.BoolProperty(
        name="Studio Lighting Enabled", default=True,
        update=_on_quick_studio_update,
    )
    master_product_brightness: bpy.props.FloatProperty(
        name="Master Product Brightness", default=1.0, min=0.0, max=5.0,
        update=_on_quick_studio_update,
    )
    lighting_contrast: bpy.props.FloatProperty(
        name="Lighting Contrast", default=1.0, min=0.25, max=3.0,
        update=_on_quick_studio_update,
    )

    # Key softbox.
    key_enabled: bpy.props.BoolProperty(name="Enable", default=True, update=_on_quick_studio_update)
    key_power: bpy.props.FloatProperty(name="Power", default=650.0, min=0.0, max=5000.0, update=_on_quick_studio_update)
    key_color: bpy.props.FloatVectorProperty(name="Color", subtype="COLOR", size=3, min=0.0, max=1.0, default=(1.0, 0.96, 0.90), update=_on_quick_studio_update)
    key_use_temperature: bpy.props.BoolProperty(name="Use Temperature", default=True, update=_on_quick_studio_update)
    key_temperature: bpy.props.FloatProperty(name="Kelvin", default=5600.0, min=2000.0, max=12000.0, update=_on_quick_studio_update)
    key_size: bpy.props.FloatProperty(name="Size", default=0.55, min=0.05, max=5.0, update=_on_quick_studio_update)
    key_azimuth: bpy.props.FloatProperty(name="Azimuth", subtype="ANGLE", default=radians(42.0), min=radians(-180.0), max=radians(180.0), update=_on_quick_studio_update)
    key_elevation: bpy.props.FloatProperty(name="Elevation", subtype="ANGLE", default=radians(48.0), min=radians(5.0), max=radians(89.0), update=_on_quick_studio_update)
    key_distance: bpy.props.FloatProperty(name="Distance", default=2.4, min=0.25, max=8.0, update=_on_quick_studio_update)
    key_horizontal_offset: bpy.props.FloatProperty(name="Horizontal Offset", default=0.0, min=-2.0, max=2.0, update=_on_quick_studio_update)
    key_vertical_offset: bpy.props.FloatProperty(name="Vertical Offset", default=0.0, min=-2.0, max=2.0, update=_on_quick_studio_update)

    # Fill softbox.
    fill_enabled: bpy.props.BoolProperty(name="Enable", default=True, update=_on_quick_studio_update)
    fill_power: bpy.props.FloatProperty(name="Power", default=650.0, min=0.0, max=5000.0, update=_on_quick_studio_update)
    fill_strength: bpy.props.FloatProperty(name="Fill Strength", default=0.30, min=0.0, max=1.0, update=_on_quick_studio_update)
    fill_color: bpy.props.FloatVectorProperty(name="Color", subtype="COLOR", size=3, min=0.0, max=1.0, default=(0.92, 0.96, 1.0), update=_on_quick_studio_update)
    fill_size: bpy.props.FloatProperty(name="Size", default=0.9, min=0.05, max=5.0, update=_on_quick_studio_update)
    fill_azimuth: bpy.props.FloatProperty(name="Azimuth", subtype="ANGLE", default=radians(-55.0), min=radians(-180.0), max=radians(180.0), update=_on_quick_studio_update)
    fill_elevation: bpy.props.FloatProperty(name="Elevation", subtype="ANGLE", default=radians(32.0), min=radians(5.0), max=radians(89.0), update=_on_quick_studio_update)
    fill_distance: bpy.props.FloatProperty(name="Distance", default=2.7, min=0.25, max=8.0, update=_on_quick_studio_update)
    fill_horizontal_offset: bpy.props.FloatProperty(name="Horizontal Offset", default=0.0, min=-2.0, max=2.0, update=_on_quick_studio_update)
    fill_vertical_offset: bpy.props.FloatProperty(name="Vertical Offset", default=0.0, min=-2.0, max=2.0, update=_on_quick_studio_update)

    # Left and right rim strips.
    left_rim_enabled: bpy.props.BoolProperty(name="Enable", default=True, update=_on_quick_studio_update)
    left_rim_power: bpy.props.FloatProperty(name="Power", default=520.0, min=0.0, max=5000.0, update=_on_quick_studio_update)
    left_rim_color: bpy.props.FloatVectorProperty(name="Color", subtype="COLOR", size=3, min=0.0, max=1.0, default=(0.72, 0.84, 1.0), update=_on_quick_studio_update)
    left_rim_size: bpy.props.FloatProperty(name="Size", default=0.75, min=0.05, max=5.0, update=_on_quick_studio_update)
    left_rim_azimuth: bpy.props.FloatProperty(name="Angle", subtype="ANGLE", default=radians(-135.0), min=radians(-180.0), max=radians(180.0), update=_on_quick_studio_update)
    left_rim_elevation: bpy.props.FloatProperty(name="Height", subtype="ANGLE", default=radians(35.0), min=radians(5.0), max=radians(89.0), update=_on_quick_studio_update)
    left_rim_distance: bpy.props.FloatProperty(name="Distance", default=2.0, min=0.25, max=8.0, update=_on_quick_studio_update)
    left_rim_horizontal_offset: bpy.props.FloatProperty(name="Horizontal Offset", default=0.0, min=-2.0, max=2.0, update=_on_quick_studio_update)
    left_rim_vertical_offset: bpy.props.FloatProperty(name="Vertical Offset", default=0.0, min=-2.0, max=2.0, update=_on_quick_studio_update)
    right_rim_enabled: bpy.props.BoolProperty(name="Enable", default=False, update=_on_quick_studio_update)
    right_rim_power: bpy.props.FloatProperty(name="Power", default=460.0, min=0.0, max=5000.0, update=_on_quick_studio_update)
    right_rim_color: bpy.props.FloatVectorProperty(name="Color", subtype="COLOR", size=3, min=0.0, max=1.0, default=(1.0, 0.82, 0.62), update=_on_quick_studio_update)
    right_rim_size: bpy.props.FloatProperty(name="Size", default=0.75, min=0.05, max=5.0, update=_on_quick_studio_update)
    right_rim_azimuth: bpy.props.FloatProperty(name="Angle", subtype="ANGLE", default=radians(135.0), min=radians(-180.0), max=radians(180.0), update=_on_quick_studio_update)
    right_rim_elevation: bpy.props.FloatProperty(name="Height", subtype="ANGLE", default=radians(35.0), min=radians(5.0), max=radians(89.0), update=_on_quick_studio_update)
    right_rim_distance: bpy.props.FloatProperty(name="Distance", default=2.0, min=0.25, max=8.0, update=_on_quick_studio_update)
    right_rim_horizontal_offset: bpy.props.FloatProperty(name="Horizontal Offset", default=0.0, min=-2.0, max=2.0, update=_on_quick_studio_update)
    right_rim_vertical_offset: bpy.props.FloatProperty(name="Vertical Offset", default=0.0, min=-2.0, max=2.0, update=_on_quick_studio_update)

    # Long rectangular top strip.
    top_light_enabled: bpy.props.BoolProperty(name="Enable", default=False, update=_on_quick_studio_update)
    top_light_power: bpy.props.FloatProperty(name="Power", default=420.0, min=0.0, max=5000.0, update=_on_quick_studio_update)
    top_light_color: bpy.props.FloatVectorProperty(name="Color", subtype="COLOR", size=3, min=0.0, max=1.0, default=(1.0, 0.98, 0.94), update=_on_quick_studio_update)
    top_light_width: bpy.props.FloatProperty(name="Width", default=0.35, min=0.02, max=4.0, update=_on_quick_studio_update)
    top_light_length: bpy.props.FloatProperty(name="Length", default=2.5, min=0.05, max=8.0, update=_on_quick_studio_update)
    top_light_height: bpy.props.FloatProperty(name="Height", default=1.8, min=0.25, max=8.0, update=_on_quick_studio_update)
    top_light_front_back: bpy.props.FloatProperty(name="Front / Back", default=-0.15, min=-2.0, max=2.0, update=_on_quick_studio_update)
    top_light_rotation: bpy.props.FloatProperty(name="Rotation", subtype="ANGLE", default=radians(18.0), min=radians(-180.0), max=radians(180.0), update=_on_quick_studio_update)

    # Front fill lights - left and right for black component detail.
    front_left_enabled: bpy.props.BoolProperty(name="Enable", default=False, update=_on_quick_studio_update)
    front_left_power: bpy.props.FloatProperty(name="Power", default=350.0, min=0.0, max=5000.0, update=_on_quick_studio_update)
    front_left_color: bpy.props.FloatVectorProperty(name="Color", subtype="COLOR", size=3, min=0.0, max=1.0, default=(0.98, 0.98, 1.0), update=_on_quick_studio_update)
    front_left_use_temperature: bpy.props.BoolProperty(name="Use Temperature", default=True, update=_on_quick_studio_update)
    front_left_temperature: bpy.props.FloatProperty(name="Kelvin", default=5400.0, min=2000.0, max=12000.0, update=_on_quick_studio_update)
    front_left_size: bpy.props.FloatProperty(name="Size", default=1.2, min=0.05, max=5.0, update=_on_quick_studio_update)
    front_left_azimuth: bpy.props.FloatProperty(name="Azimuth", subtype="ANGLE", default=radians(-35.0), min=radians(-180.0), max=radians(180.0), update=_on_quick_studio_update)
    front_left_elevation: bpy.props.FloatProperty(name="Elevation", subtype="ANGLE", default=radians(32.0), min=radians(5.0), max=radians(89.0), update=_on_quick_studio_update)
    front_left_distance: bpy.props.FloatProperty(name="Distance", default=2.0, min=0.25, max=8.0, update=_on_quick_studio_update)

    front_right_enabled: bpy.props.BoolProperty(name="Enable", default=False, update=_on_quick_studio_update)
    front_right_power: bpy.props.FloatProperty(name="Power", default=350.0, min=0.0, max=5000.0, update=_on_quick_studio_update)
    front_right_color: bpy.props.FloatVectorProperty(name="Color", subtype="COLOR", size=3, min=0.0, max=1.0, default=(0.98, 0.98, 1.0), update=_on_quick_studio_update)
    front_right_use_temperature: bpy.props.BoolProperty(name="Use Temperature", default=True, update=_on_quick_studio_update)
    front_right_temperature: bpy.props.FloatProperty(name="Kelvin", default=5400.0, min=2000.0, max=12000.0, update=_on_quick_studio_update)
    front_right_size: bpy.props.FloatProperty(name="Size", default=1.2, min=0.05, max=5.0, update=_on_quick_studio_update)
    front_right_azimuth: bpy.props.FloatProperty(name="Azimuth", subtype="ANGLE", default=radians(35.0), min=radians(-180.0), max=radians(180.0), update=_on_quick_studio_update)
    front_right_elevation: bpy.props.FloatProperty(name="Elevation", subtype="ANGLE", default=radians(32.0), min=radians(5.0), max=radians(89.0), update=_on_quick_studio_update)
    front_right_distance: bpy.props.FloatProperty(name="Distance", default=2.0, min=0.25, max=8.0, update=_on_quick_studio_update)

    highlight_position: bpy.props.FloatProperty(name="Highlight Position", default=0.0, min=-1.0, max=1.0, update=_on_quick_studio_update)

    # Background accent lights are independent from product lights.
    background_light_mode: bpy.props.EnumProperty(name="Background Light Mode", items=BACKGROUND_LIGHT_MODE_ITEMS, default="CENTER_GLOW", update=_on_quick_studio_update)
    background_glow_enabled: bpy.props.BoolProperty(name="Enable Background Glow", default=True, update=_on_quick_studio_update)
    background_glow_color: bpy.props.FloatVectorProperty(name="Glow Color", subtype="COLOR", size=3, min=0.0, max=1.0, default=(0.02, 0.16, 1.0), update=_on_quick_studio_update)
    background_glow_strength: bpy.props.FloatProperty(name="Glow Strength", default=350.0, min=0.0, max=5000.0, update=_on_quick_studio_update)
    background_glow_size: bpy.props.FloatProperty(name="Glow Size", default=1.4, min=0.05, max=8.0, update=_on_quick_studio_update)
    background_glow_horizontal: bpy.props.FloatProperty(name="Horizontal Position", default=0.0, min=-2.0, max=2.0, update=_on_quick_studio_update)
    background_glow_vertical: bpy.props.FloatProperty(name="Vertical Position", default=0.45, min=-1.0, max=3.0, update=_on_quick_studio_update)
    background_glow_spread: bpy.props.FloatProperty(name="Spread", default=1.0, min=0.1, max=4.0, update=_on_quick_studio_update)
    background_left_color: bpy.props.FloatVectorProperty(name="Left Background Color", subtype="COLOR", size=3, min=0.0, max=1.0, default=(0.02, 0.12, 1.0), update=_on_quick_studio_update)
    background_right_color: bpy.props.FloatVectorProperty(name="Right Background Color", subtype="COLOR", size=3, min=0.0, max=1.0, default=(1.0, 0.16, 0.02), update=_on_quick_studio_update)
    background_left_strength: bpy.props.FloatProperty(name="Left Strength", default=320.0, min=0.0, max=5000.0, update=_on_quick_studio_update)
    background_right_strength: bpy.props.FloatProperty(name="Right Strength", default=260.0, min=0.0, max=5000.0, update=_on_quick_studio_update)

    # Procedural cyclorama material.
    background_color: bpy.props.FloatVectorProperty(name="Background Color", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.008, 0.012, 0.022, 1.0), update=_on_quick_studio_update)
    background_color_2: bpy.props.FloatVectorProperty(name="Background Color 2", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.025, 0.055, 0.16, 1.0), update=_on_environment_surface_update)
    background_gradient_strength: bpy.props.FloatProperty(name="Gradient Strength", default=0.7, min=0.0, max=1.0, update=_on_environment_surface_update)
    background_gradient_position: bpy.props.FloatProperty(name="Gradient Position", default=0.5, min=0.0, max=1.0, update=_on_environment_surface_update)
    background_gradient_rotation: bpy.props.FloatProperty(name="Gradient Rotation", subtype="ANGLE", default=0.0, min=radians(-180.0), max=radians(180.0), update=_on_quick_studio_update)
    background_gradient_scale: bpy.props.FloatProperty(name="Gradient Scale", default=1.0, min=0.1, max=10.0, update=_on_quick_studio_update)
    background_halo_center_x: bpy.props.FloatProperty(name="Halo Center X", default=0.5, min=-1.0, max=2.0, update=_on_environment_surface_update)
    background_halo_center_y: bpy.props.FloatProperty(name="Halo Center Y", default=0.5, min=-1.0, max=2.0, update=_on_environment_surface_update)
    background_halo_radius: bpy.props.FloatProperty(name="Halo Radius", default=0.65, min=0.05, max=4.0, update=_on_quick_studio_update)

    # HDRI remains independent of the physical studio and product lights.
    hdri_mode: bpy.props.EnumProperty(name="HDRI Mode", items=HDRI_MODE_ITEMS, default="OFF", update=_on_quick_studio_update)
    world_background_color: bpy.props.FloatVectorProperty(name="World Color", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.004, 0.005, 0.008, 1.0), update=_on_quick_studio_update)

    # Floor and optional stage.
    floor_ui_mode: bpy.props.EnumProperty(name="Controls", items=(("SIMPLE", "Simple", "Essential beginner controls"), ("ADVANCED", "Advanced", "All professional controls")), default="SIMPLE")
    floor_mode: bpy.props.EnumProperty(name="Floor Mode", items=FLOOR_MODE_ITEMS, default="STANDARD", update=_on_floor_update)
    floor_material: bpy.props.EnumProperty(name="Floor Material", items=FLOOR_MATERIAL_ITEMS, default="SOFT_STUDIO")
    floor_studio_preset: bpy.props.EnumProperty(name="Studio Floor Preset", items=FLOOR_STUDIO_PRESET_ITEMS, default="SOFT_REFLECTIVE")
    floor_reflection_preset: bpy.props.EnumProperty(name="Reflection Preset", items=FLOOR_REFLECTION_PRESET_ITEMS, default="PRODUCT")
    infinite_studio_preset: bpy.props.EnumProperty(name="Infinity Preset", items=INFINITE_STUDIO_PRESET_ITEMS, default="WHITE")
    floor_custom_object: bpy.props.PointerProperty(name="Custom Floor", type=bpy.types.Object, update=_on_floor_update)
    floor_color: bpy.props.FloatVectorProperty(name="Base Color", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.018, 0.022, 0.032, 1.0), update=_on_floor_material_update)
    floor_roughness: bpy.props.FloatProperty(name="Roughness", default=0.32, min=0.0, max=1.0, update=_on_floor_material_update)
    floor_specular: bpy.props.FloatProperty(name="Specular", default=0.5, min=0.0, max=1.0, update=_on_floor_material_update)
    floor_metallic: bpy.props.FloatProperty(name="Metallic", default=0.05, min=0.0, max=1.0, update=_on_floor_material_update)
    floor_reflection_strength: bpy.props.FloatProperty(name="Reflection Strength", default=0.65, min=0.0, max=1.0, update=_on_floor_material_update)
    floor_reflection_enabled: bpy.props.BoolProperty(name="Enable Reflections", default=True, update=_on_floor_material_update)
    floor_reflection_roughness: bpy.props.FloatProperty(name="Reflection Roughness", default=0.25, min=0.0, max=1.0, update=_on_floor_material_update)
    floor_reflection_blur: bpy.props.FloatProperty(name="Reflection Blur / Softness", default=0.15, min=0.0, max=1.0, update=_on_floor_material_update)
    floor_fresnel_strength: bpy.props.FloatProperty(name="Fresnel Strength", default=0.5, min=0.0, max=1.0, update=_on_floor_material_update)
    floor_bump_strength: bpy.props.FloatProperty(name="Bump Strength", default=0.0, min=0.0, max=2.0, update=_on_floor_material_update)
    floor_bump_scale: bpy.props.FloatProperty(name="Bump Scale", default=12.0, min=0.1, max=500.0, update=_on_floor_material_update)
    floor_brightness: bpy.props.FloatProperty(name="Floor Brightness", default=1.0, min=0.0, max=3.0, update=_on_floor_material_update)
    floor_preset: bpy.props.EnumProperty(name="Floor Preset", items=FLOOR_PRESET_ITEMS, default="PREMIUM_SATIN")
    floor_size: bpy.props.FloatProperty(name="Floor Size", default=3.0, min=1.0, max=50.0, update=_on_floor_update)
    floor_height: bpy.props.FloatProperty(name="Floor Height / Z Offset", default=-0.005, min=-10.0, max=10.0, update=_on_floor_update)
    floor_offset_x: bpy.props.FloatProperty(name="X Offset", default=0.0, update=_on_floor_update)
    floor_offset_y: bpy.props.FloatProperty(name="Y Offset", default=0.0, update=_on_floor_update)
    floor_rotation: bpy.props.FloatProperty(name="Rotation", subtype="ANGLE", default=0.0, update=_on_floor_update)
    floor_thickness: bpy.props.FloatProperty(name="Floor Thickness", default=0.0, min=0.0, max=2.0, update=_on_floor_update)
    floor_receive_shadows: bpy.props.BoolProperty(name="Cast Shadows (Cycles)", default=True, update=_on_floor_update)
    floor_visible_camera: bpy.props.BoolProperty(name="Visible to Camera", default=True, update=_on_floor_update)
    floor_bevel_enabled: bpy.props.BoolProperty(name="Subtle Floor Bevel", default=False, update=_on_quick_studio_update)
    shadow_strength: bpy.props.FloatProperty(name="Shadow Strength", default=1.0, min=0.0, max=2.0, update=_on_quick_studio_update)
    contact_shadow: bpy.props.BoolProperty(name="Contact Shadow", default=True, update=_on_quick_studio_update)
    shadow_catcher_style: bpy.props.BoolProperty(name="Shadow Catcher Style", default=False, update=_on_quick_studio_update)
    disable_floor_shadow: bpy.props.BoolProperty(name="Disable Floor Shadow", default=False, update=_on_quick_studio_update)
    shadow_color: bpy.props.FloatVectorProperty(name="Shadow Color", subtype="COLOR", size=3, min=0.0, max=1.0, default=(0.0, 0.0, 0.0), update=_on_floor_material_update)
    shadow_catcher_transparent: bpy.props.BoolProperty(name="Transparent Background", default=True, update=_on_floor_update)
    contact_shadow_strength: bpy.props.FloatProperty(name="Contact Shadow Strength", default=1.0, min=0.0, max=2.0, update=_on_floor_update)
    contact_shadow_softness: bpy.props.FloatProperty(name="Contact Shadow Softness", default=0.5, min=0.0, max=3.0, update=_on_floor_update)
    shadow_radius: bpy.props.FloatProperty(name="Shadow Radius", default=0.15, min=0.0, max=5.0, update=_on_floor_update)
    shadow_density: bpy.props.FloatProperty(name="Shadow Density", default=1.0, min=0.0, max=2.0, update=_on_floor_update)
    floor_gap: bpy.props.FloatProperty(name="Floor Gap", default=0.0, min=-1.0, max=1.0, update=_on_floor_update)
    auto_ground_product: bpy.props.BoolProperty(name="Auto Ground Product", default=False, update=_on_auto_ground_update)
    infinite_width: bpy.props.FloatProperty(name="Studio Width", default=5.0, min=1.0, max=50.0, update=_on_floor_update)
    infinite_depth: bpy.props.FloatProperty(name="Studio Depth", default=5.0, min=1.0, max=50.0, update=_on_floor_update)
    infinite_height: bpy.props.FloatProperty(name="Backdrop Height", default=4.0, min=1.0, max=50.0, update=_on_floor_update)
    infinite_curve_radius: bpy.props.FloatProperty(name="Curve Radius", default=1.25, min=0.05, max=20.0, update=_on_floor_update)
    infinite_smoothness: bpy.props.IntProperty(name="Smoothness", default=24, min=4, max=64, update=_on_floor_update)
    stage_type: bpy.props.EnumProperty(name="Stage Type", items=STAGE_TYPE_ITEMS, default="FLOOR", update=_on_quick_studio_update)
    pedestal_shape: bpy.props.EnumProperty(name="Shape", items=PEDESTAL_SHAPE_ITEMS, default="ROUNDED_SQUARE", update=_on_quick_studio_update)
    pedestal_width: bpy.props.FloatProperty(name="Width", default=1.35, min=1.0, max=4.0, update=_on_quick_studio_update)
    pedestal_depth: bpy.props.FloatProperty(name="Depth", default=1.35, min=1.0, max=4.0, update=_on_quick_studio_update)
    pedestal_height: bpy.props.FloatProperty(name="Height", default=0.12, min=0.01, max=1.0, update=_on_quick_studio_update)
    pedestal_corner_radius: bpy.props.FloatProperty(name="Corner Radius", default=0.08, min=0.0, max=0.5, update=_on_quick_studio_update)
    pedestal_color: bpy.props.FloatVectorProperty(name="Color", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.025, 0.03, 0.045, 1.0), update=_on_environment_surface_update)
    pedestal_roughness: bpy.props.FloatProperty(name="Roughness", default=0.28, min=0.0, max=1.0, update=_on_environment_surface_update)
    pedestal_metallic: bpy.props.FloatProperty(name="Metallic", default=0.0, min=0.0, max=1.0, update=_on_environment_surface_update)

    # Color and restrained finishing.
    color_look: bpy.props.EnumProperty(name="Color Look", items=COLOR_LOOK_ITEMS, default="PRODUCT", update=_on_quick_studio_update)
    color_exposure: bpy.props.FloatProperty(name="Exposure", default=0.0, min=-5.0, max=5.0, update=_on_quick_studio_update)
    compositor_vignette: bpy.props.FloatProperty(name="Vignette", default=0.0, min=0.0, max=1.0)
    compositor_glow: bpy.props.FloatProperty(name="Mild Highlight Glow", default=0.0, min=0.0, max=1.0)
    compositor_contrast: bpy.props.FloatProperty(name="Contrast", default=1.0, min=0.5, max=1.5)
    compositor_saturation: bpy.props.FloatProperty(name="Saturation", default=1.0, min=0.0, max=2.0)

    # Professional still rendering. Existing animation settings stay separate.
    professional_render_engine: bpy.props.EnumProperty(name="Render Engine Mode", items=PROFESSIONAL_RENDER_ENGINE_ITEMS, default="FAST_PREVIEW")
    cycles_quality: bpy.props.EnumProperty(name="Cycles Quality", items=CYCLES_QUALITY_ITEMS, default="HIGH")
    cycles_render_device: bpy.props.EnumProperty(
        name="Render Device", items=CYCLES_RENDER_DEVICE_ITEMS, default="AUTO",
    )
    cycles_gpu_backend: bpy.props.EnumProperty(
        name="GPU Backend", items=CYCLES_GPU_BACKEND_ITEMS, default="AUTO",
    )
    cycles_fallback_to_cpu: bpy.props.BoolProperty(
        name="Fallback to CPU if GPU unavailable", default=True,
    )
    cycles_detected_devices: bpy.props.StringProperty(default="", options={"HIDDEN"})
    cycles_device_status: bpy.props.StringProperty(name="Cycles Device Status", default="")
    still_format: bpy.props.EnumProperty(name="Image Format", items=STILL_FORMAT_ITEMS, default="HD_LANDSCAPE")
    still_custom_width: bpy.props.IntProperty(name="Width", default=1920, min=64, max=16384)
    still_custom_height: bpy.props.IntProperty(name="Height", default=1080, min=64, max=16384)
    lighting_preview_resolution: bpy.props.EnumProperty(name="Preview Resolution", items=PREVIEW_RESOLUTION_ITEMS, default="50")
    professional_render_status: bpy.props.StringProperty(name="Professional Render Status", default="")

    # PCB realism and surface-layer controls.
    smooth_angle: bpy.props.FloatProperty(name="Preserve Edges Above", subtype="ANGLE", default=radians(35.0), min=0.0, max=radians(180.0))
    realism_apply_all: bpy.props.BoolProperty(name="Apply to All Components", default=False)
    micro_bevel_preset: bpy.props.EnumProperty(name="Micro Bevel", items=MICRO_BEVEL_PRESET_ITEMS, default="REALISTIC", update=_on_micro_bevel_preset)
    micro_bevel_width: bpy.props.FloatProperty(name="Custom Width", default=0.0012, min=0.0, max=1.0)
    micro_bevel_segments: bpy.props.IntProperty(name="Segments", default=3, min=1, max=8)
    micro_bevel_angle_limit: bpy.props.FloatProperty(name="Angle Limit", subtype="ANGLE", default=radians(30.0), min=0.0, max=radians(180.0))
    pcb_color_preset: bpy.props.EnumProperty(name="Solder Mask", items=PCB_COLOR_PRESET_ITEMS, default="GREEN", update=_on_pcb_color_preset)
    pcb_solder_mask_color: bpy.props.FloatVectorProperty(name="Solder Mask Color", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.025, 0.22, 0.055, 1.0))
    pcb_solder_mask_roughness: bpy.props.FloatProperty(name="Solder Mask Roughness", default=0.32, min=0.0, max=1.0)
    pcb_solder_mask_coat: bpy.props.FloatProperty(name="Solder Mask Coat", default=0.22, min=0.0, max=1.0)
    pcb_copper_color: bpy.props.FloatVectorProperty(name="Copper Color", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.82, 0.32, 0.08, 1.0))
    pcb_copper_roughness: bpy.props.FloatProperty(name="Copper Roughness", default=0.24, min=0.0, max=1.0)
    pcb_copper_metallic: bpy.props.FloatProperty(name="Copper Metallic", default=1.0, min=0.0, max=1.0)
    pcb_silkscreen_color: bpy.props.FloatVectorProperty(name="Silkscreen Color", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.88, 0.88, 0.82, 1.0))
    pcb_silkscreen_roughness: bpy.props.FloatProperty(name="Silkscreen Roughness", default=0.55, min=0.0, max=1.0)
    pcb_silkscreen_relief: bpy.props.FloatProperty(name="Silkscreen Relief", default=0.04, min=0.0, max=0.25)
    pcb_edge_color: bpy.props.FloatVectorProperty(name="PCB Edge Color", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.30, 0.20, 0.08, 1.0))
    pcb_edge_roughness: bpy.props.FloatProperty(name="PCB Edge Roughness", default=0.62, min=0.0, max=1.0)
    front_copper_mask: bpy.props.StringProperty(name="Front Copper Mask", subtype="FILE_PATH", default="")
    front_solder_mask: bpy.props.StringProperty(name="Front Solder Mask", subtype="FILE_PATH", default="")
    front_silkscreen_mask: bpy.props.StringProperty(name="Front Silkscreen", subtype="FILE_PATH", default="")
    back_copper_mask: bpy.props.StringProperty(name="Back Copper Mask", subtype="FILE_PATH", default="")
    back_solder_mask: bpy.props.StringProperty(name="Back Solder Mask", subtype="FILE_PATH", default="")
    back_silkscreen_mask: bpy.props.StringProperty(name="Back Silkscreen", subtype="FILE_PATH", default="")
    pcb_uv_rotation: bpy.props.FloatProperty(name="UV Rotation", subtype="ANGLE", default=0.0, min=radians(-180.0), max=radians(180.0))
    pcb_uv_scale: bpy.props.FloatProperty(name="UV Scale", default=1.0, min=0.01, max=20.0)
    pcb_uv_offset_x: bpy.props.FloatProperty(name="UV Offset X", default=0.0, min=-10.0, max=10.0)
    pcb_uv_offset_y: bpy.props.FloatProperty(name="UV Offset Y", default=0.0, min=-10.0, max=10.0)
    trace_relief_enabled: bpy.props.BoolProperty(name="Enable Trace Relief", default=False)
    trace_relief_strength: bpy.props.FloatProperty(name="Trace Relief Strength", default=0.10, min=0.0, max=1.0)
    trace_relief_distance: bpy.props.FloatProperty(name="Trace Relief Distance", default=0.00015, min=0.0, max=0.01, precision=5)
    trace_relief_invert: bpy.props.BoolProperty(name="Invert Trace Relief", default=False)
    surface_imperfections: bpy.props.EnumProperty(name="Surface Imperfections", items=SURFACE_IMPERFECTION_ITEMS, default="CLEAN")
    realism_status: bpy.props.StringProperty(name="PCB Realism Status", default="")
    # Panel organization.
    show_product_lighting: bpy.props.BoolProperty(name="Product Lighting", default=True)
    show_key_light: bpy.props.BoolProperty(name="Key Light", default=True)
    show_fill_light: bpy.props.BoolProperty(name="Fill Light", default=False)
    show_left_rim: bpy.props.BoolProperty(name="Left Rim", default=False)
    show_right_rim: bpy.props.BoolProperty(name="Right Rim", default=False)
    show_front_fill: bpy.props.BoolProperty(name="Front Fill Lights", default=False)

    show_top_light: bpy.props.BoolProperty(name="Top Strip", default=False)
    show_background_lighting: bpy.props.BoolProperty(name="Background Lighting", default=True)
    show_backdrop: bpy.props.BoolProperty(name="Backdrop", default=False)
    show_pcb_surface: bpy.props.BoolProperty(name="PCB Surface", default=False)
    show_studio_background: bpy.props.BoolProperty(name="Background / Walls", default=True)
    show_studio_floor: bpy.props.BoolProperty(name="Floor", default=True)
    show_floor_presets: bpy.props.BoolProperty(name="Presets", default=True)
    show_floor_transform: bpy.props.BoolProperty(name="Transform", default=True)
    show_floor_material: bpy.props.BoolProperty(name="Material", default=True)
    show_floor_reflections: bpy.props.BoolProperty(name="Reflections", default=False)
    show_floor_grounding: bpy.props.BoolProperty(name="Shadows / Grounding", default=False)
    show_floor_advanced: bpy.props.BoolProperty(name="Advanced", default=False)
    show_studio_pedestal: bpy.props.BoolProperty(name="Pedestal", default=False)
    show_studio_shadows: bpy.props.BoolProperty(name="Shadows", default=False)
    show_lighting_presets: bpy.props.BoolProperty(name="Lighting Presets", default=True)
    show_existing_lights: bpy.props.BoolProperty(name="Existing Managed Lights", default=False)
    show_custom_lights: bpy.props.BoolProperty(name="Custom Studio Lights", default=False)
    show_light_cards: bpy.props.BoolProperty(name="Reflection Cards", default=False)
    show_hdri: bpy.props.BoolProperty(name="HDRI", default=True)

    # --- Board orientation ---
    board_orientation_mode: bpy.props.EnumProperty(
        name="Board Orientation",
        description=(
            "Guess the board's facing axis from its bounds, or declare which "
            "world axis its top face and front edge point along"
        ),
        items=BOARD_ORIENTATION_MODE_ITEMS,
        default="AUTO",
    )
    board_top_axis: bpy.props.EnumProperty(
        name="Top Face",
        description="World axis the board's component side faces",
        items=BOARD_AXIS_ITEMS,
        default="POS_Z",
        update=_on_board_top_axis,
    )
    board_front_axis: bpy.props.EnumProperty(
        name="Front Edge",
        description=(
            "World axis the board's front edge faces: where a viewer stands to "
            "read the silkscreen the right way up"
        ),
        items=BOARD_AXIS_ITEMS,
        default="NEG_Y",
        update=_on_board_front_axis,
    )

    # --- Camera & Composition properties ---
    camera_preset: bpy.props.EnumProperty(
        name="Camera Preset",
        items=CAMERA_PRESET_ITEMS,
        default="TOP",
    )
    camera_focal_length: bpy.props.FloatProperty(
        name="Focal Length",
        default=75.0, min=20.0, max=200.0,
    )
    camera_control_mode: bpy.props.EnumProperty(
        name="Control Mode",
        description="Choose automatic target tracking or free manual rotation",
        items=CAMERA_CONTROL_MODE_ITEMS,
        default="AUTO_TARGET",
        update=_on_camera_control_mode,
    )
    camera_move_step_mode: bpy.props.EnumProperty(
        name="Movement Step",
        items=CAMERA_MOVE_STEP_ITEMS,
        default="NORMAL",
    )
    camera_orbit_step: bpy.props.FloatProperty(
        name="Orbit / Roll Step",
        description="Angle used by still orbit and roll buttons",
        default=radians(5.0), min=radians(0.1), max=radians(45.0),
        subtype="ANGLE",
        unit="ROTATION",
    )
    camera_fit_margin: bpy.props.FloatProperty(
        name="Fit Margin",
        description="Extra space around the framed PCB or component",
        default=0.10, min=0.0, max=1.0,
        subtype="FACTOR",
    )
    camera_azimuth: bpy.props.FloatProperty(
        name="Azimuth",
        description="Horizontal product-view angle around the target",
        default=0.0, min=radians(-180.0), max=radians(180.0),
        subtype="ANGLE", unit="ROTATION",
        update=_on_camera_product_parameter,
    )
    camera_elevation: bpy.props.FloatProperty(
        name="Elevation",
        description="Vertical product-view angle above or below the target",
        default=radians(90.0), min=radians(-90.0), max=radians(90.0),
        subtype="ANGLE", unit="ROTATION",
        update=_on_camera_product_parameter,
    )
    camera_distance: bpy.props.FloatProperty(
        name="Distance",
        description="Camera distance from the active target",
        default=10.0, min=0.0001, soft_max=1000.0,
        update=_on_camera_product_parameter,
    )
    camera_roll: bpy.props.FloatProperty(
        name="Roll",
        description="Rotation around the viewing axis",
        default=0.0, min=radians(-180.0), max=radians(180.0),
        subtype="ANGLE", unit="ROTATION",
        update=_on_camera_product_parameter,
    )
    camera_target_offset_x: bpy.props.FloatProperty(
        name="Target X", default=0.0, update=_on_camera_target_offset,
    )
    camera_target_offset_y: bpy.props.FloatProperty(
        name="Target Y", default=0.0, update=_on_camera_target_offset,
    )
    camera_target_offset_z: bpy.props.FloatProperty(
        name="Target Z", default=0.0, update=_on_camera_target_offset,
    )
    show_camera_advanced: bpy.props.BoolProperty(
        name="Advanced Camera Controls", default=False,
    )
    show_camera_nudge: bpy.props.BoolProperty(
        name="Move, Pan and Orbit", default=False,
        description="Step buttons for moving, panning and orbiting the still camera",
    )
    show_render_device: bpy.props.BoolProperty(
        name="Render Device", default=False,
        description="CPU or GPU device used by Cycles",
    )
    show_render_finishing: bpy.props.BoolProperty(
        name="Optional Finishing", default=False,
    )
    show_render_legacy: bpy.props.BoolProperty(
        name="Legacy EEVEE Render", default=False,
    )
    camera_saved_view: bpy.props.FloatVectorProperty(
        name="Saved Camera Matrix", size=16, default=(0.0,) * 16,
    )
    camera_saved_target: bpy.props.FloatVectorProperty(
        name="Saved Target", size=3, default=(0.0, 0.0, 0.0),
    )
    camera_saved_lens: bpy.props.FloatProperty(
        name="Saved Lens", default=75.0,
    )
    camera_saved_mode: bpy.props.StringProperty(
        name="Saved Mode", default="AUTO_TARGET",
    )
    camera_has_saved_view: bpy.props.BoolProperty(
        name="Has Saved View", default=False,
    )
    use_depth_of_field: bpy.props.BoolProperty(
        name="Depth of Field",
        default=False,
    )
    dof_preset: bpy.props.EnumProperty(
        name="DOF Preset",
        items=DOF_PRESET_ITEMS,
        default="PRODUCT_SHARP",
        update=_on_dof_preset,
    )
    focus_target_mode: bpy.props.EnumProperty(
        name="Focus Target",
        items=FOCUS_TARGET_ITEMS,
        default="PCB_CENTER",
    )
    camera_fstop: bpy.props.FloatProperty(
        name="F-Stop",
        default=5.6, min=1.4, max=22.0,
    )
    reflection_surface: bpy.props.EnumProperty(
        name="Reflection Surface",
        items=REFLECTION_SURFACE_ITEMS,
        default="OFF",
    )
    camera_status: bpy.props.StringProperty(
        name="Camera Status",
        default="",
    )

    # --- Animation & Video properties ---
    turntable_enabled: bpy.props.BoolProperty(
        name="Enable Animation",
        default=False,
    )
    animation_type: bpy.props.EnumProperty(
        name="Animation Type",
        items=ANIMATION_TYPE_ITEMS,
        default="PCB_TURNTABLE",
    )
    flyover_style: bpy.props.EnumProperty(
        name="Flyover Style",
        items=FLYOVER_STYLE_ITEMS,
        default="DIAGONAL_REVEAL",
    )
    flyover_height: bpy.props.EnumProperty(
        name="Flyover Height",
        items=FLYOVER_HEIGHT_ITEMS,
        default="MEDIUM",
    )
    turntable_direction: bpy.props.EnumProperty(
        name="Direction",
        items=TURNTABLE_DIRECTION_ITEMS,
        default="CLOCKWISE",
    )
    turntable_rotation_degrees: bpy.props.EnumProperty(
        name="Rotation",
        items=TURNTABLE_ROTATION_ITEMS,
        default="360",
    )
    turntable_duration: bpy.props.FloatProperty(
        name="Duration",
        default=6.0, min=2.0, max=30.0,
    )
    turntable_fps: bpy.props.EnumProperty(
        name="Frame Rate",
        items=TURNTABLE_FPS_ITEMS,
        default="30",
    )
    turntable_resolution: bpy.props.EnumProperty(
        name="Video Quality",
        items=TURNTABLE_RESOLUTION_ITEMS,
        default="HD_720P",
    )
    turntable_motion_style: bpy.props.EnumProperty(
        name="Motion Style",
        items=TURNTABLE_MOTION_ITEMS,
        default="CONSTANT",
    )
    turntable_start_angle: bpy.props.FloatProperty(
        name="Start Angle",
        default=0.0, min=0.0, max=radians(360.0),
        subtype="ANGLE",
    )
    animation_output_format: bpy.props.EnumProperty(
        name="Output Format",
        items=ANIMATION_FORMAT_ITEMS,
        default="MP4",
    )
    animation_output_directory: bpy.props.StringProperty(
        name="Output Directory",
        subtype="DIR_PATH",
        default="",
    )
    animation_filename: bpy.props.StringProperty(
        name="Filename",
        default=DEFAULT_ANIMATION_FILENAME,
    )
    animation_overwrite: bpy.props.BoolProperty(
        name="Overwrite Existing",
        default=False,
    )
    turntable_status: bpy.props.StringProperty(
        name="Turntable Status",
        default="",
    )
    last_animation_output: bpy.props.StringProperty(
        name="Last Animation Output",
        subtype="FILE_PATH",
        default="",
    )

def _on_lighting_mode_update(self, context: bpy.types.Context | None) -> None:
    """Migrate the legacy lighting selector without disabling product lights."""
    if self.lighting_mode == "HDRI" and self.hdri_mode == "OFF":
        self.hdri_mode = "VISIBLE_ENVIRONMENT"
