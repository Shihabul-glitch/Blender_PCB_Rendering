"""Render configuration, world background, and background plane utilities."""

from __future__ import annotations

import bpy
from mathutils import Vector

from ..constants import (
    BACKGROUND_MATERIAL_NAME,
    BACKGROUND_NAME,
    RENDER_SETUP_COLLECTION,
)
from .geometry import BoundingBox


def _get_eevee_engine() -> str:
    """Return the correct EEVEE render engine identifier for Blender 4.5.

    Blender 4.2+ uses ``BLENDER_EEVEE_NEXT``.  Falls back to
    ``BLENDER_EEVEE`` if the primary identifier is unavailable.
    """
    if hasattr(bpy.types, "RenderEngine"):
        # bpy.types.RenderEngine is the metaclass; check registered engines.
        pass
    # Simple heuristic: try the known 4.2+ identifier first.
    return "BLENDER_EEVEE_NEXT"


def configure_eevee_shadows(scene: bpy.types.Scene) -> None:
    """Give EEVEE Next enough samples to actually resolve a soft shadow.

    The product shadow was invisible in the viewport while rendering correctly in
    Cycles.  Nothing here had ever set the viewport sample count, and the shadow
    quality was pinned at its floor (1 ray, 8 steps), so the wide penumbra of a
    studio area light resolved to nothing on screen.  Cycles path-traces the same
    light at hundreds of samples and was unaffected.

    Scene-level and idempotent, and inert while Cycles is the active engine.
    Every attribute is EEVEE-Next-only, so each is probed individually to keep
    Blender 4.5 and 5.2 both working.
    """
    eevee = getattr(scene, "eevee", None)
    if eevee is None:
        return
    for name, value in (
        ("use_shadows", True),
        ("shadow_ray_count", 4),
        ("shadow_step_count", 16),
        # The viewport accumulator; without it jittered soft shadows never
        # converge on screen, which is what the user was actually seeing.
        ("taa_samples", 32),
    ):
        if hasattr(eevee, name):
            setattr(eevee, name, value)


def configure_render_settings() -> str:
    """Apply EEVEE preview render settings.

    Returns:
        A status message.
    """
    scene = bpy.context.scene

    engine_id = _get_eevee_engine()
    try:
        scene.render.engine = engine_id
    except TypeError:
        # Fallback for older or differently configured Blender builds.
        try:
            scene.render.engine = "BLENDER_EEVEE"
        except TypeError:
            return "EEVEE render engine not available."

    # Resolution.
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100

    # Output format.
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"

    # EEVEE quality settings (conservative, preview-oriented).
    if hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = 64
    configure_eevee_shadows(scene)

    # Color management — use existing valid setting when available.
    valid_transforms = {"Standard", "Filmic", "AgX", "False Color", "Raw"}
    current = scene.view_settings.view_transform
    if current not in valid_transforms:
        scene.view_settings.view_transform = "Standard"

    return "EEVEE render settings configured."


def setup_world_background() -> str:
    """Configure a neutral low-intensity world background.

    Uses the existing world if present; creates one otherwise.

    Returns:
        A status message.
    """
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world

    # Ensure we have a node tree.
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links

    bg_node = nodes.get("Background")
    if bg_node is None:
        bg_node = nodes.new(type="ShaderNodeBackground")
        out_node = nodes.get("World Output")
        if out_node and not bg_node.outputs[0].links:
            links.new(bg_node.outputs[0], out_node.inputs[0])

    # Neutral medium-dark gray.
    bg_node.inputs["Color"].default_value = (0.05, 0.05, 0.06, 1.0)
    bg_node.inputs["Strength"].default_value = 1.0

    return "World background configured."


def setup_background_plane(bounds: BoundingBox) -> str:
    """Create and place the managed backdrop object and its wall material.

    ``PCB_BACKGROUND`` retains its original name for saved-file compatibility.
    This function owns the object, its collection, its position and the default
    wall material; the mesh is built by ``studio._update_backdrop_geometry``,
    which is always called immediately afterwards.

    Args:
        bounds: The combined PCB bounding box.

    Returns:
        A status message.
    """
    from . import studio_environment
    scene = bpy.context.scene
    if studio_environment.enabled(scene):
        return studio_environment.update(scene, scene.pcb_studio_import)

    from .camera import get_or_create_render_setup_collection

    setup_coll = get_or_create_render_setup_collection()
    max_dim = bounds.max_dimension

    if max_dim <= 0:
        return "Skipped background: invalid bounding box."

    # --- Material ---
    mat = bpy.data.materials.get(BACKGROUND_MATERIAL_NAME)
    if mat is None:
        mat = bpy.data.materials.new(BACKGROUND_MATERIAL_NAME)
        mat.use_nodes = True
        principled = mat.node_tree.nodes.get("Principled BSDF")
        if principled:
            principled.inputs["Base Color"].default_value = (0.35, 0.35, 0.36, 1.0)
            principled.inputs["Roughness"].default_value = 0.7
            principled.inputs["Metallic"].default_value = 0.0

    # --- Managed cyclorama object ---
    plane = bpy.data.objects.get(BACKGROUND_NAME)
    if plane is None:
        mesh = bpy.data.meshes.new(BACKGROUND_NAME)
        plane = bpy.data.objects.new(BACKGROUND_NAME, mesh)
        setup_coll.objects.link(plane)

    gap = max_dim * 0.012

    # The mesh itself belongs to studio._update_backdrop_geometry, which runs
    # immediately after this and rebuilds it from the panel's shape, width,
    # depth, wall and curve-radius properties.  Building a second, differently
    # proportioned profile here would only be thrown away.

    # Position below PCB with gap.
    plane.location = Vector((
        bounds.center.x,
        bounds.center.y,
        bounds.min.z - gap,
    ))
    plane["pcbstudio_managed"] = True

    # Assign material.
    if plane.data.materials:
        plane.data.materials[0] = mat
    else:
        plane.data.materials.append(mat)

    return "Infinity cyclorama created."
