"""Material preset definitions and Blender material creation utilities.

``PRESET_DATA`` is the single source of truth for preset values *and* for the
preset enum items, so labels and values can never drift apart.  Every socket
write goes through :mod:`material_compat`, so a socket that is missing in the
running Blender version degrades to a no-op instead of raising.
"""

from __future__ import annotations

from dataclasses import dataclass

import bpy

from ..constants import MATERIAL_NAME_PREFIX
from . import material_compat as compat


@dataclass
class MaterialPreset:
    """Physically sensible starting values for one PCB Studio material."""

    display_name: str
    material_name: str
    base_color: tuple[float, float, float, float]
    metallic: float
    roughness: float
    coat_weight: float = 0.0
    transmission_weight: float = 0.0
    ior: float = 1.5
    coat_roughness: float = 0.06
    specular: float = 0.5
    anisotropic: float = 0.0
    anisotropic_rotation: float = 0.0
    emission_color: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)
    emission_strength: float = 0.0
    alpha: float = 1.0
    micro_detail: str = "OFF"
    micro_amount: float = 0.35
    micro_scale: float = 1.0
    description: str = ""


#: key, display name, base colour (linear RGB), metallic, roughness,
#: description, extra MaterialPreset fields.  Colours are deliberately not pure
#: black or pure white: real PCB parts always keep some visible shading.
_PRESET_TABLE: tuple[tuple, ...] = (
    ("SOLDER_MASK_GREEN", "PCB Green", (0.043, 0.175, 0.075), 0.0, 0.42,
     "Standard green solder mask with a thin satin coat",
     {"coat_weight": 0.20, "coat_roughness": 0.14, "micro_detail": "SOLDER_MASK", "micro_amount": 0.35}),
    ("SOLDER_MASK_GREEN_DARK", "PCB Dark Green", (0.016, 0.070, 0.034), 0.0, 0.44,
     "Deep green mask used on high density boards",
     {"coat_weight": 0.22, "coat_roughness": 0.15, "micro_detail": "SOLDER_MASK", "micro_amount": 0.35}),
    ("SOLDER_MASK_BLACK", "Black PCB", (0.017, 0.018, 0.020), 0.0, 0.46,
     "Black solder mask: very dark but never pure black",
     {"coat_weight": 0.18, "coat_roughness": 0.16, "micro_detail": "SOLDER_MASK", "micro_amount": 0.40}),
    ("SOLDER_MASK_BLUE", "Blue PCB", (0.020, 0.055, 0.190), 0.0, 0.42,
     "Blue solder mask",
     {"coat_weight": 0.20, "coat_roughness": 0.14, "micro_detail": "SOLDER_MASK", "micro_amount": 0.35}),
    ("SOLDER_MASK_RED", "Red PCB", (0.230, 0.030, 0.028), 0.0, 0.42,
     "Red solder mask",
     {"coat_weight": 0.20, "coat_roughness": 0.14, "micro_detail": "SOLDER_MASK", "micro_amount": 0.35}),
    ("SOLDER_MASK_WHITE", "White PCB", (0.780, 0.780, 0.760), 0.0, 0.48,
     "White solder mask used on LED boards",
     {"coat_weight": 0.16, "coat_roughness": 0.18, "micro_detail": "SOLDER_MASK", "micro_amount": 0.30}),
    ("FR4", "Bare FR4", (0.190, 0.150, 0.070), 0.0, 0.62,
     "Unmasked FR4 laminate with woven glass tint",
     {"coat_weight": 0.05, "micro_detail": "SOLDER_MASK", "micro_amount": 0.50, "micro_scale": 0.6}),
    ("COPPER", "Copper", (0.850, 0.500, 0.280), 1.0, 0.30,
     "Bare copper pour and traces", {}),
    ("GOLD", "Gold / ENIG", (0.900, 0.700, 0.320), 1.0, 0.22,
     "ENIG gold plating on pads and fingers", {}),
    ("TIN", "Tin / Solder", (0.720, 0.720, 0.740), 1.0, 0.32,
     "HASL tin-lead solder finish, slightly dull", {}),
    ("ALUMINUM", "Aluminum", (0.910, 0.920, 0.920), 1.0, 0.28,
     "Machined aluminium housing or heatsink", {}),
    ("BRUSHED_ALUMINUM", "Brushed Aluminum", (0.880, 0.890, 0.900), 1.0, 0.36,
     "Aluminium with a subtle directional brush",
     {"anisotropic": 0.55, "micro_detail": "BRUSHED_METAL", "micro_amount": 0.45}),
    ("STAINLESS", "Stainless Steel", (0.660, 0.670, 0.680), 1.0, 0.34,
     "Stamped stainless shield can",
     {"anisotropic": 0.25, "micro_detail": "BRUSHED_METAL", "micro_amount": 0.25}),
    ("SILVER_METAL", "Silver Metal", (0.950, 0.930, 0.880), 1.0, 0.16,
     "Polished silver-coloured metal", {}),
    ("BRUSHED_METAL", "Brushed Metal", (0.600, 0.620, 0.640), 1.0, 0.38,
     "Generic brushed metal",
     {"anisotropic": 0.55, "micro_detail": "BRUSHED_METAL", "micro_amount": 0.45}),
    ("GOLD_CONTACT", "Gold Contact", (0.940, 0.780, 0.400), 1.0, 0.14,
     "Bright gold-plated contact or edge finger", {}),
    ("METAL_SHIELD", "Metal Shield", (0.620, 0.640, 0.660), 1.0, 0.30,
     "Softly brushed RF shield",
     {"anisotropic": 0.20, "micro_detail": "BRUSHED_METAL", "micro_amount": 0.30}),
    ("BLACK_IC_PLASTIC", "Black IC", (0.015, 0.016, 0.018), 0.0, 0.36,
     "Moulded IC package: dark charcoal, never pure black, with a fine grain",
     {"coat_weight": 0.08, "coat_roughness": 0.30, "micro_detail": "IC_PLASTIC", "micro_amount": 0.45}),
    ("PLASTIC_DARK_GRAY", "Dark Gray Plastic", (0.075, 0.077, 0.082), 0.0, 0.48,
     "Dark grey moulded plastic",
     {"micro_detail": "IC_PLASTIC", "micro_amount": 0.30}),
    ("MATTE_PLASTIC", "Matte Plastic", (0.140, 0.145, 0.150), 0.0, 0.62,
     "Neutral matte engineering plastic",
     {"micro_detail": "FINE_PLASTIC", "micro_amount": 0.35}),
    ("GLOSS_PLASTIC", "Gloss Plastic", (0.100, 0.105, 0.115), 0.0, 0.16,
     "Glossy moulded plastic with a clear coat",
     {"coat_weight": 0.35, "coat_roughness": 0.06}),
    ("PLASTIC_WHITE", "White Plastic", (0.720, 0.720, 0.710), 0.0, 0.42,
     "White nylon or PBT plastic body",
     {"coat_weight": 0.10, "micro_detail": "FINE_PLASTIC", "micro_amount": 0.25}),
    ("CERAMIC_WHITE", "Ceramic White", (0.780, 0.790, 0.800), 0.0, 0.34,
     "White ceramic package or MLCC",
     {"coat_weight": 0.10, "coat_roughness": 0.20, "micro_detail": "FINE_CERAMIC", "micro_amount": 0.35}),
    ("CERAMIC_BEIGE", "Ceramic Beige", (0.620, 0.550, 0.440), 0.0, 0.40,
     "Beige ceramic capacitor or resistor body",
     {"micro_detail": "FINE_CERAMIC", "micro_amount": 0.40}),
    ("FERRITE", "Ferrite", (0.030, 0.031, 0.034), 0.0, 0.55,
     "Sintered ferrite core: dark, matte and slightly granular",
     {"specular": 0.40, "micro_detail": "FINE_CERAMIC", "micro_amount": 0.50}),
    ("RUBBER", "Black Rubber", (0.022, 0.022, 0.024), 0.0, 0.78,
     "Rubber gasket or soft keypad",
     {"specular": 0.35, "micro_detail": "FINE_PLASTIC", "micro_amount": 0.40}),
    ("EPOXY", "Epoxy", (0.100, 0.085, 0.055), 0.0, 0.30,
     "Amber potting epoxy or glob top",
     {"coat_weight": 0.25, "coat_roughness": 0.10}),
    ("PLASTIC_BLACK", "Black Plastic", (0.028, 0.029, 0.032), 0.0, 0.52,
     "Generic black plastic",
     {"micro_detail": "FINE_PLASTIC", "micro_amount": 0.30}),
    ("SEMI_GLOSS_PLASTIC", "Semi-Gloss Plastic", (0.055, 0.058, 0.065), 0.0, 0.28,
     "Slightly coated engineering plastic",
     {"coat_weight": 0.16, "coat_roughness": 0.12}),
    ("PLASTIC_LIGHT_GRAY", "Light Gray Plastic", (0.420, 0.420, 0.430), 0.0, 0.50,
     "Light grey plastic body",
     {"micro_detail": "FINE_PLASTIC", "micro_amount": 0.25}),
    ("DISPLAY_GLASS_DARK", "Dark Display Glass", (0.012, 0.013, 0.015), 0.0, 0.05,
     "Dark cover glass over an OLED or LCD window",
     {"transmission_weight": 0.15, "ior": 1.52, "coat_weight": 0.30, "coat_roughness": 0.02}),
    ("GLASS_CLEAR", "Clear Glass", (0.940, 0.950, 0.960), 0.0, 0.02,
     "Clear glass or optical window",
     {"transmission_weight": 1.0, "ior": 1.52}),
    ("GLASS_TINTED", "Tinted Glass", (0.300, 0.450, 0.420), 0.0, 0.05,
     "Tinted glass; change Base Color for the tint",
     {"transmission_weight": 0.85, "ior": 1.52}),
    ("TRANSPARENT_LED", "Transparent LED", (0.350, 0.820, 1.000), 0.0, 0.08,
     "Transparent LED lens",
     {"transmission_weight": 0.82, "ior": 1.46}),
    ("SILKSCREEN_WHITE", "White Silkscreen", (0.800, 0.800, 0.790), 0.0, 0.58,
     "White printed silkscreen legend",
     {"micro_detail": "SOLDER_MASK", "micro_amount": 0.30}),
    ("SILKSCREEN_BLACK", "Black Silkscreen", (0.030, 0.030, 0.033), 0.0, 0.58,
     "Black printed silkscreen legend",
     {"micro_detail": "SOLDER_MASK", "micro_amount": 0.30}),
    ("CONNECTOR_PLASTIC", "Connector Plastic", (0.035, 0.036, 0.040), 0.0, 0.45,
     "Dense connector housing plastic",
     {"coat_weight": 0.06, "micro_detail": "IC_PLASTIC", "micro_amount": 0.35}),
    ("CUSTOM", "Custom", (0.500, 0.500, 0.500), 0.0, 0.50,
     "Your own material: set every value by hand", {}),
    ('PLASTIC_CREAM', 'Cream Plastic', (0.65, 0.59, 0.44), 0, 0.48, 'Cream Plastic starting values', {}),
    ('PLASTIC_RED', 'Red Plastic', (0.4, 0.025, 0.02), 0, 0.48, 'Red Plastic starting values', {}),
    ('PLASTIC_BLUE', 'Blue Plastic', (0.025, 0.08, 0.38), 0, 0.48, 'Blue Plastic starting values', {}),
    ('PLASTIC_GREEN', 'Green Plastic', (0.025, 0.25, 0.07), 0, 0.48, 'Green Plastic starting values', {}),
    ('RUBBER_GRAY', 'Gray Rubber', (0.12, 0.12, 0.13), 0, 0.78, 'Gray Rubber starting values', {'specular': 0.35}),
    ('NICKEL', 'Nickel', (0.66, 0.63, 0.56), 1, 0.27, 'Nickel starting values', {}),
    ('SOLDER', 'Solder', (0.65, 0.66, 0.68), 1, 0.38, 'Solder starting values', {}),
    ('BRASS', 'Brass', (0.72, 0.5, 0.2), 1, 0.3, 'Brass starting values', {}),
    ('CHROME', 'Chrome', (0.7, 0.72, 0.74), 1, 0.08, 'Chrome starting values', {}),
    ('PLASTIC_CLEAR', 'Clear Plastic', (0.94, 0.95, 0.96), 0, 0.1, 'Clear Plastic starting values', {'transmission_weight': 1.0, 'ior': 1.46}),
    ('PLASTIC_FROSTED', 'Frosted Plastic', (0.85, 0.87, 0.89), 0, 0.45, 'Frosted Plastic starting values', {'transmission_weight': 0.85, 'ior': 1.46}),
)


