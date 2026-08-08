"""Operator that assigns the current PCB Studio material to selected objects."""

from __future__ import annotations

import traceback

import bpy

from ..constants import (
    COLLECTION_NAME,
    OPERATOR_ID_ASSIGN_MATERIAL,
    PROP_SCENE_ATTR,
)


class PCBSTUDIO_OT_assign_material(bpy.types.Operator):
    """Assign the current PCB Studio material to selected PCB mesh objects."""

    bl_idname: str = OPERATOR_ID_ASSIGN_MATERIAL
    bl_label: str = "Assign to Selected Objects"
    bl_description: str = (
        "Assign the created material to selected mesh objects in PCB_MODEL"
    )
    bl_options: set[str] = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context | None) -> set[str]:
        """Validate selection and assign material."""
        try:
            return self._execute_impl(context)
        except Exception:
            traceback.print_exc()
            self.report(
                {"ERROR"},
                "An unexpected error occurred during material assignment. "
                "Check the system console for details.",
            )
            return {"CANCELLED"}

    def _execute_impl(self, context: bpy.types.Context | None) -> set[str]:
        """Core assignment logic."""
        props = getattr(context.scene, PROP_SCENE_ATTR, None)
        if props is None:
            self.report({"ERROR"}, "Extension state not available.")
            return {"CANCELLED"}

        # --- Validate material exists ---
        mat_name = props.current_material_name
        if not mat_name:
            self.report(
                {"ERROR"},
                "No material has been created. "
                "Use 'Create or Update Material' first.",
            )
            props.material_status = "No material to assign."
            return {"CANCELLED"}

        mat = bpy.data.materials.get(mat_name)
        if mat is None:
            self.report(
                {"ERROR"},
                f"Material '{mat_name}' not found. Create it first.",
            )
            props.material_status = f"Material '{mat_name}' not found."
            return {"CANCELLED"}

        # --- Validate PCB_MODEL ---
        pcb_coll = bpy.data.collections.get(COLLECTION_NAME)
        if pcb_coll is None:
            self.report(
                {"ERROR"},
                "PCB_MODEL collection not found. Import a PCB first.",
            )
            props.material_status = "No PCB imported."
            return {"CANCELLED"}

        # --- Filter selected objects ---
        pcb_object_names = {o.name for o in pcb_coll.all_objects}
        targets: list[bpy.types.Object] = []
        skipped: list[str] = []

        for obj in context.selected_objects:
            if obj.type != "MESH":
                skipped.append(f"{obj.name} (not a mesh)")
                continue
            if obj.name not in pcb_object_names:
                skipped.append(f"{obj.name} (not in PCB_MODEL)")
                continue
            targets.append(obj)

        if not targets:
            self.report(
                {"ERROR"},
                "No valid PCB mesh objects selected. "
                "Select objects in PCB_MODEL first.",
            )
            props.material_status = "No valid PCB objects selected."
            return {"CANCELLED"}

        # --- Assign material with slot-safety rules ---
        assigned = 0
        slot_warnings: list[str] = []

        for obj in targets:
            slots = obj.material_slots

            if len(slots) == 0:
                # No slots: append.
                obj.data.materials.append(mat)
                assigned += 1

            elif len(slots) == 1:
                # One slot: replace it.
                obj.material_slots[0].material = mat
                assigned += 1

            else:
                # Multiple slots: replace only the active slot.
                idx = obj.active_material_index
                if 0 <= idx < len(slots):
                    obj.material_slots[idx].material = mat
                    assigned += 1
                else:
                    slot_warnings.append(obj.name)

        # --- Report ---
        msg = f"Material assigned to {assigned} object(s)."
        if slot_warnings:
            msg += (
                f" Skipped {len(slot_warnings)} object(s) with invalid "
                "active material slot."
            )
        if skipped:
            msg += f" Ignored {len(skipped)} non-PCB or non-mesh selection(s)."

        props.material_status = msg
        self.report({"INFO"}, msg)

        return {"FINISHED"}