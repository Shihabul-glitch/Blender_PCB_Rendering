"""Studio lighting presets, background presets, and HDRI environment utilities."""

from __future__ import annotations

from dataclasses import dataclass
from math import radians
from pathlib import Path

import bpy
from mathutils import Vector

from ..constants import (
    BACKGROUND_MATERIAL_NAME,
    BACKGROUND_NAME,
    COLLECTION_NAME,
    FILL_LIGHT_NAME,
    KEY_LIGHT_NAME,
    PCB_STUDIO_WORLD_NAME,
    RENDER_SETUP_COLLECTION,
    RIM_LIGHT_2_NAME,
    RIM_LIGHT_NAME,
    TOP_LIGHT_NAME,
)
from .geometry import BoundingBox, compute_pcb_bounds

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class LightDefinition:
    """Definition of a single managed light in a studio preset."""

    name: str
    """Managed light name constant (e.g. KEY_LIGHT_NAME)."""

    position: Vector
    """Relative offset multiplier (applied to max_dim)."""

    energy_mult: float
    """Energy multiplier relative to the baseline (500 × max_dim)."""

    size_mult: float
    """Size multiplier relative to baseline (max_dim × 1.5)."""

    color: tuple[float, float, float] = (1.0, 1.0, 1.0)


@dataclass
class StudioPreset:
    """A complete studio lighting preset."""

    display_name: str
    lights: list[LightDefinition]
    recommended_background: str


# ---------------------------------------------------------------------------
# Preset definitions
# ---------------------------------------------------------------------------

PRESETS: dict[str, StudioPreset] = {
    "BRIGHT_STUDIO": StudioPreset(
        "Bright Studio",
        [
            LightDefinition(KEY_LIGHT_NAME, Vector((1.0, -1.0, 1.0)), 1.0, 1.0),
            LightDefinition(FILL_LIGHT_NAME, Vector((-1.0, 1.0, 0.5)), 0.8, 1.0),
            LightDefinition(TOP_LIGHT_NAME, Vector((0.0, 0.0, 1.5)), 0.5, 1.2),
            LightDefinition(RIM_LIGHT_NAME, Vector((0.0, 1.0, 0.7)), 0.3, 0.8),
        ],
        "WHITE",
    ),
    "DARK_STUDIO": StudioPreset(
        "Dark Studio",
        [
            LightDefinition(KEY_LIGHT_NAME, Vector((1.0, -1.0, 0.8)), 1.2, 0.9),
            LightDefinition(FILL_LIGHT_NAME, Vector((-0.5, 0.8, 0.4)), 0.3, 1.0),
            LightDefinition(RIM_LIGHT_NAME, Vector((-1.0, 0.5, 0.6)), 0.8, 0.7),
            LightDefinition(RIM_LIGHT_2_NAME, Vector((0.5, 1.0, 0.6)), 0.8, 0.7),
        ],
        "BLACK",
    ),
    "PRODUCT_SHOT": StudioPreset(
        "Product Shot",
        [
            LightDefinition(KEY_LIGHT_NAME, Vector((1.0, -1.0, 1.0)), 1.0, 1.1),
            LightDefinition(FILL_LIGHT_NAME, Vector((-1.0, 0.7, 0.5)), 0.5, 1.0),
            LightDefinition(RIM_LIGHT_NAME, Vector((0.0, 1.0, 0.8)), 0.4, 0.9),
        ],
        "DARK_GRAY",
    ),
    "PCB_SHOWCASE": StudioPreset(
        "PCB Showcase",
        [
            LightDefinition(KEY_LIGHT_NAME, Vector((0.8, -0.8, 1.0)), 1.0, 1.0),
            LightDefinition(FILL_LIGHT_NAME, Vector((-0.6, 0.6, 0.4)), 0.4, 1.0),
            LightDefinition(RIM_LIGHT_NAME, Vector((-0.8, 0.8, 0.7)), 0.5, 0.8),
            LightDefinition(RIM_LIGHT_2_NAME, Vector((0.7, 0.8, 0.7)), 0.5, 0.8),
            LightDefinition(TOP_LIGHT_NAME, Vector((0.0, 0.0, 1.5)), 0.3, 1.2),
        ],
        "DARK_GRAY",
    ),
}

