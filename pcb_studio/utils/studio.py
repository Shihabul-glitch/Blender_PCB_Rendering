"""Professional, bounds-aware PCB product studio utilities.

This module upgrades the original managed lights and background instead of
creating a second rig.  Nothing here is parented to PCB_MODEL_ROOT or to any
camera-animation helper, so turntable, camera-orbit, and flyover motion stay
isolated from the studio.
"""

from __future__ import annotations

from math import cos, log, pi, radians, sin
from pathlib import Path

import bpy
from mathutils import Euler, Quaternion, Vector

from ..constants import (
    BACKGROUND_LIGHT_2_NAME,
    BACKGROUND_LIGHT_NAME,
    BACKGROUND_FLOOR_MATERIAL_NAME,
    BACKGROUND_MATERIAL_NAME,
    BACKGROUND_NAME,
    BACKGROUND_RECEIVER_COLLECTION,
    COLLECTION_NAME,
    CUSTOM_LIGHT_PREFIX,
    CYCLORAMA_CURVE_SEGMENTS,
    FRONT_LIGHT_LEFT_NAME,
    FRONT_LIGHT_RIGHT_NAME,

    FILL_LIGHT_NAME,
    KEY_LIGHT_NAME,
    LIGHT_TARGET_NAME,
    LIGHT_CARD_MATERIAL_PREFIX,
    LIGHT_CARD_PREFIX,
    MANAGED_COMPOSITOR_TAG,
    PCB_STUDIO_WORLD_NAME,
    PEDESTAL_MATERIAL_NAME,
    PEDESTAL_NAME,
    REFLECTION_PLANE_NAME,
    RIM_LIGHT_2_NAME,
    RIM_LIGHT_NAME,
    TOP_LIGHT_NAME,
)
from .camera import get_or_create_render_setup_collection
from .geometry import BoundingBox, compute_pcb_bounds


PRODUCT_LIGHT_NAMES = (
    KEY_LIGHT_NAME,
    FILL_LIGHT_NAME,
    RIM_LIGHT_NAME,
    RIM_LIGHT_2_NAME,
    FRONT_LIGHT_LEFT_NAME,
    FRONT_LIGHT_RIGHT_NAME,

    TOP_LIGHT_NAME,
)
BACKGROUND_LIGHT_NAMES = (BACKGROUND_LIGHT_NAME, BACKGROUND_LIGHT_2_NAME)
ALL_STUDIO_LIGHT_NAMES = PRODUCT_LIGHT_NAMES + BACKGROUND_LIGHT_NAMES


PRESET_VALUES: dict[str, dict[str, object]] = {
    # Legacy identifiers remain valid for saved .blend files.
    "BRIGHT_STUDIO": {
        "master_product_brightness": 1.05,
        "lighting_contrast": 0.78,
        "key_power": 700.0,
        "fill_strength": 0.72,
        "left_rim_power": 180.0,
        "right_rim_power": 180.0,
        "top_light_power": 300.0,
        "background_preset": "WHITE",
        "background_light_mode": "OFF",
        "background_glow_enabled": False,
        "reflection_surface": "SATIN",
        "floor_color": (0.52, 0.52, 0.54, 1.0),
        "floor_roughness": 0.42,
        "left_rim_enabled": True,
        "right_rim_enabled": False,
        "top_light_enabled": False,
        "front_left_enabled": False,
        "front_right_enabled": False,
    },
    "DARK_STUDIO": {
        "master_product_brightness": 1.15,
        "lighting_contrast": 1.35,
        "key_power": 720.0,
        "fill_strength": 0.24,
        "left_rim_power": 560.0,
        "right_rim_power": 500.0,
        "top_light_power": 380.0,
        "background_preset": "BLACK",
        "background_light_mode": "CENTER_GLOW",
        "background_glow_enabled": True,
        "background_glow_strength": 180.0,
        "reflection_surface": "SATIN",
    },
    "PRODUCT_SHOT": {
        "master_product_brightness": 1.0,
        "lighting_contrast": 1.0,
        "key_power": 680.0,
        "fill_strength": 0.45,
        "left_rim_power": 300.0,
        "right_rim_power": 260.0,
        "top_light_power": 340.0,
        "background_preset": "DARK_GRAY",
        "background_light_mode": "OFF",
        "background_glow_enabled": False,
        "reflection_surface": "SATIN",
        "left_rim_enabled": True,
        "right_rim_enabled": False,
        "top_light_enabled": False,
        "front_left_enabled": False,
        "front_right_enabled": False,
    },
    "PCB_SHOWCASE": {
        "master_product_brightness": 1.16,
        "lighting_contrast": 1.12,
        "key_power": 720.0,
        "fill_strength": 0.38,
        "left_rim_power": 420.0,
        "right_rim_power": 400.0,
        "top_light_power": 470.0,
        "background_preset": "DARK_GRAY",
        "background_light_mode": "CENTER_GLOW",
        "background_glow_enabled": True,
        "background_glow_strength": 150.0,
        "reflection_surface": "SATIN",
        "left_rim_enabled": True,
        "right_rim_enabled": False,
        "top_light_enabled": False,
        "front_left_enabled": False,
        "front_right_enabled": False,
    },
    "PREMIUM_DARK": {
        "studio_lighting_enabled": True,
        "master_product_brightness": 1.20,
        "lighting_contrast": 1.28,
        "shadow_softness": 1.15,
        "key_enabled": True,
        "key_power": 760.0,
        "key_use_temperature": True,
        "key_temperature": 5600.0,
        "key_size": 0.60,
        "key_azimuth": radians(42.0),
        "key_elevation": radians(48.0),
        "key_distance": 2.45,
        "fill_enabled": True,
        "fill_power": 700.0,
        "fill_strength": 0.30,
        "fill_size": 1.80,
        "left_rim_enabled": True,
        "left_rim_power": 540.0,
        "left_rim_color": (0.72, 0.84, 1.0),
        "right_rim_enabled": False,
        "right_rim_power": 500.0,
        "right_rim_color": (1.0, 0.92, 0.82),
        "top_light_enabled": False,
        "top_light_power": 440.0,
        "background_preset": "STUDIO_GRADIENT",
        "background_color": (0.006, 0.008, 0.013, 1.0),
        "background_color_2": (0.025, 0.032, 0.045, 1.0),
        "background_light_mode": "CENTER_GLOW",
        "background_glow_enabled": True,
        "background_glow_color": (0.015, 0.10, 0.80),
        "background_glow_strength": 220.0,
        "background_glow_size": 1.45,
        "reflection_surface": "SATIN",
        "floor_color": (0.012, 0.016, 0.024, 1.0),
        "floor_roughness": 0.34,
        "floor_metallic": 0.05,
        "floor_reflection_strength": 0.62,
        "stage_type": "FLOOR",
        "world_background_color": (0.002, 0.003, 0.005, 1.0),
        "color_look": "PRODUCT",
        "color_exposure": 0.15,
        "front_left_enabled": False,
        "front_right_enabled": False,
    },
    "CLEAN_COMMERCIAL": {
        "master_product_brightness": 1.0,
        "lighting_contrast": 0.82,
        "shadow_softness": 1.45,
        "key_power": 690.0,
        "key_temperature": 5600.0,
        "fill_strength": 0.68,
        "left_rim_power": 130.0,
        "right_rim_power": 130.0,
        "top_light_power": 250.0,
        "background_preset": "WHITE",
        "background_light_mode": "OFF",
        "background_glow_enabled": False,
        "reflection_surface": "SATIN",
        "floor_color": (0.58, 0.58, 0.60, 1.0),
        "floor_roughness": 0.46,
        "world_background_color": (0.30, 0.30, 0.30, 1.0),
        "color_look": "NATURAL",
        "color_exposure": 0.0,
        "left_rim_enabled": True,
        "right_rim_enabled": False,
        "top_light_enabled": False,
        "front_left_enabled": False,
        "front_right_enabled": False,
    },
    "ELECTRIC_BLUE": {
        "master_product_brightness": 1.16,
        "lighting_contrast": 1.25,
        "key_power": 750.0,
        "key_temperature": 5600.0,
        "fill_strength": 0.30,
        "left_rim_power": 560.0,
        "left_rim_color": (0.12, 0.36, 1.0),
        "right_rim_power": 400.0,
        "right_rim_color": (0.82, 0.90, 1.0),
        "top_light_power": 420.0,
        "top_light_color": (1.0, 0.98, 0.94),
        "background_preset": "STUDIO_GRADIENT",
        "background_color": (0.003, 0.008, 0.028, 1.0),
        "background_color_2": (0.006, 0.025, 0.12, 1.0),
        "background_light_mode": "CENTER_GLOW",
        "background_glow_enabled": True,
        "background_glow_color": (0.01, 0.08, 1.0),
        "background_glow_strength": 520.0,
        "reflection_surface": "SATIN",
        "floor_color": (0.006, 0.012, 0.032, 1.0),
        "floor_roughness": 0.30,
        "color_look": "PRODUCT",
        "color_exposure": 0.10,
        "left_rim_enabled": True,
        "right_rim_enabled": False,
        "top_light_enabled": False,
        "front_left_enabled": False,
        "front_right_enabled": False,
    },
    "WARM_AMBER": {
        "master_product_brightness": 1.14,
        "lighting_contrast": 1.22,
        "key_power": 740.0,
        "key_temperature": 5000.0,
        "fill_strength": 0.30,
        "left_rim_power": 470.0,
        "left_rim_color": (1.0, 0.42, 0.08),
        "right_rim_power": 360.0,
        "right_rim_color": (1.0, 0.86, 0.68),
        "top_light_power": 410.0,
        "top_light_color": (1.0, 0.98, 0.94),
        "background_preset": "STUDIO_GRADIENT",
        "background_color": (0.010, 0.005, 0.003, 1.0),
        "background_color_2": (0.09, 0.020, 0.004, 1.0),
        "background_light_mode": "CENTER_GLOW",
        "background_glow_enabled": True,
        "background_glow_color": (1.0, 0.16, 0.01),
        "background_glow_strength": 460.0,
        "reflection_surface": "SATIN",
        "floor_color": (0.018, 0.012, 0.009, 1.0),
        "floor_roughness": 0.34,
        "color_look": "PRODUCT",
        "color_exposure": 0.10,
        "left_rim_enabled": True,
        "right_rim_enabled": False,
        "top_light_enabled": False,
        "front_left_enabled": False,
        "front_right_enabled": False,
    },
    "DRAMATIC_RIM": {
        "master_product_brightness": 1.08,
        "lighting_contrast": 1.70,
        "key_power": 610.0,
        "fill_strength": 0.12,
        "left_rim_power": 920.0,
        "right_rim_power": 820.0,
        "top_light_power": 320.0,
        "background_preset": "BLACK",
        "background_light_mode": "OFF",
        "background_glow_enabled": False,
        "reflection_surface": "SATIN",
        "right_rim_enabled": True,
    },
    "MACRO_DETAIL": {
        "master_product_brightness": 1.08,
        "lighting_contrast": 1.08,
        "shadow_softness": 0.75,
        "key_power": 580.0,
        "key_size": 0.35,
        "fill_strength": 0.42,
        "left_rim_power": 360.0,
        "right_rim_power": 320.0,
        "top_light_power": 620.0,
        "top_light_width": 0.18,
        "top_light_length": 1.4,
        "background_preset": "DARK_GRAY",
        "background_light_mode": "OFF",
        "reflection_surface": "SATIN",
        "top_light_enabled": True,
    },
}

