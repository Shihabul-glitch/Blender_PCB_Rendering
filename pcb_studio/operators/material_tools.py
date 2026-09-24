"""Material and selection workflow tools for PCB Studio.

Every operator here runs only on explicit user action, reuses the project's
existing PCB object structure, and reports exactly how many objects it changed
so nothing is ever modified unexpectedly.
"""

from __future__ import annotations

import traceback

import bpy

from ..constants import (
    COLLECTION_NAME,
    OPERATOR_ID_ASSIGN_ACTIVE_MATERIAL,
    OPERATOR_ID_MAKE_MATERIAL_UNIQUE,
    OPERATOR_ID_PICK_ACTIVE_MATERIAL,
    OPERATOR_ID_PICK_MATERIAL_PRESET,
    OPERATOR_ID_RESET_MATERIAL_VALUES,
    OPERATOR_ID_SELECT_SAME_MATERIAL,
    OPERATOR_ID_UPDATE_ACTIVE_MATERIAL,
    PROP_SCENE_ATTR,
)
from ..utils import material_compat as compat
from ..utils.material_nodes import apply_surface_detail
from ..utils.materials import (
    PRESET_DATA,
    apply_preset_to_props,
    apply_props_to_material,
    ensure_editable,
    preset_display_name,
    read_material_into_props,
)


def _props(context):
    return getattr(context.scene, PROP_SCENE_ATTR, None)


def _pcb_meshes(context, selected_only: bool = True) -> list:
    """Return PCB mesh objects, by default only the selected ones."""
    collection = bpy.data.collections.get(COLLECTION_NAME)
    if collection is None:
        return []
    if not selected_only:
        return [obj for obj in collection.all_objects if obj.type == "MESH"]
    names = {obj.name for obj in collection.all_objects}
    return [
        obj for obj in context.selected_objects
        if obj.type == "MESH" and obj.name in names
    ]

def _select_only(context, objects) -> int:
    """Replace the selection with *objects*.  Returns how many were selected."""
    for obj in list(context.selected_objects):
        try:
            obj.select_set(False)
        except RuntimeError:
            continue
    count = 0
    for obj in objects:
        try:
            obj.select_set(True)
        except RuntimeError:
            continue
        count += 1
        context.view_layer.objects.active = obj
    return count


def _assign_to_object(obj, mat) -> bool:
    """Put *mat* in the right slot: append, replace the only slot, or the active one."""
    slots = obj.material_slots
    if len(slots) == 0:
        obj.data.materials.append(mat)
        return True
    if len(slots) == 1:
        slots[0].material = mat
        return True
    index = obj.active_material_index
    if 0 <= index < len(slots):
        slots[index].material = mat
        return True
    return False


def _active_material(context):
    """Return the active object's active material, or raise a clear error."""
    obj = context.active_object
    mat = obj.active_material if obj is not None else None
    if mat is None:
        raise ValueError("Select an object that already has a material first.")
    return obj, mat


class _MaterialToolBase:
    """Shared error handling so every tool fails with a readable message."""

    bl_options: set[str] = {"REGISTER", "UNDO"}
    status_prop: str | None = "material_status"

    def execute(self, context):
        props = _props(context)
        if props is None:
            self.report({"ERROR"}, "Extension state not available.")
            return {"CANCELLED"}
        try:
            return self.run(context, props)
        except ValueError as exc:
            self.report({"ERROR"}, str(exc))
            if self.status_prop:
                setattr(props, self.status_prop, str(exc))
            return {"CANCELLED"}
        except Exception:
            traceback.print_exc()
            self.report({"ERROR"}, "Unexpected error. Check the system console.")
            return {"CANCELLED"}

class PCBSTUDIO_OT_pick_material_preset(_MaterialToolBase, bpy.types.Operator):
    """Load one preset from the category menu into the material panel."""

    bl_idname: str = OPERATOR_ID_PICK_MATERIAL_PRESET
    bl_label: str = "Use Preset"
    bl_description: str = "Load this preset's values into the material panel"

    preset: bpy.props.StringProperty(name="Preset", default="")

    def run(self, context, props):
        if self.preset not in PRESET_DATA:
            raise ValueError(f"Unknown material preset: {self.preset}")
        props.material_preset = self.preset
        props.material_status = (
            f"{preset_display_name(self.preset)} values loaded. "
            "Click Create or Update Material to build it."
        )
        return {"FINISHED"}


class PCBSTUDIO_OT_reset_material_values(_MaterialToolBase, bpy.types.Operator):
    """Reset every value back to the current preset."""

    bl_idname: str = OPERATOR_ID_RESET_MATERIAL_VALUES
    bl_label: str = "Reset"
    bl_description: str = "Reset all values back to the current preset's defaults"

    def run(self, context, props):
        if not apply_preset_to_props(props, props.material_preset):
            raise ValueError("Choose a preset before resetting.")
        props.material_status = (
            f"Values reset to {preset_display_name(props.material_preset)}."
        )
        return {"FINISHED"}


