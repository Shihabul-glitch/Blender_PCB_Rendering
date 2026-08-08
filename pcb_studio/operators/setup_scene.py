"""Operator that prepares the complete studio scene for PCB rendering."""

from __future__ import annotations

import traceback

import bpy
from mathutils import Vector

from ..constants import (
    COLLECTION_NAME,
    EXTENSION_NAME,
    EXTENSION_VERSION,
    OPERATOR_ID_PREPARE_SCENE,
    PROP_SCENE_ATTR,
    ROOT_EMPTY_NAME,
)
from ..utils.geometry import BoundingBox, compute_pcb_bounds
from ..utils.camera import setup_camera
from ..utils.lighting import setup_lights
from ..utils.render import (
    configure_render_settings,
    setup_background_plane,
    setup_world_background,
)


def _get_pcb_collection() -> bpy.types.Collection | None:
    """Return PCB_MODEL or None."""
    return bpy.data.collections.get(COLLECTION_NAME)


def _get_usable_mesh_objects(
    collection: bpy.types.Collection,
) -> list[bpy.types.Object]:
    """Return MESH objects in *collection* that are visible and have geometry."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    result: list[bpy.types.Object] = []
    for obj in collection.all_objects:
        if obj.type != "MESH":
            continue
        evaluated = obj.evaluated_get(depsgraph)
        if evaluated.bound_box:
            result.append(obj)
    return result


def _center_pcb_assembly(
    pcb_collection: bpy.types.Collection,
) -> BoundingBox:
    """Parent top-level PCB objects to a root Empty and move it to origin.

    Returns the bounding box *after* centering.
    """
    # Identify top-level objects: in PCB_MODEL, parent NOT in PCB_MODEL.
    pcb_objects = set(pcb_collection.all_objects)
    top_level: list[bpy.types.Object] = []
    for obj in pcb_objects:
        if obj.type != "MESH":
            continue
        if obj.parent is None or obj.parent not in pcb_objects:
            top_level.append(obj)

    # Get or create the root Empty.
    root = bpy.data.objects.get(ROOT_EMPTY_NAME)
    if root is None:
        root = bpy.data.objects.new(ROOT_EMPTY_NAME, None)
        root.empty_display_type = "PLAIN_AXES"
        pcb_collection.objects.link(root)
        # Parent top-level objects only on first creation.
        for obj in top_level:
            # Preserve world transform when parenting.
            obj.parent = root

    # Calculate current bounds (before moving).
    bounds = compute_pcb_bounds(pcb_collection)
    if not bounds.is_valid:
        return bounds

    # Move root so the PCB center is at world origin.
    root.location = -bounds.center

    # Recalculate bounds after centering.
    return compute_pcb_bounds(pcb_collection)


class PCBSTUDIO_OT_prepare_scene(bpy.types.Operator):
    """Prepare the studio scene: center PCB, add camera, lights, and background."""

    bl_idname: str = OPERATOR_ID_PREPARE_SCENE
    bl_label: str = "Prepare Scene"
    bl_description: str = (
        "Center the PCB, create camera, lights, and background for rendering"
    )
    bl_options: set[str] = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context | None) -> set[str]:
        """Run the complete scene preparation pipeline."""
        try:
            return self._execute_impl(context)
        except Exception:
            traceback.print_exc()
            self.report(
                {"ERROR"},
                "An unexpected error occurred during scene setup. "
                "Check the system console for details.",
            )
            return {"CANCELLED"}

    def _execute_impl(self, context: bpy.types.Context | None) -> set[str]:
        """Core scene setup logic."""
        props = getattr(context.scene, PROP_SCENE_ATTR, None)
        if props is None:
            self.report({"ERROR"}, "Extension state not available.")
            return {"CANCELLED"}

        # --- Validate PCB_MODEL ---
        pcb_coll = _get_pcb_collection()
        if pcb_coll is None:
            self.report({"ERROR"}, "PCB_MODEL collection not found. Import a PCB first.")
            props.scene_setup_status = "No PCB imported."
            props.scene_setup_ready = False
            return {"CANCELLED"}

        mesh_objects = _get_usable_mesh_objects(pcb_coll)
        if not mesh_objects:
            self.report({"ERROR"}, "PCB_MODEL contains no usable geometry.")
            props.scene_setup_status = "No PCB geometry found."
            props.scene_setup_ready = False
            return {"CANCELLED"}

        # --- Center the PCB assembly ---
        bounds = _center_pcb_assembly(pcb_coll)
        if not bounds.is_valid:
            self.report({"ERROR"}, "Could not calculate PCB bounding box.")
            props.scene_setup_status = "Invalid PCB bounds."
            props.scene_setup_ready = False
            return {"CANCELLED"}

        # --- Camera ---
        try:
            cam_msg = setup_camera(bounds)
            props.camera_ready = True
        except Exception:
            traceback.print_exc()
            cam_msg = "Camera setup failed."
            props.camera_ready = False

        # --- Lights ---
        try:
            light_msg = setup_lights(bounds)
        except Exception:
            traceback.print_exc()
            light_msg = "Lighting setup failed."

        # --- Background plane ---
        try:
            bg_msg = setup_background_plane(bounds)
        except Exception:
            traceback.print_exc()
            bg_msg = "Background plane setup failed."

        # --- World background ---
        try:
            world_msg = setup_world_background()
        except Exception:
            traceback.print_exc()
            world_msg = "World background setup failed."

        # --- Render settings ---
        try:
            render_msg = configure_render_settings()
        except Exception:
            traceback.print_exc()
            render_msg = "Render settings configuration failed."

        # --- Update state ---
        props.scene_setup_ready = True
        props.scene_setup_status = (
            f"Scene prepared. {cam_msg} {light_msg}"
        )

        summary = (
            f"{EXTENSION_NAME} scene prepared successfully. "
            f"Camera: {cam_msg} | Lights: {light_msg} | "
            f"Background: {bg_msg} | World: {world_msg} | "
            f"Render: {render_msg}"
        )
        self.report({"INFO"}, "PCB Studio scene prepared successfully.")
        print(f"{EXTENSION_NAME} v{EXTENSION_VERSION}: {summary}")

        return {"FINISHED"}
