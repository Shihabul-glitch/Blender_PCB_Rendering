"""Studio type switching, stable ownership, product protection and native nodes."""
import sys, math
from pathlib import Path
from types import SimpleNamespace
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pcb_studio
from pcb_studio.utils import studio_environment as env, product
from pcb_studio.utils.studio import update_professional_studio
from pcb_studio.ui.studio_environment import draw
from blender_product_smoke_test import cube, close

class Layout:
    def row(self,**kw): return self
    def column(self,**kw): return self
    def box(self): return self
    def grid_flow(self,**kw): return self
    def label(self,**kw): pass
    def prop(self,obj,name,**kw): assert hasattr(obj,name),name
    def template_list(self,*args,**kw): pass
    def template_ID(self,*args,**kw): pass
    def operator(self,name,**kw):
        namespace,op=name.split('.')
        getattr(getattr(bpy.ops,namespace),op).get_rna_type()
        return SimpleNamespace()

pcb_studio.register()
ctx=bpy.context; scene=ctx.scene; p=scene.pcb_studio_import; e=scene.pcb_studio_environment
coll=bpy.data.collections.new('PCB_MODEL'); scene.collection.children.link(coll)
board=cube(coll,'PCB Board',(0,0,.1),(.2,.12,.002))
chip=cube(coll,'Chip',(.01,.01,.107),(.01,.01,.01))
scene.pcb_studio_product.board=board
ctx.view_layer.update()
p.scene_setup_ready=True
update_professional_studio(scene,p)
stationary={o:o.matrix_world.copy() for o in scene.objects if o.type in {'CAMERA','LIGHT'}}
user=bpy.data.objects.new('User Studio Object',bpy.data.meshes.new('User Mesh')); scene.collection.objects.link(user)
board_before=board.matrix_world.copy()
assert bpy.ops.pcbstudio.environment(preset='WHITE_ECOMMERCE')=={'FINISHED'}
shell=env.managed(scene,'shell')
assert len(shell.data.vertices)==134 and len(shell.data.polygons)==66
assert shell.data.has_custom_normals
assert close(board.matrix_world,board_before)
assert all(close(o.matrix_world,m) for o,m in stationary.items())
# Every studio mode, repeated updates, native material consistency and UI drawing.
for kind in ('CYCLO','TABLETOP','FLAT','CORNER','ACRYLIC','MATTE','PEDESTAL','FLOATING'):
    e.studio_type=kind
    assert bpy.ops.pcbstudio.environment()=={'FINISHED'},kind
    if kind=='CORNER': assert [f.material_index for f in shell.data.polygons]==[0,1,2]
    if kind=='FLAT': assert [f.material_index for f in shell.data.polygons]==[0,1]
    count=len(bpy.data.objects); materials=len(bpy.data.materials)
    env.update(scene,p); env.update(scene,p)
    assert len(bpy.data.objects)==count and len(bpy.data.materials)==materials,kind
    assert all(close(o.matrix_world,m) for o,m in stationary.items()),kind
    assert all(o.parent is None for o in env.objects(scene))
    e.show_advanced=True; p.show_studio_background=True; p.show_light_cards=True
    draw(Layout(),ctx,p)
    for obj in env.objects(scene):
        for mat in obj.data.materials:
            assert mat.use_nodes and any(n.type=='BSDF_PRINCIPLED' for n in mat.node_tree.nodes)
# Surface edits do not touch lights; fitting/centering do not move the product.
original=board.matrix_world.copy()
p.floor_color=(.35,.4,.45,1)
assert all(close(o.matrix_world,m) for o,m in stationary.items())
assert bpy.ops.pcbstudio.environment(action='FIT')=={'FINISHED'}
assert bpy.ops.pcbstudio.environment(action='CENTER')=={'FINISHED'}
assert close(board.matrix_world,original)
# Switching back reuses the same shell and restores original transparency.
e.studio_type='CYCLO'; env.update(scene,p)
assert env.managed(scene,'shell')==shell
assert not scene.render.film_transparent
for key in env.PRESETS:
    assert bpy.ops.pcbstudio.environment(preset=key)=={'FINISHED'}
assert bpy.ops.pcbstudio.environment(preset='HERO_PEDESTAL')=={'FINISHED'}
assert bpy.ops.pcbstudio.environment(action='PLACE')=={'FINISHED'}
podium=env.managed(scene,'pedestal')
placed=env.product_bounds(scene).min.z
assert abs(placed-(e.anchor[2]+e.offset[2]+e.pedestal_height))<1e-6
stage_before={o:o.matrix_world.copy() for o in env.objects(scene)}
assert bpy.ops.pcbstudio.product_orientation(view='RIGHT')=={'FINISHED'}
env.update(scene,p)
assert all(close(o.matrix_world,m) for o,m in stage_before.items())
assert all(close(o.matrix_world,m) for o,m in stationary.items())
assert bpy.ops.pcbstudio.environment(action='RESTORE')=={'FINISHED'}
for action in ('CARD_LEFT','CARD_RIGHT','CARD_TOP','CARD_BACK','FLAG'):
    assert bpy.ops.pcbstudio.environment(action=action)=={'FINISHED'}
assert len(p.light_cards)==5
assert all(bpy.data.objects[slot.object_name].type=='MESH' for slot in p.light_cards)
assert all(not bpy.data.objects[slot.object_name].visible_camera for slot in p.light_cards)
for mode in ('SOLID','VERTICAL','RADIAL'):
    e.gradient=mode; env.update(scene,p)
    assert env.managed(scene,'shell').data.materials[0].get('pcbstudio_graph')==mode
# Native backplate uses one reusable mesh and one shader, with clipped Fit UVs.
e.studio_type='FLOATING'; e.transparent=False; e.backplate_enabled=True
e.backplate_image=bpy.data.images.new('BackplateFixture',width=160,height=90)
for fit_mode in ('FIT','FILL'):
    for blur in (0,.005):
        e.backplate_fit=fit_mode; e.backplate_blur=blur
        env.update(scene,p)
        plate=env.managed(scene,'backplate')
        assert plate and not plate.hide_render
        assert any(n.type=='EMISSION' for n in plate.data.materials[0].node_tree.nodes)
        counts=(len(bpy.data.objects),len(bpy.data.materials))
        env.update(scene,p)
        assert counts==(len(bpy.data.objects),len(bpy.data.materials))
        draw(Layout(),ctx,p)
e.backplate_enabled=False; e.transparent=True
# The studio remains protected even when linked into the product collection.
coll.objects.link(shell)
assert product.protected(shell)
bounds=env.product_bounds(scene)
assert bounds.max_dimension<1
coll.objects.unlink(shell)
e.studio_type='FLOATING'; e.catcher=True
scene.render.engine='CYCLES'; env.update(scene,p)
assert shell.is_shadow_catcher and scene.render.film_transparent
scene.render.engine='CYCLES'  # Studio operations never select a different engine.
e.studio_type='CYCLO'; env.update(scene,p)
assert not shell.is_shadow_catcher and not scene.render.film_transparent
assert bpy.ops.pcbstudio.environment(action='REMOVE')=={'FINISHED'}
assert not env.objects(scene) and user.name in scene.objects and board.name in scene.objects
update_professional_studio(scene,p)
assert not env.objects(scene), 'Lighting refresh resurrected removed studio'
assert bpy.ops.pcbstudio.environment()=={'FINISHED'}
assert env.managed(scene,'shell')
pcb_studio.unregister(); pcb_studio.register(); pcb_studio.unregister()
print('STUDIO_ENVIRONMENT_SMOKE_TEST_PASSED')
