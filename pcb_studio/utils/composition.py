"""Camera presets, zoom-to-fit, DOF, and reflection plane utilities."""

from __future__ import annotations

from dataclasses import dataclass

import bpy
from mathutils import Matrix, Quaternion, Vector

from ..constants import (
    CAMERA_NAME,
    CAMERA_TARGET_NAME,
    COLLECTION_NAME,
    DOF_TARGET_NAME,
    REFLECTION_MATERIAL_NAME,
    REFLECTION_PLANE_NAME,
    RENDER_SETUP_COLLECTION,
)
from .geometry import (
    BoundingBox,
    board_basis,
    board_direction,
    camera_field_of_view,
    compute_pcb_bounds,
    required_camera_distance,
)
from .camera import ensure_managed_target_constraint


@dataclass
class CameraPreset:
    """Definition of a single camera preset."""

    display_name: str
    direction: Vector
    focal_length: float
    margin: float = 1.15
    #: True when the direction is authored in the board's own frame (canonical
    #: +Z is the board face).  False for studio shots that are about the floor
    #: rather than the board, so they stay in world axes whatever the export.
    board_relative: bool = True


PRESETS: dict[str, CameraPreset] = {
    "TOP": CameraPreset("Top", Vector((0.0, 0.0, 1.0)), 75.0, margin=1.10),
    "FRONT_FLAT": CameraPreset("Front Flat", Vector((0.0, -1.0, 0.0)), 75.0, margin=1.10),
    "BACK": CameraPreset("Back", Vector((0.0, 1.0, 0.0)), 75.0, margin=1.10),
    "LEFT": CameraPreset("Left", Vector((-1.0, 0.0, 0.0)), 75.0, margin=1.10),
    "RIGHT": CameraPreset("Right", Vector((1.0, 0.0, 0.0)), 75.0, margin=1.10),
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
    "HERO_ISOMETRIC": CameraPreset(
        "Hero Isometric", Vector((1.0, -1.15, 0.82)).normalized(), 80.0, margin=1.18,
        board_relative=False,
    ),
    "HERO_LOW": CameraPreset(
        "Hero Low", Vector((1.0, -1.25, 0.38)).normalized(), 85.0, margin=1.22,
        board_relative=False,
    ),
    "PRODUCT_STRAIGHT": CameraPreset(
        "Product Straight", Vector((0.0, -1.0, 0.28)).normalized(), 75.0, margin=1.18,
        board_relative=False,
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


def _aim_camera_at(
    camera: bpy.types.Object,
    target: bpy.types.Object,
    up_hint: Vector | None = None,
) -> None:
    """Aim with PCB Studio's constraint while preserving user constraints.

    *up_hint* is the world direction that should point up in frame.  Without it
    Blender picks an up axis from world Y, which rolls an elevation view of a
    board that was not exported flat.  DAMPED_TRACK rotates minimally about the
    aim axis, so the roll set here survives the constraint.
    """
    props = getattr(bpy.context.scene, "pcb_studio_import", None)
    enabled = props is None or props.camera_control_mode == "AUTO_TARGET"
    direction = target.matrix_world.translation - camera.matrix_world.translation
    if direction.length > 1e-9:
        rotation = _look_rotation(direction.normalized(), up_hint)
        camera.rotation_euler = rotation.to_euler()
    ensure_managed_target_constraint(camera, target, enabled=enabled)


def _look_rotation(forward: Vector, up_hint: Vector | None) -> Quaternion:
    """Rotation that looks along *forward* with *up_hint* upright in frame."""
    if up_hint is None:
        return forward.to_track_quat("-Z", "Y")
    up = up_hint - forward * up_hint.dot(forward)
    if up.length < 1e-6:
        return forward.to_track_quat("-Z", "Y")
    up.normalize()
    # Camera axes: -Z looks forward, so +Z points back toward the viewer.
    back = -forward
    right = up.cross(back)
    if right.length < 1e-6:
        return forward.to_track_quat("-Z", "Y")
    right.normalize()
    return Matrix((right, back.cross(right), back)).transposed().to_quaternion()


def _frame_up_hint(
    direction: Vector,
    bounds: BoundingBox,
    board_relative: bool,
) -> Vector | None:
    """Which world direction should be up in frame for this view direction.

    The board's face normal is the natural up for an elevation or angled shot.
    Looking straight down at the face it is degenerate, so the board's own
    in-plane up takes over -- that is what keeps the front edge at the bottom of
    a Top view.

    A studio shot is composed against the floor rather than the board, so world
    up is what has to be vertical in its frame.
    """
    if not board_relative:
        return Vector((0.0, 0.0, 1.0))
    _right, up, normal = board_basis(bounds)
    return up if abs(direction.dot(normal)) > 0.9 else normal


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
        "PCB_RIM_LIGHT_2", "PCB_TOP_LIGHT", "PCB_FRONT_LIGHT_LEFT", "PCB_FRONT_LIGHT_RIGHT",
        "PCB_MODEL_ROOT",
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


def describe_detected_board_axis() -> str:
    """One line naming the axis Automatic mode has guessed, for the panel.

    Shown so the user can see the guess before deciding whether to override it.
    """
    bounds = _get_pcb_bounds()
    if bounds is None:
        return "No PCB geometry to detect from."
    _right, up, normal = board_basis(bounds)
    return f"Detected top face {_axis_label(normal)}, front edge {_axis_label(-up)}."


def _axis_label(direction: Vector) -> str:
    from .board_orientation import AXIS_VECTORS

    key = max(AXIS_VECTORS, key=lambda name: direction.dot(AXIS_VECTORS[name]))
    return key.replace("POS_", "+").replace("NEG_", "-")


def apply_camera_preset(
    preset_key: str,
    focal_length: float | None = None,
    context: bpy.types.Context | None = None,
) -> str:
    from .camera_controls import camera_animation_block_reason

    blocked = camera_animation_block_reason()
    if blocked:
        return blocked
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

    direction = preset.direction
    if preset.board_relative:
        direction = board_direction(frame_bounds, direction)
    up_hint = _frame_up_hint(direction, frame_bounds, preset.board_relative)
    rotation = _look_rotation(-direction, up_hint)
    right = rotation @ Vector((1.0, 0.0, 0.0))
    up = rotation @ Vector((0.0, 1.0, 0.0))
    angle_x, angle_y = camera_field_of_view(cam_data, bpy.context.scene)
    distance = required_camera_distance(
        frame_bounds, direction, right, up, angle_x, angle_y, frame_margin,
    )
    camera.location = target.location + direction * distance
    # _aim_camera_at derives the roll from the camera's world matrix, which is
    # still the previous shot's until the move is evaluated.
    bpy.context.view_layer.update()
    _aim_camera_at(camera, target, up_hint)
    bpy.context.scene.camera = camera
    # Settle the constraint before anything reads the camera's world matrix,
    # exactly as setup_camera does after placing it.
    bpy.context.view_layer.update()
    props = getattr(bpy.context.scene, "pcb_studio_import", None)
    if props is not None:
        bpy.context.scene["pcbstudio_camera_batch_update"] = True
        try:
            props.camera_focal_length = lens
            props.camera_roll = 0.0
        finally:
            bpy.context.scene["pcbstudio_camera_batch_update"] = False
    from .camera_controls import sync_camera_properties

    sync_camera_properties(bpy.context.scene)
    return f"Camera preset applied: {preset.display_name}"


def zoom_to_fit(margin: float = 1.15) -> str:
    from .camera_controls import fit_camera_to_pcb

    return fit_camera_to_pcb(bpy.context.scene)


def apply_camera_settings(
    focal_length: float,
    use_dof: bool,
    focus_mode: str,
    fstop: float,
    context: bpy.types.Context | None = None,
) -> str:
    from .camera_controls import camera_animation_block_reason

    blocked = camera_animation_block_reason()
    if blocked:
        return blocked
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
    elif preset_key == "SATIN":
        principled.inputs["Base Color"].default_value = (0.025, 0.028, 0.035, 1.0)
        principled.inputs["Roughness"].default_value = 0.32
        principled.inputs["Metallic"].default_value = 0.05
    elif preset_key == "MIRROR":
        principled.inputs["Base Color"].default_value = (0.025, 0.025, 0.028, 1.0)
        principled.inputs["Roughness"].default_value = 0.025
        principled.inputs["Metallic"].default_value = 0.92
    elif preset_key == "DARK_GLASS":
        principled.inputs["Base Color"].default_value = (0.008, 0.012, 0.02, 1.0)
        principled.inputs["Roughness"].default_value = 0.12
        principled.inputs["Metallic"].default_value = 0.35
        if "Coat Weight" in principled.inputs:
            principled.inputs["Coat Weight"].default_value = 0.35
    elif preset_key == "CUSTOM":
        # Detailed custom values are applied by utils.studio after geometry is
        # updated.  Keep a safe neutral material for direct legacy calls.
        principled.inputs["Base Color"].default_value = (0.04, 0.04, 0.05, 1.0)
        principled.inputs["Roughness"].default_value = 0.3
        principled.inputs["Metallic"].default_value = 0.05
    if plane.data.materials:
        plane.data.materials[0] = mat
    else:
        plane.data.materials.append(mat)
    return f"Reflection surface: {preset_key}"