def _build_presets() -> dict[str, MaterialPreset]:
    """Expand the compact table into MaterialPreset objects."""
    presets: dict[str, MaterialPreset] = {}
    for key, display, colour, metallic, roughness, description, extra in _PRESET_TABLE:
        presets[key] = MaterialPreset(
            display_name=display,
            material_name=f"{MATERIAL_NAME_PREFIX}{key}",
            base_color=(colour[0], colour[1], colour[2], 1.0),
            metallic=metallic,
            roughness=roughness,
            description=description,
            **extra,
        )
    return presets


PRESET_DATA: dict[str, MaterialPreset] = _build_presets()

#: Static enum items for ``material_preset``.  Static on purpose: a dynamic
#: items callback stores integers, which would break saved .blend files.
MATERIAL_PRESET_ITEMS: list[tuple[str, str, str]] = [
    (key, preset.display_name, preset.description or preset.display_name)
    for key, preset in PRESET_DATA.items()
]


def get_or_create_pcb_material(material_name: str) -> bpy.types.Material:
    """Return an existing material by name, or create a Principled BSDF material.

    Existing materials are returned untouched; call :func:`apply_props_to_material`
    to change their values.  Newly created materials are tagged as PCB Studio
    managed so later edits are known to be safe.
    """
    mat = bpy.data.materials.get(material_name)
    if mat is not None:
        return mat

    mat = bpy.data.materials.new(material_name)
    compat.enable_nodes(mat)
    nodes = mat.node_tree.nodes
    nodes.clear()

    principled = nodes.new(type="ShaderNodeBsdfPrincipled")
    principled.location = (0, 0)

    output = nodes.new(type="ShaderNodeOutputMaterial")
    output.location = (300, 0)

    mat.node_tree.links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    compat.mark_managed(mat)
    return mat


