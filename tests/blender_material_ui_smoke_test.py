"""Validate preset nodes, manual editing, UI references and registration in Blender."""
import sys
from pathlib import Path
from types import SimpleNamespace
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pcb_studio
from pcb_studio import constants as c
from pcb_studio.utils import materials as m, material_compat as compat
from pcb_studio.ui.main_panel import PCBSTUDIO_PT_materials, PCBSTUDIO_PT_camera
from pcb_studio.ui.product import PRODUCT_PANEL_CLASSES

class Layout:
    def __init__(self):
        self.ops = []
        self.grids = []
    def row(self, **kw): return self
    def column(self, **kw): return self
    def box(self): return self
    def separator(self, **kw): pass
    def label(self, **kw): pass
    def prop(self, obj, name, **kw): assert hasattr(obj, name), name
    def prop_enum(self, obj, name, value, **kw): self.prop(obj, name)
    def grid_flow(self, **kw): self.grids.append(kw); return self
    def operator(self, name, **kw):
        namespace, operator = name.split('.')
        getattr(getattr(bpy.ops, namespace), operator).get_rna_type()
        self.ops.append(name)
        return SimpleNamespace()

pcbstudio = pcb_studio
pcbstudio.register()
classes = pcbstudio._REGISTERED_CLASSES
assert len(classes) == len(set(classes))
ids = [cls.bl_idname for cls in classes if hasattr(cls, 'bl_idname')]
assert len(ids) == len(set(ids))
props = getattr(bpy.context.scene, c.PROP_SCENE_ATTR)
props.pcb_imported = props.scene_setup_ready = True
props.custom_material_name = 'CustomTest'
assert len(m.PRESET_DATA) == len(m._PRESET_TABLE)
assert len({p.display_name for p in m.PRESET_DATA.values()}) == len(m.PRESET_DATA)
for key, preset in m.PRESET_DATA.items():
    assert bpy.ops.pcbstudio.pick_material_preset(preset=key) == {'FINISHED'}
    if key == 'CUSTOM':
        m.apply_preset_to_props(props, key)
    assert abs(props.material_roughness - preset.roughness) < 1e-6
    assert bpy.ops.pcbstudio.create_or_update_material() == {'FINISHED'}
    mat = bpy.data.materials[props.current_material_name]
    node = compat.get_principled(mat)
    assert node is not None
    assert abs(compat.get_value(node, 'roughness') - preset.roughness) < 1e-6
    props.material_roughness = .613
    assert bpy.ops.pcbstudio.create_or_update_material() == {'FINISHED'}
    assert abs(compat.get_value(node, 'roughness') - .613) < 1e-6
assert m.PRESET_DATA['PLASTIC_BLACK'].metallic == 0
assert .4 <= m.PRESET_DATA['PLASTIC_BLACK'].roughness <= .55
assert m.PRESET_DATA['BLACK_IC_PLASTIC'].base_color != m.PRESET_DATA['PLASTIC_BLACK'].base_color

# --- Per-object material independence (copy-on-write) ---------------------
def _mesh(name):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [], [(0, 1, 2, 3)])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj

def _activate(obj):
    for other in bpy.context.selected_objects:
        other.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

# An imported OBJ shares one datablock per usemtl across many layer objects.
shared_mat = bpy.data.materials.new('pcb top paste')
shared_mat.use_nodes = True
compat.set_value(compat.get_principled(shared_mat), 'base_color', (0.1, 0.2, 0.3, 1.0))
paste, silk = _mesh('PCB top paste'), _mesh('PCB top silk')
for obj in (paste, silk):
    obj.data.materials.append(shared_mat)
assert compat.is_shared_beyond(shared_mat, [paste])
assert not compat.is_shared_beyond(shared_mat, [paste, silk])

