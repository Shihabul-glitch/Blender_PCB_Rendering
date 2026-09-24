"""Persistent product presentation settings (no handlers or process state)."""
import bpy

from .constants import PRODUCT_MOVE_STEP_ITEMS


def enum(items):
    return [(key, label, "") for key, label in items]


def update_orientation(self, context):
    if self.get("syncing", False):
        return
    from .utils.product import orient_product
    try:
        self.status = "Product orientation updated."
        orient_product(context, tuple(self.orientation))
    except (ValueError, RuntimeError) as exc:
        self.status = str(exc)
        self["syncing"] = True
        self.orientation = self.get("last_orientation", (0.0, 0.0, 0.0))
        self["syncing"] = False


def update_position(self, context):
    """Apply a typed Position as a delta from the last applied one.

    ``move_product`` is relative, so this tracks the previously applied vector
    and sends only the difference.  On failure the property is reverted the same
    way ``update_orientation`` reverts rotation.
    """
    if self.get("syncing", False):
        return
    from mathutils import Vector
    from .utils.product import move_product
    previous = Vector(self.get("last_position", (0.0, 0.0, 0.0)))
    target = Vector(self.position)
    try:
        self.status = "Product position updated."
        move_product(context, target - previous)
        self["last_position"] = tuple(target)
    except (ValueError, RuntimeError) as exc:
        self.status = str(exc)
        self["syncing"] = True
        self.position = tuple(previous)
        self["syncing"] = False


class PCBSTUDIO_PG_product(bpy.types.PropertyGroup):
    board: bpy.props.PointerProperty(name="PCB Board", type=bpy.types.Object,
        description="Override automatic board detection for product orientation")
    orientation: bpy.props.FloatVectorProperty(name="Rotation", subtype="EULER", update=update_orientation)
    position: bpy.props.FloatVectorProperty(name="Position", subtype="TRANSLATION",
        unit="LENGTH", update=update_position,
        description="Product offset from its imported position, in world axes")
    move_step_mode: bpy.props.EnumProperty(name="Move Step", items=PRODUCT_MOVE_STEP_ITEMS,
        default="NORMAL", description="How far one move click travels")
    auto_frame: bpy.props.BoolProperty(name="Auto Frame Product After Rotation", default=False)
    normal_axis: bpy.props.EnumProperty(name="Board Normal Axis", items=enum([
        ("Z", "Local +Z (PCB Studio default)"), ("Y", "Local +Y"), ("X", "Local +X")]), default="Z")
    status: bpy.props.StringProperty(name="Status")


class PCBSTUDIO_PG_product_object(bpy.types.PropertyGroup):
    role: bpy.props.EnumProperty(name="Product Role", items=enum([
        ("AUTO", "Automatic"), ("BOARD", "Board / Fixed to Board"), ("COMPONENT", "Component Assembly")]))
    exclude_rotation: bpy.props.BoolProperty(name="Exclude From Product Rotation", default=False,
        description="A protected object inside a product hierarchy must be detached before rotating")
