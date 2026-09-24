"""Undoable product presentation commands."""
from math import radians
import bpy
from mathutils import Vector

from ..constants import OPERATOR_ID_PRODUCT_MOVE, PRODUCT_MOVE_ACTION_ITEMS
from ..utils import product


class PCBSTUDIO_OT_product_orientation(bpy.types.Operator):
    bl_idname = "pcbstudio.product_orientation"
    bl_label = "Product Orientation"
    bl_options = {"REGISTER", "UNDO"}
    view: bpy.props.StringProperty(default="FRONT")
    axis: bpy.props.IntProperty(default=2, min=0, max=2)
    angle: bpy.props.FloatProperty(default=90)

    def execute(self, context):
        p = product.settings(context)
        try:
            if self.view == "CENTER":
                product.center_pivot(context)
            else:
                views = {"FRONT": (0, 0, 0), "RESET": (0, 0, 0), "BACK": (0, 180, 0),
                         "LEFT": (0, -90, 0), "RIGHT": (0, 90, 0),
                         "TOP": (90, 0, 0), "BOTTOM": (-90, 0, 0)}
                values = list(p.orientation) if self.view == "STEP" else [radians(a) for a in views[self.view]]
                if self.view == "STEP":
                    values[self.axis] += radians(self.angle)
                p.status = "Product orientation updated."
                product.orient_product(context, tuple(values))
                p["syncing"] = True
                p.orientation = values
                p["syncing"] = False
            return {"FINISHED"}
        except (ValueError, RuntimeError, KeyError) as exc:
            p.status = str(exc)
            self.report({"WARNING"}, str(exc))
            return {"CANCELLED"}


class PCBSTUDIO_OT_product_move(bpy.types.Operator):
    """Move the whole product along world axes, leaving the studio stationary."""

    bl_idname = OPERATOR_ID_PRODUCT_MOVE
    bl_label = "Move Product"
    bl_options = {"REGISTER", "UNDO"}
    action: bpy.props.EnumProperty(items=PRODUCT_MOVE_ACTION_ITEMS, default="RIGHT")

    @classmethod
    def description(cls, context, properties) -> str:
        described = {key: text for key, _label, text in PRODUCT_MOVE_ACTION_ITEMS}
        return described.get(properties.action, cls.bl_label)

    def execute(self, context):
        p = product.settings(context)
        try:
            if self.action == "RESET":
                target = Vector((0.0, 0.0, 0.0))
            else:
                step = product.move_step(context)
                target = Vector(p.position) + product.MOVE_DIRECTIONS[self.action] * step
            p.status = "Product position updated."
            product.move_product(context, target - Vector(p.position))
            p["syncing"] = True
            p.position = target
            p["syncing"] = False
            p["last_position"] = tuple(target)
            return {"FINISHED"}
        except (ValueError, RuntimeError, KeyError) as exc:
            p.status = str(exc)
            self.report({"WARNING"}, str(exc))
            return {"CANCELLED"}


PRODUCT_OPERATOR_CLASSES = (PCBSTUDIO_OT_product_orientation, PCBSTUDIO_OT_product_move)
