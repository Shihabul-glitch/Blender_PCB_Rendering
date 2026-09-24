"""Managed product-photography floor geometry, materials, and grounding."""

from __future__ import annotations

from math import cos, pi, sin

import bpy
from mathutils import Vector

from ..constants import COLLECTION_NAME, REFLECTION_MATERIAL_NAME, REFLECTION_PLANE_NAME
from .camera import get_or_create_render_setup_collection
from .geometry import BoundingBox, compute_pcb_bounds


FLOOR_TAG = "pcbstudio_floor"
FLOOR_ROLE = "pcbstudio_floor_role"
INFINITE_NAME = "PCB_STUDIO_INFINITE_FLOOR"
INFINITE_MATERIAL_NAME = "PCB_STUDIO_FLOOR_MATERIAL"

MATERIAL_PRESETS = {
    "MATTE_WHITE": ((0.82, 0.82, 0.82, 1.0), 0.78, 0.0, 0.15, 0.0, 12.0),
    "MATTE_BLACK": ((0.008, 0.008, 0.010, 1.0), 0.82, 0.0, 0.12, 0.0, 12.0),
    "LIGHT_GRAY": ((0.48, 0.50, 0.52, 1.0), 0.55, 0.0, 0.28, 0.0, 12.0),
    "DARK_GRAY": ((0.055, 0.060, 0.070, 1.0), 0.48, 0.0, 0.38, 0.0, 12.0),
    "WARM_GRAY": ((0.35, 0.31, 0.27, 1.0), 0.58, 0.0, 0.25, 0.0, 12.0),
    "GLOSSY_WHITE": ((0.88, 0.88, 0.88, 1.0), 0.10, 0.0, 0.92, 0.0, 12.0),
    "GLOSSY_BLACK": ((0.006, 0.007, 0.010, 1.0), 0.08, 0.06, 0.95, 0.0, 12.0),
    "CONCRETE": ((0.28, 0.29, 0.30, 1.0), 0.84, 0.0, 0.10, 0.32, 8.0),
    "SOFT_STUDIO": ((0.62, 0.63, 0.65, 1.0), 0.38, 0.0, 0.55, 0.0, 12.0),
    "METALLIC": ((0.22, 0.23, 0.25, 1.0), 0.24, 0.88, 0.82, 0.10, 45.0),
}

STUDIO_PRESETS = {
    "CLEAN_WHITE": ("STANDARD", "MATTE_WHITE", 0.18),
    "APPLE_SOFT": ("INFINITE", "SOFT_STUDIO", 0.48),
    "DARK_LUXURY": ("STANDARD", "GLOSSY_BLACK", 0.88),
    "GRAY_STUDIO": ("STANDARD", "LIGHT_GRAY", 0.34),
    "GLOSSY_PRODUCT": ("STANDARD", "GLOSSY_WHITE", 0.92),
    "SOFT_REFLECTIVE": ("STANDARD", "SOFT_STUDIO", 0.55),
    "MATTE_PRODUCT": ("STANDARD", "MATTE_WHITE", 0.08),
    "FLOATING": ("NONE", "SOFT_STUDIO", 0.0),
}

REFLECTION_PRESETS = {
    "MATTE": (False, 0.0, 0.85, 0.65, 0.15),
    "SOFT": (True, 0.38, 0.48, 0.45, 0.35),
    "PRODUCT": (True, 0.65, 0.25, 0.18, 0.55),
    "GLOSSY": (True, 0.88, 0.10, 0.06, 0.72),
    "MIRROR": (True, 1.0, 0.0, 0.0, 1.0),
}


def _bounds() -> BoundingBox | None:
    collection = bpy.data.collections.get(COLLECTION_NAME)
    if collection is None:
        return None
    result = compute_pcb_bounds(collection)
    return result if result.is_valid else None


def _tag(obj: bpy.types.Object, role: str) -> None:
    obj[FLOOR_TAG] = True
    obj[FLOOR_ROLE] = role
    obj["pcbstudio_managed"] = True


