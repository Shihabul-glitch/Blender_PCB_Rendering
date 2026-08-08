"""Material preset definitions and Blender material creation utilities."""

from __future__ import annotations

from dataclasses import dataclass

import bpy

from ..constants import MATERIAL_NAME_PREFIX


@dataclass
class MaterialPreset:
    """Predefined material values for a PCB Studio preset."""

    display_name: str
    material_name: str
    base_color: tuple[float, float, float, float]
    metallic: float
    roughness: float
    coat_weight: float = 0.0


# --- Preset data ---
PRESET_DATA: dict[str, MaterialPreset] = {
    "SOLDER_MASK_GREEN": MaterialPreset(
        "Green Solder Mask",
        f"{MATERIAL_NAME_PREFIX}SOLDER_MASK_GREEN",
        (0.05, 0.30, 0.08, 1.0),
        0.0,
        0.4,
    ),
    "SOLDER_MASK_BLUE": MaterialPreset(
        "Blue Solder Mask",
        f"{MATERIAL_NAME_PREFIX}SOLDER_MASK_BLUE",
        (0.05, 0.10, 0.40, 1.0),
        0.0,
        0.4,
    ),
    "SOLDER_MASK_RED": MaterialPreset(
        "Red Solder Mask",
        f"{MATERIAL_NAME_PREFIX}SOLDER_MASK_RED",
        (0.40, 0.06, 0.06, 1.0),
        0.0,
        0.4,
    ),
    "SOLDER_MASK_BLACK": MaterialPreset(
        "Black Solder Mask",
        f"{MATERIAL_NAME_PREFIX}SOLDER_MASK_BLACK",
        (0.04, 0.04, 0.05, 1.0),
        0.0,
        0.4,
    ),
    "FR4": MaterialPreset(
        "FR4 Substrate",
        f"{MATERIAL_NAME_PREFIX}FR4",
        (0.25, 0.22, 0.15, 1.0),
        0.0,
        0.7,
    ),
    "PLASTIC_BLACK": MaterialPreset(
        "Black Plastic",
        f"{MATERIAL_NAME_PREFIX}PLASTIC_BLACK",
        (0.03, 0.03, 0.04, 1.0),
        0.0,
        0.5,
    ),
    "PLASTIC_DARK_GRAY": MaterialPreset(
        "Dark Gray Plastic",
        f"{MATERIAL_NAME_PREFIX}PLASTIC_DARK_GRAY",
        (0.15, 0.15, 0.16, 1.0),
        0.0,
        0.5,
    ),
    "PLASTIC_LIGHT_GRAY": MaterialPreset(
        "Light Gray Plastic",
        f"{MATERIAL_NAME_PREFIX}PLASTIC_LIGHT_GRAY",
        (0.55, 0.55, 0.56, 1.0),
        0.0,
        0.5,
    ),
    "CERAMIC_WHITE": MaterialPreset(
        "White Ceramic",
        f"{MATERIAL_NAME_PREFIX}CERAMIC_WHITE",
        (0.85, 0.85, 0.85, 1.0),
        0.0,
        0.3,
    ),
    "COPPER": MaterialPreset(
        "Copper",
        f"{MATERIAL_NAME_PREFIX}COPPER",
        (0.85, 0.45, 0.20, 1.0),
        1.0,
        0.25,
    ),
    "GOLD": MaterialPreset(
        "Gold",
        f"{MATERIAL_NAME_PREFIX}GOLD",
        (0.90, 0.70, 0.15, 1.0),
        1.0,
        0.2,
    ),
    "TIN": MaterialPreset(
        "Tin or Silver",
        f"{MATERIAL_NAME_PREFIX}TIN",
        (0.75, 0.78, 0.80, 1.0),
        1.0,
        0.3,
    ),
    "SILKSCREEN_WHITE": MaterialPreset(
        "White Silkscreen",
        f"{MATERIAL_NAME_PREFIX}SILKSCREEN_WHITE",
        (0.92, 0.92, 0.92, 1.0),
        0.0,
        0.6,
    ),
    "SILKSCREEN_BLACK": MaterialPreset(
        "Black Silkscreen",
        f"{MATERIAL_NAME_PREFIX}SILKSCREEN_BLACK",
        (0.06, 0.06, 0.07, 1.0),
        0.0,
        0.6,
    ),
    "CUSTOM": MaterialPreset(
        "Custom",
        f"{MATERIAL_NAME_PREFIX}CUSTOM",
        (0.50, 0.50, 0.50, 1.0),
        0.0,
        0.5,
    ),
}


def get_or_create_pcb_material(material_name: str) -> bpy.types.Material:
    """Return an existing material by name, or create a new Principled BSDF material.

    Only creates the node tree on first creation.  Existing materials are
    returned as-is (call :func:`update_material_from_values` to modify).

    Args:
        material_name: Exact Blender material name.

    Returns:
        The Blender material.
    """
    mat = bpy.data.materials.get(material_name)
    if mat is not None:
        return mat

    mat = bpy.data.materials.new(material_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()

    principled = nodes.new(type="ShaderNodeBsdfPrincipled")
    principled.location = (0, 0)

    output = nodes.new(type="ShaderNodeOutputMaterial")
    output.location = (300, 0)

    mat.node_tree.links.new(
        principled.outputs["BSDF"],
        output.inputs["Surface"],
    )

    return mat


def update_material_from_values(
    mat: bpy.types.Material,
    base_color: tuple[float, float, float, float],
    metallic: float,
    roughness: float,
    coat_weight: float | None = None,
) -> None:
    """Update a Principled BSDF material's inputs by socket name.

    Args:
        mat: The Blender material (must have a node tree).
        base_color: RGBA color.
        metallic: 0–1 metallic value.
        roughness: 0–1 roughness value.
        coat_weight: Optional coat weight (skipped if socket is absent).
    """
    principled = mat.node_tree.nodes.get("Principled BSDF")
    if principled is None:
        return

    inputs = principled.inputs

    if "Base Color" in inputs:
        inputs["Base Color"].default_value = base_color

    if "Metallic" in inputs:
        inputs["Metallic"].default_value = metallic

    if "Roughness" in inputs:
        inputs["Roughness"].default_value = roughness

    if coat_weight is not None and "Coat Weight" in inputs:
        inputs["Coat Weight"].default_value = coat_weight

    # Update the viewport display color.
    mat.diffuse_color = base_color[:3] + (1.0,)