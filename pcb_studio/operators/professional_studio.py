"""Operators for the managed professional product studio."""

from __future__ import annotations

import traceback

import bpy

from ..constants import (
    OPERATOR_ID_ADD_CUSTOM_LIGHT,
    OPERATOR_ID_ADD_LIGHT_CARD,
    OPERATOR_ID_APPLY_CUSTOM_LIGHT_PRESET,
    OPERATOR_ID_APPLY_FLOOR_PRESET,
    OPERATOR_ID_FLOOR_ACTION,
    OPERATOR_ID_DELETE_CUSTOM_LIGHT,
    OPERATOR_ID_REMOVE_LIGHT_CARD,
    OPERATOR_ID_RESET_STUDIO,
    OPERATOR_ID_RESTORE_LIGHTS,
    OPERATOR_ID_SOLO_LIGHT,
    OPERATOR_ID_UPDATE_STUDIO,
    OPERATOR_ID_STUDIO_HELPER,
    PROP_SCENE_ATTR,
)
from ..utils.studio import (
    add_custom_light,
    add_light_card,
    apply_floor_preset,
    delete_custom_light,
    remove_light_card,
    reset_professional_studio,
    restore_studio_lights,
    solo_studio_light,
    studio_helper,
    update_professional_studio,
)


class PCBSTUDIO_OT_update_professional_studio(bpy.types.Operator):
    bl_idname = OPERATOR_ID_UPDATE_STUDIO
    bl_label = "Update Studio"
    bl_description = "Safely update managed lights, backdrop, world, floor, stage, and color settings"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            props = getattr(context.scene, PROP_SCENE_ATTR, None)
            if props is None:
                self.report({"ERROR"}, "Extension state not available.")
                return {"CANCELLED"}
            result = update_professional_studio(context.scene, props)
            props.environment_status = result
            ok = not result.startswith(("Cannot", "No ", "Unknown"))
            self.report({"INFO"} if ok else {"ERROR"}, result)
            return {"FINISHED"} if ok else {"CANCELLED"}
        except Exception:
            traceback.print_exc()
            self.report({"ERROR"}, "Studio update failed. See system console.")
            return {"CANCELLED"}


class PCBSTUDIO_OT_reset_professional_studio(bpy.types.Operator):
    bl_idname = OPERATOR_ID_RESET_STUDIO
    bl_label = "Reset Studio"
    bl_description = "Remove only PCB Studio visual objects; preserve PCB, camera, and animation"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            result = reset_professional_studio()
            props = getattr(context.scene, PROP_SCENE_ATTR, None)
            if props is not None:
                props.environment_status = result
            self.report({"INFO"}, result)
            return {"FINISHED"}
        except Exception:
            traceback.print_exc()
            self.report({"ERROR"}, "Studio reset failed. See system console.")
            return {"CANCELLED"}


class PCBSTUDIO_OT_solo_studio_light(bpy.types.Operator):
    bl_idname = OPERATOR_ID_SOLO_LIGHT
    bl_label = "Solo Studio Light"
    bl_description = "Temporarily show only one PCB Studio-managed light"
    bl_options = {"REGISTER", "UNDO"}

    light_name: bpy.props.StringProperty(default="")

    def execute(self, context):
        result = solo_studio_light(self.light_name)
        props = getattr(context.scene, PROP_SCENE_ATTR, None)
        if props is not None:
            props.environment_status = result
        ok = result.startswith("Solo active")
        self.report({"INFO"} if ok else {"ERROR"}, result)
        return {"FINISHED"} if ok else {"CANCELLED"}


class PCBSTUDIO_OT_restore_studio_lights(bpy.types.Operator):
    bl_idname = OPERATOR_ID_RESTORE_LIGHTS
    bl_label = "Restore Studio Lights"
    bl_description = "Restore managed light visibility from before Solo"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        result = restore_studio_lights()
        props = getattr(context.scene, PROP_SCENE_ATTR, None)
        if props is not None:
            props.environment_status = result
        self.report({"INFO"}, result)
        return {"FINISHED"}


class _PCBStudioManagedStudioOperator:
    bl_options = {"REGISTER", "UNDO"}

    def run(self, context, props):
        raise NotImplementedError

    def execute(self, context):
        try:
            props = getattr(context.scene, PROP_SCENE_ATTR, None)
            if props is None:
                self.report({"ERROR"}, "Extension state not available.")
                return {"CANCELLED"}
            result = self.run(context, props)
            props.environment_status = result
            failed = result.startswith(("Cannot", "No ", "Unknown"))
            self.report({"ERROR"} if failed else {"INFO"}, result)
            return {"CANCELLED"} if failed else {"FINISHED"}
        except Exception:
            traceback.print_exc()
            self.report({"ERROR"}, "Managed studio operation failed. See system console.")
            return {"CANCELLED"}


class PCBSTUDIO_OT_add_custom_studio_light(_PCBStudioManagedStudioOperator, bpy.types.Operator):
    bl_idname = OPERATOR_ID_ADD_CUSTOM_LIGHT
    bl_label = "Add Light"
    bl_description = "Add a bounds-aware PCB Studio light from the selected starting preset"

    def run(self, context, props):
        return add_custom_light(context.scene, props, props.custom_light_preset)


