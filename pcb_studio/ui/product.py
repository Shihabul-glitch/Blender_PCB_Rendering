"""Compact product orientation panel in the existing PCB Studio sidebar."""
import bpy
from ..constants import OPERATOR_ID_PRODUCT_MOVE, PANEL_ID, SIDEBAR_CATEGORY

_MOVE_ICONS = {
    "LEFT": "TRIA_LEFT", "RIGHT": "TRIA_RIGHT",
    "DOWN": "TRIA_DOWN", "UP": "TRIA_UP",
    "BACK": "BACK", "FORWARD": "FORWARD",
}


class ProductPanel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = SIDEBAR_CATEGORY
    bl_parent_id = PANEL_ID
    bl_options = {"DEFAULT_CLOSED"}


class PCBSTUDIO_PT_product_orientation(ProductPanel, bpy.types.Panel):
    bl_idname = "PCBSTUDIO_PT_product_orientation"
    bl_label = "7. Product Orientation"
    bl_order = 7

    def draw(self, context):
        p, layout = context.scene.pcb_studio_product, self.layout
        layout.prop(p, "board")
        layout.prop(p, "normal_axis")
        layout.operator("pcbstudio.product_orientation", text="Center Product Pivot").view = "CENTER"
        for pair in (("FRONT", "BACK"), ("LEFT", "RIGHT"), ("TOP", "BOTTOM")):
            row = layout.row(align=True)
            for view in pair:
                row.operator("pcbstudio.product_orientation", text=view.title()).view = view
        layout.prop(p, "orientation")
        for axis in range(3):
            row = layout.row(align=True)
            for angle in (-90, 90):
                op = row.operator("pcbstudio.product_orientation", text=f"{'XYZ'[axis]} {angle:+}°")
                op.view, op.axis, op.angle = "STEP", axis, angle
        row = layout.row(align=True)
        op = row.operator("pcbstudio.product_orientation", text="180°")
        op.view, op.axis, op.angle = "STEP", 1, 180
        row.operator("pcbstudio.product_orientation", text="Reset Orientation").view = "RESET"
        move = layout.box()
        move.label(text="Move Product")
        move.prop(p, "move_step_mode", text="Step")
        for left, right in (("LEFT", "RIGHT"), ("DOWN", "UP"), ("BACK", "FORWARD")):
            row = move.row(align=True)
            for action, icon in ((left, _MOVE_ICONS[left]), (right, _MOVE_ICONS[right])):
                row.operator(OPERATOR_ID_PRODUCT_MOVE, text=action.title(), icon=icon).action = action
        move.prop(p, "position")
        move.operator(OPERATOR_ID_PRODUCT_MOVE, text="Reset Position").action = "RESET"

        layout.prop(p, "auto_frame")
        layout.label(text="Front = original orientation; +Z board convention.")
        if p.status:
            layout.label(text=p.status, icon="INFO")


PRODUCT_PANEL_CLASSES = (PCBSTUDIO_PT_product_orientation,)
