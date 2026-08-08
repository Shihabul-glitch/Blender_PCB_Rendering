"""Camera presets, zoom-to-fit, DOF, and reflection plane utilities."""

from __future__ import annotations

from dataclasses import dataclass
from math import atan, tan

import bpy
from mathutils import Vector

from ..constants import (
    CAMERA_NAME,
    CAMERA_TARGET_NAME,
    COLLECTION_NAME,
    DOF_TARGET_NAME,
    REFLECTION_MATERIAL_NAME,
    REFLECTION_PLANE_NAME,
    RENDER_SETUP_COLLECTION,
)
from .geometry import BoundingBox, compute_pcb_bounds


@dataclass
class CameraPreset:
    """Definition of a single camera preset."""

    display_name: str
    direction: Vector
    focal_length: float
    margin: float = 1.15


PRESETS: dict[str, CameraPreset] = {
    "TOP": CameraPreset("Top", Vector((0.0, 0.0, 1.0)), 50.0),
    "ISOMETRIC": CameraPreset(
        "Isometric", Vector((1.0, -1.0, 1.0)).normalized(), 50.0,
    ),
    "45_DEGREE": CameraPreset(
        "45 Degree", Vector((1.0, -0.4, 1.0)).normalized(), 50.0,
    ),
    "BOTTOM": CameraPreset("Bottom", Vector((0.0, 0.0, -1.0)), 50.0),
    "CONNECTOR_CLOSEUP": CameraPreset(
        "Connector Closeup",
        Vector((0.7, -0.7, 1.0)).normalized(),
        85.0,
        margin=1.4,
    ),
    "MACRO": CameraPreset(
        "Macro",
        Vector((0.5, -0.5, 1.0)).normalized(),
        100.0,
        margin=1.2,
    ),
}


def _get_setup_collection() -> bpy.types.Collection:
    coll = bpy.data.collections.get(RENDER_SETUP_COLLECTION)
    if coll is None:
        coll = bpy.data.collections.new(RENDER_SETUP_COLLECTION)
        bpy.context.scene.collection.children.link(coll)
    return coll


def _get_managed_camera() -> bpy.types.Object | None:
    return bpy.data.objects.get(CAMERA_NAME)


def _get_or_create_target(name: str) -> bpy.types.Object:
    target = bpy.data.objects.get(name)
    if target is None:
        target = bpy.data.objects.new(name, None)
        target.empty_display_type = "PLAIN_AXES"
        _get_setup_collection().objects.link(target)
    return target


def _remove_track_constraints(camera: bpy.types.Object) -> None:
    for c in list(camera.constraints):
        if c.type == "DAMPED_TRACK":
            camera.constraints.remove(c)


def _aim_camera_at(camera: bpy.types.Object, target: bpy.types.Object) -> None:
    _remove_track_constraints(camera)
    track = camera.constraints.new(type="DAMPED_TRACK")
    track.target = target
    track.track_axis = "TRACK_NEGATIVE_Z"


def _compute_camera_distance(
    dimensions: Vector,
    sensor_width: float,
    sensor_height: float,
    focal_length: float,
    margin: float = 1.15,
) -> float:
    hfov = 2.0 * atan(sensor_width / (2.0 * focal_length))
    vfov = 2.0 * atan(sensor_height / (2.0 * focal_length))
    tan_h = tan(hfov / 2.0)
    tan_v = tan(vfov / 2.0)
    dist_h = (dimensions.x * margin / 2.0) / tan_h if tan_h else 1e6
    dist_v = (dimensions.y * margin / 2.0) / tan_v if tan_v else 1e6
    return max(dist_h, dist_v)


def _get_pcb_bounds() -> BoundingBox | None:
    pcb_coll = bpy.data.collections.get(COLLECTION_NAME)
    if pcb_coll is None:
        return None
    bounds = compute_pcb_bounds(pcb_coll)
    return bounds if bounds.is_valid else None