class PCBSTUDIO_OT_apply_custom_light_preset(_PCBStudioManagedStudioOperator, bpy.types.Operator):
    bl_idname = OPERATOR_ID_APPLY_CUSTOM_LIGHT_PRESET
    bl_label = "Add Light Preset"
    bl_description = "Add a managed light using this product-photography preset"

    preset: bpy.props.StringProperty(default="LARGE_SOFTBOX")

    def run(self, context, props):
        return add_custom_light(context.scene, props, self.preset)


class PCBSTUDIO_OT_delete_custom_studio_light(_PCBStudioManagedStudioOperator, bpy.types.Operator):
    bl_idname = OPERATOR_ID_DELETE_CUSTOM_LIGHT
    bl_label = "Delete Selected Light"
    bl_description = "Delete only the selected PCB Studio custom light"

    def run(self, context, props):
        return delete_custom_light(props)


class PCBSTUDIO_OT_add_light_card(_PCBStudioManagedStudioOperator, bpy.types.Operator):
    bl_idname = OPERATOR_ID_ADD_LIGHT_CARD
    bl_label = "Add Reflection Card"
    bl_description = "Add a managed white, black, or silver reflection card"

    def run(self, context, props):
        return add_light_card(context.scene, props)


class PCBSTUDIO_OT_remove_light_card(_PCBStudioManagedStudioOperator, bpy.types.Operator):
    bl_idname = OPERATOR_ID_REMOVE_LIGHT_CARD
    bl_label = "Remove Selected Card"
    bl_description = "Remove only the selected PCB Studio reflection card"

    def run(self, context, props):
        return remove_light_card(props)


class PCBSTUDIO_OT_apply_floor_preset(_PCBStudioManagedStudioOperator, bpy.types.Operator):
    bl_idname = OPERATOR_ID_APPLY_FLOOR_PRESET
    bl_label = "Apply Floor Preset"
    bl_description = "Apply a professional managed floor finish"

    def run(self, context, props):
        return apply_floor_preset(context.scene, props, props.floor_preset)


class PCBSTUDIO_OT_floor_action(_PCBStudioManagedStudioOperator, bpy.types.Operator):
    bl_idname = OPERATOR_ID_FLOOR_ACTION
    bl_label = "Floor Action"
    bl_description = "Safely update only PCB Studio's managed floor system"

    action: bpy.props.EnumProperty(items=(
        ("FIT", "Fit Floor to Product", "Fit with a safe product margin"),
        ("CENTER", "Center Floor", "Center the floor under the product"),
        ("GROUND", "Ground Product", "Move the product vertically onto the floor"),
        ("RESET_GROUND", "Reset Ground Position", "Restore the saved product height"),
        ("RESET", "Reset Floor", "Reset floor transform values"),
        ("HIDE", "Hide Floor", "Switch to No Floor"),
        ("ENABLE", "Enable Floor", "Enable a standard floor"),
        ("MATERIAL", "Apply Material", "Apply the selected material preset"),
        ("REFLECTION", "Apply Reflection", "Apply the selected reflection preset"),
        ("STUDIO_PRESET", "Apply Studio Floor Preset", "Apply the selected floor setup"),
        ("INFINITE_PRESET", "Apply Infinity Preset", "Apply the selected infinity setup"),
    ))

    def run(self, context, props):
        from ..utils.floor import (
            apply_infinite_preset, apply_material_preset, apply_reflection_preset,
            apply_studio_floor_preset, center_floor, fit_floor_to_product,
            ground_product, reset_floor, reset_ground_position, update_floor_system,
        )
        if self.action == "FIT":
            return fit_floor_to_product(context.scene, props)
        if self.action == "CENTER":
            return center_floor(context.scene, props)
        if self.action == "GROUND":
            return ground_product(context.scene, props)
        if self.action == "RESET_GROUND":
            return reset_ground_position()
        if self.action == "RESET":
            return reset_floor(context.scene, props)
        if self.action == "HIDE":
            props.floor_mode = "NONE"
            return "Floor hidden."
        if self.action == "ENABLE":
            props.floor_mode = "STANDARD"
            return update_floor_system(context.scene, props)
        if self.action == "MATERIAL":
            return apply_material_preset(context.scene, props, props.floor_material)
        if self.action == "REFLECTION":
            return apply_reflection_preset(context.scene, props, props.floor_reflection_preset)
        if self.action == "STUDIO_PRESET":
            return apply_studio_floor_preset(context.scene, props, props.floor_studio_preset)
        if self.action == "INFINITE_PRESET":
            return apply_infinite_preset(context.scene, props, props.infinite_studio_preset)
        return "Unknown floor action."


class PCBSTUDIO_OT_studio_helper(_PCBStudioManagedStudioOperator, bpy.types.Operator):
    bl_idname = OPERATOR_ID_STUDIO_HELPER
    bl_label = "Studio Helper"
    bl_description = "Safely manage only PCB Studio-owned studio objects"

    action: bpy.props.EnumProperty(items=(
        ("AUTO_CENTER", "Auto Center Studio", "Center managed studio elements on the PCB"),
        ("FIT", "Fit Studio to PCB", "Rebuild managed studio dimensions from PCB bounds"),
        ("RESET", "Reset Studio", "Remove managed studio visual objects"),
        ("HIDE", "Hide Studio", "Hide managed studio objects in the viewport"),
        ("SHOW", "Show Studio", "Show enabled managed studio objects"),
        ("LOCK", "Lock Studio", "Prevent selection and transforms of managed studio objects"),
    ))

    def run(self, context, props):
        return studio_helper(context.scene, props, self.action)
