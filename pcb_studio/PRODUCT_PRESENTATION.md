# Product orientation

Choose PCB Board or use automatic board detection. Product Orientation provides
Front, Back, Left, Right, Top, Bottom, custom angles, and 90-degree steps.
Center Product Pivot preserves the geometry's world transforms.

Move Product shifts the whole board on world axes: Left/Right along X,
Forward/Back along Y, Up/Down along Z, one Fine/Normal/Coarse step of the
product's own size per click. Position accepts exact offsets and Reset Position
returns the product to where it was imported. Moving is relative, so it composes
with Ground Product and Center Product Pivot; a move made after grounding also
shifts the grounding restore point, so Reset Ground undoes only the grounding.

The complete product rotates and moves around PCB_MODEL_ROOT. Camera, lights,
background, floor and studio objects stay stationary. Objects marked Exclude From Product
Rotation are protected; detach protected children from the product hierarchy
first. Optional Auto Frame can move the camera backward after a rotation.

Existing camera orbit/flyover controls remain available; reset those rigs before
using product orientation. User animation on the product root is protected
against replacement — clear it before orienting the product again.

Material Presets uses one flat area with two columns in narrow sidebars and three
in wider sidebars. Black IC and Black Plastic are adjacent. Presets provide
starting values; all manual material controls remain available.

Camera Options exposes Align Camera to Active View and View Through Camera.

Validation scripts: blender_product_smoke_test.py, blender_product_geometry_test.py,
blender_product_undo_test.py and blender_material_ui_smoke_test.py in tests/.