def _compute_object_world_bounds(obj: bpy.types.Object) -> BoundingBox | None:
    if obj.type != "MESH":
        return None
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    world_mat = obj.matrix_world
    min_c = Vector((float("inf"), float("inf"), float("inf")))
    max_c = Vector((float("-inf"), float("-inf"), float("-inf")))
    for corner in evaluated.bound_box:
        wc = world_mat @ Vector(corner)
        min_c.x = min(min_c.x, wc.x)
        min_c.y = min(min_c.y, wc.y)
        min_c.z = min(min_c.z, wc.z)
        max_c.x = max(max_c.x, wc.x)
        max_c.y = max(max_c.y, wc.y)
        max_c.z = max(max_c.z, wc.z)
    dims = max_c - min_c
    center = (min_c + max_c) / 2.0
    max_dim = max(dims.x, dims.y, dims.z)
    if max_dim <= 0.0:
        return None
    return BoundingBox(
        min=min_c, max=max_c, center=center,
        dimensions=dims, max_dimension=max_dim, is_valid=True,
    )


def get_single_selected_pcb_mesh(
    context: bpy.types.Context,
) -> tuple[bpy.types.Object | None, str]:
    managed_names = {
        "PCB_BACKGROUND", "PCB_REFLECTION_PLANE",
        "PCB_RENDER_CAMERA", "PCB_CAMERA_TARGET", "PCB_DOF_TARGET",
        "PCB_KEY_LIGHT", "PCB_FILL_LIGHT", "PCB_RIM_LIGHT",
        "PCB_RIM_LIGHT_2", "PCB_TOP_LIGHT", "PCB_MODEL_ROOT",
    }
    pcb_coll = bpy.data.collections.get(COLLECTION_NAME)
    if pcb_coll is None:
        return None, "PCB_MODEL collection not found."
    pcb_names = {o.name for o in pcb_coll.all_objects}
    selected = [
        o for o in context.selected_objects
        if o.type == "MESH"
        and o.name in pcb_names
        and o.name not in managed_names
    ]
    if len(selected) == 0:
        return None, "Select one PCB object first."
    if len(selected) > 1:
        return None, "Select exactly one PCB object."
    return selected[0], ""


def apply_camera_preset(
    preset_key: str,
    focal_length: float | None = None,
    context: bpy.types.Context | None = None,
) -> str:
    preset = PRESETS.get(preset_key)
    if preset is None:
        return f"Unknown preset: {preset_key}"
    camera = _get_managed_camera()
    if camera is None:
        return "Managed camera not found. Run Prepare Scene first."
    cam_data = camera.data
    lens = focal_length if focal_length is not None else preset.focal_length
    cam_data.lens = lens
    target = _get_or_create_target(CAMERA_TARGET_NAME)

    if preset_key in {"CONNECTOR_CLOSEUP", "MACRO"}:
        if context is None:
            return "Context required for object-based presets."
        sel_obj, err = get_single_selected_pcb_mesh(context)
        if sel_obj is None:
            return err
        obj_bounds = _compute_object_world_bounds(sel_obj)
        if obj_bounds is None:
            return "Selected object has invalid bounds."
        target.location = obj_bounds.center
        frame_bounds = obj_bounds
        frame_margin = preset.margin
    else:
        pcb_bounds = _get_pcb_bounds()
        if pcb_bounds is None:
            return "No PCB geometry found."
        target.location = pcb_bounds.center
        frame_bounds = pcb_bounds
        frame_margin = preset.margin

    sensor_w = cam_data.sensor_width
    sensor_h = cam_data.sensor_height
    distance = _compute_camera_distance(
        frame_bounds.dimensions, sensor_w, sensor_h, lens, frame_margin,
    )
    camera.location = target.location + preset.direction * distance
    _aim_camera_at(camera, target)
    bpy.context.scene.camera = camera
    return f"Camera preset applied: {preset.display_name}"


def zoom_to_fit(margin: float = 1.15) -> str:
    camera = _get_managed_camera()
    if camera is None:
        return "Managed camera not found."
    target = bpy.data.objects.get(CAMERA_TARGET_NAME)
    if target is None:
        return "Camera target not found."
    bounds = _get_pcb_bounds()
    if bounds is None:
        return "No PCB geometry found."
    direction = (camera.location - target.location).normalized()
    if direction.length < 1e-6:
        direction = Vector((1.0, -1.0, 1.0)).normalized()
    cam_data = camera.data
    distance = _compute_camera_distance(
        bounds.dimensions,
        cam_data.sensor_width,
        cam_data.sensor_height,
        cam_data.lens,
        margin,
    )
    camera.location = target.location + direction * distance
    return f"Zoomed to fit PCB (distance {distance:.1f})."