class PCBSTUDIO_OT_pick_active_material(_MaterialToolBase, bpy.types.Operator):
    """Read the active object's material into the panel."""

    bl_idname: str = OPERATOR_ID_PICK_ACTIVE_MATERIAL
    bl_label: str = "Pick From Active"
    bl_description: str = (
        "Read the active object's material into the panel so you can edit it"
    )

    def run(self, context, props):
        _, mat = _active_material(context)
        if not read_material_into_props(mat, props):
            raise ValueError(f"'{mat.name}' has no Principled BSDF to read.")
        props.current_material_name = mat.name
        used = compat.count_material_objects(mat)
        props.material_status = f"Editing '{mat.name}', used by {used} PCB object(s)."
        return {"FINISHED"}

class PCBSTUDIO_OT_update_active_material(_MaterialToolBase, bpy.types.Operator):
    """Write the panel values into the active object's own material."""

    bl_idname: str = OPERATOR_ID_UPDATE_ACTIVE_MATERIAL
    bl_label: str = "Update Active Material"
    bl_description: str = (
        "Write the panel values into the active object's material. A hand built "
        "shader network is copied onto the selected objects instead of overwritten"
    )

    def run(self, context, props):
        obj, mat = _active_material(context)
        targets = _pcb_meshes(context) or [obj]
        mat, reason = ensure_editable(mat, targets)
        apply_props_to_material(mat, props)
        detail = apply_surface_detail(mat, props)
        props.current_material_name = mat.name
        used = compat.count_material_objects(mat)
        if reason == "shared":
            props.material_status = (
                f"'{mat.name}' is a new copy on {len(targets)} selected object(s); "
                "every other object keeps the original material."
            )
        elif reason == "protected":
            props.material_status = (
                f"'{mat.name}' is a managed copy on {len(targets)} object(s); "
                "the original shader network was left untouched."
            )
        else:
            note = f" ({detail})" if detail else ""
            props.material_status = (
                f"Updated '{mat.name}'{note}, used by {used} PCB object(s)."
            )
        self.report({"INFO"}, props.material_status)
        return {"FINISHED"}


class PCBSTUDIO_OT_assign_active_material(_MaterialToolBase, bpy.types.Operator):
    """Give every selected PCB object the active object's material."""

    bl_idname: str = OPERATOR_ID_ASSIGN_ACTIVE_MATERIAL
    bl_label: str = "Assign Active Material to Selected"
    bl_description: str = (
        "Give every other selected PCB object the active object's material"
    )

    def run(self, context, props):
        obj, mat = _active_material(context)
        targets = [target for target in _pcb_meshes(context) if target is not obj]
        if not targets:
            raise ValueError(
                "Select the PCB objects that should receive the material, "
                "then make the source object active."
            )
        assigned = sum(int(_assign_to_object(target, mat)) for target in targets)
        props.material_status = f"'{mat.name}' assigned to {assigned} object(s)."
        self.report({"INFO"}, props.material_status)
        return {"FINISHED"}

class PCBSTUDIO_OT_select_same_material(_MaterialToolBase, bpy.types.Operator):
    """Select every PCB object that shares the active material."""

    bl_idname: str = OPERATOR_ID_SELECT_SAME_MATERIAL
    bl_label: str = "Select Same Material"
    bl_description: str = "Select every PCB object that uses the active material"

    def run(self, context, props):
        _, mat = _active_material(context)
        matches = [
            obj for obj in _pcb_meshes(context, selected_only=False)
            if any(slot.material is mat for slot in obj.material_slots)
        ]
        if not matches:
            raise ValueError(f"No PCB object uses '{mat.name}'.")
        count = _select_only(context, matches)
        props.material_status = f"Selected {count} object(s) using '{mat.name}'."
        self.report({"INFO"}, props.material_status)
        return {"FINISHED"}


class PCBSTUDIO_OT_make_material_unique(_MaterialToolBase, bpy.types.Operator):
    """Give the selected objects their own copy of the active material."""

    bl_idname: str = OPERATOR_ID_MAKE_MATERIAL_UNIQUE
    bl_label: str = "Make Unique"
    bl_description: str = (
        "Give the selected objects their own copy of the material, so editing it "
        "cannot change the rest of the board"
    )

    def run(self, context, props):
        obj, mat = _active_material(context)
        targets = _pcb_meshes(context) or [obj]
        copy = mat.copy()
        compat.mark_managed(copy)
        changed = 0
        for target in targets:
            swapped = False
            for slot in target.material_slots:
                if slot.material is mat:
                    slot.material = copy
                    swapped = True
            changed += int(swapped)
        if changed == 0:
            bpy.data.materials.remove(copy)
            raise ValueError(
                f"None of the selected objects use '{mat.name}', so nothing was copied."
            )
        props.current_material_name = copy.name
        props.material_status = (
            f"'{copy.name}' is now used by {changed} selected object(s) only."
        )
        self.report({"INFO"}, props.material_status)
        return {"FINISHED"}


MATERIAL_TOOL_OPERATOR_CLASSES = (
    PCBSTUDIO_OT_pick_material_preset,
    PCBSTUDIO_OT_reset_material_values,
    PCBSTUDIO_OT_pick_active_material,
    PCBSTUDIO_OT_update_active_material,
    PCBSTUDIO_OT_assign_active_material,
    PCBSTUDIO_OT_select_same_material,
    PCBSTUDIO_OT_make_material_unique,
)