# New product-photography presets use the same legacy managed rig and property
# names, so saved 2.3.2 scenes and scripts remain compatible.
PRESET_VALUES.update({
    "CLEAN_WHITE_PRODUCT": {**PRESET_VALUES["CLEAN_COMMERCIAL"], "background_preset": "PURE_WHITE", "backdrop_type": "INFINITY_CYCLORAMA", "reflection_surface": "ACRYLIC"},
    "APPLE_SOFT_STUDIO": {**PRESET_VALUES["CLEAN_COMMERCIAL"], "shadow_softness": 1.9, "key_size": 0.90, "fill_size": 1.00, "background_preset": "SOFT_WHITE", "reflection_surface": "FROSTED"},
    "PREMIUM_BLACK": {**PRESET_VALUES["PREMIUM_DARK"], "background_preset": "MATTE_BLACK", "reflection_surface": "SATIN"},
    "DRAMATIC_EDGE": {**PRESET_VALUES["DRAMATIC_RIM"], "background_preset": "GRAPHITE", "left_rim_power": 980.0, "right_rim_power": 900.0},
    "METALLIC_HIGHLIGHT": {**PRESET_VALUES["PRODUCT_SHOT"], "top_light_power": 720.0, "top_light_width": 0.16, "top_light_length": 3.2, "reflection_surface": "METALLIC"},
    "PCB_MACRO": {**PRESET_VALUES["MACRO_DETAIL"], "background_preset": "GRAPHITE", "reflection_surface": "MATTE"},
    "COMMERCIAL_CATALOG": {**PRESET_VALUES["CLEAN_COMMERCIAL"], "background_preset": "LIGHT_GRAY", "reflection_surface": "MATTE"},
    "CINEMATIC_BLUE": {**PRESET_VALUES["ELECTRIC_BLUE"], "background_preset": "MIDNIGHT_BLUE", "backdrop_type": "GRADIENT_CYCLORAMA"},
    "WARM_LUXURY": {**PRESET_VALUES["WARM_AMBER"], "background_preset": "WARM_GRADIENT", "reflection_surface": "SATIN"},
})

FLOOR_PRESET_VALUES = {
    "WHITE_ACRYLIC": ("ACRYLIC", (0.82, 0.82, 0.84, 1.0), 0.12, 0.02, 0.88),
    "BLACK_ACRYLIC": ("ACRYLIC", (0.008, 0.010, 0.014, 1.0), 0.10, 0.08, 0.90),
    "PREMIUM_SATIN": ("SATIN", (0.018, 0.022, 0.032, 1.0), 0.32, 0.05, 0.65),
    "MIRROR_BLACK": ("MIRROR", (0.004, 0.005, 0.008, 1.0), 0.025, 0.92, 1.0),
    "MATTE_GRAY": ("MATTE", (0.22, 0.23, 0.25, 1.0), 0.78, 0.0, 0.12),
    "DARK_GLASS": ("DARK_GLASS", (0.008, 0.012, 0.020, 1.0), 0.12, 0.35, 0.82),
}

CUSTOM_LIGHT_PRESETS = {
    "LARGE_SOFTBOX": ("AREA", 700.0, 1.8, 1.8, (-1.8, -2.0, 2.2)),
    "SIDE_STRIP": ("STRIP", 520.0, 0.22, 2.6, (-2.0, 0.0, 1.2)),
    "TOP_STRIP": ("TOP", 620.0, 0.24, 3.0, (0.0, 0.0, 2.4)),
    "EDGE_RIM": ("RIM", 700.0, 0.18, 2.2, (1.8, 1.3, 1.3)),
    "OVERHEAD": ("TOP", 540.0, 2.0, 2.0, (0.0, 0.0, 2.8)),
    "ACCENT_SPOT": ("SPOT", 420.0, 0.35, 0.35, (1.5, -1.4, 1.8)),
}


def _get_bounds() -> BoundingBox | None:
    collection = bpy.data.collections.get(COLLECTION_NAME)
    if collection is None:
        return None
    bounds = compute_pcb_bounds(collection)
    return bounds if bounds.is_valid else None


def _ensure_area_light(name: str) -> bpy.types.Object:
    collection = get_or_create_render_setup_collection()
    obj = bpy.data.objects.get(name)
    if obj is None:
        data = bpy.data.lights.new(name=name, type="AREA")
        obj = bpy.data.objects.new(name, data)
        collection.objects.link(obj)
    elif obj.type != "LIGHT" or obj.data.type != "AREA":
        obj.data = bpy.data.lights.new(name=name, type="AREA")
    obj["pcbstudio_managed"] = True
    return obj


def _ensure_light_target(center: Vector) -> bpy.types.Object:
    target = bpy.data.objects.get(LIGHT_TARGET_NAME)
    if target is None:
        target = bpy.data.objects.new(LIGHT_TARGET_NAME, None)
        target.empty_display_type = "PLAIN_AXES"
        get_or_create_render_setup_collection().objects.link(target)
    target.location = center
    target["pcbstudio_managed"] = True
    return target


def _aim_object(obj: bpy.types.Object, target: Vector, roll: float = 0.0) -> None:
    direction = target - obj.location
    if direction.length <= 1e-8:
        return
    rotation = direction.to_track_quat("-Z", "Y")
    if roll:
        rotation = Quaternion(direction.normalized(), roll) @ rotation
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = rotation


def _kelvin_to_rgb(kelvin: float) -> tuple[float, float, float]:
    """Return a stable approximate black-body RGB value for UI temperatures."""
    temperature = max(1000.0, min(40000.0, kelvin)) / 100.0
    if temperature <= 66.0:
        red = 255.0
        green = 99.4708025861 * log(temperature) - 161.1195681661
        blue = 0.0 if temperature <= 19.0 else 138.5177312231 * log(temperature - 10.0) - 305.0447927307
    else:
        red = 329.698727446 * ((temperature - 60.0) ** -0.1332047592)
        green = 288.1221695283 * ((temperature - 60.0) ** -0.0755148492)
        blue = 255.0
    clamp = lambda value: max(0.0, min(255.0, value)) / 255.0
    return clamp(red), clamp(green), clamp(blue)


