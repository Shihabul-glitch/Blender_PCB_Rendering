"""Operator that creates or updates a PCB Studio material from current UI values."""

from __future__ import annotations

import traceback

import bpy

from ..constants import (
    MATERIAL_NAME_PREFIX,
    OPERATOR_ID_CREATE_MATERIAL,
    PROP_SCENE_ATTR,
)
from ..utils import material_compat as compat
from ..utils.material_nodes import apply_surface_detail
from ..utils.materials import (
    PRESET_DATA,
    apply_props_to_material,
    get_or_create_pcb_material,
)


class PCBSTUDIO_OT_create_or_update_material(bpy.types.Operator):
    """Create or update a PCB Studio material from the selected preset and values."""

    bl_idname: str = OPERATOR_ID_CREATE_MATERIAL
    bl_label: str = "Create or Update Material"
    bl_description: str = (
        "Create a new PCB Studio material or update the existing one"
    )
    bl_options: set[str] = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context | None) -> set[str]:
        """Create or update the material."""
        try:
            return self._execute_impl(context)
        except Exception:
            traceback.print_exc()
            self.report(
                {"ERROR"},
                "An unexpected error occurred creating the material. "
                "Check the system console for details.",
            )
            return {"CANCELLED"}

    def _execute_impl(self, context: bpy.types.Context | None) -> set[str]:
        """Core creation logic."""
        props = getattr(context.scene, PROP_SCENE_ATTR, None)
        if props is None:
            self.report({"ERROR"}, "Extension state not available.")
            return {"CANCELLED"}

        preset_key = props.material_preset
        is_custom = (preset_key == "CUSTOM")

        # --- Determine material name ---
        if is_custom:
            custom_name = props.custom_material_name.strip()
            if not custom_name:
                self.report(
                    {"ERROR"},
                    "Enter a name for the custom material.",
                )
                props.material_status = "Custom material name is empty."
                return {"CANCELLED"}
            # Sanitise: replace spaces with underscores, remove unsafe chars.
            safe_name = "".join(
                c if c.isalnum() or c == "_" else "_"
                for c in custom_name
            )
            mat_name = f"{MATERIAL_NAME_PREFIX}{safe_name}"
        else:
            preset = PRESET_DATA.get(preset_key)
            if preset is None:
                self.report({"ERROR"}, f"Unknown preset: {preset_key}")
                props.material_status = "Unknown preset."
                return {"CANCELLED"}
            mat_name = preset.material_name

        # --- Create or get the material ---
        mat = get_or_create_pcb_material(mat_name)
        compat.mark_managed(mat, preset_key)

        # --- Write the UI values (socket defaults only) ---
        apply_props_to_material(mat, props)

        # --- Optional nodes: only inside a material PCB Studio may rebuild ---
        detail = ""
        if compat.is_managed(mat) or compat.is_simple_principled(mat):
            detail = apply_surface_detail(mat, props)

        # --- Update UI state ---
        props.current_material_name = mat_name
        status = f"Material '{mat_name}' ready"
        if detail:
            status = f"{status} ({detail})"
        props.material_status = f"{status}."

        self.report(
            {"INFO"},
            f"{status}. Select objects and click 'Assign to Selected Objects'.",
        )

        return {"FINISHED"}