def _managed(role: str) -> bpy.types.Object | None:
    for obj in bpy.data.objects:
        if obj.get(FLOOR_TAG, False) and obj.get(FLOOR_ROLE) == role:
            return obj
    # Adopt only the add-on's known legacy plane, never a generic user plane.
    if role == "plane":
        obj = bpy.data.objects.get(REFLECTION_PLANE_NAME)
        setup = bpy.data.collections.get("PCB_RENDER_SETUP")
        belongs_to_setup = setup is not None and obj is not None and obj.name in setup.objects
        has_legacy_material = bool(obj is not None and obj.type == "MESH" and obj.data.materials and obj.data.materials[0].name == REFLECTION_MATERIAL_NAME)
        if obj is not None and (obj.get("pcbstudio_managed", False) or (belongs_to_setup and has_legacy_material)):
            _tag(obj, role)
            return obj
    return None


def _ensure_object(name: str, role: str) -> bpy.types.Object:
    obj = _managed(role)
    if obj is None:
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)
        get_or_create_render_setup_collection().objects.link(obj)
    _tag(obj, role)
    return obj


def _set_visible(obj: bpy.types.Object | None, visible: bool) -> None:
    if obj is not None:
        obj.hide_viewport = not visible
        obj.hide_render = not visible


def _material() -> bpy.types.Material:
    material = bpy.data.materials.get(INFINITE_MATERIAL_NAME)
    if material is None:
        material = bpy.data.materials.get(REFLECTION_MATERIAL_NAME)
    if material is None:
        material = bpy.data.materials.new(INFINITE_MATERIAL_NAME)
    material.name = INFINITE_MATERIAL_NAME
    material["pcbstudio_floor_material"] = True
    material.use_nodes = True
    return material


def _ensure_shader(material: bpy.types.Material):
    nodes = material.node_tree.nodes
    shader = nodes.get("PCB Studio Floor Shader") or nodes.get("Principled BSDF")
    if shader is None:
        shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.name = "PCB Studio Floor Shader"
    output = next((node for node in nodes if node.type == "OUTPUT_MATERIAL"), None)
    if output is None:
        output = nodes.new("ShaderNodeOutputMaterial")
    if not shader.outputs["BSDF"].is_linked:
        material.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return shader


def _assign_material(obj: bpy.types.Object) -> bpy.types.Material:
    material = _material()
    if obj.data.materials:
        obj.data.materials[0] = material
    else:
        obj.data.materials.append(material)
    return material


def apply_material_preset(scene: bpy.types.Scene, props, key: str) -> str:
    if key == "CUSTOM":
        props.floor_material = key
        update_floor_material(scene, props)
        return "Custom floor material applied from manual controls."
    values = MATERIAL_PRESETS.get(key)
    if values is None:
        return f"Unknown floor material: {key}"
    color, roughness, metallic, reflection, bump, scale = values
    scene["pcbstudio_batch_update"] = True
    try:
        props.floor_material = key
        props.floor_color = color
        props.floor_roughness = roughness
        props.floor_metallic = metallic
        props.floor_reflection_strength = reflection
        props.floor_bump_strength = bump
        props.floor_bump_scale = scale
    finally:
        scene["pcbstudio_batch_update"] = False
    update_floor_material(scene, props)
    return f"{key.replace('_', ' ').title()} floor material applied."