def _spherical_position(
    center: Vector,
    max_dim: float,
    azimuth: float,
    elevation: float,
    distance: float,
    horizontal_offset: float,
    vertical_offset: float,
) -> Vector:
    radius = max(max_dim * distance, max_dim * 0.1)
    horizontal = cos(elevation) * radius
    return center + Vector((
        sin(azimuth) * horizontal + horizontal_offset * max_dim,
        -cos(azimuth) * horizontal,
        sin(elevation) * radius + vertical_offset * max_dim,
    ))


def _set_light(
    name: str,
    enabled: bool,
    power: float,
    color: tuple[float, float, float],
    size: float,
    location: Vector,
    target: Vector,
    max_dim: float,
    master: float,
    softness: float,
    *,
    shape: str = "DISK",
    size_y: float | None = None,
    roll: float = 0.0,
) -> bpy.types.Object:
    light = _ensure_area_light(name)
    for constraint in list(light.constraints):
        if constraint.type in {"DAMPED_TRACK", "TRACK_TO"}:
            light.constraints.remove(constraint)
    legacy_target = bpy.data.objects.get(f"{name}_track_target")
    if legacy_target is not None:
        bpy.data.objects.remove(legacy_target, do_unlink=True)
    light.hide_render = not enabled
    light.hide_viewport = not enabled
    light.data.energy = max(0.0, power * max_dim * master)
    light.data.color = tuple(max(0.0, min(1.0, component)) for component in color)
    light.data.shape = shape
    light.data.size = max(max_dim * size * softness, max_dim * 0.01)
    if shape == "RECTANGLE" and size_y is not None:
        light.data.size_y = max(max_dim * size_y * softness, max_dim * 0.01)
    light.location = location
    _aim_object(light, target, roll)
    if hasattr(light, "light_linking"):
        light.light_linking.receiver_collection = None
    return light


def _update_product_lights(bounds: BoundingBox, props) -> None:
    center = bounds.center
    max_dim = max(bounds.max_dimension, 1e-6)
    _ensure_light_target(center)
    enabled_master = bool(props.studio_lighting_enabled)
    master = max(0.0, props.master_product_brightness * props.lighting_intensity)
    contrast = max(0.25, props.lighting_contrast * max(0.25, props.shadow_strength))
    softness = max(0.25, props.shadow_softness)

    key_color = _kelvin_to_rgb(props.key_temperature) if props.key_use_temperature else tuple(props.key_color)
    key_location = _spherical_position(
        center, max_dim, props.key_azimuth, props.key_elevation,
        props.key_distance, props.key_horizontal_offset, props.key_vertical_offset,
    )
    _set_light(
        KEY_LIGHT_NAME, enabled_master and props.key_enabled,
        props.key_power * (0.85 + 0.15 * contrast), key_color,
        props.key_size, key_location, center, max_dim, master, softness,
    )

    fill_location = _spherical_position(
        center, max_dim, props.fill_azimuth, props.fill_elevation,
        props.fill_distance, props.fill_horizontal_offset, props.fill_vertical_offset,
    )
    _set_light(
        FILL_LIGHT_NAME, enabled_master and props.fill_enabled,
        props.fill_power * props.fill_strength / contrast, tuple(props.fill_color),
        props.fill_size, fill_location, center, max_dim, master, softness,
    )

    for name, prefix in ((RIM_LIGHT_NAME, "left_rim"), (RIM_LIGHT_2_NAME, "right_rim")):
        location = _spherical_position(
            center, max_dim,
            getattr(props, f"{prefix}_azimuth"), getattr(props, f"{prefix}_elevation"),
            getattr(props, f"{prefix}_distance"), getattr(props, f"{prefix}_horizontal_offset"),
            getattr(props, f"{prefix}_vertical_offset"),
        )
        _set_light(
            name, enabled_master and getattr(props, f"{prefix}_enabled"),
            getattr(props, f"{prefix}_power") * (0.75 + 0.25 * contrast),
            tuple(getattr(props, f"{prefix}_color")), getattr(props, f"{prefix}_size"),
            location, center, max_dim, master, softness,
        )

    top_location = center + Vector((
        props.highlight_position * max_dim,
        props.top_light_front_back * max_dim,
        props.top_light_height * max_dim,
    ))
    _set_light(
        TOP_LIGHT_NAME, enabled_master and props.top_light_enabled,
        props.top_light_power, tuple(props.top_light_color), props.top_light_width,
        top_location, center, max_dim, master, softness,
        shape="RECTANGLE", size_y=props.top_light_length,
        roll=props.top_light_rotation,
    )

    # --- Front fill lights (left and right for black component detail) ---
    for name, prefix in ((FRONT_LIGHT_LEFT_NAME, "front_left"), (FRONT_LIGHT_RIGHT_NAME, "front_right")):
        front_color = _kelvin_to_rgb(getattr(props, f"{prefix}_temperature")) if getattr(props, f"{prefix}_use_temperature") else tuple(getattr(props, f"{prefix}_color"))
        front_location = _spherical_position(
            center, max_dim,
            getattr(props, f"{prefix}_azimuth"), getattr(props, f"{prefix}_elevation"),
            getattr(props, f"{prefix}_distance"), 0.0, 0.0,
        )
        _set_light(
            name, enabled_master and getattr(props, f"{prefix}_enabled"),
            getattr(props, f"{prefix}_power") * (0.8 + 0.2 * contrast),
            front_color, getattr(props, f"{prefix}_size"),
            front_location, center, max_dim, master, softness,
        )

    for name in PRODUCT_LIGHT_NAMES:
        light = bpy.data.objects.get(name)
        if light is None:
            continue
        light.data.use_shadow = props.shadow_strength > 0.0
        if hasattr(light.data, "use_shadow_jitter"):
            light.data.use_shadow_jitter = bool(props.contact_shadow)


def _ensure_receiver_collection() -> bpy.types.Collection:
    collection = bpy.data.collections.get(BACKGROUND_RECEIVER_COLLECTION)
    if collection is None:
        collection = bpy.data.collections.new(BACKGROUND_RECEIVER_COLLECTION)
        bpy.context.scene.collection.children.link(collection)
    collection["pcbstudio_managed"] = True
    backdrop = bpy.data.objects.get(BACKGROUND_NAME)
    if backdrop is not None and backdrop.name not in collection.objects:
        collection.objects.link(backdrop)
    return collection


def _update_background_lights(bounds: BoundingBox, props) -> None:
    max_dim = max(bounds.max_dimension, 1e-6)
    center = bounds.center
    floor_z = bounds.min.z - max_dim * 0.01
    wall_y = center.y + max_dim * 3.2
    target_z = floor_z + max_dim * props.background_glow_vertical
    mode = props.background_light_mode if props.background_glow_enabled else "OFF"
    receiver = _ensure_receiver_collection()

    configurations: list[tuple[bool, float, tuple[float, float, float], float]]
    if mode == "DUAL_GLOW":
        configurations = [
            (True, -0.85, tuple(props.background_left_color), props.background_left_strength),
            (True, 0.85, tuple(props.background_right_color), props.background_right_strength),
        ]
    elif mode == "OFF":
        configurations = [
            (False, 0.0, tuple(props.background_glow_color), 0.0),
            (False, 0.0, tuple(props.background_glow_color), 0.0),
        ]
    else:
        x = props.background_glow_horizontal
        if mode == "LEFT_GLOW":
            x -= 0.85
        elif mode == "RIGHT_GLOW":
            x += 0.85
        if mode == "BOTTOM_GLOW":
            target_z = floor_z + max_dim * 0.12
        configurations = [
            (True, x, tuple(props.background_glow_color), props.background_glow_strength),
            (False, 0.0, tuple(props.background_glow_color), 0.0),
        ]

    for name, (enabled, x, color, power) in zip(BACKGROUND_LIGHT_NAMES, configurations):
        light = _ensure_area_light(name)
        light.hide_render = not enabled
        light.hide_viewport = not enabled
        light.data.energy = max(0.0, power * max_dim)
        light.data.color = color
        light.data.shape = "DISK"
        light.data.size = max(max_dim * props.background_glow_size * props.background_glow_spread, max_dim * 0.05)
        light.location = Vector((
            center.x + x * max_dim,
            center.y + max_dim * 1.35,
            target_z + max_dim * 0.35,
        ))
        _aim_object(light, Vector((center.x + x * max_dim, wall_y, target_z)))
        if hasattr(light, "light_linking"):
            # Blender 4.5 exposes a stable receiver collection on light objects.
            # This keeps the colored accents off the PCB itself.
            light.light_linking.receiver_collection = receiver


def _material_output(nodes) -> bpy.types.Node:
    output = nodes.new(type="ShaderNodeOutputMaterial")
    output.name = "PCB Studio Material Output"
    output.location = (620, 0)
    return output


