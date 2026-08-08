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
    eevee = scene.eevee
    eevee.taa_render_samples = 64
    eevee.use_shadows = True
    eevee.shadow_ray_count = 1
    eevee.shadow_step_count = 8

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
    """Create or update a background plane below the PCB.

    The plane is sized to fill the camera view and positioned with a
    small gap below the lowest point of the PCB.

    Args:
        bounds: The combined PCB bounding box.

    Returns:
        A status message.
    """
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

    # --- Plane ---
    plane = bpy.data.objects.get(BACKGROUND_NAME)
    if plane is None:
        mesh = bpy.data.meshes.new(BACKGROUND_NAME)
        plane = bpy.data.objects.new(BACKGROUND_NAME, mesh)
        setup_coll.objects.link(plane)

    # Size: cover at least 3x the max dimension for safety.
    plane_size = max_dim * 3.0
    gap = max_dim * 0.01  # 1% gap below lowest point.

    # Update mesh (simple quad).
    mesh = plane.data
    mesh.clear_geometry()
    half = plane_size / 2.0
    verts = [
        Vector((-half, -half, 0.0)),
        Vector((half, -half, 0.0)),
        Vector((-half, half, 0.0)),
        Vector((half, half, 0.0)),
    ]
    mesh.from_pydata(verts, [], [(0, 1, 3, 2)])
    mesh.update()

    # Position below PCB with gap.
    plane.location = Vector((
        bounds.center.x,
        bounds.center.y,
        bounds.min.z - gap,
    ))

    # Assign material.
    if plane.data.materials:
        plane.data.materials[0] = mat
    else:
        plane.data.materials.append(mat)

    return "Background plane created."