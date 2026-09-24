"""Configurable scene preparation with conservative defaults for existing work."""

import traceback

import bpy
from mathutils import Vector

from ..constants import (
    BACKGROUND_NAME, CAMERA_NAME, CAMERA_PRESET_ITEMS, COLLECTION_NAME,
    EXTENSION_NAME, EXTENSION_VERSION, FLOOR_MODE_ITEMS, KEY_LIGHT_NAME,
    OPERATOR_ID_PREPARE_SCENE, PROP_SCENE_ATTR, ROOT_EMPTY_NAME,
    STILL_FORMAT_ITEMS, STUDIO_PRESET_ITEMS,
)
from ..utils.animation import has_managed_animation
from ..utils.camera import setup_camera
from ..utils.camera_controls import sync_camera_properties
from ..utils.composition import apply_camera_preset
from ..utils.geometry import (
    BoundingBox,
    camera_field_of_view,
    compute_pcb_bounds,
    required_camera_distance,
)
from ..utils.professional_render import STILL_DIMENSIONS, configure_cycles_final
from ..utils.render import configure_render_settings
from ..utils.studio import apply_professional_preset


# Component close-ups belong in the Camera panel after preparing the assembly.
#: Prepare Scene offers the whole-board views.  The close-ups need a selected
#: component, and Bottom opens on the solder side, which is never the first look.
_PREPARE_CAMERA_ITEMS = [
    item for item in CAMERA_PRESET_ITEMS
    if item[0] not in {"BOTTOM", "CONNECTOR_CLOSEUP", "MACRO"}
]
_OUTPUT_ITEMS = [
    ("KEEP", "Keep Current Resolution", "Preserve the scene's dimensions and percentage"),
    ("HD_720P", "720p Landscape", "1280 x 720, suitable for a quick first render"),
    *STILL_FORMAT_ITEMS,
]


def _get_pcb_collection() -> bpy.types.Collection | None:
    return bpy.data.collections.get(COLLECTION_NAME)


def _get_usable_mesh_objects(collection: bpy.types.Collection) -> list[bpy.types.Object]:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    return [
        obj for obj in collection.all_objects
        if obj.type == "MESH" and len(obj.evaluated_get(depsgraph).data.vertices) > 0
    ]


def _center_pcb_assembly(
    pcb_collection: bpy.types.Collection, center: bool = True,
) -> BoundingBox:
    """Group mesh hierarchies while preserving their world transforms.

    Keep a root for later animation even when centering is disabled. Centering
    applies a world-space delta, so repeated preparation does not move the PCB.
    """
    from ..utils.product import ensure_root, SNAPSHOT
    if any(SNAPSHOT in obj for obj in pcb_collection.all_objects):
        raise ValueError(f"Clear the legacy '{SNAPSHOT}' custom property on the PCB objects "
                         f"before preparing the scene.")
    bpy.context.view_layer.update()
    root = ensure_root(bpy.context)
    bpy.context.view_layer.update()
    bounds = compute_pcb_bounds(pcb_collection)
    if center and bounds.is_valid:
        matrix = root.matrix_world.copy()
        matrix.translation -= bounds.center
        root.matrix_world = matrix
        bpy.context.view_layer.update()
        bounds = compute_pcb_bounds(pcb_collection)
    return bounds


def _fit_prepared_camera(context, bounds: BoundingBox, margin: float) -> None:
    """Frame the board for the actual output aspect, along the preset's axis.

    ``Object.camera_fit_coords`` was used here before.  It can return a location
    off the camera-to-target ray, which the managed track constraint then aims
    away from, undoing the fit -- visibly so on a wide output.  Projecting the
    corners onto the camera's own axes keeps the move on that ray, so the aim
    and the framing both survive.
    """
    camera = bpy.data.objects[CAMERA_NAME]
    context.view_layer.update()
    rotation = camera.matrix_world.to_quaternion()
    back = camera.matrix_world.translation - bounds.center
    if back.length < 1e-9:
        back = rotation @ Vector((0.0, 0.0, 1.0))
    back.normalize()
    angle_x, angle_y = camera_field_of_view(camera.data, context.scene)
    distance = required_camera_distance(
        bounds, back,
        rotation @ Vector((1.0, 0.0, 0.0)),
        rotation @ Vector((0.0, 1.0, 0.0)),
        angle_x, angle_y, 1.0 + margin,
    )
    location = bounds.center + back * distance
    matrix = camera.matrix_world.copy()
    matrix.translation = location
    camera.matrix_world = matrix
    camera.data.clip_start = max(0.000001, min(0.01, distance * 0.01))
    camera.data.clip_end = max(1.0, distance * 4.0, bounds.max_dimension * 20.0)
    context.view_layer.update()
    sync_camera_properties(context.scene)


