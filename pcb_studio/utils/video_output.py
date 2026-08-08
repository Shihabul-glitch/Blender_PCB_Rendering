"""Video output configuration for turntable renders."""

from __future__ import annotations

from pathlib import Path

import bpy

RESOLUTION_PRESETS: dict[str, dict[str, object]] = {
    "DRAFT": {"x": 854, "y": 480, "samples": 16},
    "HD_720P": {"x": 1280, "y": 720, "samples": 32},
    "FULL_HD_1080P": {"x": 1920, "y": 1080, "samples": 64},
    "LINKEDIN_SQUARE": {"x": 1080, "y": 1080, "samples": 64},
    "LINKEDIN_PORTRAIT": {"x": 1080, "y": 1350, "samples": 64},
}


def apply_resolution_preset(preset: str) -> str:
    """Apply a resolution preset to the scene.

    Args:
        preset: Key from ``RESOLUTION_PRESETS``.

    Returns:
        A status message.
    """
    data = RESOLUTION_PRESETS.get(preset, RESOLUTION_PRESETS["HD_720P"])
    scene = bpy.context.scene
    scene.render.resolution_x = data["x"]
    scene.render.resolution_y = data["y"]
    scene.render.resolution_percentage = 100

    samples = data["samples"]
    if hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = samples

    return f"Resolution: {data['x']}×{data['y']}, {samples} EEVEE samples."


def configure_mp4_output(filepath: str) -> str:
    """Configure the scene for MP4/H.264 output.

    Args:
        filepath: Full path including ``.mp4`` extension.

    Returns:
        A status message.
    """
    scene = bpy.context.scene
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"

    # Conservative constant-rate quality.
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    scene.render.ffmpeg.use_autosplit = False

    scene.render.filepath = filepath

    return f"MP4 output configured: {filepath}"


def configure_png_sequence_output(directory: str) -> str:
    """Configure the scene for numbered PNG sequence output.

    Frames are saved as ``directory/frame_0001.png`` etc.

    Args:
        directory: Output directory path.  A subfolder is created
            if it does not exist.

    Returns:
        A status message.
    """
    dir_path = Path(directory).resolve()
    dir_path.mkdir(parents=True, exist_ok=True)

    scene = bpy.context.scene
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"

    # Blender's frame-number naming: directory//filename####.png
    # Use a template so frames are saved as frame_0001.png etc.
    output_template = str(dir_path / "frame_")
    scene.render.filepath = output_template

    return f"PNG sequence configured: {dir_path}"


def validate_animation_output(
    directory: str,
    filename: str,
    output_format: str,
    overwrite: bool,
) -> tuple[str, str]:
    """Validate and construct the animation output path.

    Returns:
        Tuple of ``(status_message, full_path_str)``.  If validation
        fails, *status_message* is an error message and
        *full_path_str* is empty.

    Raises:
        ValueError: For invalid parameters (caught by caller).
    """
    stripped_name = filename.strip()
    if not stripped_name:
        raise ValueError("Filename must not be empty.")

    if not directory or not directory.strip():
        raise ValueError("Output directory must not be empty.")

    dir_path = Path(directory).resolve()
    if not dir_path.is_dir():
        raise ValueError(f"Output directory does not exist: {dir_path}")

    if output_format == "MP4":
        full_path = dir_path / f"{stripped_name}.mp4"
    else:
        full_path = dir_path / f"{stripped_name}_frames"

    full_str = str(full_path.resolve())

    if output_format == "MP4":
        if full_path.exists() and not overwrite:
            return (
                f"File already exists: {full_path.name}. "
                "Enable Overwrite Existing.",
                "",
            )
    else:
        png_dir = full_path
        if png_dir.is_dir() and not overwrite:
            existing_frames = list(png_dir.glob("frame_*.png"))
            if existing_frames:
                return (
                    f"Output folder already contains {len(existing_frames)} "
                    f"PNG frames: {png_dir.name}. Enable Overwrite Existing.",
                    "",
                )

    return "", full_str