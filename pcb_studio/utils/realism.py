"""Optional, non-destructive PCB geometry and layered-material realism tools."""

from __future__ import annotations

from math import cos, sin
from pathlib import Path

import bpy

from ..constants import (
    COLLECTION_NAME,
    MICRO_BEVEL_MODIFIER_NAME,
    PCB_EDGE_MATERIAL_NAME,
    PCB_SURFACE_MATERIAL_NAME,
    PCB_UV_LAYER_NAME,
)


def pcb_mesh_objects(selected_only: bool = True) -> list[bpy.types.Object]:
    collection = bpy.data.collections.get(COLLECTION_NAME)
    if collection is None:
        return []
    allowed = {obj.name for obj in collection.all_objects if obj.type == "MESH"}
    source = bpy.context.selected_objects if selected_only else collection.all_objects
    return [obj for obj in source if obj.type == "MESH" and obj.name in allowed]


def smooth_components(objects: list[bpy.types.Object], angle: float) -> str:
    count = 0
    for obj in objects:
        mesh = obj.data
        if not mesh.polygons:
            continue
        # Blender 4.5's mesh API replaces the old auto_smooth flag.  It marks
        # mechanical edges sharp, then smooths faces between those boundaries.
        mesh.set_sharp_from_angle(angle=max(0.0, angle))
        mesh.shade_smooth()
        mesh.update()
        count += 1
    return f"Smoothed {count} PCB component object(s) with angle-preserved edges."


def _bevel_width(obj: bpy.types.Object, preset: str, custom_width: float) -> float:
    dimensions = [abs(value) for value in obj.dimensions if abs(value) > 1e-8]
    if not dimensions:
        return 0.0
    max_dim = max(dimensions)
    min_dim = min(dimensions)
    factors = {"SUBTLE": 0.00045, "REALISTIC": 0.0010, "STRONG": 0.0022}
    requested = custom_width if preset == "CUSTOM" else max_dim * factors.get(preset, 0.0)
    return min(max(0.0, requested), min_dim * 0.20)


def apply_micro_bevel(
    objects: list[bpy.types.Object],
    preset: str,
    custom_width: float,
    segments: int,
    angle_limit: float,
) -> str:
    if preset == "OFF":
        return remove_micro_bevel(objects)
    applied = 0
    for obj in objects:
        width = _bevel_width(obj, preset, custom_width)
        if width <= 0.0:
            continue
        modifier = obj.modifiers.get(MICRO_BEVEL_MODIFIER_NAME)
        if modifier is None:
            modifier = obj.modifiers.new(MICRO_BEVEL_MODIFIER_NAME, "BEVEL")
        modifier.width = width
        modifier.segments = max(1, segments)
        modifier.limit_method = "ANGLE"
        modifier.angle_limit = angle_limit
        modifier.affect = "EDGES"
        modifier.harden_normals = True
        applied += 1
    return f"Scale-aware micro bevel applied to {applied} object(s); existing managed modifiers were reused."


def remove_micro_bevel(objects: list[bpy.types.Object]) -> str:
    removed = 0
    for obj in objects:
        modifier = obj.modifiers.get(MICRO_BEVEL_MODIFIER_NAME)
        if modifier is not None:
            obj.modifiers.remove(modifier)
            removed += 1
    return f"Removed managed micro bevel from {removed} object(s)."


def setup_planar_uv(objects: list[bpy.types.Object], props) -> str:
    mapped = 0
    angle = props.pcb_uv_rotation
    scale = props.pcb_uv_scale
    cos_a, sin_a = cos(angle), sin(angle)
    for obj in objects:
        mesh = obj.data
        if not mesh.vertices or not mesh.loops:
            continue
        xs = [vertex.co.x for vertex in mesh.vertices]
        ys = [vertex.co.y for vertex in mesh.vertices]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        width = max(max_x - min_x, 1e-9)
        depth = max(max_y - min_y, 1e-9)
        uv_layer = mesh.uv_layers.get(PCB_UV_LAYER_NAME)
        if uv_layer is None:
            uv_layer = mesh.uv_layers.new(name=PCB_UV_LAYER_NAME)
        mesh.uv_layers.active = uv_layer
        for loop in mesh.loops:
            co = mesh.vertices[loop.vertex_index].co
            u = (co.x - min_x) / width - 0.5
            v = (co.y - min_y) / depth - 0.5
            rotated_u = (u * cos_a - v * sin_a) * scale
            rotated_v = (u * sin_a + v * cos_a) * scale
            uv_layer.data[loop.index].uv = (
                rotated_u + 0.5 + props.pcb_uv_offset_x,
                rotated_v + 0.5 + props.pcb_uv_offset_y,
            )
        mesh.update()
        mapped += 1
    return f"Shared top-down PCB UV mapping updated on {mapped} object(s)."