def _set_blend_for_alpha(mat: bpy.types.Material, alpha: float) -> None:
    """Enable alpha blending only when it is actually needed.

    Touches the material, never the scene's render settings, and stays quiet on
    Blender versions that renamed or removed these properties.
    """
    if alpha >= 0.999:
        return
    try:
        mat.surface_render_method = "BLENDED"
        return
    except (AttributeError, TypeError):
        pass
    try:
        mat.blend_method = "BLEND"
    except (AttributeError, TypeError):
        pass


#: Logical socket key -> scene property name.
_VALUE_MAP: tuple[tuple[str, str], ...] = (
    ("base_color", "material_base_color"),
    ("metallic", "material_metallic"),
    ("roughness", "material_roughness"),
    ("ior", "material_ior"),
    ("specular", "material_specular"),
    ("coat_weight", "material_coat_weight"),
    ("coat_roughness", "material_coat_roughness"),
    ("anisotropic", "material_anisotropic"),
    ("anisotropic_rotation", "material_anisotropic_rotation"),
    ("transmission", "material_transmission_weight"),
    ("emission_color", "material_emission_color"),
    ("emission_strength", "material_emission_strength"),
    ("alpha", "material_alpha"),
)

def apply_props_to_material(mat: bpy.types.Material, props) -> int:
    """Write the UI values into a material's Principled BSDF.

    Only socket default values are written, and never a socket that is driven by
    a texture, so this never rebuilds or damages a shader graph.  Returns the
    number of values that the running Blender version accepted.
    """
    node = compat.get_principled(mat)
    if node is None:
        return 0
    written = 0
    for key, prop_name in _VALUE_MAP:
        if not hasattr(props, prop_name):
            continue
        value = getattr(props, prop_name)
        if hasattr(value, "__len__"):
            value = tuple(value)
        written += int(compat.set_value(node, key, value))

    colour = tuple(props.material_base_color)
    mat.diffuse_color = colour[:3] + (1.0,)
    mat.roughness = float(props.material_roughness)
    mat.metallic = float(props.material_metallic)
    _set_blend_for_alpha(mat, float(getattr(props, "material_alpha", 1.0)))
    return written