def update_floor_material(scene: bpy.types.Scene, props) -> str:
    from . import studio_environment
    if studio_environment.enabled(scene):
        return studio_environment.update(scene, props)
    material = _material()
    shader = _ensure_shader(material)
    strength = props.floor_reflection_strength if props.floor_reflection_enabled else 0.0
    roughness = min(1.0, max(props.floor_roughness, props.floor_reflection_roughness) + props.floor_reflection_blur * 0.25)
    color = tuple(min(1.0, channel * props.floor_brightness) for channel in props.floor_color[:3]) + (props.floor_color[3],)
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = min(1.0, roughness + (1.0 - strength) * 0.35)
    shader.inputs["Metallic"].default_value = props.floor_metallic * strength
    specular = shader.inputs.get("Specular IOR Level") or shader.inputs.get("Specular")
    if specular is not None:
        specular.default_value = props.floor_specular * (0.25 + strength * 0.75)
    coat = shader.inputs.get("Coat Weight") or shader.inputs.get("Clearcoat")
    if coat is not None:
        coat.default_value = strength * props.floor_fresnel_strength
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    bump = nodes.get("PCB Studio Floor Bump")
    noise = nodes.get("PCB Studio Floor Texture")
    if props.floor_bump_strength > 0.0:
        if noise is None:
            noise = nodes.new("ShaderNodeTexNoise")
            noise.name = "PCB Studio Floor Texture"
        if bump is None:
            bump = nodes.new("ShaderNodeBump")
            bump.name = "PCB Studio Floor Bump"
        noise.inputs["Scale"].default_value = props.floor_bump_scale
        bump.inputs["Strength"].default_value = props.floor_bump_strength
        if not bump.inputs["Height"].is_linked:
            links.new(noise.outputs["Fac"], bump.inputs["Height"])
        if not shader.inputs["Normal"].is_linked:
            links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    elif shader.inputs["Normal"].is_linked:
        links.remove(shader.inputs["Normal"].links[0])
    material.diffuse_color = color
    for obj in (_managed("plane"), _managed("infinite")):
        if obj is not None and obj.type == "MESH":
            _assign_material(obj)
    custom = props.floor_custom_object
    if props.floor_mode == "CUSTOM" and custom is not None and custom.type == "MESH":
        _assign_material(custom)
    return "Floor material updated."


FLOOR_BASE_Z = "pcbstudio_floor_base_z"


def _floor_base_z(obj: bpy.types.Object, bounds: BoundingBox) -> float:
    """Cached floor height, re-seeded whenever it no longer suits the product.

    The value is cached so the floor does not chase the product every update --
    Ground Product moves the product down onto the floor, and a floor that
    followed it would never settle.  But caching it forever was a bug: Prepare
    Scene re-centres the assembly, so a floor created for an earlier position
    stayed put and sliced straight through the board.

    It is therefore re-seeded when the cached height is at or above the product's
    lowest point (it would sit inside the board), or more than one product-length
    below it (stale after a large move).  A deliberate small offset survives.
    """
    span = max(bounds.max_dimension, 1e-6)
    cached = obj.get(FLOOR_BASE_Z)
    if cached is not None:
        gap = float(cached) - bounds.min.z
        if -span < gap < 0.0:
            return float(cached)
    base = float(bounds.min.z)
    obj[FLOOR_BASE_Z] = base
    return base


def _floor_location(obj: bpy.types.Object, bounds: BoundingBox, props):
    """World position for a managed floor.

    ``floor_height`` is a fraction of the product's largest dimension, matching
    ``studio._update_floor_geometry``.  It used to be added here as absolute
    Blender units, so the default -0.005 was sub-millimetre on a real board and
    the floor z-fought with the underside of the PCB.
    """
    span = max(bounds.max_dimension, 1e-6)
    return (
        bounds.center.x + props.floor_offset_x,
        bounds.center.y + props.floor_offset_y,
        _floor_base_z(obj, bounds) + span * props.floor_height,
    )


def _plane_geometry(obj: bpy.types.Object, bounds: BoundingBox, props) -> None:
    half = max(bounds.max_dimension, 1e-6) * props.floor_size * 0.5
    mesh = obj.data
    mesh.clear_geometry()
    mesh.from_pydata([(-half, -half, 0), (half, -half, 0), (half, half, 0), (-half, half, 0)], [], [(0, 1, 2, 3)])
    mesh.update()
    obj.location = _floor_location(obj, bounds, props)
    obj.rotation_euler[2] = props.floor_rotation
    modifier = obj.modifiers.get("PCB_STUDIO_FLOOR_THICKNESS")
    if props.floor_thickness > 0.0:
        if modifier is None:
            modifier = obj.modifiers.new("PCB_STUDIO_FLOOR_THICKNESS", "SOLIDIFY")
        modifier.thickness = props.floor_thickness
    elif modifier is not None:
        obj.modifiers.remove(modifier)