# All light names potentially managed by any preset.
_ALL_MANAGED_LIGHT_NAMES = {
    KEY_LIGHT_NAME,
    FILL_LIGHT_NAME,
    RIM_LIGHT_NAME,
    RIM_LIGHT_2_NAME,
    TOP_LIGHT_NAME,
}

# Per-light default colours for presets that do not specify a colour override.
_DEFAULT_LIGHT_COLOR = (1.0, 1.0, 1.0)

# Baseline values from the existing Milestone 3 lighting.
_BASELINE_ENERGY_FACTOR = 500.0
_BASELINE_SIZE_FACTOR = 1.5

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_or_create_area_light(
    name: str,
    collection: bpy.types.Collection,
) -> bpy.types.Object:
    """Return an existing Area light by name, or create a new one."""
    obj = bpy.data.objects.get(name)
    if obj is None:
        light_data = bpy.data.lights.new(name, "AREA")
        obj = bpy.data.objects.new(name, light_data)
        collection.objects.link(obj)
    if obj.data.type != "AREA":
        new_data = bpy.data.lights.new(name, "AREA")
        obj.data = new_data
    return obj


def _clear_track_constraints(light: bpy.types.Object) -> None:
    """Remove all Damped Track and Track To constraints from *light*."""
    for c in list(light.constraints):
        if c.type in {"DAMPED_TRACK", "TRACK_TO"}:
            light.constraints.remove(c)


def _aim_light_at(light: bpy.types.Object, target: Vector) -> None:
    """Point *light* toward *target* using a Damped Track constraint."""
    _clear_track_constraints(light)

    track_target = bpy.data.objects.new(
        f"{light.name}_track_target", None,
    )
    track_target.location = target
    for coll in light.users_collection:
        coll.objects.link(track_target)
        break

    track = light.constraints.new(type="DAMPED_TRACK")
    track.target = track_target
    track.track_axis = "TRACK_NEGATIVE_Z"


def _cleanup_orphan_track_targets() -> None:
    """Remove track-target empties whose owning light no longer exists."""
    for obj in list(bpy.data.objects):
        if not obj.name.endswith("_track_target"):
            continue
        light_name = obj.name[: -len("_track_target")]
        if bpy.data.objects.get(light_name) is None:
            bpy.data.objects.remove(obj, do_unlink=True)


def _get_pcb_bounds() -> BoundingBox | None:
    """Return the PCB_MODEL bounding box, or None."""
    pcb_coll = bpy.data.collections.get(COLLECTION_NAME)
    if pcb_coll is None:
        return None
    bounds = compute_pcb_bounds(pcb_coll)
    return bounds if bounds.is_valid else None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def apply_lighting_preset(
    preset_key: str,
    intensity: float = 1.0,
    shadow_softness: float = 1.0,
) -> str:
    """Apply a studio lighting preset.

    Creates/updates managed lights, positions them relative to the PCB
    bounding box, and hides any managed lights not in the preset.

    Args:
        preset_key: Key in ``PRESETS``.
        intensity: Global energy multiplier (default 1.0).
        shadow_softness: Size multiplier for softness (0.5–2.0).

    Returns:
        A status message.
    """
    preset = PRESETS.get(preset_key)
    if preset is None:
        return f"Unknown preset: {preset_key}"

    bounds = _get_pcb_bounds()
    if bounds is None:
        return "Cannot apply lighting: no PCB geometry found."

    from .camera import get_or_create_render_setup_collection

    setup_coll = get_or_create_render_setup_collection()
    center = bounds.center
    max_dim = bounds.max_dimension

    preset_light_names = {ld.name for ld in preset.lights}

    # Create / update preset lights.
    for ld in preset.lights:
        light = _get_or_create_area_light(ld.name, setup_coll)
        light.hide_render = False

        safe_intensity = max(0.0, intensity)
        safe_softness = max(0.1, shadow_softness)

        base_energy = _BASELINE_ENERGY_FACTOR * max_dim * ld.energy_mult
        light.data.energy = base_energy * safe_intensity
        light.data.color = ld.color

        base_size = max_dim * _BASELINE_SIZE_FACTOR * ld.size_mult
        light.data.size = base_size * safe_softness

        light.location = center + ld.position * max_dim
        _aim_light_at(light, center)

    # Hide managed lights that are *not* in this preset.
    for name in _ALL_MANAGED_LIGHT_NAMES - preset_light_names:
        obj = bpy.data.objects.get(name)
        if obj is not None:
            obj.hide_render = True

    _cleanup_orphan_track_targets()

    return f"{preset.display_name} lighting applied."