# Editing the shared material must split it off, leaving the other object alone.
untouched = tuple(compat.get_value(compat.get_principled(shared_mat), 'base_color'))
_activate(paste)
props.material_base_color = (0.9, 0.05, 0.05, 1.0)
assert bpy.ops.pcbstudio.update_active_material() == {'FINISHED'}
assert silk.data.materials[0] is shared_mat, 'unselected object lost its material'
assert paste.data.materials[0] is not shared_mat, 'selected object was not split off'
assert tuple(compat.get_value(compat.get_principled(shared_mat), 'base_color')) == untouched
edited = paste.data.materials[0]
assert abs(compat.get_value(compat.get_principled(edited), 'base_color')[0] - 0.9) < 1e-6

# A material that is already exclusive is edited in place, not duplicated.
before = len(bpy.data.materials)
props.material_base_color = (0.2, 0.8, 0.4, 1.0)
assert bpy.ops.pcbstudio.update_active_material() == {'FINISHED'}
assert len(bpy.data.materials) == before, 'exclusive material was needlessly copied'
assert paste.data.materials[0] is edited

# Live preview follows the selection, and creates nothing: a property update
# callback must not add datablocks, so a shared material is left alone until the
# Make Unique operator splits it.
mask = _mesh('PCB top mask')
mask.data.materials.append(shared_mat)
props.material_live_preview = True
_activate(silk)
before = len(bpy.data.materials)
shared_before = tuple(compat.get_value(compat.get_principled(shared_mat), 'base_color'))
props.material_base_color = (0.05, 0.05, 0.9, 1.0)
assert len(bpy.data.materials) == before, 'live preview created a datablock in an update callback'
assert silk.data.materials[0] is shared_mat and mask.data.materials[0] is shared_mat
assert tuple(compat.get_value(compat.get_principled(shared_mat), 'base_color')) == shared_before, \
    'live preview wrote into a shared material'
assert abs(compat.get_value(compat.get_principled(edited), 'base_color')[2] - 0.9) > 1e-6, \
    'live preview wrote into the previously edited object'

# Make Unique is an operator, so it may create data and it registers undo.
assert bpy.ops.pcbstudio.make_material_unique() == {'FINISHED'}
silk_mat = silk.data.materials[0]
assert silk_mat is not shared_mat, 'Make Unique did not split the material'
assert mask.data.materials[0] is shared_mat, 'Make Unique touched an unselected object'
props.material_base_color = (0.05, 0.05, 0.85, 1.0)
assert abs(compat.get_value(compat.get_principled(silk_mat), 'base_color')[2] - 0.85) < 1e-6, \
    'live preview did not write into the now-exclusive material'
assert tuple(compat.get_value(compat.get_principled(shared_mat), 'base_color')) == shared_before
props.material_live_preview = False
for prop in props.bl_rna.properties:
    if prop.identifier.startswith(('show_material_', 'show_camera_')):
        setattr(props, prop.identifier, True)
for panel in (PCBSTUDIO_PT_materials, PCBSTUDIO_PT_camera, *PRODUCT_PANEL_CLASSES):
    layout = Layout()
    panel.draw(SimpleNamespace(layout=layout), bpy.context)
    if panel == PCBSTUDIO_PT_materials:
        assert layout.grids[0]['columns'] in (2, 3)
        assert layout.ops.count(c.OPERATOR_ID_PICK_MATERIAL_PRESET) == len(m.PRESET_DATA)
    if panel == PCBSTUDIO_PT_camera:
        assert layout.ops.count(c.OPERATOR_ID_ALIGN_CAMERA_TO_VIEW) == 1
        # Automatic mode reports the guess instead of offering the axis pickers.
        assert layout.ops.count(c.OPERATOR_ID_SET_BOARD_AXIS_FROM_VIEW) == 0

# Declaring the faces adds a pick-from-view button for each of them.
props.board_orientation_mode = 'MANUAL'
layout = Layout()
PCBSTUDIO_PT_camera.draw(SimpleNamespace(layout=layout), bpy.context)
assert layout.ops.count(c.OPERATOR_ID_SET_BOARD_AXIS_FROM_VIEW) == 2
props.board_orientation_mode = 'AUTO' 
pcbstudio.unregister()
pcbstudio.register()
pcbstudio.unregister()
print('MATERIAL_UI_SMOKE_TEST_PASSED', len(m.PRESET_DATA), 'presets')