def _infinite_geometry(obj: bpy.types.Object, bounds: BoundingBox, props) -> None:
    scale = max(bounds.max_dimension, 1e-6)
    half_width = scale * props.infinite_width * 0.5
    depth = scale * props.infinite_depth
    height = scale * props.infinite_height
    radius = min(scale * props.infinite_curve_radius, depth * 0.8, height * 0.8)
    wall_y = depth * 0.5
    curve_start = wall_y - radius
    # Analytic per-vertex normals: the strip is welded, so smooth shading works,
    # but without explicit normals the flat floor and wall would have their
    # shading bent into the curve near the transition.
    profile = [
        (-depth * 0.5, 0.0, (0.0, 0.0, 1.0)),
        (curve_start, 0.0, (0.0, 0.0, 1.0)),
    ]
    for index in range(1, props.infinite_smoothness + 1):
        angle = (pi / 2.0) * index / props.infinite_smoothness
        profile.append((
            curve_start + radius * sin(angle),
            radius * (1.0 - cos(angle)),
            (0.0, -sin(angle), cos(angle)),
        ))
    profile.append((wall_y, height, (0.0, -1.0, 0.0)))
    vertices = []
    normals = []
    faces = []
    for y, z, normal in profile:
        vertices.extend(((-half_width, y, z), (half_width, y, z)))
        normals.extend((normal, normal))
    for index in range(len(profile) - 1):
        start = index * 2
        faces.append((start, start + 1, start + 3, start + 2))
    obj.data.clear_geometry()
    obj.data.from_pydata(vertices, [], faces)
    obj.data.update()
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    obj.data.normals_split_custom_set_from_vertices(normals)
    obj.location = _floor_location(obj, bounds, props)
    obj.rotation_euler[2] = props.floor_rotation


def _visibility_settings(obj: bpy.types.Object, props) -> None:
    if hasattr(obj, "visible_camera"):
        obj.visible_camera = props.floor_visible_camera
    if hasattr(obj, "visible_shadow"):
        obj.visible_shadow = props.floor_receive_shadows and not props.disable_floor_shadow


def _restore_custom_floor(custom) -> None:
    prefix = "pcbstudio_custom_floor_"
    if prefix + "original_viewport" not in custom:
        return
    custom.hide_viewport = bool(custom[prefix + "original_viewport"])
    custom.hide_render = bool(custom[prefix + "original_render"])
    for attribute in ("visible_camera", "visible_shadow"):
        key = prefix + attribute
        if key in custom:
            setattr(custom, attribute, bool(custom[key]))
    original = bpy.data.materials.get(custom.get(prefix + "original_material", ""))
    if custom.get(prefix + "had_material", False):
        if custom.data.materials:
            custom.data.materials[0] = original
        else:
            custom.data.materials.append(original)
    elif custom.data.materials and custom.data.materials[0] is not None and custom.data.materials[0].get("pcbstudio_floor_material", False):
        custom.data.materials.pop(index=0)
    for key in list(custom.keys()):
        if key.startswith(prefix):
            del custom[key]