def _apply_backdrop_grain(nodes, links, principled, props) -> None:
    """Give the backdrop a fine procedural tooth instead of a flat gradient.

    Real seamless paper is not perfectly smooth; the fine grain that shows up as
    a Cycles render resolves is what makes a sweep read as a physical surface.
    This bakes that into the surface so it survives any sample count and renders
    the same in EEVEE.

    Uses only Noise, Bump and Map Range, which are stable across 4.5 and 5.2.
    """
    amount = max(0.0, min(1.0, props.backdrop_grain))
    if amount <= 0.0:
        return
    noise = nodes.new(type="ShaderNodeTexNoise")
    noise.name = "PCB Studio Backdrop Grain"
    noise.location = (-230, -340)
    noise.inputs["Scale"].default_value = max(1.0, props.backdrop_grain_scale)
    noise.inputs["Detail"].default_value = 2.0

    bump = nodes.new(type="ShaderNodeBump")
    bump.name = "PCB Studio Backdrop Grain Bump"
    bump.location = (60, -340)
    bump.inputs["Strength"].default_value = min(1.0, amount * 0.6)
    bump.inputs["Distance"].default_value = 0.002
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], principled.inputs["Normal"])

    # A little roughness break-up is what actually catches the light and reads
    # as grain; the bump alone is nearly invisible on a matte sweep.
    spread = amount * 0.18
    rough = nodes.new(type="ShaderNodeMapRange")
    rough.name = "PCB Studio Backdrop Grain Roughness"
    rough.location = (60, -520)
    rough.inputs["From Min"].default_value = 0.0
    rough.inputs["From Max"].default_value = 1.0
    rough.inputs["To Min"].default_value = max(0.0, props.wall_roughness - spread)
    rough.inputs["To Max"].default_value = min(1.0, props.wall_roughness + spread)
    links.new(noise.outputs["Fac"], rough.inputs["Value"])
    links.new(rough.outputs["Result"], principled.inputs["Roughness"])


def update_background_material(props) -> str:
    mat = bpy.data.materials.get(BACKGROUND_MATERIAL_NAME)
    if mat is None:
        mat = bpy.data.materials.new(BACKGROUND_MATERIAL_NAME)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    principled = nodes.new(type="ShaderNodeBsdfPrincipled")
    principled.name = "PCB Studio Backdrop Shader"
    principled.location = (360, 0)
    principled.inputs["Roughness"].default_value = props.wall_roughness
    principled.inputs["Metallic"].default_value = 0.0
    output = _material_output(nodes)
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])

    preset = props.background_preset
    preset_colors = {
        "WHITE": ((0.82, 0.82, 0.84, 1.0), (0.96, 0.96, 0.96, 1.0)),
        "BLACK": ((0.002, 0.0025, 0.004, 1.0), (0.012, 0.014, 0.020, 1.0)),
        "DARK_GRAY": ((0.025, 0.027, 0.033, 1.0), (0.11, 0.115, 0.13, 1.0)),
        "BLUE_GRADIENT": ((0.003, 0.008, 0.035, 1.0), (0.015, 0.055, 0.22, 1.0)),
        "PURE_WHITE": ((1.0, 1.0, 1.0, 1.0), (0.90, 0.90, 0.92, 1.0)),
        "SOFT_WHITE": ((0.82, 0.80, 0.75, 1.0), (0.96, 0.94, 0.88, 1.0)),
        "LIGHT_GRAY": ((0.42, 0.44, 0.47, 1.0), (0.70, 0.72, 0.74, 1.0)),
        "GRAPHITE": ((0.015, 0.018, 0.024, 1.0), (0.075, 0.082, 0.095, 1.0)),
        "MATTE_BLACK": ((0.001, 0.001, 0.002, 1.0), (0.008, 0.009, 0.012, 1.0)),
        "MIDNIGHT_BLUE": ((0.002, 0.006, 0.018, 1.0), (0.010, 0.025, 0.065, 1.0)),
        "WARM_GRAY": ((0.18, 0.16, 0.14, 1.0), (0.36, 0.32, 0.28, 1.0)),
        "DARK_NAVY": ((0.002, 0.006, 0.016, 1.0), (0.008, 0.018, 0.044, 1.0)),
        "CONCRETE": ((0.18, 0.19, 0.20, 1.0), (0.34, 0.35, 0.36, 1.0)),
        "SOFT_GRADIENT": ((0.16, 0.17, 0.19, 1.0), (0.48, 0.50, 0.53, 1.0)),
        "WARM_GRADIENT": ((0.06, 0.025, 0.012, 1.0), (0.42, 0.18, 0.055, 1.0)),
    }
    color_1, color_2 = preset_colors.get(
        preset, (tuple(props.wall_color), tuple(props.background_color_2)),
    )
    brightness = max(0.0, props.background_brightness)
    color_1 = tuple(min(1.0, channel * brightness) for channel in color_1[:3]) + (1.0,)
    color_2 = tuple(min(1.0, channel * brightness * props.background_gradient_intensity) for channel in color_2[:3]) + (1.0,)
    if preset == "CUSTOM_SOLID":
        principled.inputs["Base Color"].default_value = color_1
        mat.diffuse_color = color_1
        _apply_backdrop_grain(nodes, links, principled, props)
        return "Background: Custom Solid"
    if preset in {"WHITE", "BLACK", "DARK_GRAY", "PURE_WHITE", "SOFT_WHITE", "LIGHT_GRAY", "GRAPHITE", "MATTE_BLACK", "MIDNIGHT_BLUE", "WARM_GRAY", "DARK_NAVY", "CONCRETE"}:
        # Preset colors retain a faint vertical value shift so the cyclorama
        # reads as a studio surface instead of a flat world color.
        pass

    texcoord = nodes.new(type="ShaderNodeTexCoord")
    texcoord.location = (-620, 0)
    mapping = nodes.new(type="ShaderNodeMapping")
    mapping.location = (-440, 0)
    mapping.inputs["Location"].default_value = (
        -props.background_halo_center_x,
        -props.background_halo_center_y,
        0.0,
    )
    mapping.inputs["Rotation"].default_value[2] = props.background_gradient_rotation
    gradient_scale = props.background_gradient_scale
    if preset == "RADIAL_GRADIENT":
        gradient_scale /= max(0.05, props.background_halo_radius)
    mapping.inputs["Scale"].default_value = (
        gradient_scale, gradient_scale, gradient_scale,
    )
    gradient = nodes.new(type="ShaderNodeTexGradient")
    gradient.location = (-230, 0)
    if preset == "RADIAL_GRADIENT":
        gradient.gradient_type = "SPHERICAL"
    elif preset == "TWO_TONE":
        gradient.gradient_type = "LINEAR"
    else:
        gradient.gradient_type = "EASING"
    ramp = nodes.new(type="ShaderNodeValToRGB")
    ramp.location = (0, 0)
    strength = max(0.02, props.background_gradient_strength)
    position = props.background_gradient_position
    ramp.color_ramp.elements[0].position = max(0.0, position - strength * 0.5)
    ramp.color_ramp.elements[0].color = color_1
    ramp.color_ramp.elements[1].position = min(1.0, position + strength * 0.5)
    ramp.color_ramp.elements[1].color = color_2
    if preset == "TWO_TONE":
        ramp.color_ramp.interpolation = "CONSTANT"
    if preset == "STUDIO_GRADIENT":
        middle = ramp.color_ramp.elements.new(position)
        middle.color = tuple((color_1[i] * 0.35 + color_2[i] * 0.65) for i in range(4))
        ramp.color_ramp.interpolation = "EASE"
    links.new(texcoord.outputs["Generated"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], gradient.inputs["Vector"])
    links.new(gradient.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], principled.inputs["Base Color"])
    _apply_backdrop_grain(nodes, links, principled, props)
    mat.diffuse_color = color_1
    return f"Background: {preset.replace('_', ' ').title()}"


def _load_image(filepath: str):
    path = Path(bpy.path.abspath(filepath)) if filepath else None
    if path is None or not path.is_file():
        return None
    try:
        return bpy.data.images.load(str(path), check_existing=True)
    except RuntimeError:
        return None


