"""Operator for selecting and importing an Altium-exported OBJ file."""

from __future__ import annotations

import traceback
from pathlib import Path

import bpy
from bpy_extras.io_utils import ImportHelper

from ..constants import (
    EXTENSION_NAME,
    EXTENSION_VERSION,
    OPERATOR_ID_IMPORT_OBJ,
    PROP_SCENE_ATTR,
)
from ..utils.collections import (
    collection_has_objects,
    get_or_create_pcb_collection,
    move_objects_to_collection,
)
from ..utils.obj_mtl import find_mtl_for_obj


class PCBSTUDIO_OT_import_obj(bpy.types.Operator, ImportHelper):
    """Select an Altium-exported OBJ file and import it into Blender.

    The MTL material library is detected automatically from the OBJ —
    no separate MTL selection is required.
    """

    bl_idname: str = OPERATOR_ID_IMPORT_OBJ
    bl_label: str = "Select and Import OBJ"
    bl_description: str = (
        "Select a Wavefront OBJ file. Materials are imported automatically."
    )
    bl_options: set[str] = {"REGISTER", "UNDO"}

    # ImportHelper settings
    filename_ext: str = ".obj"
    filter_glob: bpy.props.StringProperty(
        default="*.obj",
        options={"HIDDEN"},
    )

    def _validate_file(self, filepath: str) -> Path | None:
        """Validate the selected file path and return a Path or None."""
        if not filepath:
            self.report({"ERROR"}, "No file selected.")
            return None

        path = Path(filepath).resolve()

        if not path.is_file():
            self.report({"ERROR"}, f"File does not exist: {path}")
            return None

        if path.suffix.lower() != ".obj":
            self.report(
                {"ERROR"},
                f"Not an OBJ file: {path}. Please select a .obj file.",
            )
            return None

        return path

    def _snapshot_scene_data(self) -> tuple[set[bpy.types.Object], set[bpy.types.Material]]:
        """Capture the current set of objects and materials."""
        objects_before = set(bpy.data.objects)
        materials_before = set(bpy.data.materials)
        return objects_before, materials_before

    def _compute_new_data(
        self,
        objects_before: set[bpy.types.Object],
        materials_before: set[bpy.types.Material],
    ) -> tuple[set[bpy.types.Object], set[bpy.types.Material]]:
        """Return newly created objects and materials since the snapshot."""
        new_objects = set(bpy.data.objects) - objects_before
        new_materials = set(bpy.data.materials) - materials_before
        return new_objects, new_materials

    def execute(self, context: bpy.types.Context | None) -> set[str]:
        """Validate, detect MTL, import OBJ, and update UI state."""
        try:
            return self._execute_impl(context)
        except Exception:
            traceback.print_exc()
            self.report(
                {"ERROR"},
                "An unexpected error occurred during import. "
                "Check the system console for details.",
            )
            return {"CANCELLED"}

    def _execute_impl(self, context: bpy.types.Context | None) -> set[str]:
        """Core import logic, wrapped by execute for exception safety."""
        props = getattr(context.scene, PROP_SCENE_ATTR, None)
        if props is None:
            self.report({"ERROR"}, "Extension state not available.")
            return {"CANCELLED"}

        # --- Validate the selected file ---
        obj_path = self._validate_file(self.filepath)
        if obj_path is None:
            props.import_status = "Invalid file selection."
            return {"CANCELLED"}

        # Store the absolute OBJ path for display.
        props.obj_filepath = str(obj_path)

        # --- Duplicate import protection ---
        pcb_coll = get_or_create_pcb_collection()
        if collection_has_objects(pcb_coll):
            self.report(
                {"WARNING"},
                "A PCB model is already imported. "
                "Remove it before importing another PCB.",
            )
            props.import_status = (
                "Import cancelled: PCB_MODEL already contains objects."
            )
            return {"CANCELLED"}

        # --- MTL detection ---
        mtl_result = find_mtl_for_obj(obj_path)

        if mtl_result.status == "ERROR":
            self.report({"ERROR"}, mtl_result.message)
            props.mtl_filepath = ""
            props.import_status = f"OBJ read error: {mtl_result.message}"
            return {"CANCELLED"}

        if mtl_result.status == "AMBIGUOUS":
            self.report({"WARNING"}, mtl_result.message)
            props.mtl_filepath = ""
            props.import_status = (
                "MTL detection ambiguous — importing geometry only."
            )

        elif mtl_result.status == "NOT_FOUND":
            self.report(
                {"WARNING"},
                f"No MTL file found. {mtl_result.message} "
                "Importing geometry without materials.",
            )
            props.mtl_filepath = ""
            props.import_status = (
                "MTL not found — importing geometry without materials."
            )

        elif mtl_result.status == "FOUND":
            props.mtl_filepath = str(mtl_result.path)
            props.import_status = f"MTL detected: {mtl_result.path.name}"
        else:
            props.mtl_filepath = ""
            props.import_status = f"Unknown MTL status: {mtl_result.status}"

        # --- Import the OBJ ---
        objects_before, materials_before = self._snapshot_scene_data()

        try:
            result = bpy.ops.wm.obj_import(filepath=str(obj_path))
            if result == {"CANCELLED"}:
                self.report({"ERROR"}, "Blender OBJ import operator failed.")
                props.import_status = "OBJ import failed."
                return {"CANCELLED"}
        except Exception:
            traceback.print_exc()
            self.report(
                {"ERROR"},
                "Blender OBJ import raised an exception. "
                "Check the system console for details.",
            )
            props.import_status = "OBJ import crashed."
            return {"CANCELLED"}

        # --- Identify new data ---
        new_objects, new_materials = self._compute_new_data(
            objects_before, materials_before,
        )

        if not new_objects:
            self.report({"WARNING"}, "OBJ imported but no new objects were created.")
            props.imported_object_count = 0
            props.imported_material_count = 0
            props.pcb_imported = False
            props.import_status = "Import completed but no objects were created."
            return {"CANCELLED"}

        # --- Move imported objects into PCB_MODEL ---
        move_objects_to_collection(new_objects, pcb_coll)

        # --- Update UI state ---
        props.imported_object_count = len(new_objects)
        props.imported_material_count = len(new_materials)
        props.pcb_imported = True

        material_note = ""
        if mtl_result.status == "FOUND" and not new_materials:
            material_note = " (MTL found but no materials were created)."
        elif mtl_result.status != "FOUND":
            material_note = " (no MTL to import)."

        status_msg = (
            f"Imported {len(new_objects)} object(s)"
            f" and {len(new_materials)} material(s)."
            f"{material_note}"
        )
        props.import_status = status_msg

        self.report({"INFO"}, status_msg)
        print(f"{EXTENSION_NAME} v{EXTENSION_VERSION}: {status_msg}")

        return {"FINISHED"}