def update_floor_system(scene: bpy.types.Scene, props) -> str:
    from . import studio_environment
    if studio_environment.enabled(scene):
        return studio_environment.update(scene, props)
    mode = props.floor_mode
    plane = _managed("plane")
    infinite = _managed("infinite")
    custom = props.floor_custom_object
    for previous in bpy.data.objects:
        if mode != "CUSTOM" or previous != custom:
            _restore_custom_floor(previous)
    if (mode != "SHADOW_CATCHER" or not props.shadow_catcher_transparent) and "pcbstudio_floor_film_transparent" in scene:
        scene.render.film_transparent = bool(scene["pcbstudio_floor_film_transparent"])
        del scene["pcbstudio_floor_film_transparent"]
    if mode == "NONE":
        _set_visible(plane, False)
        _set_visible(infinite, False)
        return "Floor disabled; product floats without floor geometry."
    bounds = _bounds()
    if bounds is None:
        return "Cannot update floor: no product geometry found."
    if mode in {"STANDARD", "SHADOW_CATCHER"}:
        plane = _ensure_object(REFLECTION_PLANE_NAME, "plane")
        _plane_geometry(plane, bounds, props)
        _assign_material(plane)
        _set_visible(plane, True)
        _set_visible(infinite, False)
        _visibility_settings(plane, props)
        catcher_supported = hasattr(plane, "is_shadow_catcher")
        if catcher_supported:
            plane.is_shadow_catcher = mode == "SHADOW_CATCHER"
        if mode == "SHADOW_CATCHER" and props.shadow_catcher_transparent:
            if "pcbstudio_floor_film_transparent" not in scene:
                scene["pcbstudio_floor_film_transparent"] = bool(scene.render.film_transparent)
            scene.render.film_transparent = True
        update_floor_material(scene, props)
        if mode == "SHADOW_CATCHER" and scene.render.engine != "CYCLES":
            return "Shadow Catcher created; switch the render engine to Cycles for native shadow catching."
        return "Managed floor updated."
    if mode == "INFINITE":
        infinite = _ensure_object(INFINITE_NAME, "infinite")
        _infinite_geometry(infinite, bounds, props)
        _assign_material(infinite)
        _set_visible(infinite, True)
        _set_visible(plane, False)
        _visibility_settings(infinite, props)
        update_floor_material(scene, props)
        return "Infinite studio floor updated."
    _set_visible(plane, False)
    _set_visible(infinite, False)
    if custom is None or custom.type != "MESH":
        return "Cannot update floor: Custom Floor needs a mesh object."
    if "pcbstudio_custom_floor_original_viewport" not in custom:
        custom["pcbstudio_custom_floor_original_viewport"] = bool(custom.hide_viewport)
        custom["pcbstudio_custom_floor_original_render"] = bool(custom.hide_render)
        custom["pcbstudio_custom_floor_had_material"] = bool(custom.data.materials)
        custom["pcbstudio_custom_floor_original_material"] = custom.data.materials[0].name if custom.data.materials and custom.data.materials[0] else ""
        for attribute in ("visible_camera", "visible_shadow"):
            if hasattr(custom, attribute):
                custom["pcbstudio_custom_floor_" + attribute] = bool(getattr(custom, attribute))
    custom.hide_viewport = False
    custom.hide_render = False
    _visibility_settings(custom, props)
    update_floor_material(scene, props)
    return "Custom floor active."


def fit_floor_to_product(scene: bpy.types.Scene, props) -> str:
    bounds = _bounds()
    if bounds is None:
        return "Cannot fit floor: no product geometry found."
    props.floor_size = max(1.25, max(bounds.dimensions.x, bounds.dimensions.y) / max(bounds.max_dimension, 1e-6) * 1.5)
    props.floor_offset_x = 0.0
    props.floor_offset_y = 0.0
    return update_floor_system(scene, props)


def center_floor(scene: bpy.types.Scene, props) -> str:
    scene["pcbstudio_batch_update"] = True
    try:
        props.floor_offset_x = 0.0
        props.floor_offset_y = 0.0
        props.floor_rotation = 0.0
    finally:
        scene["pcbstudio_batch_update"] = False
    return update_floor_system(scene, props)


def _product_roots() -> list[bpy.types.Object]:
    collection = bpy.data.collections.get(COLLECTION_NAME)
    if collection is None:
        return []
    objects = [obj for obj in collection.all_objects if not obj.get("pcbstudio_managed", False)]
    object_set = set(objects)
    return [obj for obj in objects if obj.parent not in object_set]


def ground_product(scene: bpy.types.Scene, props) -> str:
    bounds = _bounds()
    roots = _product_roots()
    if bounds is None or not roots:
        return "Cannot ground product: no product geometry found."
    if props.floor_mode == "NONE":
        return "Cannot ground product: enable a floor first."
    floor = props.floor_custom_object if props.floor_mode == "CUSTOM" else (_managed("infinite") if props.floor_mode == "INFINITE" else _managed("plane"))
    if floor is None:
        return "Cannot ground product: create or select a floor first."
    span = max(bounds.max_dimension, 1e-6)
    floor_z = (floor.matrix_world.translation.z if floor is not None
               else bounds.min.z + span * props.floor_height) + props.floor_gap
    delta = floor_z - bounds.min.z
    for obj in roots:
        if "pcbstudio_ground_original_location" not in obj:
            obj["pcbstudio_ground_original_location"] = list(obj.location)
        matrix = obj.matrix_world.copy()
        matrix.translation.z += delta
        obj.matrix_world = matrix
    bpy.context.view_layer.update()
    return "Product grounded without changing X/Y position."