def update_material_from_values(
    mat: bpy.types.Material,
    base_color: tuple[float, float, float, float],
    metallic: float,
    roughness: float,
    coat_weight: float | None = None,
    transmission_weight: float | None = None,
    ior: float | None = None,
) -> None:
    """Update the core Principled values by logical name (version tolerant)."""
    node = compat.get_principled(mat)
    if node is None:
        return
    compat.set_value(node, "base_color", base_color)
    compat.set_value(node, "metallic", metallic)
    compat.set_value(node, "roughness", roughness)
    if coat_weight is not None:
        compat.set_value(node, "coat_weight", coat_weight)
    if transmission_weight is not None:
        compat.set_value(node, "transmission", transmission_weight)
    if ior is not None:
        compat.set_value(node, "ior", ior)
    mat.diffuse_color = tuple(base_color)[:3] + (1.0,)

#: Scene property name -> MaterialPreset field, used when a preset is chosen.
_PRESET_TO_PROP: tuple[tuple[str, str], ...] = (
    ("material_base_color", "base_color"),
    ("material_metallic", "metallic"),
    ("material_roughness", "roughness"),
    ("material_ior", "ior"),
    ("material_specular", "specular"),
    ("material_coat_weight", "coat_weight"),
    ("material_coat_roughness", "coat_roughness"),
    ("material_anisotropic", "anisotropic"),
    ("material_anisotropic_rotation", "anisotropic_rotation"),
    ("material_transmission_weight", "transmission_weight"),
    ("material_emission_color", "emission_color"),
    ("material_emission_strength", "emission_strength"),
    ("material_alpha", "alpha"),
    ("material_micro_detail", "micro_detail"),
    ("material_micro_amount", "micro_amount"),
    ("material_micro_scale", "micro_scale"),
)


