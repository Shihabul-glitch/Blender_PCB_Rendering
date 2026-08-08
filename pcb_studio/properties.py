"""PropertyGroup for PCB Studio import state."""

import bpy

from .constants import (
    ANIMATION_FORMAT_ITEMS,
    BACKGROUND_PRESET_ITEMS,
    CAMERA_PRESET_ITEMS,
    DEFAULT_ANIMATION_FILENAME,
    DEFAULT_OUTPUT_FILENAME,
    FOCUS_TARGET_ITEMS,
    LIGHTING_MODE_ITEMS,
    MATERIAL_PRESET_ITEMS,
    PROP_GROUP_ID,
    REFLECTION_SURFACE_ITEMS,
    RENDER_QUALITY_ITEMS,
    STUDIO_PRESET_ITEMS,
    TURNTABLE_DIRECTION_ITEMS,
    TURNTABLE_FPS_ITEMS,
    TURNTABLE_MOTION_ITEMS,
    TURNTABLE_RESOLUTION_ITEMS,
    TURNTABLE_ROTATION_ITEMS,
)
from .utils.materials import PRESET_DATA


def _on_material_preset_update(self, context: bpy.types.Context | None) -> None:
    """Sync material UI values from the selected preset."""
    if self.material_preset == "CUSTOM":
        return
    preset = PRESET_DATA.get(self.material_preset)
    if preset is None:
        return
    self.material_base_color = preset.base_color
    self.material_metallic = preset.metallic
    self.material_roughness = preset.roughness
    self.material_coat_weight = preset.coat_weight


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
        items=MATERIAL_PRESET_ITEMS,
        default="SOLDER_MASK_GREEN",
        update=_on_material_preset_update,
    )
    custom_material_name: bpy.props.StringProperty(default="")
    material_base_color: bpy.props.FloatVectorProperty(
        subtype="COLOR", size=4, min=0.0, max=1.0,
        default=(0.05, 0.30, 0.08, 1.0),
    )
    material_metallic: bpy.props.FloatProperty(default=0.0, min=0.0, max=1.0)
    material_roughness: bpy.props.FloatProperty(default=0.4, min=0.0, max=1.0)
    material_coat_weight: bpy.props.FloatProperty(default=0.0, min=0.0, max=1.0)
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
        default="BRIGHT_STUDIO",
    )
    lighting_intensity: bpy.props.FloatProperty(
        name="Lighting Intensity",
        default=1.0, min=0.25, max=2.0,
    )
    shadow_softness: bpy.props.FloatProperty(
        name="Shadow Softness",
        default=1.0, min=0.5, max=2.0,
    )
    background_preset: bpy.props.EnumProperty(
        name="Background Preset",
        items=BACKGROUND_PRESET_ITEMS,
        default="DARK_GRAY",
    )
    hdri_filepath: bpy.props.StringProperty(
        name="HDRI File",
        subtype="FILE_PATH",
        default="",
    )
    hdri_rotation: bpy.props.FloatProperty(
        name="HDRI Rotation",
        default=0.0, min=-180.0, max=180.0,
        subtype="ANGLE",
    )
    hdri_brightness: bpy.props.FloatProperty(
        name="HDRI Brightness",
        default=1.0, min=0.0, max=5.0,
    )
    environment_status: bpy.props.StringProperty(
        name="Environment Status",
        default="",
    )

    # --- Camera & Composition properties ---
    camera_preset: bpy.props.EnumProperty(
        name="Camera Preset",
        items=CAMERA_PRESET_ITEMS,
        default="ISOMETRIC",
    )
    camera_focal_length: bpy.props.FloatProperty(
        name="Focal Length",
        default=50.0, min=20.0, max=200.0,
    )
    use_depth_of_field: bpy.props.BoolProperty(
        name="Depth of Field",
        default=False,
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
        name="Enable Turntable",
        default=False,
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
        default=0.0, min=0.0, max=360.0,
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
    """Switch managed light visibility when mode changes."""
    from .utils.environment import set_light_visibility
    set_light_visibility(self.lighting_mode == "STUDIO")