def reset_ground_position() -> str:
    restored = 0
    for obj in _product_roots():
        if "pcbstudio_ground_original_location" in obj:
            obj.location = obj["pcbstudio_ground_original_location"]
            del obj["pcbstudio_ground_original_location"]
            restored += 1
        elif "pcbstudio_ground_original_z" in obj:
            obj.location.z = float(obj["pcbstudio_ground_original_z"])
            del obj["pcbstudio_ground_original_z"]
            restored += 1
    bpy.context.view_layer.update()
    return f"Restored ground position for {restored} product root object(s)."


def reset_floor(scene: bpy.types.Scene, props) -> str:
    scene["pcbstudio_batch_update"] = True
    try:
        props.floor_size = 3.0
        props.floor_height = -0.005
        props.floor_offset_x = props.floor_offset_y = 0.0
        props.floor_rotation = 0.0
        props.floor_thickness = 0.0
    finally:
        scene["pcbstudio_batch_update"] = False
    for obj in (_managed("plane"), _managed("infinite")):
        if obj is not None:
            obj[FLOOR_BASE_Z] = float(_bounds().min.z) if _bounds() is not None else 0.0
    return update_floor_system(scene, props)


def apply_reflection_preset(scene: bpy.types.Scene, props, key: str) -> str:
    values = REFLECTION_PRESETS.get(key)
    if values is None:
        return f"Unknown reflection preset: {key}"
    scene["pcbstudio_batch_update"] = True
    try:
        props.floor_reflection_enabled, props.floor_reflection_strength, props.floor_reflection_roughness, props.floor_reflection_blur, props.floor_fresnel_strength = values
    finally:
        scene["pcbstudio_batch_update"] = False
    update_floor_material(scene, props)
    return f"{key.title()} reflection applied."


def apply_studio_floor_preset(scene: bpy.types.Scene, props, key: str) -> str:
    values = STUDIO_PRESETS.get(key)
    if values is None:
        return f"Unknown studio floor preset: {key}"
    mode, material, reflection = values
    scene["pcbstudio_batch_update"] = True
    try:
        props.floor_mode = mode
        props.floor_reflection_strength = reflection
    finally:
        scene["pcbstudio_batch_update"] = False
    apply_material_preset(scene, props, material)
    props.floor_reflection_strength = reflection
    return update_floor_system(scene, props)


def apply_infinite_preset(scene: bpy.types.Scene, props, key: str) -> str:
    mapping = {"WHITE": "GLOSSY_WHITE", "GRAY": "LIGHT_GRAY", "BLACK": "MATTE_BLACK", "SOFT_GRADIENT": "SOFT_STUDIO"}
    material = mapping.get(key)
    if material is None:
        return f"Unknown infinity preset: {key}"
    scene["pcbstudio_batch_update"] = True
    try:
        props.floor_mode = "INFINITE"
    finally:
        scene["pcbstudio_batch_update"] = False
    apply_material_preset(scene, props, material)
    return update_floor_system(scene, props)


def cleanup_floor_system() -> int:
    """Remove only tagged generated floors and restore referenced custom floors."""
    removed = 0
    for scene in bpy.data.scenes:
        if "pcbstudio_floor_film_transparent" in scene:
            scene.render.film_transparent = bool(scene["pcbstudio_floor_film_transparent"])
            del scene["pcbstudio_floor_film_transparent"]
    for obj in list(bpy.data.objects):
        _restore_custom_floor(obj)
        if not obj.get(FLOOR_TAG, False):
            continue
        data = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if isinstance(data, bpy.types.Mesh) and data.users == 0:
            bpy.data.meshes.remove(data)
        removed += 1
    material = bpy.data.materials.get(INFINITE_MATERIAL_NAME)
    if material is not None and material.users == 0:
        bpy.data.materials.remove(material)
    return removed
