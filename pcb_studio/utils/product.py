"""Product-only presentation integrated with PCB_MODEL and PCB_MODEL_ROOT.

Orientation and pivot centering act on PCB_MODEL_ROOT alone; the studio, camera
and lights stay stationary.
"""
import bpy
from mathutils import Euler, Quaternion, Vector

from .. import constants
from .geometry import compute_world_bounds

# Legacy-data marker: written by the removed product turntable. Nothing creates
# it any more, but guards still refuse to act on objects that carry it, so old
# blend files cannot be silently corrupted. Do not delete as "unused".
SNAPSHOT = "pcbstudio_product_snapshot"
BASE = "pcbstudio_product_base"
AXES = {"X": Vector((1, 0, 0)), "Y": Vector((0, 1, 0)), "Z": Vector((0, 0, 1))}


def settings(context):
    return context.scene.pcb_studio_product


def product_objects(context):
    collection = bpy.data.collections.get(constants.COLLECTION_NAME)
    if collection is None or collection not in context.scene.collection.children_recursive:
        raise ValueError("No PCB product was detected. Import a PCB first.")
    objects = set(collection.all_objects) & set(context.scene.objects)
    if not any(o.type == "MESH" for o in objects):
        raise ValueError("No PCB product geometry was detected.")
    return collection, objects


def protected(obj):
    studio = bpy.data.collections.get(constants.RENDER_SETUP_COLLECTION)
    reserved = {value for key, value in vars(constants).items()
                if key.endswith("_NAME") and isinstance(value, str)
                and key != "ROOT_EMPTY_NAME"}
    return (obj.get("pcbstudio_environment_role") or obj.get("pcbstudio_role") == "light_card"
            or obj.type in {"CAMERA", "LIGHT", "SPEAKER"} or obj.name in reserved
            or obj.name.startswith((constants.CUSTOM_LIGHT_PREFIX, constants.LIGHT_CARD_PREFIX))
            or (studio is not None and obj.name in studio.all_objects)
            or obj.pcb_studio_product.exclude_rotation)


def board_object(context, objects=None):
    if objects is None:
        _, objects = product_objects(context)
    candidates = [o for o in objects if o.type == "MESH" and not protected(o)]
    explicit = settings(context).board
    if explicit:
        if explicit not in candidates:
            raise ValueError("PCB Board must be a mesh in PCB_MODEL, outside the studio.")
        return explicit
    marked = [o for o in candidates if o.pcb_studio_product.role == "BOARD"]
    named = [o for o in candidates if "board" in o.name.lower() or o.name.lower() in {"pcb", "fr4"}]
    pool = marked or named
    if len(pool) == 1:
        return pool[0]
    # Conservative geometry fallback: one broad, thin object dominates in area.
    def area(o):
        d = sorted(abs(v) for v in o.dimensions)
        return d[1] * d[2] if d[0] < d[1] * 0.2 else 0
    ranked = sorted(candidates, key=area, reverse=True)
    if ranked and area(ranked[0]) > 0 and (len(ranked) == 1 or area(ranked[0]) > 2 * area(ranked[1])):
        return ranked[0]
    raise ValueError("Board detection is ambiguous. Choose PCB Board in Product Orientation.")