def update_hdri_world(props) -> str:
    world = bpy.data.worlds.get(PCB_STUDIO_WORLD_NAME)
    if world is None:
        world = bpy.data.worlds.new(PCB_STUDIO_WORLD_NAME)
    bpy.context.scene.world = world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    nodes.clear()

    output = nodes.new(type="ShaderNodeOutputWorld")
    output.location = (520, 0)
    solid = nodes.new(type="ShaderNodeBackground")
    solid.name = "PCB Studio Camera Background"
    solid.location = (80, -150)
    solid.inputs["Color"].default_value = tuple(props.world_background_color)
    solid.inputs["Strength"].default_value = 0.12

    mode = props.hdri_mode
    image = _load_image(props.hdri_filepath)
    if mode == "OFF" or image is None:
        links.new(solid.outputs["Background"], output.inputs["Surface"])
        return "HDRI off; neutral managed world active." if mode == "OFF" else "HDRI file is not available; neutral world active."

    texcoord = nodes.new(type="ShaderNodeTexCoord")
    texcoord.location = (-650, 120)
    mapping = nodes.new(type="ShaderNodeMapping")
    mapping.location = (-450, 120)
    mapping.inputs["Rotation"].default_value[2] = props.hdri_rotation
    environment = nodes.new(type="ShaderNodeTexEnvironment")
    environment.name = "PCB Studio Environment Texture"
    environment.location = (-220, 120)
    environment.image = image
    hdri_background = nodes.new(type="ShaderNodeBackground")
    hdri_background.name = "PCB Studio Environment Lighting"
    hdri_background.location = (40, 120)
    hdri_background.inputs["Strength"].default_value = max(0.0, props.hdri_brightness)
    links.new(texcoord.outputs["Generated"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], environment.inputs["Vector"])
    links.new(environment.outputs["Color"], hdri_background.inputs["Color"])

    if mode in {"LIGHTING_ONLY", "LIGHTING_BACKGROUND"}:
        # Both modes light the scene with the full-strength HDRI and give camera
        # rays something quieter, so the physical backdrop stays the subject.
        # Lighting Only hides the HDRI behind the flat world colour; Lighting +
        # Background keeps it visible but dimmed, reading as glow behind the set.
        if mode == "LIGHTING_BACKGROUND":
            camera_shader = nodes.new(type="ShaderNodeBackground")
            camera_shader.name = "PCB Studio Backdrop Environment"
            camera_shader.location = (80, -320)
            camera_shader.inputs["Strength"].default_value = max(0.0, props.hdri_brightness) * 0.25
            links.new(environment.outputs["Color"], camera_shader.inputs["Color"])
        else:
            camera_shader = solid
        light_path = nodes.new(type="ShaderNodeLightPath")
        light_path.location = (50, 330)
        mix = nodes.new(type="ShaderNodeMixShader")
        mix.name = "PCB Studio Camera Ray Separation"
        mix.location = (300, 60)
        links.new(light_path.outputs["Is Camera Ray"], mix.inputs[0])
        links.new(hdri_background.outputs["Background"], mix.inputs[1])
        links.new(camera_shader.outputs["Background"], mix.inputs[2])
        links.new(mix.outputs["Shader"], output.inputs["Surface"])
        return (
            "HDRI Lighting Only active." if mode == "LIGHTING_ONLY"
            else "HDRI lighting with a dimmed background behind the studio."
        )

    links.new(hdri_background.outputs["Background"], output.inputs["Surface"])
    return "HDRI visible environment active."


def _ensure_simple_material(name: str, color, roughness: float, metallic: float = 0.0):
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    if shader is not None:
        shader.inputs["Base Color"].default_value = tuple(color)
        shader.inputs["Roughness"].default_value = roughness
        shader.inputs["Metallic"].default_value = metallic
    material.diffuse_color = tuple(color)
    return material


#: Backdrop shapes built as a continuous floor-to-wall sweep.  These are smooth
#: shaded and use a single seamless material; every other shape is a set of flat
#: panels whose corners must stay hard.
_CYCLORAMA_KINDS: frozenset[str] = frozenset(
    {"INFINITY_CYCLORAMA", "GRADIENT_CYCLORAMA", "SEAMLESS_PAPER", "CURVED_WALL"}
)


def _update_backdrop_geometry(bounds: BoundingBox, props) -> None:
    """Rebuild the one managed backdrop for the selected bounds-aware shape."""
    backdrop = bpy.data.objects.get(BACKGROUND_NAME)
    if backdrop is None or backdrop.type != "MESH":
        return
    max_dim = max(bounds.max_dimension, 1e-6)
    half_width = max_dim * props.studio_width
    depth = max_dim * props.studio_depth
    wall_y = max_dim * props.wall_distance
    height = max_dim * props.wall_height
    radius = min(max_dim * props.cyclorama_radius, wall_y + depth)
    kind = props.backdrop_type
    if kind == "SEAMLESS_PAPER":
        half_width *= 0.68
        radius *= 0.72

    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int, int]] = []
    material_indices: list[int] = []
    normals: list[tuple[float, float, float]] = []

    def quad(a, b, c, d, material_index=0):
        offset = len(vertices)
        vertices.extend((a, b, c, d))
        faces.append((offset, offset + 1, offset + 2, offset + 3))
        material_indices.append(material_index)

    if kind in _CYCLORAMA_KINDS:
        # A welded quad strip carrying analytic per-vertex normals.  Sharing the
        # profile vertices is what makes ``use_smooth`` do anything at all, and
        # the explicit normals keep the long floor and the rear wall perfectly
        # planar instead of bending their shading into the curve.
        curve_start = wall_y - radius
        profile: list[tuple[float, float, tuple[float, float, float]]] = []
        if kind != "CURVED_WALL":
            profile.append((-depth, 0.0, (0.0, 0.0, 1.0)))
        profile.append((curve_start, 0.0, (0.0, 0.0, 1.0)))
        for index in range(1, CYCLORAMA_CURVE_SEGMENTS + 1):
            angle = (pi / 2.0) * index / CYCLORAMA_CURVE_SEGMENTS
            profile.append((
                curve_start + radius * sin(angle),
                radius * (1.0 - cos(angle)),
                (0.0, -sin(angle), cos(angle)),
            ))
        profile.append((wall_y, height, (0.0, -1.0, 0.0)))
        for y, z, normal in profile:
            vertices.extend(((-half_width, y, z), (half_width, y, z)))
            normals.extend((normal, normal))
        for index in range(len(profile) - 1):
            start = index * 2
            faces.append((start, start + 1, start + 3, start + 2))
            # One seamless material: a cyclorama has no floor-to-wall boundary.
            material_indices.append(0)
    else:
        quad((-half_width, wall_y, 0.0), (half_width, wall_y, 0.0), (half_width, wall_y, height), (-half_width, wall_y, height), 0)
        if kind in {"FLOOR_BACK_WALL", "THREE_WALL", "CORNER_STUDIO"}:
            quad((-half_width, -depth, 0.0), (half_width, -depth, 0.0), (half_width, wall_y, 0.0), (-half_width, wall_y, 0.0), 1)
        if kind in {"THREE_WALL", "CORNER_STUDIO"}:
            quad((-half_width, -depth, 0.0), (-half_width, wall_y, 0.0), (-half_width, wall_y, height), (-half_width, -depth, height), 0)
        if kind == "THREE_WALL":
            quad((half_width, wall_y, 0.0), (half_width, -depth, 0.0), (half_width, -depth, height), (half_width, wall_y, height), 0)

    smooth = kind in _CYCLORAMA_KINDS
    mesh = backdrop.data
    # clear_geometry() also drops the custom-normal attribute, so switching from
    # a cyclorama to a flat shape leaves no stale normals behind.
    mesh.clear_geometry()
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    for polygon, material_index in zip(mesh.polygons, material_indices):
        polygon.material_index = material_index
        polygon.use_smooth = smooth
    if smooth and normals:
        mesh.normals_split_custom_set_from_vertices(normals)
    # Slot 0 is the wall material for every shape, so it must exist before the
    # floor material is appended or the flat shapes' index 1 would be orphaned.
    wall_material = bpy.data.materials.get(BACKGROUND_MATERIAL_NAME)
    if wall_material is None:
        wall_material = _ensure_simple_material(
            BACKGROUND_MATERIAL_NAME, (0.35, 0.35, 0.36, 1.0), 0.7, 0.0
        )
    floor_material = _ensure_simple_material(
        BACKGROUND_FLOOR_MATERIAL_NAME,
        tuple(min(1.0, value * props.floor_brightness) for value in props.floor_color[:3]) + (1.0,),
        props.floor_roughness,
        props.floor_metallic,
    )
    mesh.materials.clear()
    mesh.materials.append(wall_material)
    if not smooth:
        mesh.materials.append(floor_material)
    backdrop.location = (bounds.center.x, bounds.center.y, bounds.min.z - max_dim * 0.012)
    backdrop["pcbstudio_managed"] = True


