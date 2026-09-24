"""Headless Blender acceptance coverage for transactional Cycles devices."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pcb_studio
from pcb_studio.operators import professional_render as professional_render_operator
from pcb_studio.constants import COLLECTION_NAME, PROP_SCENE_ATTR
from pcb_studio.utils.cycles_devices import (
    configure_requested_cycles_device,
    detect_cycles_devices,
    restore_cycles_device_state,
    save_cycles_device_state,
)


def _state():
    preferences = bpy.context.preferences.addons["cycles"].preferences
    return (
        bpy.context.scene.cycles.device,
        preferences.compute_device_type,
        tuple((device.name, device.id, device.type, bool(device.use)) for device in preferences.devices),
    )


def _box():
    mesh = bpy.data.meshes.new("DeviceTestBoardMesh")
    mesh.from_pydata(
        [
            (-1, -0.7, -0.08), (1, -0.7, -0.08),
            (1, 0.7, -0.08), (-1, 0.7, -0.08),
            (-1, -0.7, 0.08), (1, -0.7, 0.08),
            (1, 0.7, 0.08), (-1, 0.7, 0.08),
        ],
        [],
        [
            (0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
            (1, 5, 6, 2), (2, 6, 7, 3), (4, 0, 3, 7),
        ],
    )
    mesh.update()
    obj = bpy.data.objects.new("DeviceTestBoard", mesh)
    bpy.data.collections[COLLECTION_NAME].objects.link(obj)
    material = bpy.data.materials.new("DeviceTestMaterial")
    material.use_nodes = True
    material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.02, 0.22, 0.04, 1.0)
    obj.data.materials.append(material)
    return obj


def _render(props, directory: Path, name: str, device: str, backend: str):
    props.final_output_directory = str(directory)
    props.final_filename = name
    props.overwrite_existing = True
    props.still_format = "CUSTOM"
    props.still_custom_width = 32
    props.still_custom_height = 32
    props.cycles_quality = "DRAFT"
    props.cycles_render_device = device
    props.cycles_gpu_backend = backend
    props.cycles_fallback_to_cpu = False
    before = _state()
    result = bpy.ops.pcbstudio.render_professional_still()
    after = _state()
    assert result == {"FINISHED"}, props.professional_render_status
    assert before == after
    assert (directory / f"{name}.png").is_file()
    return props.professional_render_status


def run():
    pcb_studio.register()
    try:
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete(use_global=False)
        collection = bpy.data.collections.new(COLLECTION_NAME)
        bpy.context.scene.collection.children.link(collection)
        _box()
        props = getattr(bpy.context.scene, PROP_SCENE_ATTR)
        props.pcb_imported = True
        assert bpy.ops.pcbstudio.prepare_scene() == {"FINISHED"}

        # Detection populates no persistent preference entries and recognizes
        # any device name Blender exposes, including the test MX110 here.
        before_detection = _state()
        devices = detect_cycles_devices(bpy.context.scene, bpy.context)
        assert _state() == before_detection
        assert any(device.is_cpu for device in devices)
        cuda_devices = [device for device in devices if device.backend == "CUDA"]
        print("Detected Cycles devices:", [(device.name, device.backend) for device in devices])

        with tempfile.TemporaryDirectory(prefix="pcbstudio_devices_") as temp_directory:
            temp = Path(temp_directory)
            cpu_status = _render(props, temp, "cpu_professional", "CPU", "AUTO")
            assert "Backend: CPU" in cpu_status

            if cuda_devices:
                gpu_status = _render(props, temp, "cuda_professional", "GPU", "CUDA")
                assert "Backend: CUDA" in gpu_status
                assert any(device.name in gpu_status for device in cuda_devices)

                auto_status = _render(props, temp, "auto_professional", "AUTO", "AUTO")
                assert "Backend: " in auto_status and "Backend: CPU" not in auto_status

        # Explicit unavailable GPU behavior is clear in both fallback modes.
        state = save_cycles_device_state(bpy.context.scene, bpy.context)
        before = _state()
        try:
            fallback = configure_requested_cycles_device(
                bpy.context.scene, "GPU", "METAL", True, bpy.context,
            )
            assert fallback.used_cpu and fallback.used_fallback
            assert "Falling back to CPU" in fallback.message
        finally:
            restore_cycles_device_state(bpy.context.scene, state, bpy.context)
        assert _state() == before

        state = save_cycles_device_state(bpy.context.scene, bpy.context)
        before = _state()
        try:
            try:
                configure_requested_cycles_device(
                    bpy.context.scene, "GPU", "METAL", False, bpy.context,
                )
            except ValueError as exc:
                assert "no usable" in str(exc).lower()
            else:
                raise AssertionError("Unavailable GPU without fallback did not fail")
        finally:
            restore_cycles_device_state(bpy.context.scene, state, bpy.context)
        assert _state() == before

        # A forced error inside the real Professional Still operator still
        # reaches its device-restore finally block.
        props.cycles_render_device = "GPU" if cuda_devices else "CPU"
        props.cycles_gpu_backend = "CUDA" if cuda_devices else "AUTO"
        props.cycles_fallback_to_cpu = False
        props.final_output_directory = tempfile.gettempdir()
        props.final_filename = "forced_failure"
        before = _state()
        original_render_still = professional_render_operator._render_still
        try:
            def _forced_failure():
                raise RuntimeError("forced render failure")

            professional_render_operator._render_still = _forced_failure
            try:
                result = bpy.ops.pcbstudio.render_professional_still()
            except RuntimeError as exc:
                # Blender propagates an ERROR report from a cancelled operator
                # to background Python callers.
                assert "forced render failure" in str(exc)
            else:
                assert result == {"CANCELLED"}
            assert "forced render failure" in props.professional_render_status
        finally:
            professional_render_operator._render_still = original_render_still
        assert _state() == before

        print("PCB Studio Cycles device acceptance tests passed.")
    finally:
        pcb_studio.unregister()


if __name__ == "__main__":
    run()