def _principled(nodes, name: str, location: tuple[float, float], color, roughness: float, metallic: float = 0.0):
    node = nodes.new(type="ShaderNodeBsdfPrincipled")
    node.name = name
    node.location = location
    node.inputs["Base Color"].default_value = tuple(color)
    node.inputs["Roughness"].default_value = roughness
    node.inputs["Metallic"].default_value = metallic
    return node


def _mask_output(nodes, filepath: str, name: str, location, default: float):
    path = Path(bpy.path.abspath(filepath)) if filepath else None
    if path is not None and path.is_file():
        try:
            image = bpy.data.images.load(str(path), check_existing=True)
            try:
                image.colorspace_settings.name = "Non-Color"
            except TypeError:
                pass
            texture = nodes.new(type="ShaderNodeTexImage")
            texture.name = name
            texture.label = path.name
            texture.location = location
            texture.image = image
            texture.interpolation = "Linear"
            return texture.outputs["Color"], True
        except RuntimeError:
            pass
    value = nodes.new(type="ShaderNodeValue")
    value.name = f"{name} Default"
    value.location = location
    value.outputs[0].default_value = default
    return value.outputs[0], False


def _surface_branch(nodes, links, props, side: str, y_offset: float):
    prefix = side.title()
    copper_path = getattr(props, f"{side}_copper_mask")
    solder_path = getattr(props, f"{side}_solder_mask")
    silk_path = getattr(props, f"{side}_silkscreen_mask")
    solder_out, solder_loaded = _mask_output(nodes, solder_path, f"{prefix} Solder Mask", (-900, y_offset + 260), 1.0)
    copper_out, copper_loaded = _mask_output(nodes, copper_path, f"{prefix} Copper Mask", (-900, y_offset), 0.0)
    silk_out, silk_loaded = _mask_output(nodes, silk_path, f"{prefix} Silkscreen Mask", (-900, y_offset - 260), 0.0)

    substrate = _principled(
        nodes, f"{prefix} FR4", (-330, y_offset + 330),
        props.pcb_edge_color, props.pcb_edge_roughness,
    )
    solder = _principled(
        nodes, f"{prefix} Solder Mask Shader", (-330, y_offset + 170),
        props.pcb_solder_mask_color, props.pcb_solder_mask_roughness,
    )
    if "Coat Weight" in solder.inputs:
        solder.inputs["Coat Weight"].default_value = props.pcb_solder_mask_coat
        solder.inputs["Coat Roughness"].default_value = min(1.0, props.pcb_solder_mask_roughness * 0.75)
    copper = _principled(
        nodes, f"{prefix} Copper Shader", (-330, y_offset - 10),
        props.pcb_copper_color, props.pcb_copper_roughness, props.pcb_copper_metallic,
    )
    silk = _principled(
        nodes, f"{prefix} Silkscreen Shader", (-330, y_offset - 210),
        props.pcb_silkscreen_color, props.pcb_silkscreen_roughness,
    )

    normal_output = None
    if props.surface_imperfections != "OFF":
        strength = {"CLEAN": 0.025, "SUBTLE": 0.055, "USED": 0.10}.get(props.surface_imperfections, 0.025)
        noise = nodes.new(type="ShaderNodeTexNoise")
        noise.name = f"{prefix} Surface Microtexture"
        noise.location = (-680, y_offset - 500)
        noise.inputs["Scale"].default_value = 220.0
        noise.inputs["Detail"].default_value = 2.0
        bump = nodes.new(type="ShaderNodeBump")
        bump.name = f"{prefix} Surface Imperfection Bump"
        bump.location = (-500, y_offset - 450)
        bump.inputs["Strength"].default_value = strength
        bump.inputs["Distance"].default_value = 0.00004
        links.new(noise.outputs["Fac"], bump.inputs["Height"])
        normal_output = bump.outputs["Normal"]

    if props.trace_relief_enabled and copper_loaded:
        height_output = copper_out
        if props.trace_relief_invert:
            invert = nodes.new(type="ShaderNodeMath")
            invert.operation = "SUBTRACT"
            invert.inputs[0].default_value = 1.0
            invert.location = (-650, y_offset - 80)
            links.new(copper_out, invert.inputs[1])
            height_output = invert.outputs[0]
        bump = nodes.new(type="ShaderNodeBump")
        bump.name = f"{prefix} Trace Relief"
        bump.location = (-500, y_offset - 80)
        bump.inputs["Strength"].default_value = props.trace_relief_strength
        bump.inputs["Distance"].default_value = props.trace_relief_distance
        links.new(height_output, bump.inputs["Height"])
        if normal_output is not None:
            links.new(normal_output, bump.inputs["Normal"])
        normal_output = bump.outputs["Normal"]

    if normal_output is not None:
        for shader in (substrate, solder, copper, silk):
            links.new(normal_output, shader.inputs["Normal"])

    solder_mix = nodes.new(type="ShaderNodeMixShader")
    solder_mix.name = f"{prefix} FR4 Solder Mix"
    solder_mix.location = (-40, y_offset + 240)
    links.new(solder_out, solder_mix.inputs[0])
    links.new(substrate.outputs["BSDF"], solder_mix.inputs[1])
    links.new(solder.outputs["BSDF"], solder_mix.inputs[2])

    copper_mix = nodes.new(type="ShaderNodeMixShader")
    copper_mix.name = f"{prefix} Copper Surface Mix"
    copper_mix.location = (160, y_offset + 100)
    links.new(copper_out, copper_mix.inputs[0])
    links.new(solder_mix.outputs["Shader"], copper_mix.inputs[1])
    links.new(copper.outputs["BSDF"], copper_mix.inputs[2])

    if props.pcb_silkscreen_relief > 0.0 and silk_loaded:
        silk_bump = nodes.new(type="ShaderNodeBump")
        silk_bump.name = f"{prefix} Silkscreen Relief"
        silk_bump.location = (-80, y_offset - 260)
        silk_bump.inputs["Strength"].default_value = props.pcb_silkscreen_relief
        silk_bump.inputs["Distance"].default_value = 0.00005
        links.new(silk_out, silk_bump.inputs["Height"])
        if normal_output is not None:
            links.new(normal_output, silk_bump.inputs["Normal"])
        links.new(silk_bump.outputs["Normal"], silk.inputs["Normal"])

    silk_mix = nodes.new(type="ShaderNodeMixShader")
    silk_mix.name = f"{prefix} Silkscreen Surface Mix"
    silk_mix.location = (370, y_offset)
    links.new(silk_out, silk_mix.inputs[0])
    links.new(copper_mix.outputs["Shader"], silk_mix.inputs[1])
    links.new(silk.outputs["BSDF"], silk_mix.inputs[2])
    return silk_mix.outputs["Shader"], (solder_loaded, copper_loaded, silk_loaded)