def _update_floor_geometry(bounds: BoundingBox, props) -> None:
    plane = bpy.data.objects.get(REFLECTION_PLANE_NAME)
    if plane is None or plane.type != "MESH":
        return
    max_dim = max(bounds.max_dimension, 1e-6)
    half = max_dim * props.floor_size * 0.5
    plane.data.clear_geometry()
    plane.data.from_pydata(
        [(-half, -half, 0.0), (half, -half, 0.0), (half, half, 0.0), (-half, half, 0.0)],
        [], [(0, 1, 2, 3)],
    )
    plane.data.update()
    plane.location = (bounds.center.x, bounds.center.y, bounds.min.z + max_dim * props.floor_height)
    plane["pcbstudio_managed"] = True
    if hasattr(plane, "visible_shadow"):
        plane.visible_shadow = not props.disable_floor_shadow
    if hasattr(plane, "is_shadow_catcher"):
        plane.is_shadow_catcher = bool(props.shadow_catcher_style)
    solidify = plane.modifiers.get("PCB_STUDIO_FLOOR_THICKNESS")
    bevel = plane.modifiers.get("PCB_STUDIO_FLOOR_BEVEL")
    if props.floor_bevel_enabled:
        if solidify is None:
            solidify = plane.modifiers.new("PCB_STUDIO_FLOOR_THICKNESS", "SOLIDIFY")
        solidify.thickness = max_dim * 0.01
        if bevel is None:
            bevel = plane.modifiers.new("PCB_STUDIO_FLOOR_BEVEL", "BEVEL")
        bevel.width = max_dim * 0.004
        bevel.segments = 3
    else:
        if bevel is not None:
            plane.modifiers.remove(bevel)
        if solidify is not None:
            plane.modifiers.remove(solidify)


def _update_floor_material(props) -> None:
    plane = bpy.data.objects.get(REFLECTION_PLANE_NAME)
    if plane is None or plane.type != "MESH" or not plane.data.materials:
        return
    material = plane.data.materials[0]
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF")
    if principled is None:
        return
    color = tuple(min(1.0, channel * props.floor_brightness) for channel in props.floor_color[:3]) + (1.0,)
    roughness = props.floor_roughness
    metallic = props.floor_metallic
    if props.reflection_surface == "SUBTLE":
        roughness, metallic = 0.42, 0.02
    elif props.reflection_surface == "GLOSSY":
        roughness, metallic = 0.16, 0.12
    elif props.reflection_surface == "SATIN":
        roughness, metallic = 0.32, 0.05
    elif props.reflection_surface == "MIRROR":
        roughness, metallic = 0.025, 0.92
    elif props.reflection_surface == "DARK_GLASS":
        roughness, metallic = 0.12, 0.35
    elif props.reflection_surface == "MATTE":
        roughness, metallic = 0.82, 0.0
    elif props.reflection_surface == "FROSTED":
        roughness, metallic = 0.48, 0.02
    elif props.reflection_surface == "CONCRETE":
        roughness, metallic = 0.88, 0.0
    elif props.reflection_surface == "ACRYLIC":
        roughness, metallic = 0.10, 0.04
    elif props.reflection_surface == "METALLIC":
        roughness, metallic = 0.22, 0.82
    # Reflection Strength deliberately moves the material between matte and
    # the selected finish instead of faking reflections in the compositor.
    strength = props.floor_reflection_strength
    principled.inputs["Base Color"].default_value = color
    principled.inputs["Roughness"].default_value = min(1.0, roughness + (1.0 - strength) * 0.45)
    principled.inputs["Metallic"].default_value = metallic * strength
    if "Coat Weight" in principled.inputs:
        principled.inputs["Coat Weight"].default_value = 0.35 * strength if props.reflection_surface in {"ACRYLIC", "DARK_GLASS"} else 0.0
    material.diffuse_color = color


