"""Operators for PCB Studio's non-animated camera controls."""

from __future__ import annotations

import traceback

import bpy

from ..constants import (
    OPERATOR_ID_AIM_CAMERA_PCB,
    OPERATOR_ID_AIM_CAMERA_SELECTED,
    OPERATOR_ID_CAMERA_NUDGE,
    OPERATOR_ID_FIT_CAMERA_SELECTED,
    OPERATOR_ID_RESET_CAMERA,
    OPERATOR_ID_RESET_CAMERA_TARGET,
    OPERATOR_ID_RESTORE_CAMERA_VIEW,
    OPERATOR_ID_SAVE_CAMERA_VIEW,
    OPERATOR_ID_SET_CAMERA_MODE,
    PROP_SCENE_ATTR,
)
from ..utils.camera_controls import (
    aim_camera_at_pcb,
    aim_camera_at_selected,
    fit_camera_to_selected,
    nudge_camera,
    reset_camera,
    restore_camera_view,
    save_camera_view,
    set_camera_control_mode,
)


_ACTION_ITEMS = [
    ("LEFT", "Left", "Move camera left"),
    ("RIGHT", "Right", "Move camera right"),
    ("UP", "Up", "Move camera up"),
    ("DOWN", "Down", "Move camera down"),
    ("FORWARD", "Forward", "Move camera forward"),
    ("BACK", "Back", "Move camera backward"),
    ("DOLLY_IN", "Dolly In", "Move closer without changing focal length"),
    ("DOLLY_OUT", "Dolly Out", "Move farther without changing focal length"),
    ("PAN_LEFT", "Pan Left", "Move camera and target left together"),
    ("PAN_RIGHT", "Pan Right", "Move camera and target right together"),
    ("PAN_UP", "Pan Up", "Move camera and target up together"),
    ("PAN_DOWN", "Pan Down", "Move camera and target down together"),
    ("ORBIT_LEFT", "Orbit Left", "Orbit the still camera left around its target"),
    ("ORBIT_RIGHT", "Orbit Right", "Orbit the still camera right around its target"),
    ("ORBIT_UP", "Orbit Up", "Orbit the still camera upward around its target"),
    ("ORBIT_DOWN", "Orbit Down", "Orbit the still camera downward around its target"),
    ("ROLL_LEFT", "Roll Left", "Roll the camera counter-clockwise"),
    ("ROLL_RIGHT", "Roll Right", "Roll the camera clockwise"),
    ("ROLL_RESET", "Reset Roll", "Reset camera roll to zero"),
]


def _is_error(message: str) -> bool:
    markers = (
        "not found", "No PCB", "No saved", "Select one", "Select exactly",
        "invalid", "controls are locked", "Unknown", "not available", "Could not",
    )
    return any(marker in message for marker in markers)


def _finish(operator: bpy.types.Operator, context: bpy.types.Context, message: str) -> set[str]:
    props = getattr(context.scene, PROP_SCENE_ATTR, None)
    if props is not None:
        props.camera_status = message
    error = _is_error(message)
    operator.report({"ERROR"} if error else {"INFO"}, message)
    return {"CANCELLED"} if error else {"FINISHED"}


class _CameraControlOperator:
    """Shared exception handling for camera control operators."""

    def execute(self, context: bpy.types.Context | None) -> set[str]:
        if context is None:
            self.report({"ERROR"}, "No active Blender context.")
            return {"CANCELLED"}
        try:
            return _finish(self, context, self.run(context))
        except Exception:
            traceback.print_exc()
            self.report({"ERROR"}, "Unexpected camera control error. See system console.")
            return {"CANCELLED"}


class PCBSTUDIO_OT_camera_nudge(_CameraControlOperator, bpy.types.Operator):
    """Move, pan, orbit, or roll the still camera by one step."""

    bl_idname = OPERATOR_ID_CAMERA_NUDGE
    bl_label = "Adjust Still Camera"
    bl_description = "Adjust the still camera without creating animation keyframes"
    bl_options = {"REGISTER", "UNDO"}

    action: bpy.props.EnumProperty(items=_ACTION_ITEMS, options={"HIDDEN"})

    @classmethod
    def description(cls, context, properties) -> str:
        descriptions = {identifier: description for identifier, _label, description in _ACTION_ITEMS}
        return descriptions.get(properties.action, cls.bl_description)

    def run(self, context: bpy.types.Context) -> str:
        return nudge_camera(context.scene, self.action)


