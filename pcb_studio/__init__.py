"""PCB Studio — Blender extension for PCB rendering from Altium Designer."""

from __future__ import annotations

import bpy

from .constants import (
    EXTENSION_NAME,
    EXTENSION_VERSION,
    PROP_SCENE_ATTR,
)
from .operators.apply_background import PCBSTUDIO_OT_apply_background
from .operators.apply_camera_preset import PCBSTUDIO_OT_apply_camera_preset
from .operators.board_orientation import PCBSTUDIO_OT_set_board_axis_from_view
from .operators.apply_camera_settings import (
    PCBSTUDIO_OT_align_camera_to_view,
    PCBSTUDIO_OT_apply_camera_settings,
    PCBSTUDIO_OT_apply_reflection_plane,
    PCBSTUDIO_OT_zoom_to_fit,
)
from .operators.apply_lighting_preset import PCBSTUDIO_OT_apply_lighting_preset
from .operators.assign_material import PCBSTUDIO_OT_assign_material
from .operators.create_material import PCBSTUDIO_OT_create_or_update_material
from .operators.cycles_devices import PCBSTUDIO_OT_refresh_cycles_devices
from .operators.camera_controls import CAMERA_CONTROL_OPERATOR_CLASSES
from .operators.diagnostics import PCBSTUDIO_OT_system_check
from .operators.import_obj import PCBSTUDIO_OT_import_obj
from .operators.load_hdri import (
    PCBSTUDIO_OT_apply_hdri,
    PCBSTUDIO_OT_load_hdri,
    PCBSTUDIO_OT_remove_hdri,
)
from .operators.material_tools import MATERIAL_TOOL_OPERATOR_CLASSES
from .operators.preview_materials import PCBSTUDIO_OT_preview_materials
from .operators.professional_render import (
    PCBSTUDIO_OT_render_lighting_preview,
    PCBSTUDIO_OT_render_professional_still,
)
from .operators.professional_studio import (
    PCBSTUDIO_OT_add_custom_studio_light,
    PCBSTUDIO_OT_add_light_card,
    PCBSTUDIO_OT_apply_custom_light_preset,
    PCBSTUDIO_OT_apply_floor_preset,
    PCBSTUDIO_OT_floor_action,
    PCBSTUDIO_OT_delete_custom_studio_light,
    PCBSTUDIO_OT_remove_light_card,
    PCBSTUDIO_OT_reset_professional_studio,
    PCBSTUDIO_OT_restore_studio_lights,
    PCBSTUDIO_OT_solo_studio_light,
    PCBSTUDIO_OT_studio_helper,
    PCBSTUDIO_OT_update_professional_studio,
)
from .operators.realism import (
    PCBSTUDIO_OT_apply_micro_bevel,
    PCBSTUDIO_OT_create_pcb_surface_material,
    PCBSTUDIO_OT_remove_micro_bevel,
    PCBSTUDIO_OT_setup_pcb_uv_mapping,
    PCBSTUDIO_OT_smooth_all_components,
    PCBSTUDIO_OT_smooth_selected_components,
)
from .operators.render_final import PCBSTUDIO_OT_render_final
from .operators.render_preview import PCBSTUDIO_OT_render_preview
from .operators.render_turntable import (
    PCBSTUDIO_OT_preview_turntable,
    PCBSTUDIO_OT_render_test_frame,
    PCBSTUDIO_OT_render_turntable,
)
from .operators.reset_turntable import PCBSTUDIO_OT_reset_turntable
from .operators.setup_scene import PCBSTUDIO_OT_prepare_scene
from .operators.setup_turntable import PCBSTUDIO_OT_setup_turntable
from .properties import (
    PCBSTUDIO_PG_custom_light,
    PCBSTUDIO_PG_import_state,
    PCBSTUDIO_PG_light_card,
)
from .ui.main_panel import PANEL_CLASSES
from .product_properties import PCBSTUDIO_PG_product, PCBSTUDIO_PG_product_object
from .operators.product import PRODUCT_OPERATOR_CLASSES
from .ui.product import PRODUCT_PANEL_CLASSES

from .studio_properties import PCBSTUDIO_PG_environment
from .operators.studio_environment import PCBSTUDIO_OT_environment