def ensure_root(context):
    collection, objects = product_objects(context)
    if any(bpy.data.objects.get(name) for name in (constants.CAMERA_ORBIT_ROOT_NAME, constants.CAMERA_FLYOVER_ROOT_NAME)):
        raise ValueError("Reset the existing camera orbit/flyover before creating a stationary-studio product presentation.")
    root = bpy.data.objects.get(constants.ROOT_EMPTY_NAME)
    if root and (root not in objects or root.type != "EMPTY"):
        raise ValueError("PCB_MODEL_ROOT is used outside this product; rename that object first.")
    allowed = {o for o in objects if o != root and not protected(o)}
    if not any(o.type == "MESH" for o in allowed):
        raise ValueError("No rotatable PCB geometry detected. Check product exclusions and collections.")
    tops = set()
    for obj in allowed:
        if obj.library or not obj.is_editable or obj.constraints or obj.parent_type != "OBJECT":
            raise ValueError(f"{obj.name} is linked, constrained, or bone/vertex parented. Resolve it before product presentation.")
        top = obj
        while top.parent in allowed:
            top = top.parent
        if top.parent not in (None, root):
            raise ValueError(f"{top.name} has an external/protected parent. Resolve its hierarchy first.")
        tops.add(top)
    # Validate *all* descendants before any mutation; never rotate a stray studio child.
    for obj in tuple(tops) + ((root,) if root else ()):
        for child in obj.children_recursive:
            if child not in allowed:
                raise ValueError(f"Detach {child.name} from the product hierarchy before rotating; it is protected or outside PCB_MODEL.")
    if root and (root.parent or root.constraints):
        raise ValueError("Product Root has a parent or constraints. Resolve these before product orientation.")
    if root is None:
        root = bpy.data.objects.new(constants.ROOT_EMPTY_NAME, None)
        collection.objects.link(root)
        root.empty_display_type = "PLAIN_AXES"
        try:
            pivot_objects = [board_object(context, objects)]
        except ValueError:
            pivot_objects = [o for o in allowed if o.type == "MESH"]
        root.location = compute_world_bounds(pivot_objects).center
        context.view_layer.update()
    inverse = root.matrix_world.inverted()
    for obj in tops:
        if obj.parent == root:
            continue
        # Keep original local channels, including any existing keys/deltas.
        obj.parent = root
        obj.matrix_parent_inverse = inverse
    context.view_layer.update()
    if BASE not in root:
        root[BASE] = list(root.rotation_euler.to_quaternion() if root.rotation_mode not in {"QUATERNION", "AXIS_ANGLE"}
                          else root.matrix_basis.to_quaternion())
    return root


def center_pivot(context):
    _, objects = product_objects(context)
    board = board_object(context, objects)
    if any(SNAPSHOT in o for o in objects):
        raise ValueError(f"Clear the legacy '{SNAPSHOT}' custom property on the product objects "
                         f"before centering the pivot.")
    root = ensure_root(context)
    if root.animation_data and (root.animation_data.action or root.animation_data.nla_tracks or root.animation_data.drivers):
        raise ValueError("Clear Product Root animation before centering the pivot.")
    center = compute_world_bounds([board]).center
    old = root.matrix_world.copy()
    new = old.copy()
    new.translation = center
    compensation = new.inverted() @ old
    for child in root.children:
        child.matrix_parent_inverse = compensation @ child.matrix_parent_inverse
    root.matrix_world = new
    context.view_layer.update()


def orientation_basis(context):
    # FRONT_FLAT in composition.py looks along +Z; preserve that convention.
    # Axis override maps non-standard board exports into that reference frame.
    return AXES["Z"].rotation_difference(AXES[settings(context).normal_axis])


def orient_product(context, angles):
    existing = bpy.data.objects.get(constants.ROOT_EMPTY_NAME)
    if existing:
        validate_static(existing)
    root = ensure_root(context)
    mapping = orientation_basis(context)
    q = Quaternion(root[BASE]) @ mapping @ Euler(angles, "XYZ").to_quaternion() @ mapping.inverted()
    root.rotation_mode = "XYZ"
    root.rotation_euler = q.to_euler("XYZ", root.rotation_euler)
    settings(context)["last_orientation"] = angles
    context.view_layer.update()
    if settings(context).auto_frame:
        auto_frame(context)


#: Share of the product's own size moved per click, by step mode.
MOVE_STEP_FACTORS = {"FINE": 0.015, "NORMAL": 0.05, "COARSE": 0.12}

#: World-axis unit vectors for each move action.  The render camera looks along
#: +Y at the backdrop, so Forward pushes the product away from the camera.
MOVE_DIRECTIONS = {
    "LEFT": Vector((-1.0, 0.0, 0.0)),
    "RIGHT": Vector((1.0, 0.0, 0.0)),
    "FORWARD": Vector((0.0, 1.0, 0.0)),
    "BACK": Vector((0.0, -1.0, 0.0)),
    "UP": Vector((0.0, 0.0, 1.0)),
    "DOWN": Vector((0.0, 0.0, -1.0)),
}

#: Written by floor.ground_product as its restore point.  Moving the product
#: has to shift it too, or Reset Ground would undo the user's move as well.
GROUND_ORIGINAL = "pcbstudio_ground_original_location"


def move_step(context):
    """Distance one move click travels, scaled to the product's own size."""
    _, objects = product_objects(context)
    meshes = [o for o in objects if o.type == "MESH"]
    base = compute_world_bounds(meshes).max_dimension if meshes else 1.0
    factor = MOVE_STEP_FACTORS.get(settings(context).move_step_mode, 0.05)
    return max(base * factor, 0.0001)


