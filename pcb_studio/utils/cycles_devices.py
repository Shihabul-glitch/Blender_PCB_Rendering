"""Transactional Cycles CPU/GPU discovery and render-device selection."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json

import bpy


CYCLES_GPU_BACKENDS = ("CUDA", "OPTIX", "HIP", "ONEAPI", "METAL")
AUTO_BACKEND_PRIORITY = ("OPTIX", "CUDA", "HIP", "ONEAPI", "METAL")


@dataclass(frozen=True)
class CyclesDeviceInfo:
    """One device exposed by the Cycles add-on preferences."""

    name: str
    identifier: str
    device_type: str
    backend: str
    is_cpu: bool


@dataclass(frozen=True)
class _CyclesDevicePreference:
    name: str
    identifier: str
    device_type: str
    use: bool


@dataclass(frozen=True)
class CyclesDeviceState:
    """Scene and user-preference state captured before a PCB Studio render."""

    scene_device: str
    compute_device_type: str
    devices: tuple[_CyclesDevicePreference, ...]


@dataclass(frozen=True)
class CyclesDeviceSelection:
    """Resolved device configuration used by one professional still render."""

    requested: str
    backend: str
    active_devices: tuple[str, ...]
    used_cpu: bool
    used_fallback: bool
    message: str


def get_cycles_preferences(context: bpy.types.Context | None = None):
    """Return Blender's built-in Cycles add-on preferences."""
    active_context = context or bpy.context
    addon = active_context.preferences.addons.get("cycles")
    if addon is None or addon.preferences is None:
        raise RuntimeError("Cycles add-on preferences are not available.")
    return addon.preferences


def _device_key(device) -> tuple[str, str, str]:
    return str(device.name), str(device.id), str(device.type)


def save_cycles_device_state(
    scene: bpy.types.Scene,
    context: bpy.types.Context | None = None,
) -> CyclesDeviceState:
    """Capture state without refreshing devices or mutating preferences."""
    preferences = get_cycles_preferences(context)
    devices = tuple(
        _CyclesDevicePreference(
            name=str(device.name),
            identifier=str(device.id),
            device_type=str(device.type),
            use=bool(device.use),
        )
        for device in preferences.devices
    )
    return CyclesDeviceState(
        scene_device=str(scene.cycles.device),
        compute_device_type=str(preferences.compute_device_type),
        devices=devices,
    )


def restore_cycles_device_state(
    scene: bpy.types.Scene,
    state: CyclesDeviceState,
    context: bpy.types.Context | None = None,
) -> list[str]:
    """Restore the exact pre-render Cycles state as far as Blender permits.

    ``get_devices()`` may populate new preference collection entries. Those
    entries are removed again when they did not exist in the snapshot, so a
    detection or render transaction does not leave in-session preference
    changes behind. PCB Studio never saves user preferences.
    """
    warnings: list[str] = []
    preferences = get_cycles_preferences(context)
    original = {
        (device.name, device.identifier, device.device_type): device
        for device in state.devices
    }

    try:
        preferences.compute_device_type = state.compute_device_type
    except (TypeError, ValueError, AttributeError) as exc:
        warnings.append(f"Could not restore Cycles backend: {exc}")

    try:
        for index in range(len(preferences.devices) - 1, -1, -1):
            device = preferences.devices[index]
            if _device_key(device) not in original:
                preferences.devices.remove(index)
    except (AttributeError, RuntimeError, TypeError) as exc:
        warnings.append(f"Could not remove temporary Cycles device entries: {exc}")

    for device in preferences.devices:
        saved = original.get(_device_key(device))
        if saved is None:
            continue
        try:
            device.use = saved.use
        except (AttributeError, TypeError) as exc:
            warnings.append(f"Could not restore {device.name}: {exc}")

    try:
        scene.cycles.device = state.scene_device
    except (TypeError, AttributeError) as exc:
        warnings.append(f"Could not restore scene Cycles device: {exc}")
    return warnings


def _discover_cycles_devices_unrestored(preferences) -> list[CyclesDeviceInfo]:
    """Refresh every backend Blender accepts, leaving restoration to caller."""
    discovered: dict[tuple[str, str], CyclesDeviceInfo] = {}
    cpu_devices: dict[tuple[str, str], CyclesDeviceInfo] = {}

    for backend in CYCLES_GPU_BACKENDS:
        try:
            preferences.compute_device_type = backend
        except (TypeError, ValueError, AttributeError):
            continue
        try:
            preferences.get_devices()
        except (RuntimeError, TypeError, AttributeError):
            continue

        for device in preferences.devices:
            device_type = str(device.type).upper()
            info = CyclesDeviceInfo(
                name=str(device.name),
                identifier=str(device.id),
                device_type=device_type,
                backend="CPU" if device_type == "CPU" else device_type,
                is_cpu=device_type == "CPU",
            )
            key = (info.identifier, info.device_type)
            if info.is_cpu:
                cpu_devices[key] = info
            elif device_type == backend:
                discovered[key] = info

    if not cpu_devices:
        cpu = CyclesDeviceInfo(
            name="CPU", identifier="CPU", device_type="CPU",
            backend="CPU", is_cpu=True,
        )
        cpu_devices[(cpu.identifier, cpu.device_type)] = cpu
    return [*discovered.values(), *cpu_devices.values()]


