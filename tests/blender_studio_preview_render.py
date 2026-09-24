"""Small native Cycles renders for reviewing studio geometry and materials."""
import sys
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pcb_studio
from pcb_studio.utils import studio_environment as env
from blender_floor_system_smoke_test import _box
pcb_studio.register()
scene=bpy.context.scene; p=scene.pcb_studio_import
# The factory cube is not part of the product fixture.
bpy.data.objects.remove(bpy.data.objects['Cube'],do_unlink=True)
coll=bpy.data.collections.new('PCB_MODEL'); scene.collection.children.link(coll)
board=_box('PCB Board',(.2,.12,.004),(0,0,.05))
chip=_box('Chip',(.045,.045,.015),(.01,0,.0595))
for obj,color in ((board,(.018,.2,.055,1)),(chip,(.018,.02,.023,1))):
    m=bpy.data.materials.new(obj.name);m.use_nodes=True
    m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=color
    obj.data.materials.append(m)
    bevel=obj.modifiers.new('Edge highlights','BEVEL');bevel.width=.001;bevel.segments=3
bpy.context.view_layer.update()
scene.pcb_studio_product.board=board
camera=scene.camera
camera.location=(.32,-.5,.32)
camera.rotation_euler=(Vector((0,0,.065))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.lens=50
light=bpy.data.objects['Light']; light.data.type='AREA';light.data.energy=35;light.data.shape='DISK';light.data.size=.35
light.location=(-.2,-.1,.5);light.rotation_euler=(Vector((0,0,.05))-light.location).to_track_quat('-Z','Y').to_euler()
scene.world.use_nodes=True; scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.25
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=480;scene.render.resolution_y=360;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
output=Path(__file__).resolve().parent/'studio_previews';output.mkdir(exist_ok=True)
for key in ('WHITE_ECOMMERCE','GLOSSY_BLACK','HERO_PEDESTAL'):
    env.apply_preset(scene,p,key)
    if key=='HERO_PEDESTAL':env.place(scene)
    scene.render.filepath=str(output/(key.lower()+'.png'))
    bpy.ops.render.render(write_still=True)
    assert Path(scene.render.filepath).exists()
print('STUDIO_PREVIEW_RENDERS_PASSED')
pcb_studio.unregister()
