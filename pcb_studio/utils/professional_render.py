"""Temporary EEVEE/Cycles still-render configuration for PCB Studio."""

from __future__ import annotations

from dataclasses import dataclass

import bpy

from ..constants import MANAGED_COMPOSITOR_TAG


CYCLES_SAMPLES = {
    "DRAFT": 64,
    "STANDARD": 256,
    "HIGH": 512,
    "ULTRA": 1024,
}

STILL_DIMENSIONS = {
    "HD_LANDSCAPE": (1920, 1080),
    "INSTAGRAM_SQUARE": (1080, 1080),
    "INSTAGRAM_PORTRAIT": (1080, 1350),
    "STORY": (1080, 1920),
    "PORTRAIT_1600": (1600, 2000),
    "FOUR_K": (3840, 2160),
}


@dataclass
class RenderSettingsSnapshot:
    engine: str
    resolution_x: int
    resolution_y: int
    resolution_percentage: int
    filepath: str
    file_format: str
    color_mode: str
    cycles_samples: int
    cycles_use_adaptive_sampling: bool
    cycles_adaptive_threshold: float
    cycles_use_denoising: bool
    cycles_device: str


def snapshot_render_settings(scene: bpy.types.Scene) -> RenderSettingsSnapshot:
    return RenderSettingsSnapshot(
        engine=scene.render.engine,
        resolution_x=scene.render.resolution_x,
        resolution_y=scene.render.resolution_y,
        resolution_percentage=scene.render.resolution_percentage,
        filepath=scene.render.filepath,
        file_format=scene.render.image_settings.file_format,
        color_mode=scene.render.image_settings.color_mode,
        cycles_samples=scene.cycles.samples,
        cycles_use_adaptive_sampling=scene.cycles.use_adaptive_sampling,
        cycles_adaptive_threshold=scene.cycles.adaptive_threshold,
        cycles_use_denoising=scene.cycles.use_denoising,
        cycles_device=scene.cycles.device,
    )


def restore_render_settings(scene: bpy.types.Scene, snapshot: RenderSettingsSnapshot) -> None:
    scene.render.engine = snapshot.engine
    scene.render.resolution_x = snapshot.resolution_x
    scene.render.resolution_y = snapshot.resolution_y
    scene.render.resolution_percentage = snapshot.resolution_percentage
    scene.render.filepath = snapshot.filepath
    scene.render.image_settings.file_format = snapshot.file_format
    scene.render.image_settings.color_mode = snapshot.color_mode
    scene.cycles.samples = snapshot.cycles_samples
    scene.cycles.use_adaptive_sampling = snapshot.cycles_use_adaptive_sampling
    scene.cycles.adaptive_threshold = snapshot.cycles_adaptive_threshold
    scene.cycles.use_denoising = snapshot.cycles_use_denoising
    scene.cycles.device = snapshot.cycles_device


def configure_still_dimensions(scene: bpy.types.Scene, props) -> tuple[int, int]:
    if props.still_format == "CUSTOM":
        dimensions = (props.still_custom_width, props.still_custom_height)
    else:
        dimensions = STILL_DIMENSIONS.get(props.still_format, (1920, 1080))
    scene.render.resolution_x, scene.render.resolution_y = dimensions
    scene.render.resolution_percentage = 100
    return dimensions


def configure_eevee_preview(scene: bpy.types.Scene, props) -> str:
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE"
    configure_still_dimensions(scene, props)
    scene.render.resolution_percentage = int(props.lighting_preview_resolution)
    if hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = 32
    from .render import configure_eevee_shadows
    configure_eevee_shadows(scene)
    return f"EEVEE lighting preview at {props.lighting_preview_resolution}%."


def configure_cycles_final(scene: bpy.types.Scene, props) -> str:
    scene.render.engine = "CYCLES"
    samples = CYCLES_SAMPLES.get(props.cycles_quality, 256)
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = {
        "DRAFT": 0.08,
        "STANDARD": 0.035,
        "HIGH": 0.02,
        "ULTRA": 0.01,
    }.get(props.cycles_quality, 0.035)
    scene.cycles.use_denoising = True
    configure_still_dimensions(scene, props)
    return f"Cycles {props.cycles_quality.title()}: {samples} adaptive samples, denoising."


def configure_managed_finishing(scene: bpy.types.Scene, props) -> str:
    """Add restrained finishing only when no custom compositor graph exists."""
    requested = (
        abs(props.compositor_contrast - 1.0) > 1e-4
        or abs(props.compositor_saturation - 1.0) > 1e-4
        or props.compositor_glow > 1e-4
    )
    if not requested:
        return "Compositor finishing off."

    scene.use_nodes = True
    tree = scene.node_tree
    nodes = tree.nodes
    links = tree.links
    user_nodes = [
        node for node in nodes
        if node.type not in {"R_LAYERS", "COMPOSITE"}
        and not node.get(MANAGED_COMPOSITOR_TAG, False)
    ]
    if user_nodes:
        return "Custom compositor detected; PCB Studio finishing was not injected."

    for node in list(nodes):
        if node.get(MANAGED_COMPOSITOR_TAG, False):
            nodes.remove(node)
    render_layers = next((node for node in nodes if node.type == "R_LAYERS"), None)
    composite = next((node for node in nodes if node.type == "COMPOSITE"), None)
    if render_layers is None:
        render_layers = nodes.new(type="CompositorNodeRLayers")
    if composite is None:
        composite = nodes.new(type="CompositorNodeComposite")
    for link in list(composite.inputs["Image"].links):
        links.remove(link)

    previous = render_layers.outputs["Image"]
    hue = nodes.new(type="CompositorNodeHueSat")
    hue[MANAGED_COMPOSITOR_TAG] = True
    hue.name = "PCB Studio Saturation"
    hue.inputs["Saturation"].default_value = props.compositor_saturation
    links.new(previous, hue.inputs["Image"])
    previous = hue.outputs["Image"]

    contrast = nodes.new(type="CompositorNodeBrightContrast")
    contrast[MANAGED_COMPOSITOR_TAG] = True
    contrast.name = "PCB Studio Contrast"
    contrast.inputs["Contrast"].default_value = (props.compositor_contrast - 1.0) * 100.0
    links.new(previous, contrast.inputs["Image"])
    previous = contrast.outputs["Image"]

    if props.compositor_glow > 1e-4:
        glare = nodes.new(type="CompositorNodeGlare")
        glare[MANAGED_COMPOSITOR_TAG] = True
        glare.name = "PCB Studio Mild Highlight Glow"
        glare.glare_type = "FOG_GLOW"
        glare.quality = "HIGH"
        glare.threshold = 1.2
        glare.size = 6
        glare.mix = -1.0 + min(1.0, props.compositor_glow) * 0.22
        links.new(previous, glare.inputs["Image"])
        previous = glare.outputs["Image"]

    links.new(previous, composite.inputs["Image"])
    return "Managed contrast, saturation, and mild glow configured."
