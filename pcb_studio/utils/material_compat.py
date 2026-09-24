"""Blender-version-tolerant access to Principled BSDF sockets.

Principled BSDF socket names changed between Blender 3.x, 4.x, and 5.x.  All
PCB Studio material code goes through this module instead of hardcoding socket
names, so an unavailable socket degrades to a no-op instead of an exception.
"""

from __future__ import annotations

import bpy

from ..constants import COLLECTION_NAME

#: Logical value name -> candidate socket names, most recent Blender first.
SOCKET_ALIASES: dict[str, tuple[str, ...]] = {
    "base_color": ("Base Color",),
    "metallic": ("Metallic",),
    "roughness": ("Roughness",),
    "ior": ("IOR",),
    "specular": ("Specular IOR Level", "Specular"),
    "coat_weight": ("Coat Weight", "Clearcoat"),
    "coat_roughness": ("Coat Roughness", "Clearcoat Roughness"),
    "anisotropic": ("Anisotropic",),
    "anisotropic_rotation": ("Anisotropic Rotation",),
    "transmission": ("Transmission Weight", "Transmission"),
    "emission_color": ("Emission Color", "Emission"),
    "emission_strength": ("Emission Strength",),
    "alpha": ("Alpha",),
    "normal": ("Normal",),
}

MANAGED_KEY: str = "pcb_studio_managed"
PRESET_KEY: str = "pcb_studio_preset"

#: ``Material.use_nodes`` is deprecated from Blender 5.0 and materials always
#: have a node tree there, so it is only read or written on older versions.
_HAS_USE_NODES: bool = bpy.app.version < (5, 0, 0)


def uses_nodes(mat: bpy.types.Material | None) -> bool:
    """Return True when *mat* has a usable shader node tree."""
    if mat is None or mat.node_tree is None:
        return False
    return bool(mat.use_nodes) if _HAS_USE_NODES else True


def enable_nodes(mat: bpy.types.Material) -> None:
    """Make sure *mat* has a shader node tree, on every supported version."""
    if _HAS_USE_NODES:
        mat.use_nodes = True


def get_principled(mat: bpy.types.Material | None):
    """Return the Principled BSDF driving the material output, or None.

    Prefers the node actually connected to the Material Output surface so that
    renamed or duplicated nodes still resolve correctly.
    """
    if not uses_nodes(mat):
        return None
    nodes = mat.node_tree.nodes
    output = next(
        (n for n in nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output),
        None,
    )
    if output is not None:
        surface = output.inputs.get("Surface")
        if surface is not None and surface.is_linked:
            linked = surface.links[0].from_node
            if linked.type == "BSDF_PRINCIPLED":
                return linked
    return next((n for n in nodes if n.type == "BSDF_PRINCIPLED"), None)


def get_socket(node, key: str):
    """Return the input socket for a logical value name, or None."""
    if node is None:
        return None
    for name in SOCKET_ALIASES.get(key, (key,)):
        socket = node.inputs.get(name)
        if socket is not None:
            return socket
    return None


def set_value(node, key: str, value) -> bool:
    """Write a logical value into the Principled BSDF.

    Returns True when the socket exists and was written.  Colour sockets accept
    3- or 4-component values; scalar sockets accept numbers.  Linked sockets are
    left alone so texture maps are never silently overridden.
    """
    socket = get_socket(node, key)
    if socket is None or socket.is_linked:
        return False
    try:
        if hasattr(socket.default_value, "__len__"):
            size = len(socket.default_value)
            values = tuple(value) if hasattr(value, "__len__") else (value,) * 3
            if len(values) < size:
                values = values + (1.0,) * (size - len(values))
            socket.default_value = values[:size]
        else:
            socket.default_value = float(value)
    except (TypeError, ValueError, AttributeError):
        return False
    return True


def get_value(node, key: str, default=None):
    """Read a logical value from the Principled BSDF, or *default*."""
    socket = get_socket(node, key)
    if socket is None:
        return default
    try:
        raw = socket.default_value
    except AttributeError:
        return default
    if hasattr(raw, "__len__"):
        return tuple(raw)
    return raw


def is_managed(mat: bpy.types.Material | None) -> bool:
    """Return True when PCB Studio created or adopted this material."""
    return bool(mat is not None and mat.get(MANAGED_KEY, False))


def mark_managed(mat: bpy.types.Material, preset_key: str = "") -> None:
    """Tag a material as PCB Studio managed so edits are non-destructive."""
    mat[MANAGED_KEY] = True
    if preset_key:
        mat[PRESET_KEY] = preset_key


def is_simple_principled(mat: bpy.types.Material | None) -> bool:
    """Return True for a plain Principled + Output graph plus PCB Studio nodes.

    Used to decide whether writing values into an unmanaged material is safe.
    A user's hand-built shader network returns False.
    """
    if mat is None or not uses_nodes(mat):
        return False
    if get_principled(mat) is None:
        return False
    allowed = {"BSDF_PRINCIPLED", "OUTPUT_MATERIAL"}
    for node in mat.node_tree.nodes:
        if node.type in allowed or node.name.startswith("PCBSTUDIO_"):
            continue
        return False
    return True


def count_material_objects(mat: bpy.types.Material | None) -> int:
    """Count PCB objects using *mat* in any material slot.

    Only walks the PCB collection, and is called from operators or an expanded
    panel section rather than on every redraw.
    """
    if mat is None:
        return 0
    collection = bpy.data.collections.get(COLLECTION_NAME)
    if collection is None:
        return 0
    return sum(
        1
        for obj in collection.all_objects
        if obj.type == "MESH"
        and any(slot.material is mat for slot in obj.material_slots)
    )


def objects_using_material(mat: bpy.types.Material | None) -> list:
    """Every object in the file with *mat* in a slot.

    Unlike :func:`count_material_objects` this walks all of ``bpy.data.objects``
    rather than only the PCB collection, because an OBJ import shares one
    datablock per ``usemtl`` name and those objects are not always moved into
    ``PCB_MODEL``.  Only called from operators and update callbacks, never on
    every panel redraw.
    """
    if mat is None:
        return []
    return [
        obj
        for obj in bpy.data.objects
        if any(slot.material is mat for slot in obj.material_slots)
    ]


def is_shared(mat: bpy.types.Material | None) -> bool:
    """Return True when more than one datablock references *mat*.

    O(1), so unlike :func:`is_shared_beyond` this is safe to call from a panel
    ``draw()``.  It counts mesh datablocks rather than objects, which matches
    how this add-on assigns materials (``link='DATA'``, never linked
    duplicates).
    """
    if mat is None:
        return False
    return mat.users - int(mat.use_fake_user) > 1


def is_shared_beyond(mat: bpy.types.Material | None, objects=()) -> bool:
    """Return True when an object outside *objects* also uses *mat*.

    This is the test for whether editing *mat* in place would silently change
    something the user did not select.
    """
    if mat is None or not mat.users:
        return False
    keep = {obj.name for obj in objects}
    return any(obj.name not in keep for obj in objects_using_material(mat))