class PCBSTUDIO_OT_set_camera_control_mode(_CameraControlOperator, bpy.types.Operator):
    """Enable Auto Target or unlock manual camera rotation."""

    bl_idname = OPERATOR_ID_SET_CAMERA_MODE
    bl_label = "Set Camera Control Mode"
    bl_description = "Enable PCB Studio targeting or unlock free camera rotation"
    bl_options = {"REGISTER", "UNDO"}

    mode: bpy.props.EnumProperty(
        items=(
            ("AUTO_TARGET", "Auto Target", "Enable managed camera targeting"),
            ("MANUAL", "Manual", "Mute managed targeting for free rotation"),
        ),
        options={"HIDDEN"},
    )

    def run(self, context: bpy.types.Context) -> str:
        props = getattr(context.scene, PROP_SCENE_ATTR, None)
        if props is None:
            return "Extension state not available."
        context.scene["pcbstudio_camera_batch_update"] = True
        try:
            props.camera_control_mode = self.mode
        finally:
            context.scene["pcbstudio_camera_batch_update"] = False
        return set_camera_control_mode(context.scene, self.mode)


class PCBSTUDIO_OT_aim_camera_at_pcb(_CameraControlOperator, bpy.types.Operator):
    bl_idname = OPERATOR_ID_AIM_CAMERA_PCB
    bl_label = "Aim at PCB"
    bl_description = "Aim at the PCB center without moving the camera"
    bl_options = {"REGISTER", "UNDO"}

    def run(self, context: bpy.types.Context) -> str:
        return aim_camera_at_pcb(context.scene)


class PCBSTUDIO_OT_aim_camera_at_selected(_CameraControlOperator, bpy.types.Operator):
    bl_idname = OPERATOR_ID_AIM_CAMERA_SELECTED
    bl_label = "Aim at Selected"
    bl_description = "Aim at the center of exactly one selected PCB component"
    bl_options = {"REGISTER", "UNDO"}

    def run(self, context: bpy.types.Context) -> str:
        return aim_camera_at_selected(context.scene, context)


class PCBSTUDIO_OT_reset_camera_target(_CameraControlOperator, bpy.types.Operator):
    bl_idname = OPERATOR_ID_RESET_CAMERA_TARGET
    bl_label = "Reset Target"
    bl_description = "Return the camera target and its offsets to the PCB center"
    bl_options = {"REGISTER", "UNDO"}

    def run(self, context: bpy.types.Context) -> str:
        result = aim_camera_at_pcb(context.scene)
        return result.replace("aimed at PCB center", "target reset to PCB center")


class PCBSTUDIO_OT_fit_camera_selected(_CameraControlOperator, bpy.types.Operator):
    bl_idname = OPERATOR_ID_FIT_CAMERA_SELECTED
    bl_label = "Fit Selected"
    bl_description = "Frame exactly one selected PCB component"
    bl_options = {"REGISTER", "UNDO"}

    def run(self, context: bpy.types.Context) -> str:
        return fit_camera_to_selected(context.scene, context)


class PCBSTUDIO_OT_save_camera_view(_CameraControlOperator, bpy.types.Operator):
    bl_idname = OPERATOR_ID_SAVE_CAMERA_VIEW
    bl_label = "Save View"
    bl_description = "Save camera transform, target, lens, and control mode"
    bl_options = {"REGISTER", "UNDO"}

    def run(self, context: bpy.types.Context) -> str:
        return save_camera_view(context.scene)


class PCBSTUDIO_OT_restore_camera_view(_CameraControlOperator, bpy.types.Operator):
    bl_idname = OPERATOR_ID_RESTORE_CAMERA_VIEW
    bl_label = "Restore View"
    bl_description = "Restore the last camera view saved in this scene"
    bl_options = {"REGISTER", "UNDO"}

    def run(self, context: bpy.types.Context) -> str:
        return restore_camera_view(context.scene)


class PCBSTUDIO_OT_reset_camera(_CameraControlOperator, bpy.types.Operator):
    bl_idname = OPERATOR_ID_RESET_CAMERA
    bl_label = "Reset Camera"
    bl_description = "Restore the 75 mm Front Flat view and fit the PCB"
    bl_options = {"REGISTER", "UNDO"}

    def run(self, context: bpy.types.Context) -> str:
        return reset_camera(context.scene)


CAMERA_CONTROL_OPERATOR_CLASSES = (
    PCBSTUDIO_OT_camera_nudge,
    PCBSTUDIO_OT_set_camera_control_mode,
    PCBSTUDIO_OT_aim_camera_at_pcb,
    PCBSTUDIO_OT_aim_camera_at_selected,
    PCBSTUDIO_OT_reset_camera_target,
    PCBSTUDIO_OT_fit_camera_selected,
    PCBSTUDIO_OT_save_camera_view,
    PCBSTUDIO_OT_restore_camera_view,
    PCBSTUDIO_OT_reset_camera,
)
