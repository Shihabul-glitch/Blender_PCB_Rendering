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
from .operators.apply_camera_settings import (
    PCBSTUDIO_OT_apply_camera_settings,
    PCBSTUDIO_OT_apply_reflection_plane,
    PCBSTUDIO_OT_zoom_to_fit,
)
from .operators.apply_lighting_preset import PCBSTUDIO_OT_apply_lighting_preset
from .operators.assign_material import PCBSTUDIO_OT_assign_material
from .operators.create_material import PCBSTUDIO_OT_create_or_update_material
from .operators.diagnostics import PCBSTUDIO_OT_system_check
from .operators.import_obj import PCBSTUDIO_OT_import_obj
from .operators.load_hdri import (
    PCBSTUDIO_OT_apply_hdri,
    PCBSTUDIO_OT_load_hdri,
    PCBSTUDIO_OT_remove_hdri,
)
from .operators.preview_materials import PCBSTUDIO_OT_preview_materials
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
from .properties import PCBSTUDIO_PG_import_state
from .ui.main_panel import PCBSTUDIO_PT_main_panel

_REGISTERED_CLASSES = (
    PCBSTUDIO_PG_import_state,
    PCBSTUDIO_PT_main_panel,
    PCBSTUDIO_OT_system_check,
    PCBSTUDIO_OT_import_obj,
    PCBSTUDIO_OT_prepare_scene,
    PCBSTUDIO_OT_render_preview,
    PCBSTUDIO_OT_create_or_update_material,
    PCBSTUDIO_OT_assign_material,
    PCBSTUDIO_OT_preview_materials,
    PCBSTUDIO_OT_render_final,
    PCBSTUDIO_OT_apply_lighting_preset,
    PCBSTUDIO_OT_apply_background,
    PCBSTUDIO_OT_load_hdri,
    PCBSTUDIO_OT_apply_hdri,
    PCBSTUDIO_OT_remove_hdri,
    PCBSTUDIO_OT_apply_camera_preset,
    PCBSTUDIO_OT_apply_camera_settings,
    PCBSTUDIO_OT_zoom_to_fit,
    PCBSTUDIO_OT_apply_reflection_plane,
    PCBSTUDIO_OT_setup_turntable,
    PCBSTUDIO_OT_reset_turntable,
    PCBSTUDIO_OT_preview_turntable,
    PCBSTUDIO_OT_render_test_frame,
    PCBSTUDIO_OT_render_turntable,
)


def register() -> None:
    for cls in _REGISTERED_CLASSES:
        bpy.utils.register_class(cls)
    setattr(
        bpy.types.Scene,
        PROP_SCENE_ATTR,
        bpy.props.PointerProperty(type=PCBSTUDIO_PG_import_state),
    )
    print(f"{EXTENSION_NAME} v{EXTENSION_VERSION} registered.")


def unregister() -> None:
    if hasattr(bpy.types.Scene, PROP_SCENE_ATTR):
        delattr(bpy.types.Scene, PROP_SCENE_ATTR)
    for cls in reversed(_REGISTERED_CLASSES):
        bpy.utils.unregister_class(cls)
    print(f"{EXTENSION_NAME} v{EXTENSION_VERSION} unregistered.")