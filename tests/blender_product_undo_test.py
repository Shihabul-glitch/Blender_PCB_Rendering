"""Undo/redo with Blender's real undo stack; also validates live RNA callbacks."""
import sys
from pathlib import Path
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pcb_studio


def run():
    pcb_studio.register()
    scene = bpy.context.scene
    collection = bpy.data.collections.new("PCB_MODEL")
    scene.collection.children.link(collection)
    for name, scale, z in (("Board", (2, 1, 0.01), 0), ("IC", (0.1, 0.1, 0.1), 0.1)):
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.object
        obj.name, obj.scale, obj.location.z = name, scale, z
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        collection.objects.link(obj)
    scene.pcb_studio_product.board = bpy.data.objects["Board"]
    bpy.context.view_layer.update()
    bpy.ops.ed.undo_push(message="Initial PCB")
    assert bpy.ops.pcbstudio.product_orientation(view="RIGHT") == {"FINISHED"}
    bpy.ops.ed.undo_push(message="Rotate PCB")
    assert bpy.ops.ed.undo() == {"FINISHED"}
    assert "PCB_MODEL_ROOT" not in bpy.data.objects
    assert bpy.ops.ed.redo() == {"FINISHED"}
    assert "PCB_MODEL_ROOT" in bpy.data.objects
    # Orientation changes round-trip through the undo stack without losing the root.
    rotated = bpy.data.objects["PCB_MODEL_ROOT"].rotation_euler.copy()
    assert bpy.ops.pcbstudio.product_orientation(view="RESET") == {"FINISHED"}
    bpy.ops.ed.undo_push(message="Reset PCB orientation")
    assert bpy.ops.ed.undo() == {"FINISHED"}
    assert tuple(bpy.data.objects["PCB_MODEL_ROOT"].rotation_euler) == tuple(rotated)
    assert bpy.ops.ed.redo() == {"FINISHED"}
    print("PRODUCT_UNDO_REDO_TEST_PASSED")
    pcb_studio.unregister()


if __name__ == "__main__":
    run()
