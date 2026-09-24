"""Idempotent PCB Studio shader nodes: micro surface detail and texture maps.

Every node this module creates is named with the ``PCBSTUDIO_`` prefix and is
looked up by name before creation, so repeated updates never duplicate nodes.
Turning a feature off removes only PCB Studio's own nodes; user-authored nodes
are never touched.
"""

from __future__ import annotations

from pathlib import Path

import bpy

from . import material_compat as compat

NODE_PREFIX: str = "PCBSTUDIO_"
MICRO_PREFIX: str = "PCBSTUDIO_MICRO_"
TEX_PREFIX: str = "PCBSTUDIO_TEX_"

#: Micro detail mode -> (noise scale, detail, roughness, distortion, stretch Y).
MICRO_PROFILES: dict[str, tuple[float, float, float, float, float]] = {
    "SOLDER_MASK": (620.0, 3.0, 0.55, 0.0, 1.0),
    "IC_PLASTIC": (900.0, 4.0, 0.65, 0.0, 1.0),
    "FINE_PLASTIC": (420.0, 2.0, 0.45, 0.0, 1.0),
    "FINE_CERAMIC": (300.0, 5.0, 0.70, 0.15, 1.0),
    "BRUSHED_METAL": (260.0, 2.0, 0.50, 0.0, 60.0),
}

#: Texture slot -> (property name, logical Principled key, non-colour data).
TEXTURE_SLOTS: tuple[tuple[str, str, bool], ...] = (
    ("base_color", "base_color", False),
    ("roughness", "roughness", True),
    ("metallic", "metallic", True),
    ("emission", "emission_color", False),
)


def _node(tree, name: str, node_type: str, location=(0.0, 0.0)):
    """Return the existing node called *name*, creating it once if missing."""
    node = tree.nodes.get(name)
    if node is not None and node.bl_idname != node_type:
        tree.nodes.remove(node)
        node = None
    if node is None:
        node = tree.nodes.new(type=node_type)
        node.name = name
        node.location = location
    return node


def _remove_nodes(tree, prefix: str) -> None:
    """Remove every PCB Studio node whose name starts with *prefix*."""
    for node in [n for n in tree.nodes if n.name.startswith(prefix)]:
        tree.nodes.remove(node)


def _load_image(filepath: str):
    """Load an image for a texture slot, or return None when unavailable."""
    if not filepath:
        return None
    path = Path(bpy.path.abspath(filepath))
    if not path.is_file():
        return None
    try:
        return bpy.data.images.load(str(path), check_existing=True)
    except RuntimeError:
        return None


def _set_colorspace(image, non_color: bool) -> None:
    """Use Non-Color for data maps; ignore builds without that colour space."""
    try:
        image.colorspace_settings.name = "Non-Color" if non_color else "sRGB"
    except TypeError:
        pass


def _build_micro_detail(tree, props, y: float):
    """Create the micro-detail bump chain and return its Normal output.

    Returns None when micro detail is off or the amount is zero.
    """
    mode = getattr(props, "material_micro_detail", "OFF")
    amount = float(getattr(props, "material_micro_amount", 0.0))
    if mode == "OFF" or amount <= 0.0 or mode not in MICRO_PROFILES:
        _remove_nodes(tree, MICRO_PREFIX)
        return None

    scale, detail, roughness, distortion, stretch = MICRO_PROFILES[mode]
    user_scale = max(0.01, float(getattr(props, "material_micro_scale", 1.0)))

    coord = _node(tree, f"{MICRO_PREFIX}COORD", "ShaderNodeTexCoord", (-1200.0, y))
    mapping = _node(tree, f"{MICRO_PREFIX}MAPPING", "ShaderNodeMapping", (-1000.0, y))
    noise = _node(tree, f"{MICRO_PREFIX}NOISE", "ShaderNodeTexNoise", (-800.0, y))
    bump = _node(tree, f"{MICRO_PREFIX}BUMP", "ShaderNodeBump", (-560.0, y))

    mapping.inputs["Scale"].default_value = (1.0, stretch, 1.0)
    noise.inputs["Scale"].default_value = scale / user_scale
    noise.inputs["Detail"].default_value = detail
    if "Roughness" in noise.inputs:
        noise.inputs["Roughness"].default_value = roughness
    if "Distortion" in noise.inputs:
        noise.inputs["Distortion"].default_value = distortion
    # Deliberately small: micro detail must survive close-ups without noise.
    bump.inputs["Strength"].default_value = min(0.5, amount * 0.5)
    bump.inputs["Distance"].default_value = 0.0006

    links = tree.links
    links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    return bump


