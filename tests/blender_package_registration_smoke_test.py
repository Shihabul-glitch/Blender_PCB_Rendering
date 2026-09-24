"""Register the built PCB Studio archive from an isolated temporary folder."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile

import bpy


def run() -> None:
    arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(arguments) != 1:
        raise RuntimeError("Pass exactly one PCB Studio ZIP path after --")
    archive = Path(arguments[0]).resolve()
    assert archive.is_file()

    with tempfile.TemporaryDirectory(prefix="pcbstudio_package_") as directory:
        root = Path(directory)
        package = root / "pcb_studio"
        package.mkdir()
        with ZipFile(archive) as bundle:
            bundle.extractall(package)

        sys.path.insert(0, str(root))
        import pcb_studio

        assert Path(pcb_studio.__file__).resolve().is_relative_to(package)
        assert pcb_studio.EXTENSION_VERSION == "2.3.2"
        pcb_studio.register()
        try:
            assert hasattr(bpy.types.Scene, "pcb_studio_import")
            bpy.ops.pcbstudio.refresh_cycles_devices.get_rna_type()
            bpy.ops.pcbstudio.camera_nudge.get_rna_type()
            bpy.ops.pcbstudio.product_orientation.get_rna_type()
            assert hasattr(bpy.types.Scene, "pcb_studio_product")
            assert hasattr(bpy.types.Object, "pcb_studio_product")
        finally:
            pcb_studio.unregister()

    print("PCB Studio packaged-extension registration test passed.")


if __name__ == "__main__":
    run()