def move_product(context, delta):
    """Translate PCB_MODEL_ROOT by *delta* in world space.

    Deliberately relative, not absolute: the root's position is also written by
    Ground Product and Center Product Pivot, so there is no stable "original"
    location to offset from.  Applying deltas composes correctly with both.

    Only the root's translation changes.  ``matrix_parent_inverse`` is left
    alone — unlike :func:`center_pivot`, which compensates the children so the
    geometry stays put, a move is supposed to take the geometry with it.  The
    studio, camera and lights are never touched.
    """
    delta = Vector(delta)
    existing = bpy.data.objects.get(constants.ROOT_EMPTY_NAME)
    if existing:
        validate_static(existing)
    root = ensure_root(context)
    matrix = root.matrix_world.copy()
    matrix.translation = matrix.translation + delta
    root.matrix_world = matrix
    if GROUND_ORIGINAL in root:
        root[GROUND_ORIGINAL] = list(Vector(root[GROUND_ORIGINAL]) + delta)
    context.view_layer.update()
    if settings(context).auto_frame:
        auto_frame(context)


def auto_frame(context):
    """Move backward along the camera's existing view axis only when clipped.

    Permit the existing PCB Studio target constraint if rotation stays fixed.
    Other rigs and orthographic framing need explicit camera controls.
    """
    from bpy_extras.object_utils import world_to_camera_view
    camera = context.scene.camera
    if camera is None:
        settings(context).status = "Orientation applied; no camera to auto-frame."
        return
    _, objects = product_objects(context)
    corners = [o.matrix_world @ Vector(c) for o in objects if o.type == "MESH" and not protected(o) for c in o.bound_box]
    def fits():
        points = [world_to_camera_view(context.scene, camera, c) for c in corners]
        return all(0.03 <= p.x <= 0.97 and 0.03 <= p.y <= 0.97 and p.z > camera.data.clip_start for p in points)
    if fits():
        return
    unsupported_constraints = any(c.name != constants.CAMERA_TARGET_CONSTRAINT_NAME
                                  or c.type not in {"TRACK_TO", "DAMPED_TRACK"} for c in camera.constraints)
    if camera.data.type != "PERSP" or camera.parent or unsupported_constraints or camera.animation_data:
        settings(context).status = "Orientation applied; auto-frame needs an unrigged perspective camera. Use camera framing controls."
        return
    original = camera.matrix_world.copy()
    axis = original.to_quaternion() @ AXES["Z"]
    step = max(compute_world_bounds([o for o in objects if o.type == "MESH"]).max_dimension * 0.1, 0.001)
    high = step
    for _ in range(30):
        matrix = original.copy()
        matrix.translation += axis * high
        camera.matrix_world = matrix
        context.view_layer.update()
        if fits():
            break
        high *= 2
    else:
        camera.matrix_world = original
        settings(context).status = "Orientation applied; camera could not be framed by distance alone."
        return
    low = 0.0
    for _ in range(20):
        middle = (low + high) / 2
        matrix.translation = original.translation + axis * middle
        camera.matrix_world = matrix
        context.view_layer.update()
        if fits():
            high = middle
        else:
            low = middle
    matrix.translation = original.translation + axis * high
    camera.matrix_world = matrix
    context.view_layer.update()
    rotation_changed = original.to_quaternion().rotation_difference(camera.matrix_world.to_quaternion()).angle > 1e-5
    clipped = any((camera.matrix_world.inverted() @ c).z < -camera.data.clip_end for c in corners)
    if rotation_changed or clipped:
        camera.matrix_world = original
        context.view_layer.update()
        settings(context).status = "Orientation applied; auto-frame would alter camera rotation or exceed clipping. Use camera framing controls."


def validate_static(obj):
    if obj.library or not obj.is_editable:
        raise ValueError(f"{obj.name} is linked/read-only. Make the product local first.")
    if obj.constraints or obj.parent_type != "OBJECT":
        raise ValueError(f"{obj.name} has constraints or bone/vertex parenting; bake or resolve these first.")
    if abs(obj.matrix_world.to_3x3().determinant()) < 1e-15:
        raise ValueError(f"{obj.name} has a zero/singular scale; correct it before animation.")
    if SNAPSHOT in obj:
        raise ValueError(f"{obj.name} carries product-turntable data from an older PCB Studio. "
                         f"Delete its '{SNAPSHOT}' custom property and the generated action first.")
    ad = obj.animation_data
    if ad and (ad.drivers or ad.nla_tracks or ad.action):
        raise ValueError(f"{obj.name} already has animation. Preserve or bake that animation first.")