def _build_texture_maps(tree, principled, props) -> int:
    """Wire optional image maps into the Principled BSDF.

    Empty paths remove their own nodes, so clearing a field is reversible.
    Returns the number of connected maps.
    """
    connected = 0
    y = 500.0
    for slot, socket_key, non_color in TEXTURE_SLOTS:
        name = f"{TEX_PREFIX}{slot.upper()}"
        image = _load_image(getattr(props, f"material_map_{slot}", ""))
        socket = compat.get_socket(principled, socket_key)
        if image is None or socket is None:
            _remove_nodes(tree, name)
            continue
        _set_colorspace(image, non_color)
        texture = _node(tree, name, "ShaderNodeTexImage", (-620.0, y))
        texture.image = image
        texture.label = slot.replace("_", " ").title()
        tree.links.new(texture.outputs["Color"], socket)
        connected += 1
        y -= 300.0
    return connected


def _build_normal_chain(tree, principled, props, micro_bump) -> None:
    """Chain normal map, height bump, and micro detail into Normal."""
    normal_socket = compat.get_socket(principled, "normal")
    if normal_socket is None:
        return
    links = tree.links
    upstream = None

    normal_image = _load_image(getattr(props, "material_map_normal", ""))
    if normal_image is None:
        _remove_nodes(tree, f"{TEX_PREFIX}NORMAL")
        _remove_nodes(tree, f"{NODE_PREFIX}NORMAL_MAP")
    else:
        _set_colorspace(normal_image, True)
        texture = _node(tree, f"{TEX_PREFIX}NORMAL", "ShaderNodeTexImage", (-1000.0, -300.0))
        texture.image = normal_image
        texture.label = "Normal Map"
        normal_map = _node(tree, f"{NODE_PREFIX}NORMAL_MAP", "ShaderNodeNormalMap", (-700.0, -300.0))
        normal_map.inputs["Strength"].default_value = float(
            getattr(props, "material_normal_strength", 1.0)
        )
        links.new(texture.outputs["Color"], normal_map.inputs["Color"])
        upstream = normal_map.outputs["Normal"]

    bump_image = _load_image(getattr(props, "material_map_bump", ""))
    bump_strength = float(getattr(props, "material_bump_strength", 0.0))
    if bump_image is None or bump_strength <= 0.0:
        _remove_nodes(tree, f"{TEX_PREFIX}BUMP")
        _remove_nodes(tree, f"{NODE_PREFIX}HEIGHT_BUMP")
    else:
        _set_colorspace(bump_image, True)
        texture = _node(tree, f"{TEX_PREFIX}BUMP", "ShaderNodeTexImage", (-1000.0, -650.0))
        texture.image = bump_image
        texture.label = "Bump Map"
        bump = _node(tree, f"{NODE_PREFIX}HEIGHT_BUMP", "ShaderNodeBump", (-700.0, -650.0))
        bump.inputs["Strength"].default_value = min(1.0, bump_strength)
        links.new(texture.outputs["Color"], bump.inputs["Height"])
        if upstream is not None:
            links.new(upstream, bump.inputs["Normal"])
        upstream = bump.outputs["Normal"]

    if micro_bump is not None:
        if upstream is not None:
            links.new(upstream, micro_bump.inputs["Normal"])
        upstream = micro_bump.outputs["Normal"]

    if upstream is not None:
        links.new(upstream, normal_socket)
    else:
        for link in list(normal_socket.links):
            if link.from_node.name.startswith(NODE_PREFIX):
                links.remove(link)


def apply_surface_detail(mat: bpy.types.Material, props) -> str:
    """Rebuild PCB Studio's optional texture and micro-detail nodes.

    Safe to call repeatedly: nodes are reused by name and features that are off
    remove only their own nodes.  Called from explicit operators, never from a
    slider callback.
    """
    principled = compat.get_principled(mat)
    if principled is None or mat.node_tree is None:
        return ""
    tree = mat.node_tree
    maps = _build_texture_maps(tree, principled, props)
    micro_bump = _build_micro_detail(tree, props, -1000.0)
    _build_normal_chain(tree, principled, props, micro_bump)

    notes: list[str] = []
    if maps:
        notes.append(f"{maps} texture map(s)")
    if getattr(props, "material_map_normal", ""):
        notes.append("normal map")
    if micro_bump is not None:
        notes.append("micro detail")
    return ", ".join(notes)


def clear_pcb_studio_nodes(mat: bpy.types.Material) -> None:
    """Remove every PCB Studio-created helper node from *mat*."""
    if mat.node_tree is None:
        return
    _remove_nodes(mat.node_tree, NODE_PREFIX)