def apply_camera_settings(
    focal_length: float,
    use_dof: bool,
    focus_mode: str,
    fstop: float,
    context: bpy.types.Context | None = None,
) -> str:
    camera = _get_managed_camera()
    if camera is None:
        return "Managed camera not found."
    cam_data = camera.data
    cam_data.lens = max(20.0, min(200.0, focal_length))
    cam_data.dof.use_dof = use_dof
    if use_dof:
        cam_data.dof.aperture_fstop = max(1.4, min(22.0, fstop))
        dof_target = _get_or_create_target(DOF_TARGET_NAME)
        if focus_mode == "SELECTED_OBJECT" and context is not None:
            sel_obj, err = get_single_selected_pcb_mesh(context)
            if sel_obj is not None:
                obj_bounds = _compute_object_world_bounds(sel_obj)
                if obj_bounds is not None:
                    dof_target.location = obj_bounds.center
                else:
                    dof_target.location = Vector((0, 0, 0))
            else:
                bounds = _get_pcb_bounds()
                dof_target.location = bounds.center if bounds else Vector((0, 0, 0))
        else:
            bounds = _get_pcb_bounds()
            dof_target.location = bounds.center if bounds else Vector((0, 0, 0))
        cam_data.dof.focus_object = dof_target
    else:
        cam_data.dof.focus_object = None
    zoom_msg = zoom_to_fit()
    return f"Camera settings applied. {zoom_msg}"


def apply_reflection_plane(preset_key: str) -> str:
    setup_coll = _get_setup_collection()
    mat = bpy.data.materials.get(REFLECTION_MATERIAL_NAME)
    if mat is None:
        mat = bpy.data.materials.new(REFLECTION_MATERIAL_NAME)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.clear()
        principled = nodes.new(type="ShaderNodeBsdfPrincipled")
        output = nodes.new(type="ShaderNodeOutputMaterial")
        mat.node_tree.links.new(
            principled.outputs["BSDF"], output.inputs["Surface"],
        )
    plane = bpy.data.objects.get(REFLECTION_PLANE_NAME)
    if plane is None:
        mesh = bpy.data.meshes.new(REFLECTION_PLANE_NAME)
        plane = bpy.data.objects.new(REFLECTION_PLANE_NAME, mesh)
        setup_coll.objects.link(plane)
    if preset_key == "OFF":
        plane.hide_render = True
        plane.hide_viewport = True
        return "Reflection surface: Off"
    plane.hide_render = False
    plane.hide_viewport = False
    bounds = _get_pcb_bounds()
    if bounds is not None:
        max_dim = bounds.max_dimension
        plane_size = max_dim * 3.0
        gap = max_dim * 0.005
        half = plane_size / 2.0
        mesh = plane.data
        mesh.clear_geometry()
        verts = [
            Vector((-half, -half, 0.0)),
            Vector((half, -half, 0.0)),
            Vector((-half, half, 0.0)),
            Vector((half, half, 0.0)),
        ]
        mesh.from_pydata(verts, [], [(0, 1, 3, 2)])
        mesh.update()
        plane.location = Vector((
            bounds.center.x, bounds.center.y, bounds.min.z - gap,
        ))
    principled = mat.node_tree.nodes.get("Principled BSDF")
    if principled is None:
        principled = mat.node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    if preset_key == "SUBTLE":
        principled.inputs["Base Color"].default_value = (0.08, 0.08, 0.09, 1.0)
        principled.inputs["Roughness"].default_value = 0.35
        principled.inputs["Metallic"].default_value = 0.1
    elif preset_key == "GLOSSY":
        principled.inputs["Base Color"].default_value = (0.06, 0.06, 0.07, 1.0)
        principled.inputs["Roughness"].default_value = 0.1
        principled.inputs["Metallic"].default_value = 0.3
    if plane.data.materials:
        plane.data.materials[0] = mat
    else:
        plane.data.materials.append(mat)
    return f"Reflection surface: {preset_key}"