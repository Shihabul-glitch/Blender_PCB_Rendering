"""Prepare Scene options, preservation, framing, and repeatability checks."""

import sys
from pathlib import Path
from types import SimpleNamespace

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pcb_studio
from pcb_studio.constants import CAMERA_NAME, COLLECTION_NAME, ROOT_EMPTY_NAME
from pcb_studio.operators import setup_scene
from pcb_studio.utils.geometry import compute_pcb_bounds


def matrix_close(left, right):
    return all(abs(left[r][c] - right[r][c]) < 1e-5 for r in range(4) for c in range(4))


def prepare(**options):
    assert bpy.ops.pcbstudio.prepare_scene(**options) == {"FINISHED"}
    assert bpy.context.scene.pcb_studio_import.scene_setup_ready


KEEP = dict(center_pcb=False, prepare_camera=False, prepare_studio=False,
            render_setup="KEEP", output_size="KEEP")


def run():
    pcb_studio.register()
    try:
        scene = bpy.context.scene
        props = scene.pcb_studio_import
        collection = bpy.data.collections.new(COLLECTION_NAME)
        scene.collection.children.link(collection)
        parent = bpy.data.objects.new("ImportedHierarchy", None)
        collection.objects.link(parent)
        parent.location = (7.0, -4.0, 2.0)
        parent.rotation_euler = (0.15, 0.2, 0.4)
        parent.scale = (1.4, 0.8, 1.2)
        mesh = bpy.data.meshes.new("OptionsBoardMesh")
        mesh.from_pydata(
            [(-2, -1, -0.1), (2, -1, -0.1), (2, 1, -0.1), (-2, 1, -0.1),
             (-2, -1, 0.1), (2, -1, 0.1), (2, 1, 0.1), (-2, 1, 0.1)],
            [], [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4),
                 (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)],
        )
        board = bpy.data.objects.new("OptionsBoard", mesh)
        collection.objects.link(board)
        board.parent = parent
        board.location = (0.5, 0.2, 0.3)
        props.pcb_imported = True
        bpy.context.view_layer.update()

        # Opening/cancelling a dialog must not prepare or modify scene data.
        before_objects = set(bpy.data.objects)
        before_matrix = board.matrix_world.copy()
        original_camera = scene.camera
        original_world = scene.world
        operator_class = setup_scene.PCBSTUDIO_OT_prepare_scene
        operator = SimpleNamespace()
        operator._set_dialog_defaults = lambda context: operator_class._set_dialog_defaults(operator, context)
        rna = bpy.ops.pcbstudio.prepare_scene.get_rna_type()
        assert "prepare_camera" in rna.properties and "output_size" in rna.properties
        fake_context = SimpleNamespace(
            scene=scene,
            window_manager=SimpleNamespace(invoke_props_dialog=lambda op, width: {"RUNNING_MODAL"}),
        )
        assert operator_class.invoke(operator, fake_context, None) == {"RUNNING_MODAL"}
        assert operator.center_pcb and operator.prepare_camera and operator.prepare_studio
        assert set(bpy.data.objects) == before_objects
        assert matrix_close(board.matrix_world, before_matrix)
        assert not props.scene_setup_ready

        # Optional grouping preserves nested imported transforms and user world/camera.
        prepare(**KEEP)
        assert matrix_close(board.matrix_world, before_matrix)
        assert board.parent == parent
        assert parent.parent == bpy.data.objects[ROOT_EMPTY_NAME]
        assert scene.camera == original_camera and scene.world == original_world
        assert bpy.data.objects.get(CAMERA_NAME) is None

        # Re-centering an offset hierarchy must not drift on subsequent preparation.
        prepare(**{**KEEP, "center_pcb": True})
        centered = board.matrix_world.copy()
        assert compute_pcb_bounds(collection).center.length < 1e-5
        for _ in range(3):
            prepare(**{**KEEP, "center_pcb": True})
            assert matrix_close(board.matrix_world, centered)
            assert compute_pcb_bounds(collection).center.length < 1e-5

        # Native camera fitting must honor output aspect and perspective view.
        for output in ("HD_LANDSCAPE", "INSTAGRAM_SQUARE", "STORY"):
            prepare(center_pcb=False, initial_camera_preset="HERO_ISOMETRIC",
                    initial_studio_preset="CLEAN_COMMERCIAL", output_size=output)
            assert props.still_format == output
            camera = bpy.data.objects[CAMERA_NAME]
            assert abs(camera.data.lens - 80.0) < 1e-5
            bounds = compute_pcb_bounds(collection)
            for x in (bounds.min.x, bounds.max.x):
                for y in (bounds.min.y, bounds.max.y):
                    for z in (bounds.min.z, bounds.max.z):
                        point = world_to_camera_view(scene, camera, Vector((x, y, z)))
                        assert 0.0 < point.x < 1.0 and 0.0 < point.y < 1.0 and point.z > 0, point

        # Reopening defaults to preserving the prepared scene and is read-only.
        camera_matrix = camera.matrix_world.copy()
        world_tree = scene.world.node_tree
        world_nodes = tuple(node.as_pointer() for node in world_tree.nodes)
        lights = {obj.name: (obj.matrix_world.copy(), obj.data.energy)
                  for obj in scene.objects if obj.type == "LIGHT"}
        operator._set_dialog_defaults(bpy.context)
        assert not operator.center_pcb and not operator.prepare_camera and not operator.prepare_studio
        assert operator.render_setup == "KEEP" and operator.output_size == "KEEP"
        prepare(**KEEP)
        assert matrix_close(camera.matrix_world, camera_matrix)
        assert tuple(node.as_pointer() for node in world_tree.nodes) == world_nodes
        for name, (matrix, energy) in lights.items():
            assert matrix_close(bpy.data.objects[name].matrix_world, matrix)
            assert bpy.data.objects[name].data.energy == energy

        # Engine-only changes retain output size and do not touch device preferences.
        preferences = bpy.context.preferences.addons["cycles"].preferences
        backend = preferences.compute_device_type
        device = scene.cycles.device
        scene.render.resolution_percentage = 67
        dimensions = (scene.render.resolution_x, scene.render.resolution_y, 67)
        prepare(**{**KEEP, "render_setup": "CYCLES"})
        assert scene.render.engine == "CYCLES" and scene.cycles.use_denoising
        assert (scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage) == dimensions
        assert preferences.compute_device_type == backend and scene.cycles.device == device
        prepare(**{**KEEP, "output_size": "CUSTOM", "output_width": 1500, "output_height": 1000})
        assert (scene.render.resolution_x, scene.render.resolution_y) == (1500, 1000)
        assert props.still_format == "CUSTOM" and props.still_custom_width == 1500
        assert matrix_close(camera.matrix_world, camera_matrix)

        # Animation refusal happens before any scene preparation mutations.
        props.animation_type = "PCB_TURNTABLE"
        assert bpy.ops.pcbstudio.setup_turntable() == {"FINISHED"}
        root = bpy.data.objects[ROOT_EMPTY_NAME]
        root_matrix = root.matrix_world.copy()
        try:
            result = bpy.ops.pcbstudio.prepare_scene()
        except RuntimeError as exc:
            assert "Reset Animation" in str(exc)
        else:
            assert result == {"CANCELLED"}
        assert matrix_close(root.matrix_world, root_matrix)
        assert bpy.ops.pcbstudio.reset_turntable() == {"FINISHED"}

        # A failed optional stage must be reported as incomplete, not success.
        original_setup = setup_scene.apply_professional_preset
        try:
            def fail(*args):
                raise RuntimeError("simulated studio setup failure")
            setup_scene.apply_professional_preset = fail
            assert bpy.ops.pcbstudio.prepare_scene(**{**KEEP, "prepare_studio": True}) == {"FINISHED"}
            assert not props.scene_setup_ready
            assert "Preparation incomplete" in props.scene_setup_status
        finally:
            setup_scene.apply_professional_preset = original_setup
        print("PREPARE_SCENE_OPTIONS_SMOKE_TEST_PASSED")
    finally:
        pcb_studio.unregister()


if __name__ == "__main__":
    run()