def _edge_material(props) -> bpy.types.Material:
    material = bpy.data.materials.get(PCB_EDGE_MATERIAL_NAME)
    if material is None:
        material = bpy.data.materials.new(PCB_EDGE_MATERIAL_NAME)
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF")
    if principled is None:
        material.node_tree.nodes.clear()
        principled = material.node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
        output = material.node_tree.nodes.new(type="ShaderNodeOutputMaterial")
        material.node_tree.links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    principled.inputs["Base Color"].default_value = tuple(props.pcb_edge_color)
    principled.inputs["Roughness"].default_value = props.pcb_edge_roughness
    material.diffuse_color = tuple(props.pcb_edge_color)
    return material


def create_pcb_surface_material(objects: list[bpy.types.Object], props) -> str:
    if not objects:
        return "Select at least one PCB mesh object."
    material = bpy.data.materials.get(PCB_SURFACE_MATERIAL_NAME)
    if material is None:
        material = bpy.data.materials.new(PCB_SURFACE_MATERIAL_NAME)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    front, front_loaded = _surface_branch(nodes, links, props, "front", 420.0)
    back, back_loaded = _surface_branch(nodes, links, props, "back", -520.0)
    geometry = nodes.new(type="ShaderNodeNewGeometry")
    geometry.name = "PCB Front Back Selector"
    geometry.location = (390, -500)
    side_mix = nodes.new(type="ShaderNodeMixShader")
    side_mix.name = "PCB Front Back Material"
    side_mix.location = (650, 0)
    output = nodes.new(type="ShaderNodeOutputMaterial")
    output.location = (880, 0)
    links.new(geometry.outputs["Backfacing"], side_mix.inputs[0])
    links.new(front, side_mix.inputs[1])
    links.new(back, side_mix.inputs[2])
    links.new(side_mix.outputs["Shader"], output.inputs["Surface"])
    material.diffuse_color = tuple(props.pcb_solder_mask_color)

    edge_material = _edge_material(props)
    assigned = 0
    for obj in objects:
        if material.name in obj.data.materials:
            surface_index = list(obj.data.materials).index(material)
        else:
            obj.data.materials.append(material)
            surface_index = len(obj.data.materials) - 1
        if edge_material.name in obj.data.materials:
            edge_index = list(obj.data.materials).index(edge_material)
        else:
            obj.data.materials.append(edge_material)
            edge_index = len(obj.data.materials) - 1
        for polygon in obj.data.polygons:
            polygon.material_index = edge_index if abs(polygon.normal.z) < 0.5 else surface_index
        assigned += 1

    loaded_count = sum(front_loaded) + sum(back_loaded)
    return f"Layered PCB surface assigned to {assigned} object(s); {loaded_count} optional layer image(s) loaded."
