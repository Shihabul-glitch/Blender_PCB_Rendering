"""Collection helpers for PCB Studio."""

from __future__ import annotations

import bpy

from ..constants import COLLECTION_NAME


def get_or_create_pcb_collection() -> bpy.types.Collection:
    """Return the PCB_MODEL collection, creating it if necessary.

    The collection is linked to the scene's master collection but not
    to any view layer directly — standard Blender child collection behaviour.
    """
    coll = bpy.data.collections.get(COLLECTION_NAME)
    if coll is None:
        coll = bpy.data.collections.new(COLLECTION_NAME)
        bpy.context.scene.collection.children.link(coll)
    return coll


def collection_has_objects(coll: bpy.types.Collection) -> bool:
    """Return True if the collection contains any objects (recursively)."""
    return len(coll.all_objects) > 0


def move_objects_to_collection(
    objects: set[bpy.types.Object],
    target: bpy.types.Collection,
) -> None:
    """Link each object into *target*, removing it from other collections only
    if doing so won't orphan it.

    Strategy:
    1. Link the object to *target* if not already linked.
    2. For every other collection the object belongs to, unlink it
       provided at least one collection link remains (prevents orphaning).
    """
    for obj in objects:
        # Link to target first (safe — objects can belong to many collections).
        if obj.name not in target.objects:
            target.objects.link(obj)

        # Unlink from every other collection as long as a safety link remains.
        other_collections = [
            c for c in obj.users_collection if c != target
        ]
        for coll in other_collections:
            if len(obj.users_collection) > 1:
                coll.objects.unlink(obj)