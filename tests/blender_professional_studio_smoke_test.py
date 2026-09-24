"""Headless Blender acceptance coverage for PCB Studio Milestone 10."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import bpy
from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pcb_studio
from pcb_studio.constants import (
    BACKGROUND_LIGHT_2_NAME,
    BACKGROUND_MATERIAL_NAME,
    BACKGROUND_LIGHT_NAME,
    BACKGROUND_NAME,
    BACKGROUND_RECEIVER_COLLECTION,
    CAMERA_NAME,
    COLLECTION_NAME,
    CUSTOM_LIGHT_PREFIX,
    FILL_LIGHT_NAME,
    KEY_LIGHT_NAME,
    LIGHT_TARGET_NAME,
    LIGHT_CARD_PREFIX,
    MICRO_BEVEL_MODIFIER_NAME,
    PCB_SURFACE_MATERIAL_NAME,
    PCB_UV_LAYER_NAME,
    PEDESTAL_NAME,
    PROP_SCENE_ATTR,
    REFLECTION_PLANE_NAME,
    RIM_LIGHT_2_NAME,
    RIM_LIGHT_NAME,
    ROOT_EMPTY_NAME,
    TOP_LIGHT_NAME,
)
from pcb_studio.utils import studio
from pcb_studio.utils.geometry import compute_pcb_bounds


STUDIO_NAMES = (
    KEY_LIGHT_NAME, FILL_LIGHT_NAME, RIM_LIGHT_NAME, RIM_LIGHT_2_NAME,
    TOP_LIGHT_NAME, BACKGROUND_LIGHT_NAME, BACKGROUND_LIGHT_2_NAME,
    BACKGROUND_NAME, REFLECTION_PLANE_NAME,
)


def _create_box(name: str, size: tuple[float, float, float], location=(0.0, 0.0, 0.0)):
    x, y, z = (value * 0.5 for value in size)
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    mesh.from_pydata(
        [
            (-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z),
            (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z),
        ],
        [],
        [
            (0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
            (1, 5, 6, 2), (2, 6, 7, 3), (4, 0, 3, 7),
        ],
    )
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.data.collections[COLLECTION_NAME].objects.link(obj)
    obj.location = location
    return obj


def _assert_matrix_close(left: Matrix, right: Matrix, tolerance=1e-5):
    for row in range(4):
        for column in range(4):
            assert abs(left[row][column] - right[row][column]) <= tolerance


def _create_test_image(filepath: Path, file_format: str, color):
    image = bpy.data.images.new(f"Test{file_format}{filepath.stem}", width=4, height=2, float_buffer=True)
    image.generated_color = color
    image.filepath_raw = str(filepath)
    image.file_format = file_format
    image.save()
    return image


def _assert_studio_stationary(matrices, frame: int):
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    for name, matrix in matrices.items():
        _assert_matrix_close(bpy.data.objects[name].matrix_world, matrix)


def run() -> None:
    pcb_studio.register()
    try:
        collection = bpy.data.collections.new(COLLECTION_NAME)
        bpy.context.scene.collection.children.link(collection)
        board = _create_box("TestBoard", (4.0, 2.4, 0.16))
        component = _create_box("TestIC", (0.8, 0.55, 0.22), (0.4, -0.2, 0.19))
        user_material = bpy.data.materials.new("UserPCBMaterial")
        user_material.diffuse_color = (0.04, 0.22, 0.06, 1.0)
        board.data.materials.append(user_material)
        user_light_data = bpy.data.lights.new("UserPhotographyLight", "AREA")
        user_light_data.energy = 321.0
        user_light = bpy.data.objects.new("UserPhotographyLight", user_light_data)
        bpy.context.scene.collection.objects.link(user_light)

        props = getattr(bpy.context.scene, PROP_SCENE_ATTR)
        props.pcb_imported = True
        assert bpy.ops.pcbstudio.prepare_scene() == {"FINISHED"}

        # Bounds-aware managed studio and shared light target.
        for name in STUDIO_NAMES:
            assert bpy.data.objects.get(name) is not None, name
            assert len([obj for obj in bpy.data.objects if obj.name == name]) == 1
        for name in STUDIO_NAMES[:7]:
            assert bpy.data.objects[name].parent is None
        assert bpy.data.objects[LIGHT_TARGET_NAME].parent is None
        assert len(bpy.data.objects[BACKGROUND_NAME].data.polygons) > 4

        # Prepare Scene ships a three-point rig: key, fill and one rim.
        emitting = [
            name for name in studio.PRODUCT_LIGHT_NAMES
            if bpy.data.objects.get(name) is not None
            and not bpy.data.objects[name].hide_render
        ]
        assert emitting == [KEY_LIGHT_NAME, FILL_LIGHT_NAME, RIM_LIGHT_NAME], emitting

        # The key emitter must be smaller than the product, or EEVEE has no
        # penumbra to resolve and the viewport shadow disappears.
        prepared_bounds = compute_pcb_bounds(bpy.data.collections[COLLECTION_NAME])
        assert bpy.data.objects[KEY_LIGHT_NAME].data.size < prepared_bounds.max_dimension

        # Camera presets follow the board's own facing axis, so an export that
        # stands the board on Y is not framed edge-on by a top-down preset.
        from pcb_studio.utils.geometry import board_direction, board_normal_axis
        from mathutils import Vector
        flat = compute_pcb_bounds(bpy.data.collections[COLLECTION_NAME])
        assert tuple(round(v, 6) for v in board_normal_axis(flat)) == (0.0, 0.0, 1.0)
        # A flat board keeps the historical world-axis behaviour exactly.
        assert (board_direction(flat, Vector((0.0, 0.0, 1.0))) - Vector((0.0, 0.0, 1.0))).length < 1e-6
        assert (board_direction(flat, Vector((1.0, -1.0, 1.0)).normalized())
                - Vector((1.0, -1.0, 1.0)).normalized()).length < 1e-6
        camera_direction = (
            bpy.data.objects[CAMERA_NAME].location - flat.center
        ).normalized()
        assert camera_direction.z > 0.9, "flat board should still be framed from above"

        # The backdrop carries a fine procedural grain rather than a flat gradient.
        backdrop_nodes = bpy.data.materials[BACKGROUND_MATERIAL_NAME].node_tree.nodes
        assert backdrop_nodes.get("PCB Studio Backdrop Grain") is not None
        shader = backdrop_nodes.get("PCB Studio Backdrop Shader")
        assert shader.inputs["Normal"].is_linked and shader.inputs["Roughness"].is_linked
        props.backdrop_grain = 0.0
        assert bpy.ops.pcbstudio.update_professional_studio() == {"FINISHED"}
        backdrop_nodes = bpy.data.materials[BACKGROUND_MATERIAL_NAME].node_tree.nodes
        assert backdrop_nodes.get("PCB Studio Backdrop Grain") is None
        props.backdrop_grain = 0.15
        assert bpy.ops.pcbstudio.update_professional_studio() == {"FINISHED"}

        # EEVEE shadow quality is configured, so the viewport matches Cycles.
        eevee = bpy.context.scene.eevee
        if hasattr(eevee, "use_shadows"):
            assert eevee.use_shadows
        if hasattr(eevee, "shadow_ray_count"):
            assert eevee.shadow_ray_count > 1
        if hasattr(eevee, "taa_samples"):
            assert eevee.taa_samples >= 16
        receiver = bpy.data.collections[BACKGROUND_RECEIVER_COLLECTION]
        assert BACKGROUND_NAME in receiver.objects
        assert bpy.data.objects[BACKGROUND_LIGHT_NAME].light_linking.receiver_collection == receiver

        # Background changes do not alter PCB materials or product-light state.
        original_material = board.data.materials[0]
        props.background_preset = "BLACK"
        assert bpy.ops.pcbstudio.apply_background() == {"FINISHED"}
        assert board.data.materials[0] == original_material
        props.master_product_brightness = 0.0
        assert bpy.data.objects[KEY_LIGHT_NAME].data.energy == 0.0
        assert bpy.data.objects[BACKGROUND_LIGHT_NAME].data.energy > 0.0
        props.master_product_brightness = 1.2

        # All new and legacy presets update the same singular managed rig.
        for preset in (
            "BRIGHT_STUDIO", "PCB_SHOWCASE", "PREMIUM_DARK", "ELECTRIC_BLUE", "WARM_AMBER",
            "CLEAN_WHITE_PRODUCT", "APPLE_SOFT_STUDIO", "PREMIUM_BLACK",
            "DRAMATIC_EDGE", "METALLIC_HIGHLIGHT", "PCB_MACRO",
            "COMMERCIAL_CATALOG", "CINEMATIC_BLUE", "WARM_LUXURY",
        ):
            props.studio_lighting_preset = preset
            assert bpy.ops.pcbstudio.apply_lighting_preset() == {"FINISHED"}
            for _ in range(2):
                assert bpy.ops.pcbstudio.update_professional_studio() == {"FINISHED"}
            for name in STUDIO_NAMES:
                assert len([obj for obj in bpy.data.objects if obj.name == name]) == 1
        assert tuple(bpy.data.objects[KEY_LIGHT_NAME].data.color) != tuple(bpy.data.objects[BACKGROUND_LIGHT_NAME].data.color)
        assert bpy.data.objects["UserPhotographyLight"] == user_light
        assert user_light.data.energy == 321.0

        # Bounds-aware procedural backdrop variants and wall looks remain singular.
        CYCLORAMA_TYPES = {
            "INFINITY_CYCLORAMA", "GRADIENT_CYCLORAMA", "SEAMLESS_PAPER", "CURVED_WALL",
        }
        for backdrop_type in (
            "INFINITY_CYCLORAMA", "CURVED_WALL", "FLAT_WALL", "FLOOR_BACK_WALL",
            "THREE_WALL", "CORNER_STUDIO", "SEAMLESS_PAPER", "GRADIENT_CYCLORAMA",
        ):
            props.backdrop_type = backdrop_type
            assert bpy.ops.pcbstudio.update_professional_studio() == {"FINISHED"}
            backdrop = bpy.data.objects[BACKGROUND_NAME].data
            assert len(backdrop.polygons) >= 1
            assert len([obj for obj in bpy.data.objects if obj.name == BACKGROUND_NAME]) == 1
            if backdrop_type in CYCLORAMA_TYPES:
                # A welded strip: two vertices per profile point, one face
                # between each pair.  Unwelded quads would give 4 * polygons.
                assert len(backdrop.vertices) == 2 * (len(backdrop.polygons) + 1), backdrop_type
                assert backdrop.has_custom_normals, backdrop_type
                assert all(polygon.use_smooth for polygon in backdrop.polygons), backdrop_type
                # Seamless: one material across floor, curve and wall.
                assert len({p.material_index for p in backdrop.polygons}) == 1, backdrop_type
                assert len(backdrop.materials) == 1, backdrop_type
            else:
                assert not backdrop.has_custom_normals, backdrop_type
                assert not any(polygon.use_smooth for polygon in backdrop.polygons), backdrop_type
        for wall_preset in (
            "PURE_WHITE", "SOFT_WHITE", "LIGHT_GRAY", "GRAPHITE", "MATTE_BLACK",
            "MIDNIGHT_BLUE", "WARM_GRAY", "DARK_NAVY", "CONCRETE",
            "SOFT_GRADIENT", "BLUE_GRADIENT", "WARM_GRADIENT",
        ):
            props.background_preset = wall_preset
            assert bpy.ops.pcbstudio.apply_background() == {"FINISHED"}

        # Custom lights support every starter and remain one object per slot.
        for light_preset in (
            "LARGE_SOFTBOX", "SIDE_STRIP", "TOP_STRIP", "EDGE_RIM", "OVERHEAD", "ACCENT_SPOT",
        ):
            props.custom_light_preset = light_preset
            assert bpy.ops.pcbstudio.add_custom_studio_light() == {"FINISHED"}
        assert len(props.custom_lights) == 6
        custom_names = {slot.object_name for slot in props.custom_lights}
        assert all(name.startswith(CUSTOM_LIGHT_PREFIX) for name in custom_names)
        assert all(bpy.data.objects[name].get("pcbstudio_role") == "custom_light" for name in custom_names)
        assert bpy.ops.pcbstudio.update_professional_studio() == {"FINISHED"}
        assert {obj.name for obj in bpy.data.objects if obj.get("pcbstudio_role") == "custom_light"} == custom_names
        props.custom_light_index = 0
        props.custom_lights[0].light_type = "SPOT"
        props.custom_lights[0].spot_softness = 0.6
        assert bpy.data.objects[props.custom_lights[0].object_name].data.type == "SPOT"
        assert bpy.ops.pcbstudio.delete_custom_studio_light() == {"FINISHED"}
        assert len(props.custom_lights) == 5

        # White, black, and silver reflection cards are independently managed.
        for card_type in ("WHITE", "BLACK", "SILVER"):
            props.light_card_type = card_type
            assert bpy.ops.pcbstudio.add_light_card() == {"FINISHED"}
        assert len(props.light_cards) == 3
        assert all(slot.object_name.startswith(LIGHT_CARD_PREFIX) for slot in props.light_cards)
        assert bpy.ops.pcbstudio.update_professional_studio() == {"FINISHED"}
        props.light_card_index = 1
        removed_card = props.light_cards[1].object_name
        assert bpy.ops.pcbstudio.remove_light_card() == {"FINISHED"}
        assert bpy.data.objects.get(removed_card) is None

        # Solo affects only managed lights and restores exact visibility.
        before = {name: bpy.data.objects[name].hide_render for name in STUDIO_NAMES[:7]}
        operator = bpy.ops.pcbstudio.solo_studio_light
        assert operator(light_name=KEY_LIGHT_NAME) == {"FINISHED"}
        assert not bpy.data.objects[KEY_LIGHT_NAME].hide_render
        assert bpy.data.objects[FILL_LIGHT_NAME].hide_render
        assert bpy.ops.pcbstudio.restore_studio_lights() == {"FINISHED"}
        assert {name: bpy.data.objects[name].hide_render for name in STUDIO_NAMES[:7]} == before

        # Floor modes and the optional scale-aware pedestal.
        props.reflection_surface = "DARK_GLASS"
        props.stage_type = "ROUNDED_PEDESTAL"
        assert bpy.ops.pcbstudio.update_professional_studio() == {"FINISHED"}
        assert not bpy.data.objects[REFLECTION_PLANE_NAME].hide_render
        assert bpy.data.objects.get(PEDESTAL_NAME) is not None
        assert bpy.data.objects[PEDESTAL_NAME].modifiers.get("PCB_STUDIO_STAGE_BEVEL") is not None
        for floor_type in ("MATTE", "SATIN", "GLOSSY", "MIRROR", "DARK_GLASS", "FROSTED", "CONCRETE", "ACRYLIC", "METALLIC"):
            props.reflection_surface = floor_type
            assert bpy.ops.pcbstudio.update_professional_studio() == {"FINISHED"}
            assert not bpy.data.objects[REFLECTION_PLANE_NAME].hide_render
        for floor_preset in ("WHITE_ACRYLIC", "BLACK_ACRYLIC", "PREMIUM_SATIN", "MIRROR_BLACK", "MATTE_GRAY", "DARK_GLASS"):
            props.floor_preset = floor_preset
            assert bpy.ops.pcbstudio.apply_floor_preset() == {"FINISHED"}
        for pedestal_shape in ("CIRCULAR", "ROUNDED_SQUARE", "RECTANGULAR", "LOW_PLATFORM"):
            props.pedestal_shape = pedestal_shape
            assert bpy.ops.pcbstudio.update_professional_studio() == {"FINISHED"}
            pedestal = bpy.data.objects[PEDESTAL_NAME]
            assert pedestal.get("pcbstudio_managed")
            # The pedestal must clear the board. Object.dimensions divides by the
            # evaluated bounding box, so without a depsgraph update between the
            # mesh rebuild and the assignment it is sized from the previous shape
            # and its top face pushes up through the product.
            bpy.context.view_layer.update()
            bounds = compute_pcb_bounds(bpy.data.collections[COLLECTION_NAME])
            top = pedestal.matrix_world.translation.z + pedestal.dimensions.z / 2.0
            assert top <= bounds.min.z, (pedestal_shape, top, bounds.min.z)

        # Turning the stage off removes the pedestal instead of leaving a hidden
        # object behind in the outliner forever.
        props.stage_type = "FLOOR"
        assert bpy.ops.pcbstudio.update_professional_studio() == {"FINISHED"}
        assert bpy.data.objects.get(PEDESTAL_NAME) is None

        # Composition helpers affect studio visuals, never the camera or user light.
        assert bpy.ops.pcbstudio.studio_helper(action="HIDE") == {"FINISHED"}
        assert not bpy.data.objects[CAMERA_NAME].hide_viewport
        assert not user_light.hide_viewport
        assert bpy.ops.pcbstudio.studio_helper(action="SHOW") == {"FINISHED"}
        assert bpy.ops.pcbstudio.studio_helper(action="LOCK") == {"FINISHED"}
        assert user_light.hide_select is False

        # Conservative smoothing, idempotent bevel, shared UV, and layered PCB material.
        bpy.ops.object.select_all(action="DESELECT")
        board.select_set(True)
        component.select_set(True)
        bpy.context.view_layer.objects.active = board
        assert bpy.ops.pcbstudio.smooth_selected_components() == {"FINISHED"}
        assert all(polygon.use_smooth for polygon in component.data.polygons)
        props.micro_bevel_preset = "REALISTIC"
        assert bpy.ops.pcbstudio.apply_micro_bevel() == {"FINISHED"}
        assert bpy.ops.pcbstudio.apply_micro_bevel() == {"FINISHED"}
        assert len([modifier for modifier in board.modifiers if modifier.name == MICRO_BEVEL_MODIFIER_NAME]) == 1
        assert bpy.ops.pcbstudio.setup_pcb_uv_mapping() == {"FINISHED"}
        assert board.data.uv_layers.get(PCB_UV_LAYER_NAME) is not None

        with tempfile.TemporaryDirectory(prefix="pcbstudio_test_") as temp_directory:
            temp = Path(temp_directory)
            copper_path = temp / "copper.png"
            hdri_path = temp / "studio.hdr"
            _create_test_image(copper_path, "PNG", (1.0, 1.0, 1.0, 1.0))
            _create_test_image(hdri_path, "HDR", (0.15, 0.22, 0.35, 1.0))
            props.front_copper_mask = str(copper_path)
            props.trace_relief_enabled = True
            assert bpy.ops.pcbstudio.create_pcb_surface_material() == {"FINISHED"}
            surface = bpy.data.materials[PCB_SURFACE_MATERIAL_NAME]
            assert any(node.type == "TEX_IMAGE" for node in surface.node_tree.nodes)
            assert any(node.type == "BUMP" and "Trace Relief" in node.name for node in surface.node_tree.nodes)

            # HDRI Lighting Only uses Light Path camera-ray separation while
            # retaining the neutral product lights.
            props.hdri_mode = "LIGHTING_ONLY"
            result = bpy.ops.pcbstudio.load_hdri("EXEC_DEFAULT", filepath=str(hdri_path))
            assert result == {"FINISHED"}
            world_nodes = bpy.context.scene.world.node_tree.nodes
            assert any(node.type == "LIGHT_PATH" for node in world_nodes)
            assert world_nodes.get("PCB Studio Camera Ray Separation") is not None
            assert not bpy.data.objects[KEY_LIGHT_NAME].hide_render
            # Lighting Only shows the flat world colour to camera rays.
            assert world_nodes.get("PCB Studio Backdrop Environment") is None

            # Lighting + Background is a distinct graph: camera rays see the
            # HDRI itself, dimmed, rather than the flat world colour.
            props.hdri_mode = "LIGHTING_BACKGROUND"
            assert bpy.ops.pcbstudio.apply_hdri() == {"FINISHED"}
            world_nodes = bpy.context.scene.world.node_tree.nodes
            backdrop = world_nodes.get("PCB Studio Backdrop Environment")
            assert backdrop is not None
            assert world_nodes.get("PCB Studio Camera Ray Separation") is not None
            lighting = world_nodes.get("PCB Studio Environment Lighting")
            assert backdrop.inputs["Strength"].default_value < lighting.inputs["Strength"].default_value
            assert backdrop.inputs["Color"].is_linked

            # Visible Environment routes the HDRI straight to the output.
            props.hdri_mode = "VISIBLE_ENVIRONMENT"
            assert bpy.ops.pcbstudio.apply_hdri() == {"FINISHED"}
            world_nodes = bpy.context.scene.world.node_tree.nodes
            assert world_nodes.get("PCB Studio Camera Ray Separation") is None
            assert world_nodes.get("PCB Studio Environment Texture") is not None

            # Remove clears the file and returns to the neutral managed world.
            assert bpy.ops.pcbstudio.remove_hdri() == {"FINISHED"}
            assert props.hdri_filepath == ""
            assert props.hdri_mode == "OFF"
            assert bpy.context.scene.world.node_tree.nodes.get(
                "PCB Studio Environment Texture") is None
            props.hdri_mode = "LIGHTING_ONLY"
            assert bpy.ops.pcbstudio.load_hdri("EXEC_DEFAULT", filepath=str(hdri_path)) == {"FINISHED"}

            # Fast EEVEE preview and a tiny real Cycles still both restore the
            # user's engine and resolution after rendering.
            props.still_format = "CUSTOM"
            props.still_custom_width = 64
            props.still_custom_height = 64
            props.lighting_preview_resolution = "25"
            original_engine = bpy.context.scene.render.engine
            original_resolution = (
                bpy.context.scene.render.resolution_x,
                bpy.context.scene.render.resolution_y,
                bpy.context.scene.render.resolution_percentage,
            )
            assert bpy.ops.pcbstudio.render_lighting_preview() == {"FINISHED"}
            assert bpy.context.scene.render.engine == original_engine
            assert (
                bpy.context.scene.render.resolution_x,
                bpy.context.scene.render.resolution_y,
                bpy.context.scene.render.resolution_percentage,
            ) == original_resolution

            props.final_output_directory = str(temp)
            props.final_filename = "professional_test.png"
            props.overwrite_existing = True
            props.cycles_quality = "DRAFT"
            assert bpy.ops.pcbstudio.render_professional_still() == {"FINISHED"}
            assert (temp / "professional_test.png").is_file()
            assert bpy.context.scene.render.engine == original_engine

            # Rendering with the adaptive studio active: update_professional_studio
            # returns that subsystem's own success string, which a whitelist check
            # used to reject and report as an error.
            environment = bpy.context.scene.pcb_studio_environment
            for studio_type in ("CYCLO", "TABLETOP", "FLAT", "FLOATING"):
                environment.studio_type = studio_type
                assert bpy.ops.pcbstudio.environment(action="UPDATE") == {"FINISHED"}
                assert bpy.ops.pcbstudio.update_professional_studio() == {"FINISHED"}, studio_type
                assert bpy.ops.pcbstudio.render_lighting_preview() == {"FINISHED"}, studio_type
                props.final_filename = f"adaptive_{studio_type}.png"
                assert bpy.ops.pcbstudio.render_professional_still() == {"FINISHED"}, studio_type
                assert (temp / f"adaptive_{studio_type}.png").is_file(), studio_type
            environment.studio_type = "LEGACY"
            assert bpy.ops.pcbstudio.environment(action="UPDATE") == {"FINISHED"}
            props.final_filename = "professional_test.png"
            assert bpy.context.scene.render.engine == original_engine

        assert bpy.ops.pcbstudio.remove_micro_bevel() == {"FINISHED"}
        assert board.modifiers.get(MICRO_BEVEL_MODIFIER_NAME) is None

        # Each animation mode leaves every visual studio object stationary.
        props.stage_type = "FLOOR"
        props.camera_preset = "ISOMETRIC"
        assert bpy.ops.pcbstudio.apply_camera_preset() == {"FINISHED"}
        assert bpy.ops.pcbstudio.update_professional_studio() == {"FINISHED"}
        studio_matrices = {
            name: bpy.data.objects[name].matrix_world.copy()
            for name in STUDIO_NAMES if bpy.data.objects.get(name) is not None
        }
        for animation_type, preset in (
            ("PCB_TURNTABLE", "PREMIUM_DARK"),
            ("CAMERA_ORBIT", "ELECTRIC_BLUE"),
            ("CINEMATIC_FLYOVER", "WARM_AMBER"),
        ):
            props.studio_lighting_preset = preset
            assert bpy.ops.pcbstudio.apply_lighting_preset() == {"FINISHED"}
            studio_matrices = {
                name: bpy.data.objects[name].matrix_world.copy()
                for name in STUDIO_NAMES if bpy.data.objects.get(name) is not None
            }
            props.animation_type = animation_type
            props.turntable_duration = 2.0
            props.turntable_fps = "24"
            assert bpy.ops.pcbstudio.setup_turntable() == {"FINISHED"}
            _assert_studio_stationary(studio_matrices, 24)
            _assert_studio_stationary(studio_matrices, 48)
            assert bpy.ops.pcbstudio.reset_turntable() == {"FINISHED"}

        # Studio reset is separate: camera, PCB root, and imported PCB survive.
        camera = bpy.data.objects[CAMERA_NAME]
        root = bpy.data.objects[ROOT_EMPTY_NAME]
        assert bpy.ops.pcbstudio.reset_professional_studio() == {"FINISHED"}
        assert bpy.data.objects.get(CAMERA_NAME) == camera
        assert bpy.data.objects.get(ROOT_EMPTY_NAME) == root
        assert bpy.data.objects.get("TestBoard") == board
        assert bpy.data.objects.get(KEY_LIGHT_NAME) is None
        assert not any(obj.get("pcbstudio_role") == "custom_light" for obj in bpy.data.objects)
        assert not any(obj.get("pcbstudio_role") == "light_card" for obj in bpy.data.objects)
        assert bpy.data.objects.get("UserPhotographyLight") == user_light
        assert user_light.data.energy == 321.0

        print("PCB Studio professional-studio, realism, render, and regression tests passed.")
    finally:
        pcb_studio.unregister()


if __name__ == "__main__":
    run()
