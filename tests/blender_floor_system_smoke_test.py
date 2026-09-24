"""Headless acceptance checks for the product-photography floor system."""

from __future__ import annotations

import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pcb_studio
from pcb_studio.constants import COLLECTION_NAME, PROP_SCENE_ATTR, REFLECTION_PLANE_NAME
from pcb_studio.utils.floor import INFINITE_NAME, INFINITE_MATERIAL_NAME, update_floor_system
from pcb_studio.utils.geometry import compute_pcb_bounds
from pcb_studio.utils.studio import refresh_studio_values


def _box(name, size=(2.0, 1.0, 0.4), location=(0.0, 0.0, 1.0)):
    x, y, z = (value * 0.5 for value in size)
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(
        [(-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z),
         (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)],
        [], [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
             (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)],
    )
    obj = bpy.data.objects.new(name, mesh)
    bpy.data.collections[COLLECTION_NAME].objects.link(obj)
    obj.location = location
    return obj


def run():
    pcb_studio.register()
    try:
        product_collection = bpy.data.collections.new(COLLECTION_NAME)
        bpy.context.scene.collection.children.link(product_collection)
        product = _box("Product")
        user_plane = _box("Plane", (5.0, 5.0, 0.02), (8.0, 8.0, 0.0))
        product_collection.objects.unlink(user_plane)
        bpy.context.scene.collection.objects.link(user_plane)
        user_floor_material = bpy.data.materials.new("UserFloorMaterial")
        user_plane.data.materials.append(user_floor_material)
        props = getattr(bpy.context.scene, PROP_SCENE_ATTR)
        props.scene_setup_ready = True

        props.floor_mode = "NONE"
        assert bpy.data.objects.get(REFLECTION_PLANE_NAME) is None
        assert user_plane.hide_render is False

        props.floor_mode = "STANDARD"
        floor = bpy.data.objects[REFLECTION_PLANE_NAME]
        assert floor.get("pcbstudio_floor") is True
        assert floor.get("pcbstudio_floor_role") == "plane"
        assert floor.data.materials[0].name == INFINITE_MATERIAL_NAME
        assert user_plane.hide_render is False
        vertices_before = [tuple(vertex.co) for vertex in floor.data.vertices]
        props.floor_color = (0.2, 0.3, 0.4, 1.0)
        assert [tuple(vertex.co) for vertex in floor.data.vertices] == vertices_before
        props.floor_brightness = 2.0
        shader = floor.data.materials[0].node_tree.nodes["PCB Studio Floor Shader"]
        assert abs(shader.inputs["Base Color"].default_value[0] - 0.4) < 1e-6
        props.floor_offset_x = 0.7
        props.floor_height = -0.1
        location_before = floor.location.copy()
        refresh_studio_values(bpy.context.scene, props)
        assert (floor.location - location_before).length < 1e-6

        for _ in range(3):
            assert bpy.ops.pcbstudio.floor_action(action="FIT") == {"FINISHED"}
        assert len([obj for obj in bpy.data.objects if obj.get("pcbstudio_floor_role") == "plane"]) == 1

        original_x, original_y, original_z = product.location
        assert bpy.ops.pcbstudio.floor_action(action="GROUND") == {"FINISHED"}
        assert product.location.x == original_x and product.location.y == original_y
        assert bpy.ops.pcbstudio.floor_action(action="RESET_GROUND") == {"FINISHED"}
        assert abs(product.location.z - original_z) < 1e-6
        props.auto_ground_product = True
        props.floor_gap = 0.12
        from pcb_studio.utils.geometry import compute_pcb_bounds
        assert abs(compute_pcb_bounds(product_collection).min.z - floor.matrix_world.translation.z - 0.12) < 1e-6
        props.auto_ground_product = False
        assert bpy.ops.pcbstudio.floor_action(action="RESET_GROUND") == {"FINISHED"}
        props.floor_studio_preset = "MATTE_PRODUCT"
        assert bpy.ops.pcbstudio.floor_action(action="STUDIO_PRESET") == {"FINISHED"}
        assert abs(props.floor_reflection_strength - 0.08) < 1e-6

        # The floor follows the product instead of keeping the Z it was first
        # built at. Caching that height forever meant re-running Prepare Scene,
        # which re-centres the assembly, left the floor slicing through the board.
        def floor_gap():
            bpy.context.view_layer.update()
            bounds = compute_pcb_bounds(bpy.data.collections[COLLECTION_NAME])
            return bounds.min.z - bpy.data.objects[REFLECTION_PLANE_NAME].location.z, bounds

        gap, bounds = floor_gap()
        assert gap >= 0.0, "floor started inside the product"
        for delta in (40.0, -65.0):
            for obj in list(bpy.data.collections[COLLECTION_NAME].all_objects):
                if not obj.get("pcbstudio_managed", False):
                    obj.location.z += delta
            bpy.context.view_layer.update()
            update_floor_system(bpy.context.scene, props)
            gap, bounds = floor_gap()
            assert gap >= 0.0, f"floor cut through the product after moving {delta}"
            assert gap <= bounds.max_dimension, f"floor stranded after moving {delta}"
        # floor_height is a fraction of product size, so it survives a no-op run.
        props.floor_height = -0.05
        update_floor_system(bpy.context.scene, props)
        moved, bounds = floor_gap()
        update_floor_system(bpy.context.scene, props)
        repeated, _ = floor_gap()
        assert abs(moved - repeated) < 1e-6, "floor drifted on an idempotent update"
        assert abs(moved - bounds.max_dimension * 0.05) < 1e-4
        props.floor_height = -0.005
        update_floor_system(bpy.context.scene, props)

        props.floor_mode = "INFINITE"
        infinite = bpy.data.objects[INFINITE_NAME]
        assert len(infinite.data.polygons) > 8
        assert all(polygon.use_smooth for polygon in infinite.data.polygons)
        assert len(infinite.data.vertices) == 2 * (len(infinite.data.polygons) + 1)
        # Analytic normals keep the flat floor and wall planar through the curve.
        assert infinite.data.has_custom_normals
        props.floor_rotation = 0.5
        assert abs(infinite.rotation_euler.z - 0.5) < 1e-6
        assert floor.hide_render

        props.floor_mode = "SHADOW_CATCHER"
        assert not floor.hide_render and infinite.hide_render
        assert bpy.context.scene.render.film_transparent
        assert floor.is_shadow_catcher
        props.shadow_catcher_transparent = False
        assert not bpy.context.scene.render.film_transparent
        props.shadow_catcher_transparent = True

        props.floor_mode = "CUSTOM"
        assert not bpy.context.scene.render.film_transparent
        user_plane.visible_camera = False
        props.floor_custom_object = user_plane
        assert user_plane.hide_render is False
        assert user_plane.visible_camera
        props.floor_custom_object = None
        assert user_plane.data.materials[0] == user_floor_material
        assert not user_plane.visible_camera
        props.floor_custom_object = user_plane
        props.floor_mode = "NONE"
        assert user_plane.hide_render is False
        assert user_plane.data.materials[0] == user_floor_material
        assert floor.hide_render and infinite.hide_render

        props.floor_mode = "SHADOW_CATCHER"
        assert bpy.ops.pcbstudio.reset_professional_studio() == {"FINISHED"}
        assert not bpy.context.scene.render.film_transparent
        assert bpy.data.objects.get(INFINITE_NAME) is None
        assert bpy.data.objects.get("Plane") == user_plane
        assert user_plane.data.materials[0] == user_floor_material

        print("FLOOR_SYSTEM_SMOKE_TEST_PASSED")
    finally:
        pcb_studio.unregister()


if __name__ == "__main__":
    run()
