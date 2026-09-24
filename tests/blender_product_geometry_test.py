"""Nested/scaled hierarchy, board overrides, auto-frame, and protected data."""
import sys
import math
from pathlib import Path
import bpy
from mathutils import Matrix, Vector
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from blender_product_smoke_test import cube, close, reject
import pcb_studio
from pcb_studio.utils import product as u
from bpy_extras.object_utils import world_to_camera_view


def run():
    pcb_studio.register()
    ctx, scene = bpy.context, bpy.context.scene
    coll = bpy.data.collections.new("PCB_MODEL")
    scene.collection.children.link(coll)
    hierarchy = bpy.data.objects.new("Imported Assembly", None)
    coll.objects.link(hierarchy)
    hierarchy.location = (0.1, 0.2, 0.3)
    hierarchy.rotation_euler = (0.2, 0.3, 0.4)
    hierarchy.scale = (1.2, 0.8, 1.1)
    board = cube(coll, "Substrate", (0, 0, 0), (0.2, 0.12, 0.002))
    board.parent = hierarchy
    chip = cube(coll, "IC", (0.02, 0.03, 0.01), (0.01, 0.01, 0.005))
    chip.parent = hierarchy
    chip.matrix_parent_inverse = Matrix.Translation((0.005, 0.003, 0.001))
    ctx.view_layer.update()
    p = scene.pcb_studio_product
    assert u.board_object(ctx) == board  # dominant thin-area fallback
    before = {o: o.matrix_world.copy() for o in (board, hierarchy, chip)}
    u.ensure_root(ctx)
    u.center_pivot(ctx)
    assert all(close(o.matrix_world, m) for o, m in before.items())
    p.orientation = (0, math.pi / 2, 0)
    ctx.view_layer.update()
    assert chip.parent == hierarchy
    assert not close(chip.matrix_world, before[chip])
    hierarchy.pcb_studio_product.exclude_rotation = True
    reject(lambda: u.ensure_root(ctx))
    hierarchy.pcb_studio_product.exclude_rotation = False
    # Auto-frame moves only backward along view axis, and only when necessary.
    p.orientation = (0, 0, 0)
    ctx.view_layer.update()
    camera = scene.camera
    center = u.compute_world_bounds([board, chip]).center
    camera.location = center + Vector((0, 0, 0.03))
    camera.rotation_euler = (0, 0, 0)
    camera.data.clip_start, camera.data.clip_end = 0.0001, 100
    ctx.view_layer.update()
    rotation = camera.rotation_euler.copy()
    original = camera.location.copy()
    u.auto_frame(ctx)
    assert camera.location.z > original.z
    assert abs(camera.location.x - original.x) < 1e-7
    assert abs(camera.location.y - original.y) < 1e-7
    assert tuple(camera.rotation_euler) == tuple(rotation)
    for obj in (board, chip):
        for corner in obj.bound_box:
            point = world_to_camera_view(scene, camera, obj.matrix_world @ Vector(corner))
            assert 0.029 <= point.x <= 0.971 and 0.029 <= point.y <= 0.971
    framed = camera.matrix_world.copy()
    u.auto_frame(ctx)
    assert close(camera.matrix_world, framed)
    pcb_studio.unregister()
    print("PRODUCT_GEOMETRY_TEST_PASSED")


if __name__ == "__main__":
    run()

# A board exported standing in XZ faces Y, and every board-relative camera
# preset has to follow that instead of assuming a flat board facing +Z.
from mathutils import Vector as _V
from pcb_studio.utils.geometry import BoundingBox as _BB, board_direction, board_normal_axis


def _bounds(dimensions):
    half = _V(dimensions) / 2.0
    return _BB(min=-half, max=half, center=_V((0.0, 0.0, 0.0)), dimensions=_V(dimensions),
               max_dimension=max(dimensions), is_valid=True)


flat = _bounds((20.0, 16.0, 1.0))
standing = _bounds((20.0, 1.0, 16.0))
edge_on = _bounds((1.0, 20.0, 16.0))
assert tuple(board_normal_axis(flat)) == (0.0, 0.0, 1.0)
assert tuple(board_normal_axis(standing)) == (0.0, -1.0, 0.0)
assert tuple(board_normal_axis(edge_on)) == (-1.0, 0.0, 0.0)
# An ambiguous, near-cubic volume falls back to the flat-board convention.
assert tuple(board_normal_axis(_bounds((10.0, 10.5, 11.0)))) == (0.0, 0.0, 1.0)

front = _V((0.0, 0.0, 1.0))
assert (board_direction(flat, front) - _V((0.0, 0.0, 1.0))).length < 1e-6
assert (board_direction(standing, front) - _V((0.0, -1.0, 0.0))).length < 1e-6
assert (board_direction(edge_on, front) - _V((-1.0, 0.0, 0.0))).length < 1e-6
# Bottom is the opposite face, not the world underside.
assert (board_direction(standing, -front) - _V((0.0, 1.0, 0.0))).length < 1e-6
# Isometric stays above the board rather than dropping underneath it.
iso = board_direction(standing, _V((1.0, -1.0, 1.0)).normalized())
assert iso.z > 0.5 and iso.y < -0.5, tuple(iso)
# The frame stays orthonormal and right-handed for every orientation.
for case in (flat, standing, edge_on):
    from pcb_studio.utils.geometry import board_basis
    right, up, normal = board_basis(case)
    assert abs(right.dot(up)) < 1e-6 and abs(right.dot(normal)) < 1e-6 and abs(up.dot(normal)) < 1e-6
    assert (right.cross(up) - normal).length < 1e-6, tuple(case.dimensions)

# A declared orientation replaces the guess.  These run unregistered, so the
# frame has to be handed in explicitly rather than read off the scene.
from pcb_studio.utils.board_orientation import (
    is_perpendicular, nearest_world_axis, perpendicular_front,
)
from pcb_studio.utils.geometry import required_camera_distance

assert nearest_world_axis(_V((0.0, 0.0, 1.0))) == "POS_Z"
assert nearest_world_axis(_V((-0.2, 0.9, 0.3))) == "POS_Y"
assert nearest_world_axis(_V((0.0, 0.0, 0.0))) == "POS_Z"  # degenerate view
assert is_perpendicular("POS_Z", "NEG_Y") and not is_perpendicular("POS_Z", "NEG_Z")
# A front edge along the top face is replaced, never stored as given.
assert is_perpendicular("POS_Y", perpendicular_front("POS_Y", "NEG_Y"))
assert perpendicular_front("POS_Z", "NEG_Y") == "NEG_Y"

# Framing projects the corners onto the camera's own axes, so an edge-on view of
# a thin board needs far less distance than a face-on one at the same lens.
_square = _bounds((20.0, 16.0, 1.0))
_face_on = required_camera_distance(
    _square, _V((0.0, 0.0, 1.0)), _V((1.0, 0.0, 0.0)), _V((0.0, 1.0, 0.0)), 0.6, 0.4)
_edge_on = required_camera_distance(
    _square, _V((0.0, -1.0, 0.0)), _V((1.0, 0.0, 0.0)), _V((0.0, 0.0, 1.0)), 0.6, 0.4)
assert _edge_on < _face_on, (_edge_on, _face_on)
assert _face_on > 0.0
print("BOARD_AXIS_CHECKS_PASSED")