def _cube_geometry(mesh: bpy.types.Mesh) -> None:
    verts = [
        (-0.5, -0.5, -0.5), (0.5, -0.5, -0.5),
        (0.5, 0.5, -0.5), (-0.5, 0.5, -0.5),
        (-0.5, -0.5, 0.5), (0.5, -0.5, 0.5),
        (0.5, 0.5, 0.5), (-0.5, 0.5, 0.5),
    ]
    faces = [
        (0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
        (1, 5, 6, 2), (2, 6, 7, 3), (4, 0, 3, 7),
    ]
    mesh.clear_geometry()
    mesh.from_pydata(verts, [], faces)
    mesh.update()


def _cylinder_geometry(mesh: bpy.types.Mesh, segments: int = 64) -> None:
    vertices = []
    for z in (-0.5, 0.5):
        vertices.extend((0.5 * cos(2.0 * pi * i / segments), 0.5 * sin(2.0 * pi * i / segments), z) for i in range(segments))
    faces = [tuple(range(segments - 1, -1, -1)), tuple(range(segments, segments * 2))]
    for index in range(segments):
        nxt = (index + 1) % segments
        faces.append((index, nxt, segments + nxt, segments + index))
    mesh.clear_geometry()
    mesh.from_pydata(vertices, [], faces)
    mesh.update()


def _update_pedestal(bounds: BoundingBox, props) -> None:
    pedestal = bpy.data.objects.get(PEDESTAL_NAME)
    enabled = props.stage_type in {"ROUNDED_PEDESTAL", "RAISED_PLATFORM"}
    if not enabled:
        # Delete rather than hide: a hidden pedestal lingered in the outliner
        # forever once created, and re-appeared on the next stage change.
        if pedestal is not None and pedestal.get("pcbstudio_managed", False):
            mesh = pedestal.data
            bpy.data.objects.remove(pedestal, do_unlink=True)
            if mesh is not None and mesh.users == 0:
                bpy.data.meshes.remove(mesh)
        return
    if pedestal is None:
        mesh = bpy.data.meshes.new(PEDESTAL_NAME)
        pedestal = bpy.data.objects.new(PEDESTAL_NAME, mesh)
        get_or_create_render_setup_collection().objects.link(pedestal)
    if props.pedestal_shape == "CIRCULAR":
        _cylinder_geometry(pedestal.data)
    else:
        _cube_geometry(pedestal.data)
    pedestal.hide_render = False
    pedestal.hide_viewport = False
    pedestal["pcbstudio_managed"] = True
    max_dim = max(bounds.max_dimension, 1e-6)
    width = max(bounds.dimensions.x * props.pedestal_width, max_dim * 0.5)
    depth = max(bounds.dimensions.y * props.pedestal_depth, max_dim * 0.5)
    height_factor = min(props.pedestal_height, 0.06) if props.pedestal_shape == "LOW_PLATFORM" else props.pedestal_height
    height = max_dim * height_factor
    if props.pedestal_shape == "CIRCULAR":
        depth = width
    # Object.dimensions divides by the evaluated bounding box, so the depsgraph
    # has to catch up with the mesh that was just rebuilt.  Without this the
    # scale is derived from the previous shape and the pedestal ends up taller
    # than `height`, pushing its top face up through the board.
    bpy.context.view_layer.update()
    pedestal.dimensions = (width, depth, height)
    pedestal.location = (
        bounds.center.x,
        bounds.center.y,
        bounds.min.z - max_dim * 0.008 - height * 0.5,
    )
    bpy.context.view_layer.update()
    bevel = pedestal.modifiers.get("PCB_STUDIO_STAGE_BEVEL")
    if bevel is None:
        bevel = pedestal.modifiers.new("PCB_STUDIO_STAGE_BEVEL", "BEVEL")
    bevel.width = max_dim * props.pedestal_corner_radius
    bevel.segments = 6 if props.pedestal_shape in {"CIRCULAR", "ROUNDED_SQUARE"} else 2
    bevel.limit_method = "ANGLE"

    material = bpy.data.materials.get(PEDESTAL_MATERIAL_NAME)
    if material is None:
        material = bpy.data.materials.new(PEDESTAL_MATERIAL_NAME)
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF")
    principled.inputs["Base Color"].default_value = tuple(props.pedestal_color)
    principled.inputs["Roughness"].default_value = props.pedestal_roughness
    principled.inputs["Metallic"].default_value = props.pedestal_metallic
    if pedestal.data.materials:
        pedestal.data.materials[0] = material
    else:
        pedestal.data.materials.append(material)


def apply_color_management(scene: bpy.types.Scene, props) -> str:
    try:
        scene.view_settings.view_transform = "AgX"
    except TypeError:
        pass
    candidates = {
        "NATURAL": ("AgX - Medium Low Contrast", "Medium Low Contrast", "None"),
        "PRODUCT": ("AgX - Medium High Contrast", "Medium High Contrast", "None"),
        "HIGH_CONTRAST": ("AgX - Very High Contrast", "Very High Contrast", "None"),
        "MOODY": ("AgX - High Contrast", "High Contrast", "None"),
    }.get(props.color_look, ("None",))
    for look in candidates:
        try:
            scene.view_settings.look = look
            break
        except TypeError:
            continue
    scene.view_settings.exposure = props.color_exposure
    return f"Color management: {scene.view_settings.view_transform}, {scene.view_settings.look}."


def _next_managed_name(prefix: str) -> str:
    index = 1
    while bpy.data.objects.get(f"{prefix}{index:02d}") is not None:
        index += 1
    return f"{prefix}{index:02d}"


def _remove_managed_object(name: str, role: str) -> bool:
    obj = bpy.data.objects.get(name)
    if obj is None or obj.get("pcbstudio_role") != role:
        return False
    data = obj.data
    bpy.data.objects.remove(obj, do_unlink=True)
    if data is not None and data.users == 0:
        if isinstance(data, bpy.types.Light):
            bpy.data.lights.remove(data)
        elif isinstance(data, bpy.types.Mesh):
            bpy.data.meshes.remove(data)
    return True


def sync_custom_light_slot(scene: bpy.types.Scene, slot) -> bpy.types.Object | None:
    if not slot.object_name:
        return None
    obj = bpy.data.objects.get(slot.object_name)
    if obj is not None and obj.get("pcbstudio_role") != "custom_light":
        return None
    blender_type = "POINT" if slot.light_type == "POINT" else "SPOT" if slot.light_type == "SPOT" else "AREA"
    if obj is None:
        data = bpy.data.lights.new(slot.object_name, blender_type)
        obj = bpy.data.objects.new(slot.object_name, data)
        get_or_create_render_setup_collection().objects.link(obj)
    elif obj.type != "LIGHT" or obj.data.type != blender_type:
        old_data = obj.data
        obj.data = bpy.data.lights.new(slot.object_name, blender_type)
        if old_data is not None and old_data.users == 0 and isinstance(old_data, bpy.types.Light):
            bpy.data.lights.remove(old_data)
    obj["pcbstudio_managed"] = True
    obj["pcbstudio_role"] = "custom_light"
    obj["pcbstudio_temperature"] = float(slot.temperature)
    obj.name = slot.object_name
    obj.data.name = slot.object_name
    obj.hide_render = not slot.enabled
    obj.hide_viewport = not slot.enabled
    bounds = _get_bounds()
    scale = max(bounds.max_dimension, 1e-6) if bounds is not None else 1.0
    obj.data.energy = max(0.0, slot.power * scale)
    obj.data.color = _kelvin_to_rgb(slot.temperature) if slot.use_temperature else tuple(slot.color)
    obj.location = tuple(slot.position)
    if blender_type == "AREA":
        obj.data.shape = "RECTANGLE" if slot.light_type in {"STRIP", "RIM", "TOP"} else "DISK"
        obj.data.size = max(0.001, slot.size * scale)
        if obj.data.shape == "RECTANGLE":
            obj.data.size_y = max(0.001, slot.length * scale)
    elif blender_type == "SPOT":
        obj.data.shadow_soft_size = max(0.001, slot.size * scale)
        obj.data.spot_size = slot.spot_size
        obj.data.spot_blend = slot.spot_softness
    else:
        obj.data.shadow_soft_size = max(0.001, slot.size * scale)
    if slot.auto_aim and bounds is not None and slot.light_type != "POINT":
        _aim_object(obj, bounds.center)
        obj.rotation_quaternion = obj.rotation_quaternion @ Euler(tuple(slot.rotation)).to_quaternion()
    else:
        obj.rotation_mode = "XYZ"
        obj.rotation_euler = tuple(slot.rotation)
    return obj


def add_custom_light(scene: bpy.types.Scene, props, preset_key: str) -> str:
    preset = CUSTOM_LIGHT_PRESETS.get(preset_key, CUSTOM_LIGHT_PRESETS["LARGE_SOFTBOX"])
    bounds = _get_bounds()
    if bounds is None:
        return "Cannot add light: no PCB geometry found."
    light_type, power, size, length, relative_position = preset
    slot = props.custom_lights.add()
    slot.object_name = _next_managed_name(CUSTOM_LIGHT_PREFIX)
    slot.display_name = preset_key.replace("_", " ").title()
    slot.light_type = light_type
    slot.power = power
    slot.size = size
    slot.length = length
    slot.position = tuple(bounds.center + Vector(relative_position) * bounds.max_dimension)
    slot.auto_aim = light_type != "POINT"
    props.custom_light_index = len(props.custom_lights) - 1
    sync_custom_light_slot(scene, slot)
    return f"Added {slot.display_name}: {slot.object_name}"


def delete_custom_light(props) -> str:
    if not props.custom_lights:
        return "No custom studio light selected."
    index = min(max(0, props.custom_light_index), len(props.custom_lights) - 1)
    slot = props.custom_lights[index]
    name = slot.object_name
    _remove_managed_object(name, "custom_light")
    props.custom_lights.remove(index)
    props.custom_light_index = max(0, min(index, len(props.custom_lights) - 1))
    return f"Deleted managed light: {name}"


def sync_light_card_slot(scene: bpy.types.Scene, slot) -> bpy.types.Object | None:
    if not slot.object_name:
        return None
    obj = bpy.data.objects.get(slot.object_name)
    if obj is not None and obj.get("pcbstudio_role") != "light_card":
        return None
    if obj is None:
        mesh = bpy.data.meshes.new(slot.object_name)
        _cube_geometry(mesh)
        obj = bpy.data.objects.new(slot.object_name, mesh)
        get_or_create_render_setup_collection().objects.link(obj)
    obj["pcbstudio_managed"] = True
    obj["pcbstudio_role"] = "light_card"
    obj.name = slot.object_name
    obj.location = tuple(slot.position)
    obj.rotation_mode = "XYZ"
    obj.rotation_euler = tuple(slot.rotation)
    obj.scale = tuple(slot.scale)
    obj.hide_render = not slot.visible_render
    if hasattr(obj, "visible_camera"):
        obj.visible_camera = slot.visible_camera
    colors = {
        "WHITE": ((0.92, 0.92, 0.92, 1.0), 0.62, 0.0),
        "BLACK": ((0.003, 0.003, 0.004, 1.0), 0.82, 0.0),
        "SILVER": ((0.55, 0.58, 0.62, 1.0), 0.24, 0.82),
    }
    color, roughness, metallic = colors[slot.card_type]
    if slot.card_type == "WHITE":
        color = tuple(min(1.0, channel * slot.brightness) for channel in slot.color[:3]) + (1.0,)
    material = _ensure_simple_material(f"{LIGHT_CARD_MATERIAL_PREFIX}{slot.object_name}", color, roughness, metallic)
    material["pcbstudio_role"] = "light_card_material"
    obj.data.materials.clear()
    obj.data.materials.append(material)
    return obj


def add_light_card(scene: bpy.types.Scene, props) -> str:
    bounds = _get_bounds()
    if bounds is None:
        return "Cannot add reflection card: no PCB geometry found."
    slot = props.light_cards.add()
    slot.object_name = _next_managed_name(LIGHT_CARD_PREFIX)
    slot.display_name = f"{props.light_card_type.title()} Card"
    slot.card_type = props.light_card_type
    scale = bounds.max_dimension
    slot.position = tuple(bounds.center + Vector((-1.3, 0.25, 0.8)) * scale)
    slot.scale = (scale * 0.025, scale * 0.75, scale * 0.9)
    props.light_card_index = len(props.light_cards) - 1
    sync_light_card_slot(scene, slot)
    return f"Added {slot.display_name}: {slot.object_name}"


def remove_light_card(props) -> str:
    if not props.light_cards:
        return "No reflection card selected."
    index = min(max(0, props.light_card_index), len(props.light_cards) - 1)
    slot = props.light_cards[index]
    name = slot.object_name
    _remove_managed_object(name, "light_card")
    props.light_cards.remove(index)
    props.light_card_index = max(0, min(index, len(props.light_cards) - 1))
    return f"Removed reflection card: {name}"


def apply_floor_preset(scene: bpy.types.Scene, props, preset_key: str) -> str:
    values = FLOOR_PRESET_VALUES.get(preset_key)
    if values is None:
        return f"Unknown floor preset: {preset_key}"
    surface, color, roughness, metallic, strength = values
    scene["pcbstudio_batch_update"] = True
    try:
        props.floor_preset = preset_key
        props.reflection_surface = surface
        props.floor_color = color
        props.floor_roughness = roughness
        props.floor_metallic = metallic
        props.floor_reflection_strength = strength
        if props.stage_type == "NONE":
            props.stage_type = "FLOOR"
    finally:
        scene["pcbstudio_batch_update"] = False
    studio_result = update_professional_studio(scene, props)
    if studio_result.startswith(("Cannot", "No ", "Unknown")):
        return studio_result
    return f"{preset_key.replace('_', ' ').title()} floor applied. {studio_result}"


def studio_helper(scene: bpy.types.Scene, props, action: str) -> str:
    collection = bpy.data.collections.get("PCB_RENDER_SETUP")
    studio_names = set(ALL_STUDIO_LIGHT_NAMES) | {LIGHT_TARGET_NAME, BACKGROUND_NAME, REFLECTION_PLANE_NAME, PEDESTAL_NAME}
    managed = [
        obj for obj in collection.all_objects
        if obj.get("pcbstudio_managed", False)
        and (obj.name in studio_names or obj.get("pcbstudio_role") in {"custom_light", "light_card"} or obj.get("pcbstudio_floor", False))
    ] if collection else []
    if action in {"AUTO_CENTER", "FIT"}:
        return update_professional_studio(scene, props)
    if action == "RESET":
        return reset_professional_studio()
    if action == "HIDE":
        for obj in managed:
            obj.hide_viewport = True
        return f"Hidden {len(managed)} managed studio object(s) in the viewport."
    if action == "SHOW":
        for obj in managed:
            enabled = obj.type != "LIGHT" or not obj.hide_render
            obj.hide_viewport = not enabled
        return f"Shown {len(managed)} managed studio object(s)."
    if action == "LOCK":
        for obj in managed:
            obj.hide_select = True
            obj.lock_location = (True, True, True)
            obj.lock_rotation = (True, True, True)
            obj.lock_scale = (True, True, True)
        return f"Locked {len(managed)} managed studio object(s)."
    return f"Unknown studio helper: {action}"


def refresh_studio_values(scene: bpy.types.Scene, props) -> str:
    """Update lights and shader values without rebuilding managed geometry."""
    from . import studio_environment
    if studio_environment.enabled(scene):
        result = studio_environment.update(scene, props)
        bounds = _get_bounds()
        if bounds is not None:
            _update_product_lights(bounds, props)
            _update_background_lights(bounds, props)
        update_hdri_world(props)
        for slot in props.custom_lights:
            sync_custom_light_slot(scene, slot)
        for slot in props.light_cards:
            sync_light_card_slot(scene, slot)
        apply_color_management(scene, props)
        return result
    bounds = _get_bounds()
    if bounds is None:
        return "Cannot update studio: no PCB geometry found."
    _update_product_lights(bounds, props)
    _update_background_lights(bounds, props)
    update_background_material(props)
    _update_backdrop_geometry(bounds, props)
    update_hdri_world(props)
    from .floor import update_floor_system
    update_floor_system(scene, props)
    for slot in props.custom_lights:
        sync_custom_light_slot(scene, slot)
    for slot in props.light_cards:
        sync_light_card_slot(scene, slot)
    apply_color_management(scene, props)
    return "Professional studio values updated."


def update_professional_studio(scene: bpy.types.Scene, props) -> str:
    """Create or update every managed visual studio element idempotently."""
    from . import studio_environment
    if studio_environment.enabled(scene):
        result = studio_environment.update(scene, props)
        bounds = _get_bounds()
        if bounds is not None:
            _update_product_lights(bounds, props)
            _update_background_lights(bounds, props)
        update_hdri_world(props)
        for slot in props.custom_lights:
            sync_custom_light_slot(scene, slot)
        for slot in props.light_cards:
            sync_light_card_slot(scene, slot)
        apply_color_management(scene, props)
        return result
    bounds = _get_bounds()
    if bounds is None:
        return "Cannot update studio: no PCB geometry found."
    from .render import configure_eevee_shadows, setup_background_plane
    from .floor import update_floor_system

    # Prepare Scene's engine stage defaults to KEEP on every re-run, so this is
    # the only path that runs often enough to keep the viewport shadow correct.
    configure_eevee_shadows(scene)
    setup_background_plane(bounds)
    update_background_material(props)
    _update_backdrop_geometry(bounds, props)
    _update_product_lights(bounds, props)
    _update_background_lights(bounds, props)
    update_hdri_world(props)

    # The dedicated floor system owns its geometry. In particular, No Floor
    # must not call the legacy reflection helper because that helper creates an
    # empty plane even for its OFF preset.
    if hasattr(props, "floor_mode"):
        update_floor_system(scene, props)
    else:
        from .composition import apply_reflection_plane
        floor_mode = props.reflection_surface if props.stage_type != "NONE" else "OFF"
        apply_reflection_plane(floor_mode)
        _update_floor_geometry(bounds, props)
        _update_floor_material(props)
    _update_pedestal(bounds, props)
    for slot in props.custom_lights:
        sync_custom_light_slot(scene, slot)
    for slot in props.light_cards:
        sync_light_card_slot(scene, slot)
    apply_color_management(scene, props)
    return "Professional studio updated without duplicate managed objects."


def apply_professional_preset(scene: bpy.types.Scene, props, preset_key: str) -> str:
    values = PRESET_VALUES.get(preset_key)
    if values is None:
        return f"Unknown preset: {preset_key}"
    scene["pcbstudio_batch_update"] = True
    try:
        for name, value in values.items():
            if hasattr(props, name):
                setattr(props, name, value)
        props.studio_lighting_preset = preset_key
    finally:
        scene["pcbstudio_batch_update"] = False
    result = update_professional_studio(scene, props)
    if result.startswith(("Cannot", "No ", "Unknown")):
        return result
    display = preset_key.replace("_", " ").title()
    return f"{display} preset applied. {result}"


def set_product_light_visibility(visible: bool) -> None:
    for name in PRODUCT_LIGHT_NAMES:
        light = bpy.data.objects.get(name)
        if light is not None:
            light.hide_render = not visible
            light.hide_viewport = not visible


def solo_studio_light(light_name: str) -> str:
    if light_name not in ALL_STUDIO_LIGHT_NAMES:
        return f"Unknown managed light: {light_name}"
    if bpy.data.objects.get(light_name) is None:
        return f"Managed light not found: {light_name}"
    for name in ALL_STUDIO_LIGHT_NAMES:
        light = bpy.data.objects.get(name)
        if light is None:
            continue
        if "pcbstudio_pre_solo_hide_render" not in light:
            light["pcbstudio_pre_solo_hide_render"] = bool(light.hide_render)
            light["pcbstudio_pre_solo_hide_viewport"] = bool(light.hide_viewport)
        hidden = name != light_name
        light.hide_render = hidden
        light.hide_viewport = hidden
    return f"Solo active: {light_name}"


def restore_studio_lights() -> str:
    restored = 0
    for name in ALL_STUDIO_LIGHT_NAMES:
        light = bpy.data.objects.get(name)
        if light is None:
            continue
        if "pcbstudio_pre_solo_hide_render" in light:
            light.hide_render = bool(light["pcbstudio_pre_solo_hide_render"])
            light.hide_viewport = bool(light["pcbstudio_pre_solo_hide_viewport"])
            del light["pcbstudio_pre_solo_hide_render"]
            del light["pcbstudio_pre_solo_hide_viewport"]
            restored += 1
    return f"Restored {restored} managed studio light(s)."


def reset_professional_studio() -> str:
    """Remove only managed visual objects; camera and animation stay intact."""
    from .floor import cleanup_floor_system

    cleanup_floor_system()
    for name in ALL_STUDIO_LIGHT_NAMES + (
        LIGHT_TARGET_NAME,
        BACKGROUND_NAME,
        REFLECTION_PLANE_NAME,
        PEDESTAL_NAME,
    ):
        obj = bpy.data.objects.get(name)
        if obj is not None and obj.get("pcbstudio_managed", False):
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if data is not None and data.users == 0:
                if isinstance(data, bpy.types.Light):
                    bpy.data.lights.remove(data)
                elif isinstance(data, bpy.types.Mesh):
                    bpy.data.meshes.remove(data)
    for obj in list(bpy.data.objects):
        if obj.get("pcbstudio_role") in {"custom_light", "light_card"}:
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if data is not None and data.users == 0:
                if isinstance(data, bpy.types.Light):
                    bpy.data.lights.remove(data)
                elif isinstance(data, bpy.types.Mesh):
                    bpy.data.meshes.remove(data)

    receiver = bpy.data.collections.get(BACKGROUND_RECEIVER_COLLECTION)
    if receiver is not None and receiver.get("pcbstudio_managed", False):
        bpy.data.collections.remove(receiver)

    world = bpy.data.worlds.get(PCB_STUDIO_WORLD_NAME)
    if world is not None:
        world.use_nodes = True
        nodes = world.node_tree.nodes
        links = world.node_tree.links
        nodes.clear()
        background = nodes.new(type="ShaderNodeBackground")
        background.inputs["Color"].default_value = (0.005, 0.006, 0.008, 1.0)
        background.inputs["Strength"].default_value = 0.12
        output = nodes.new(type="ShaderNodeOutputWorld")
        links.new(background.outputs["Background"], output.inputs["Surface"])

    props = getattr(bpy.context.scene, "pcb_studio_import", None)
    if props is not None:
        props.custom_lights.clear()
        props.custom_light_index = 0
        props.light_cards.clear()
        props.light_card_index = 0

    scene = bpy.context.scene
    tree = getattr(scene, "node_tree", None) or getattr(scene, "compositing_node_group", None)
    if tree is not None:
        for node in list(tree.nodes):
            if node.get(MANAGED_COMPOSITOR_TAG, False):
                tree.nodes.remove(node)
    return "Professional studio visual objects reset; PCB, camera, and animation were preserved."
