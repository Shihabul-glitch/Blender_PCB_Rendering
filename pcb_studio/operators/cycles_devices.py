"""Operator for transactional Cycles device detection."""

from __future__ import annotations

import traceback

import bpy

from ..constants import OPERATOR_ID_REFRESH_CYCLES_DEVICES, PROP_SCENE_ATTR
from ..utils.cycles_devices import cycles_devices_to_json, detect_cycles_devices


class PCBSTUDIO_OT_refresh_cycles_devices(bpy.types.Operator):
    bl_idname = OPERATOR_ID_REFRESH_CYCLES_DEVICES
    bl_label = "Detect / Refresh Devices"
    bl_description = "Detect Cycles CPU/GPU devices without retaining preference changes"
    bl_options = {"REGISTER"}

    def execute(self, context):
        props = getattr(context.scene, PROP_SCENE_ATTR, None)
        if props is None:
            return {"CANCELLED"}
        try:
            devices = detect_cycles_devices(context.scene, context)
            props.cycles_detected_devices = cycles_devices_to_json(devices)
            gpu_count = sum(not device.is_cpu for device in devices)
            backends = sorted({
                device.backend for device in devices if not device.is_cpu
            })
            backend_text = ", ".join(backends) if backends else "none"
            props.cycles_device_status = (
                f"Detected {gpu_count} GPU device(s); backends: {backend_text}."
            )
            self.report({"INFO"}, props.cycles_device_status)
            return {"FINISHED"}
        except Exception:
            traceback.print_exc()
            props.cycles_device_status = "Cycles device detection failed."
            self.report({"ERROR"}, "Cycles device detection failed. See system console.")
            return {"CANCELLED"}