_REGISTERED_CLASSES = (
    PCBSTUDIO_PG_environment,
    PCBSTUDIO_OT_environment,
    PCBSTUDIO_PG_product,
    PCBSTUDIO_PG_product_object,
    PCBSTUDIO_PG_custom_light,
    PCBSTUDIO_PG_light_card,
    PCBSTUDIO_PG_import_state,
    *PANEL_CLASSES,
    *PRODUCT_OPERATOR_CLASSES,
    *PRODUCT_PANEL_CLASSES,
    PCBSTUDIO_OT_system_check,
    PCBSTUDIO_OT_import_obj,
    PCBSTUDIO_OT_prepare_scene,
    PCBSTUDIO_OT_render_preview,
    PCBSTUDIO_OT_create_or_update_material,
    PCBSTUDIO_OT_assign_material,
    PCBSTUDIO_OT_preview_materials,
    *MATERIAL_TOOL_OPERATOR_CLASSES,
    PCBSTUDIO_OT_render_final,
    PCBSTUDIO_OT_apply_lighting_preset,
    PCBSTUDIO_OT_apply_background,
    PCBSTUDIO_OT_load_hdri,
    PCBSTUDIO_OT_apply_hdri,
    PCBSTUDIO_OT_remove_hdri,
    PCBSTUDIO_OT_apply_camera_preset,
    PCBSTUDIO_OT_set_board_axis_from_view,
    PCBSTUDIO_OT_align_camera_to_view,
    PCBSTUDIO_OT_apply_camera_settings,
    PCBSTUDIO_OT_zoom_to_fit,
    PCBSTUDIO_OT_apply_reflection_plane,
    *CAMERA_CONTROL_OPERATOR_CLASSES,
    PCBSTUDIO_OT_setup_turntable,
    PCBSTUDIO_OT_reset_turntable,
    PCBSTUDIO_OT_preview_turntable,
    PCBSTUDIO_OT_render_test_frame,
    PCBSTUDIO_OT_render_turntable,
    PCBSTUDIO_OT_update_professional_studio,
    PCBSTUDIO_OT_reset_professional_studio,
    PCBSTUDIO_OT_solo_studio_light,
    PCBSTUDIO_OT_restore_studio_lights,
    PCBSTUDIO_OT_render_lighting_preview,
    PCBSTUDIO_OT_render_professional_still,
    PCBSTUDIO_OT_refresh_cycles_devices,
    PCBSTUDIO_OT_add_custom_studio_light,
    PCBSTUDIO_OT_apply_custom_light_preset,
    PCBSTUDIO_OT_delete_custom_studio_light,
    PCBSTUDIO_OT_add_light_card,
    PCBSTUDIO_OT_remove_light_card,
    PCBSTUDIO_OT_apply_floor_preset,
    PCBSTUDIO_OT_floor_action,
    PCBSTUDIO_OT_studio_helper,
    PCBSTUDIO_OT_smooth_selected_components,
    PCBSTUDIO_OT_smooth_all_components,
    PCBSTUDIO_OT_apply_micro_bevel,
    PCBSTUDIO_OT_remove_micro_bevel,
    PCBSTUDIO_OT_setup_pcb_uv_mapping,
    PCBSTUDIO_OT_create_pcb_surface_material,
)


def register() -> None:
    for cls in _REGISTERED_CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.pcb_studio_environment = bpy.props.PointerProperty(type=PCBSTUDIO_PG_environment)
    bpy.types.Scene.pcb_studio_product = bpy.props.PointerProperty(type=PCBSTUDIO_PG_product)
    bpy.types.Object.pcb_studio_product = bpy.props.PointerProperty(type=PCBSTUDIO_PG_product_object)
    setattr(
        bpy.types.Scene,
        PROP_SCENE_ATTR,
        bpy.props.PointerProperty(type=PCBSTUDIO_PG_import_state),
    )
    print(f"{EXTENSION_NAME} v{EXTENSION_VERSION} registered.")


def unregister() -> None:
    if hasattr(bpy.types.Scene, "pcb_studio_environment"):
        del bpy.types.Scene.pcb_studio_environment
    for owner in (bpy.types.Object, bpy.types.Scene):
        if hasattr(owner, "pcb_studio_product"):
            del owner.pcb_studio_product
    if hasattr(bpy.types.Scene, PROP_SCENE_ATTR):
        delattr(bpy.types.Scene, PROP_SCENE_ATTR)
    for cls in reversed(_REGISTERED_CLASSES):
        bpy.utils.unregister_class(cls)
    print(f"{EXTENSION_NAME} v{EXTENSION_VERSION} unregistered.")