class PCBSTUDIO_OT_prepare_scene(bpy.types.Operator):
    """Choose placement, camera, studio, and render settings before preparation."""

    bl_idname = OPERATOR_ID_PREPARE_SCENE
    bl_label = "Prepare Scene"
    bl_description = "Choose how to prepare the PCB, camera, studio, and render settings"
    bl_options = {"REGISTER", "UNDO"}

    center_pcb: bpy.props.BoolProperty(
        name="Center PCB at Origin", default=True, options={"SKIP_SAVE"},
        description="Move the complete assembly to the origin; disable to keep its current placement",
    )
    prepare_camera: bpy.props.BoolProperty(
        name="Set Up Camera", default=True, options={"SKIP_SAVE"},
        description="Create or reframe the PCB Studio camera; disable to keep the current camera",
    )
    initial_camera_preset: bpy.props.EnumProperty(
        name="View", items=_PREPARE_CAMERA_ITEMS, default="TOP", options={"SKIP_SAVE"},
    )
    fit_margin: bpy.props.FloatProperty(
        name="Framing Margin", default=0.10, min=0.0, max=1.0,
        subtype="FACTOR", options={"SKIP_SAVE"},
        description="Extra space around the complete PCB in the chosen output format",
    )
    prepare_studio: bpy.props.BoolProperty(
        name="Set Up Lighting and Background", default=True, options={"SKIP_SAVE"},
        description="Apply a complete studio preset; disable to preserve existing studio work",
    )
    initial_studio_preset: bpy.props.EnumProperty(
        name="Studio Look", items=STUDIO_PRESET_ITEMS, default="PREMIUM_DARK", options={"SKIP_SAVE"},
    )
    initial_floor_mode: bpy.props.EnumProperty(
        name="Floor", items=FLOOR_MODE_ITEMS, default="STANDARD", options={"SKIP_SAVE"},
        description="Floor built under the product; choose No Floor to leave it floating",
    )
    render_setup: bpy.props.EnumProperty(
        name="Render Setup", default="EEVEE", options={"SKIP_SAVE"},
        items=(
            ("KEEP", "Keep Current Settings", "Keep the current render engine and quality"),
            ("EEVEE", "EEVEE Preview", "Configure fast EEVEE rendering"),
            ("CYCLES", "Cycles Still", "Use the existing Cycles quality with adaptive sampling and denoising"),
        ),
    )
    output_size: bpy.props.EnumProperty(
        name="Output Size", items=_OUTPUT_ITEMS, default="HD_720P", options={"SKIP_SAVE"},
    )
    output_width: bpy.props.IntProperty(
        name="Width", default=1920, min=64, max=16384, options={"SKIP_SAVE"},
    )
    output_height: bpy.props.IntProperty(
        name="Height", default=1080, min=64, max=16384, options={"SKIP_SAVE"},
    )

    def _set_dialog_defaults(self, context):
        """Initialize operator-local choices without modifying the scene."""
        props = getattr(context.scene, PROP_SCENE_ATTR, None)
        prepared = bool(props and props.scene_setup_ready) or bpy.data.objects.get(ROOT_EMPTY_NAME) is not None
        self.center_pcb = not prepared
        self.prepare_camera = bpy.data.objects.get(CAMERA_NAME) is None
        self.prepare_studio = not any(
            bpy.data.objects.get(name) is not None for name in (BACKGROUND_NAME, KEY_LIGHT_NAME)
        )
        self.render_setup = "KEEP" if prepared else "EEVEE"
        self.output_size = "KEEP" if prepared else "HD_720P"
        self.output_width = context.scene.render.resolution_x
        self.output_height = context.scene.render.resolution_y
        if props:
            self.initial_studio_preset = props.studio_lighting_preset
            self.initial_floor_mode = props.floor_mode
            if props.camera_preset in {item[0] for item in _PREPARE_CAMERA_ITEMS}:
                self.initial_camera_preset = props.camera_preset
            self.fit_margin = props.camera_fit_margin

    def invoke(self, context, event):
        self._set_dialog_defaults(context)
        return context.window_manager.invoke_props_dialog(self, width=460)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        placement = layout.box()
        placement.label(text="PCB Placement", icon="OBJECT_ORIGIN")
        placement.prop(self, "center_pcb")
        if self.center_pcb and not self.prepare_camera:
            placement.label(text="Moving the PCB can change its framing.", icon="INFO")
        camera = layout.box()
        camera.prop(self, "prepare_camera")
        if self.prepare_camera:
            camera.prop(self, "initial_camera_preset")
            camera.prop(self, "fit_margin")
        else:
            camera.label(text="Keep current camera and composition.", icon="CAMERA_DATA")
        studio = layout.box()
        studio.prop(self, "prepare_studio")
        if self.prepare_studio:
            studio.prop(self, "initial_studio_preset")
            studio.prop(self, "initial_floor_mode")
        else:
            studio.label(text="Keep current lighting and background.", icon="LIGHT")
        render = layout.box()
        render.label(text="Engine and Output", icon="RENDER_STILL")
        render.prop(self, "render_setup")
        render.prop(self, "output_size")
        if self.output_size == "CUSTOM":
            render.prop(self, "output_width")
            render.prop(self, "output_height")
        if self.output_size != "KEEP" and not self.prepare_camera:
            render.label(text="A new aspect ratio can change the crop.", icon="INFO")

    def _configure_output(self, scene, props):
        old_resolution = (
            scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage,
        )
        if self.render_setup == "EEVEE":
            configure_render_settings()
            props.professional_render_engine = "FAST_PREVIEW"
        elif self.render_setup == "CYCLES":
            configure_cycles_final(scene, props)
            props.professional_render_engine = "PROFESSIONAL_FINAL"
        if self.output_size == "KEEP":
            scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = old_resolution
            return
        dimensions = (
            (self.output_width, self.output_height) if self.output_size == "CUSTOM"
            else (1280, 720) if self.output_size == "HD_720P"
            else STILL_DIMENSIONS[self.output_size]
        )
        scene.render.resolution_x, scene.render.resolution_y = dimensions
        scene.render.resolution_percentage = 100
        props.still_format = "CUSTOM" if self.output_size == "HD_720P" else self.output_size
        props.still_custom_width, props.still_custom_height = dimensions

    def execute(self, context):
        props = getattr(context.scene, PROP_SCENE_ATTR, None)
        if props is None:
            self.report({"ERROR"}, "Extension state not available.")
            return {"CANCELLED"}
        collection = _get_pcb_collection()
        if collection is None or not _get_usable_mesh_objects(collection):
            props.scene_setup_ready = False
            props.scene_setup_status = "No PCB geometry found. Import a PCB first."
            self.report({"ERROR"}, props.scene_setup_status)
            return {"CANCELLED"}
        if any(has_managed_animation(kind) for kind in ("PCB_TURNTABLE", "CAMERA_ORBIT", "CINEMATIC_FLYOVER")):
            self.report({"ERROR"}, "Use Reset Animation before preparing the scene.")
            return {"CANCELLED"}
        try:
            bounds = _center_pcb_assembly(collection, self.center_pcb)
            if not bounds.is_valid:
                raise ValueError("Could not calculate PCB bounds.")
        except Exception as exc:
            traceback.print_exc()
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        # Suppress live scene callbacks until the selected stages are complete.
        props.scene_setup_ready = False
        errors = []

        def stage(label, operation):
            try:
                operation()
            except Exception as exc:
                traceback.print_exc()
                errors.append(f"{label}: {exc}")

        # Establish output aspect before fitting the camera.
        stage("Render settings", lambda: self._configure_output(context.scene, props))
        if self.prepare_camera:
            def prepare_camera():
                setup_camera(bounds)
                camera = bpy.data.objects[CAMERA_NAME]
                camera.data.type = "PERSP"
                props.camera_preset = self.initial_camera_preset
                props.camera_fit_margin = self.fit_margin
                apply_camera_preset(self.initial_camera_preset, context=context)
                _fit_prepared_camera(context, bounds, self.fit_margin)
            stage("Camera", prepare_camera)
        if self.prepare_studio:
            def prepare_studio():
                # Set the floor before the preset so the one rebuild it triggers
                # already builds the requested floor.
                props.floor_mode = self.initial_floor_mode
                return apply_professional_preset(context.scene, props, self.initial_studio_preset)
            stage("Studio", prepare_studio)

        camera = bpy.data.objects.get(CAMERA_NAME)
        props.camera_ready = camera is not None and camera.type == "CAMERA"
        props.scene_setup_ready = not errors
        if errors:
            message = "Preparation incomplete. " + " | ".join(errors)
            self.report({"WARNING"}, message + " Undo to revert this preparation.")
        else:
            message = "Scene prepared. " + "; ".join((
                "PCB centered" if self.center_pcb else "PCB placement kept",
                "camera set up" if self.prepare_camera else "camera kept",
                "studio set up" if self.prepare_studio else "studio kept",
            )) + "."
            self.report({"INFO"}, message)
        props.scene_setup_status = message
        print(f"{EXTENSION_NAME} v{EXTENSION_VERSION}: {message}")
        # FINISHED retains an undo step even if one stage failed after changes.
        return {"FINISHED"}