def set_light_visibility(visible: bool) -> None:
    """Show or hide all managed studio lights from renders.

    Args:
        visible: ``True`` to show, ``False`` to hide from renders.
    """
    for name in _ALL_MANAGED_LIGHT_NAMES:
        obj = bpy.data.objects.get(name)
        if obj is not None:
            obj.hide_render = not visible


def apply_background_preset(preset_key: str) -> str:
    """Apply a background preset to the managed background plane.

    Args:
        preset_key: One of ``WHITE``, ``BLACK``, ``DARK_GRAY``, ``BLUE_GRADIENT``.

    Returns:
        A status message.
    """
    mat = bpy.data.materials.get(BACKGROUND_MATERIAL_NAME)
    if mat is None:
        mat = bpy.data.materials.new(BACKGROUND_MATERIAL_NAME)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.clear()
        principled = nodes.new(type="ShaderNodeBsdfPrincipled")
        output = nodes.new(type="ShaderNodeOutputMaterial")
        mat.node_tree.links.new(
            principled.outputs["BSDF"], output.inputs["Surface"],
        )

    if preset_key == "BLUE_GRADIENT":
        return _configure_blue_gradient_nodes(mat)
    else:
        return _configure_solid_background(mat, preset_key)


def _configure_solid_background(
    mat: bpy.types.Material, preset_key: str,
) -> str:
    """Set the background material to a solid colour."""
    colors = {
        "WHITE": (0.85, 0.85, 0.86, 1.0),
        "BLACK": (0.02, 0.02, 0.03, 1.0),
        "DARK_GRAY": (0.12, 0.12, 0.13, 1.0),
    }
    color = colors.get(preset_key, (0.12, 0.12, 0.13, 1.0))
    roughness = {"WHITE": 0.7, "BLACK": 0.5, "DARK_GRAY": 0.6}.get(
        preset_key, 0.6,
    )

    # Clear any gradient nodes; rebuild simple Principled-only tree.
    nodes = mat.node_tree.nodes
    nodes.clear()
    principled = nodes.new(type="ShaderNodeBsdfPrincipled")
    output = nodes.new(type="ShaderNodeOutputMaterial")
    mat.node_tree.links.new(
        principled.outputs["BSDF"], output.inputs["Surface"],
    )

    principled.inputs["Base Color"].default_value = color
    principled.inputs["Roughness"].default_value = roughness
    principled.inputs["Metallic"].default_value = 0.0

    mat.diffuse_color = color[:3] + (1.0,)
    return f"Background: {preset_key}"


def _configure_blue_gradient_nodes(mat: bpy.types.Material) -> str:
    """Build a procedural dark-blue gradient on the background material."""
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Nodes
    tc = nodes.new(type="ShaderNodeTexCoord")
    tc.location = (-600, 0)

    mapping = nodes.new(type="ShaderNodeMapping")
    mapping.location = (-400, 0)
    mapping.inputs["Location"].default_value = (0.0, 0.0, 0.0)

    gradient = nodes.new(type="ShaderNodeTexGradient")
    gradient.location = (-200, 0)
    gradient.gradient_type = "SPHERICAL"

    ramp = nodes.new(type="ShaderNodeValToRGB")
    ramp.location = (0, 0)
    ramp.color_ramp.color_mode = "RGB"
    # Dark blue stop
    ramp.color_ramp.elements[0].color = (0.01, 0.02, 0.08, 1.0)
    ramp.color_ramp.elements[0].position = 0.0
    # Medium blue stop
    ramp.color_ramp.elements[1].color = (0.03, 0.06, 0.18, 1.0)
    ramp.color_ramp.elements[1].position = 1.0

    principled = nodes.new(type="ShaderNodeBsdfPrincipled")
    principled.location = (200, 0)
    principled.inputs["Roughness"].default_value = 0.8
    principled.inputs["Metallic"].default_value = 0.0

    output = nodes.new(type="ShaderNodeOutputMaterial")
    output.location = (400, 0)

    # Links
    links.new(tc.outputs["Generated"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], gradient.inputs["Vector"])
    links.new(gradient.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], principled.inputs["Base Color"])
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])

    mat.diffuse_color = (0.03, 0.06, 0.18, 1.0)
    return "Background: Blue Gradient"


