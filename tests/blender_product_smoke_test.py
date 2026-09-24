"""Run in Blender 4.5+ with --background --factory-startup --python-exit-code 1."""
import json
import math
import sys
import tempfile
import time
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pcb_studio
from pcb_studio.constants import COLLECTION_NAME, RENDER_SETUP_COLLECTION, ROOT_EMPTY_NAME
from pcb_studio.utils import product as u
from pcb_studio.utils.animation import setup_animation, reset_animation


def close(a, b, epsilon=2e-5):
    return all(abs(a[r][c] - b[r][c]) < epsilon for r in range(4) for c in range(4))


def cube(collection, name, location, size):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([(x * size[0], y * size[1], z * size[2])
                     for x in (-0.5, 0.5) for y in (-0.5, 0.5) for z in (-0.5, 0.5)], [], [])
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.location = location
    return obj


def reject(fn):
    try:
        fn()
    except ValueError:
        return
    raise AssertionError("Expected a safe preflight rejection")


def run():
    pcb_studio.register()
    ctx, scene = bpy.context, bpy.context.scene
    p = scene.pcb_studio_product
    collection = bpy.data.collections.new(COLLECTION_NAME)
    scene.collection.children.link(collection)
    studio = bpy.data.collections.new(RENDER_SETUP_COLLECTION)
    scene.collection.children.link(studio)
    board = cube(collection, "PCB Board", (0.2, -0.1, 0.05), (0.2, 0.12, 0.002))
    board.rotation_euler = (0.1, 0.2, 0.0)
    p.board = board
    pieces = [cube(collection, f"U{i:03d}", (0.13 + i * 0.015, -0.1, 0.065), (0.01, 0.008, 0.005)) for i in range(12)]
    pieces[0].rotation_mode = "QUATERNION"
    pieces[0].rotation_quaternion = (0.98, 0.1, 0.05, 0.02)
    pieces[1].rotation_mode = "ZYX"
    pieces[1].rotation_euler = (0.2, -0.1, 0.3)
    pieces[2].rotation_mode = "AXIS_ANGLE"
    pieces[2].rotation_axis_angle = (0.1, 0, 1, 0)
    pieces[3].delta_location = (0.002, 0.001, 0.003)
    pieces[3].delta_rotation_euler = (0.1, 0.2, 0.3)
    pieces[3].scale = (1.2, 0.8, 1.1)
    # Nested component mesh travels once with its selected assembly.
    child = cube(collection, "U000_pin", (0.001, 0.002, 0), (0.001, 0.001, 0.001))
    child.parent = pieces[0]
    floor = cube(studio, "PCB_BACKGROUND", (0, 0, -0.1), (2, 2, 0.01))
    ctx.view_layer.update()
    stationary = {o: o.matrix_world.copy() for o in studio.all_objects}
    stationary.update({o: o.matrix_world.copy() for o in scene.objects if o.type in {"CAMERA", "LIGHT"}})
    before = {o: o.matrix_world.copy() for o in collection.all_objects}
    root = u.ensure_root(ctx)
    assert all(close(o.matrix_world, m) for o, m in before.items()), "parenting jump"
    u.center_pivot(ctx)
    assert all(close(o.matrix_world, m) for o, m in before.items()), "pivot jump"
    assert u.ensure_root(ctx) == root
    assert len([o for o in scene.objects if o.name.startswith(ROOT_EMPTY_NAME)]) == 1
    for view in ("FRONT", "RIGHT", "LEFT", "BACK", "TOP", "BOTTOM", "RESET"):
        assert bpy.ops.pcbstudio.product_orientation(view=view) == {"FINISHED"}
        ctx.view_layer.update()
        assert all(close(o.matrix_world, m) for o, m in stationary.items()), view
    assert all(close(o.matrix_world, m) for o, m in before.items())

    # Moving the product translates every product object by the same world
    # delta, leaves the studio/camera/lights stationary, and reverts exactly.
    for action in ("LEFT", "RIGHT", "FORWARD", "BACK", "UP", "DOWN"):
        assert bpy.ops.pcbstudio.product_move(action=action) == {"FINISHED"}, action
        ctx.view_layer.update()
        assert all(close(o.matrix_world, m) for o, m in stationary.items()), action
    assert all(close(o.matrix_world, m) for o, m in before.items()), "six moves did not cancel out"
    assert tuple(round(v, 6) for v in p.position) == (0.0, 0.0, 0.0)
    root_before = root.matrix_world.translation.copy()
    inverses = {o: o.matrix_parent_inverse.copy() for o in root.children}
    assert bpy.ops.pcbstudio.product_move(action="UP") == {"FINISHED"}
    ctx.view_layer.update()
    step = p.position.z
    assert step > 0.0
    # The delta lands on the root, not on the children's parent inverses.
    assert abs((root.matrix_world.translation.z - root_before.z) - step) < 2e-5
    assert all(o.matrix_parent_inverse == m for o, m in inverses.items()), "parent inverse touched"
    assert all(
        abs((o.matrix_world.translation.z - m.translation.z) - step) < 2e-5
        for o, m in before.items()
    ), "product objects did not all move together"
    p.position = (0.0, 0.0, step)
    ctx.view_layer.update()
    assert abs((root.matrix_world.translation.z - root_before.z) - step) < 2e-5,         "re-typing the same position drifted"
    assert bpy.ops.pcbstudio.product_move(action="RESET") == {"FINISHED"}
    ctx.view_layer.update()
    assert tuple(round(v, 6) for v in p.position) == (0.0, 0.0, 0.0)
    assert all(close(o.matrix_world, m) for o, m in before.items()), "reset position"
    assert all(close(o.matrix_world, m) for o, m in stationary.items()), "reset position studio"

    p.orientation = (0.0, math.pi / 2, 0.0)
    ctx.view_layer.update()
    assembled = {o: o.matrix_world.copy() for o in pieces + [child, board]}
    floor.parent = root
    ctx.view_layer.update()
    reject(lambda: u.ensure_root(ctx))
    floor.parent = None
    floor.matrix_world = stationary[floor]
    scene.frame_set(1)
    # Legacy camera/PCB animation stays blocked while a product orientation is applied.
    assert setup_animation("PCB_TURNTABLE", 3, 30, 360, "CLOCKWISE", 0, "CONSTANT").startswith("Clear product")
    assert reset_animation().startswith("Reset Product Orientation")
    ctx.view_layer.update()
    assert all(close(o.matrix_world, m) for o, m in assembled.items())
    assert all(close(o.matrix_world, m) for o, m in stationary.items())
    # User animation on the product root blocks further orientation changes.
    root.keyframe_insert(data_path="location", frame=1)
    user_action = root.animation_data.action
    reject(lambda: u.orient_product(ctx, (0.0, 0.0, 0.0)))
    assert root.animation_data.action == user_action
    root.animation_data.action = None
    # Save/reopen: the product root and its orientation survive a reload.
    with tempfile.TemporaryDirectory() as directory:
        path = str(Path(directory) / "product.blend")
        bpy.ops.wm.save_as_mainfile(filepath=path)
        bpy.ops.wm.open_mainfile(filepath=path)
        ctx = bpy.context
        assert ROOT_EMPTY_NAME in bpy.data.objects
        assert bpy.ops.pcbstudio.product_orientation(view="RESET") == {"FINISHED"}
    pcb_studio.unregister()
    pcb_studio.register()
    pcb_studio.unregister()
    print("PRODUCT_PRESENTATION_SMOKE_TEST_PASSED")


if __name__ == "__main__":
    run()