def detect_cycles_devices(
    scene: bpy.types.Scene,
    context: bpy.types.Context | None = None,
) -> list[CyclesDeviceInfo]:
    """Detect usable Cycles devices and restore preferences afterward."""
    state = save_cycles_device_state(scene, context)
    preferences = get_cycles_preferences(context)
    try:
        return _discover_cycles_devices_unrestored(preferences)
    finally:
        restore_cycles_device_state(scene, state, context)


def cycles_devices_to_json(devices: list[CyclesDeviceInfo]) -> str:
    return json.dumps([asdict(device) for device in devices], separators=(",", ":"))


def cycles_devices_from_json(value: str) -> list[CyclesDeviceInfo]:
    if not value:
        return []
    try:
        payload = json.loads(value)
        return [CyclesDeviceInfo(**item) for item in payload]
    except (TypeError, ValueError, KeyError):
        return []


def _configure_cycles_cpu(scene: bpy.types.Scene, preferences) -> tuple[str, ...]:
    try:
        preferences.compute_device_type = "NONE"
    except (TypeError, ValueError, AttributeError):
        pass
    cpu_names: list[str] = []
    for device in preferences.devices:
        is_cpu = str(device.type).upper() == "CPU"
        device.use = is_cpu
        if is_cpu:
            cpu_names.append(str(device.name))
    scene.cycles.device = "CPU"
    return tuple(cpu_names or ("CPU",))


def _select_backend(
    devices: list[CyclesDeviceInfo],
    requested_backend: str,
) -> tuple[str | None, list[CyclesDeviceInfo]]:
    gpu_devices = [device for device in devices if not device.is_cpu]
    if requested_backend != "AUTO":
        matching = [
            device for device in gpu_devices
            if device.backend == requested_backend
        ]
        return (requested_backend if matching else None), matching
    for backend in AUTO_BACKEND_PRIORITY:
        matching = [device for device in gpu_devices if device.backend == backend]
        if matching:
            return backend, matching
    return None, []


def _configure_cycles_gpu(
    scene: bpy.types.Scene,
    preferences,
    backend: str,
) -> tuple[str, ...]:
    preferences.compute_device_type = backend
    preferences.get_devices()
    active: list[str] = []
    for device in preferences.devices:
        enabled = str(device.type).upper() == backend
        device.use = enabled
        if enabled:
            active.append(str(device.name))
    if not active:
        raise ValueError(f"No usable {backend} Cycles device was detected.")
    scene.cycles.device = "GPU"
    return tuple(active)


def configure_requested_cycles_device(
    scene: bpy.types.Scene,
    requested_device: str,
    requested_backend: str,
    fallback_to_cpu: bool,
    context: bpy.types.Context | None = None,
) -> CyclesDeviceSelection:
    """Resolve and configure one temporary PCB Studio Cycles device choice.

    The caller must wrap this function with :func:`save_cycles_device_state`
    and :func:`restore_cycles_device_state` in a ``try/finally`` transaction.
    """
    preferences = get_cycles_preferences(context)
    requested_device = requested_device.upper()
    requested_backend = requested_backend.upper()

    if requested_device == "CPU":
        active = _configure_cycles_cpu(scene, preferences)
        return CyclesDeviceSelection(
            requested="CPU", backend="CPU", active_devices=active,
            used_cpu=True, used_fallback=False,
            message=f"Rendering with Cycles CPU: {', '.join(active)}.",
        )

    devices = _discover_cycles_devices_unrestored(preferences)
    backend_request = "AUTO" if requested_device == "AUTO" else requested_backend
    backend, matching = _select_backend(devices, backend_request)
    if backend is not None and matching:
        active = _configure_cycles_gpu(scene, preferences, backend)
        return CyclesDeviceSelection(
            requested=requested_device,
            backend=backend,
            active_devices=active,
            used_cpu=False,
            used_fallback=False,
            message=(
                f"Rendering with Cycles {backend} GPU: "
                f"{', '.join(active)}."
            ),
        )

    if requested_device == "AUTO":
        active = _configure_cycles_cpu(scene, preferences)
        return CyclesDeviceSelection(
            requested="AUTO", backend="CPU", active_devices=active,
            used_cpu=True, used_fallback=False,
            message="No usable Cycles GPU detected; AUTO selected CPU.",
        )

    backend_label = requested_backend if requested_backend != "AUTO" else "compatible"
    if fallback_to_cpu:
        active = _configure_cycles_cpu(scene, preferences)
        return CyclesDeviceSelection(
            requested="GPU", backend="CPU", active_devices=active,
            used_cpu=True, used_fallback=True,
            message=(
                f"Requested {backend_label} GPU is unavailable. "
                "Falling back to CPU."
            ),
        )
    raise ValueError(
        f"{backend_label} GPU requested but no usable "
        f"{backend_label} Cycles device was detected."
    )


def format_cycles_render_status(selection: CyclesDeviceSelection, props) -> str:
    samples = {
        "DRAFT": 64, "STANDARD": 256, "HIGH": 512, "ULTRA": 1024,
    }.get(props.cycles_quality, 256)
    active = ", ".join(selection.active_devices)
    return (
        "Render Engine: Cycles | "
        f"Requested: {selection.requested} | "
        f"Backend: {selection.backend} | "
        f"Active Device: {active} | "
        f"Quality: {props.cycles_quality.title()} | "
        f"Samples: {samples} adaptive max | Denoising: Enabled"
    )