def setup_hdri_world(
    filepath: str,
    rotation_degrees: float = 0.0,
    brightness: float = 1.0,
) -> str:
    """Load an HDR/EXR file into the managed PCB_STUDIO_WORLD.

    Creates the World and node tree on first call; reuses existing
    nodes on subsequent calls.

    Args:
        filepath: Absolute path to .hdr or .exr file.
        rotation_degrees: Z-axis rotation in degrees.
        brightness: Background node strength (0.0–5.0).

    Returns:
        A status message.
    """
    path = Path(filepath)
    if not path.is_file():
        return f"HDRI file not found: {filepath}"

    suffix = path.suffix.lower()
    if suffix not in {".hdr", ".exr"}:
        return f"Unsupported HDRI format: {suffix}"

    # Load or reuse image.
    try:
        img = bpy.data.images.load(str(path))
    except Exception:
        return f"Failed to load image: {filepath}"

    # Get or create the managed World.
    world = bpy.data.worlds.get(PCB_STUDIO_WORLD_NAME)
    if world is None:
        world = bpy.data.worlds.new(PCB_STUDIO_WORLD_NAME)
        world.use_nodes = True

    bpy.context.scene.world = world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links

    # Reuse or create nodes.
    tc = nodes.get("Texture Coordinate")
    if tc is None:
        tc = nodes.new(type="ShaderNodeTexCoord")
        tc.location = (-600, 0)

    mapping = nodes.get("Mapping")
    if mapping is None:
        mapping = nodes.new(type="ShaderNodeMapping")
        mapping.location = (-400, 0)

    env_tex = nodes.get("Environment Texture")
    if env_tex is None:
        env_tex = nodes.new(type="ShaderNodeTexEnvironment")
        env_tex.location = (-200, 0)

    bg = nodes.get("Background")
    if bg is None:
        bg = nodes.new(type="ShaderNodeBackground")
        bg.location = (0, 0)

    out = nodes.get("World Output")
    if out is None:
        out = nodes.new(type="ShaderNodeOutputWorld")
        out.location = (200, 0)

    # Connect if not already.
    if not tc.outputs["Generated"].links:
        links.new(tc.outputs["Generated"], mapping.inputs["Vector"])
    if not mapping.outputs["Vector"].links:
        links.new(mapping.outputs["Vector"], env_tex.inputs["Vector"])
    if not env_tex.outputs["Color"].links:
        links.new(env_tex.outputs["Color"], bg.inputs["Color"])
    if not bg.outputs["Background"].links:
        links.new(bg.outputs["Background"], out.inputs["Surface"])

    # Apply settings.
    env_tex.image = img
    mapping.inputs["Rotation"].default_value[2] = radians(rotation_degrees)
    bg.inputs["Strength"].default_value = max(0.0, brightness)

    return f"HDRI loaded: {path.name}"


def remove_hdri_from_world() -> str:
    """Remove the HDRI environment, restoring a neutral World.

    Returns:
        A status message.
    """
    world = bpy.data.worlds.get(PCB_STUDIO_WORLD_NAME)
    if world is None:
        return "No PCB Studio world to remove."

    world.use_nodes = True
    nodes = world.node_tree.nodes

    env_tex = nodes.get("Environment Texture")
    if env_tex is not None:
        nodes.remove(env_tex)

    bg = nodes.get("Background")
    if bg is not None:
        bg.inputs["Color"].default_value = (0.05, 0.05, 0.06, 1.0)
        bg.inputs["Strength"].default_value = 1.0

    return "HDRI removed."