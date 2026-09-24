"""Operators for optional PCB smoothing, bevel, UVs, and layered surfaces."""

from __future__ import annotations

import traceback

import bpy

from ..constants import (
    OPERATOR_ID_APPLY_MICRO_BEVEL,
    OPERATOR_ID_CREATE_PCB_SURFACE,
    OPERATOR_ID_REMOVE_MICRO_BEVEL,
    OPERATOR_ID_SETUP_PCB_UV,
    OPERATOR_ID_SMOOTH_ALL,
    OPERATOR_ID_SMOOTH_SELECTED,
    PROP_SCENE_ATTR,
)
from ..utils.realism import (
    apply_micro_bevel,
    create_pcb_surface_material,
    pcb_mesh_objects,
    remove_micro_bevel,
    setup_planar_uv,
    smooth_components,
)


class _RealismOperator:
    def _props(self, context):
        return getattr(context.scene, PROP_SCENE_ATTR, None)

    def _finish(self, props, result: str):
        props.realism_status = result
        success = not result.startswith(("Select", "No ", "Cannot"))
        self.report({"INFO"} if success else {"ERROR"}, result)
        return {"FINISHED"} if success else {"CANCELLED"}

    def _fail(self):
        traceback.print_exc()
        self.report({"ERROR"}, "PCB realism operation failed. See system console.")
        return {"CANCELLED"}


class PCBSTUDIO_OT_smooth_selected_components(_RealismOperator, bpy.types.Operator):
    bl_idname = OPERATOR_ID_SMOOTH_SELECTED
    bl_label = "Smooth Selected"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            props = self._props(context)
            return self._finish(props, smooth_components(pcb_mesh_objects(True), props.smooth_angle))
        except Exception:
            return self._fail()


class PCBSTUDIO_OT_smooth_all_components(_RealismOperator, bpy.types.Operator):
    bl_idname = OPERATOR_ID_SMOOTH_ALL
    bl_label = "Smooth PCB Components"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            props = self._props(context)
            return self._finish(props, smooth_components(pcb_mesh_objects(False), props.smooth_angle))
        except Exception:
            return self._fail()


class PCBSTUDIO_OT_apply_micro_bevel(_RealismOperator, bpy.types.Operator):
    bl_idname = OPERATOR_ID_APPLY_MICRO_BEVEL
    bl_label = "Apply Micro Bevel"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            props = self._props(context)
            objects = pcb_mesh_objects(not props.realism_apply_all)
            result = apply_micro_bevel(
                objects, props.micro_bevel_preset, props.micro_bevel_width,
                props.micro_bevel_segments, props.micro_bevel_angle_limit,
            )
            return self._finish(props, result)
        except Exception:
            return self._fail()


class PCBSTUDIO_OT_remove_micro_bevel(_RealismOperator, bpy.types.Operator):
    bl_idname = OPERATOR_ID_REMOVE_MICRO_BEVEL
    bl_label = "Remove Micro Bevel"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            props = self._props(context)
            return self._finish(props, remove_micro_bevel(pcb_mesh_objects(not props.realism_apply_all)))
        except Exception:
            return self._fail()


class PCBSTUDIO_OT_setup_pcb_uv_mapping(_RealismOperator, bpy.types.Operator):
    bl_idname = OPERATOR_ID_SETUP_PCB_UV
    bl_label = "Setup PCB UV Mapping"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            props = self._props(context)
            return self._finish(props, setup_planar_uv(pcb_mesh_objects(True), props))
        except Exception:
            return self._fail()


class PCBSTUDIO_OT_create_pcb_surface_material(_RealismOperator, bpy.types.Operator):
    bl_idname = OPERATOR_ID_CREATE_PCB_SURFACE
    bl_label = "Create PCB Surface"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            props = self._props(context)
            return self._finish(props, create_pcb_surface_material(pcb_mesh_objects(True), props))
        except Exception:
            return self._fail()