def preset_display_name(key: str) -> str:
    """Friendly preset label used by material operator reports."""
    preset = PRESET_DATA.get(key)
    return preset.display_name if preset is not None else key


def apply_preset_to_props(props, preset_key: str) -> bool:
    """Load a preset's values into the UI properties.  Returns False if unknown."""
    preset = PRESET_DATA.get(preset_key)
    if preset is None:
        return False
    for prop_name, field_name in _PRESET_TO_PROP:
        if hasattr(props, prop_name):
            setattr(props, prop_name, getattr(preset, field_name))
    return True


def read_material_into_props(mat: bpy.types.Material, props) -> bool:
    """Load an existing material's Principled values into the UI properties."""
    node = compat.get_principled(mat)
    if node is None:
        return False
    for key, prop_name in _VALUE_MAP:
        value = compat.get_value(node, key)
        if value is None or not hasattr(props, prop_name):
            continue
        try:
            setattr(props, prop_name, value)
        except (TypeError, ValueError):
            continue
    return True


def live_preview_target(context, props):
    """Return the material a live-preview slider may safely write into, or None.

    This never copies.  Property update callbacks must not create or remove
    datablocks — that is an operator's job — so instead of splitting a shared
    material mid-drag this simply refuses, and the panel offers Make Unique.

    The active object's own material wins, so dragging a colour edits the thing
    that is actually selected rather than whatever was created or picked last.
    It is returned only when no other object uses it, so the write cannot reach
    a component the user did not select.

    With no active object carrying a material, ``props.current_material_name``
    is used instead: nothing is selected, so no object's independence is at
    stake and the user is deliberately editing a named material.  That keeps the
    "create a preset, then tune it with the sliders" flow working.

    A hand-built shader network is never written to in either case.
    """
    obj = getattr(context, "active_object", None) if context is not None else None
    mat = getattr(obj, "active_material", None) if obj is not None else None
    if mat is not None:
        if compat.is_shared_beyond(mat, [obj]):
            return None
    else:
        mat = bpy.data.materials.get(props.current_material_name)
        if mat is None:
            return None
    if not (compat.is_managed(mat) or compat.is_simple_principled(mat)):
        return None
    return mat


def ensure_editable(
    mat: bpy.types.Material,
    objects=(),
) -> tuple[bpy.types.Material, str]:
    """Return a material PCB Studio may safely write into for *objects*.

    A material is copied, and the copy swapped into *objects*, when either:

    * it is a hand-built shader network, which must never be overwritten, or
    * it is **shared** with an object outside *objects*, in which case editing
      it in place would recolour components the user did not select.  An OBJ
      import shares one datablock per ``usemtl`` across many layer objects, so
      this is the common case on a real board.

    Anything already exclusive to *objects* is edited in place, so no duplicate
    is created in the ordinary "edit my own material" flow.

    Returns ``(material, reason)`` where *reason* is ``""`` when the original
    was edited in place, ``"shared"`` when it was split off other objects, or
    ``"protected"`` when a custom shader network was preserved.
    """
    users = [
        obj for obj in objects
        if any(slot.material is mat for slot in obj.material_slots)
    ]
    protected = not (compat.is_managed(mat) or compat.is_simple_principled(mat))
    shared = compat.is_shared_beyond(mat, users)
    if not protected and not shared:
        compat.mark_managed(mat)
        return mat, ""
    copy = mat.copy()
    copy.name = f"{MATERIAL_NAME_PREFIX}{mat.name}"
    compat.mark_managed(copy)
    for obj in (users or objects):
        for slot in obj.material_slots:
            if slot.material is mat:
                slot.material = copy
    return copy, "shared" if shared else "protected"
