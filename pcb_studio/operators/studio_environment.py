"""Undoable studio-only actions, separate from the lighting presets."""
import bpy
from ..constants import PROP_SCENE_ATTR
from ..utils import studio_environment as env

class PCBSTUDIO_OT_environment(bpy.types.Operator):
    bl_idname='pcbstudio.environment'
    bl_label='Create / Update Studio'
    bl_options={'REGISTER','UNDO'}
    action: bpy.props.EnumProperty(items=[(k,k.replace('_',' ').title(),'') for k in
        ('UPDATE','FIT','CENTER','RESET','REMOVE','PLACE','RESTORE','CARD_LEFT','CARD_RIGHT','CARD_TOP','CARD_BACK','FLAG','REMOVE_CARDS')])
    preset: bpy.props.StringProperty(default='')

    def execute(self,context):
        scene=context.scene; props=getattr(scene,PROP_SCENE_ATTR); e=scene.pcb_studio_environment
        try:
            if self.preset:
                result=env.apply_preset(scene,props,self.preset)
            elif self.action=='REMOVE': result=env.remove(scene,props)
            elif self.action=='PLACE': result=env.place(scene)
            elif self.action=='RESTORE': result=env.restore_placement(scene)
            elif self.action.startswith('CARD_') or self.action=='FLAG':
                result=env.add_card(scene,props,self.action)
            elif self.action=='REMOVE_CARDS': result=env.remove_cards(scene,props)
            else:
                e.removed=False
                if self.action=='RESET':
                    env.restore_placement(scene)
                    with env.batch(scene):
                        for prop in e.bl_rna.properties:
                            if prop.identifier!='rna_type' and not prop.is_readonly: e.property_unset(prop.identifier)
                    env.fit(scene,props)
                    result=env.apply_preset(scene,props,'LIGHT_GRAY')
                else:
                    if self.action=='FIT': env.fit(scene,props,center=not e.initialized)
                    elif self.action=='CENTER': env.center(scene)
                    if e.get('applied_type')!=e.studio_type:
                        with env.batch(scene):
                            if e.studio_type=='ACRYLIC':
                                props.floor_roughness=.19; e.reflection='GLOSSY'
                            elif e.studio_type=='MATTE':
                                props.floor_roughness=.85; e.reflection='NONE'
                            else:
                                props.floor_roughness=.65; e.reflection='SOFT'
                        e['applied_type']=e.studio_type
                    result=env.update(scene,props)
            props.environment_status=result
            self.report({'INFO'},result)
            return {'FINISHED'}
        except (ValueError,RuntimeError,KeyError) as exc:
            props.environment_status=str(exc); self.report({'WARNING'},str(exc))
            return {'CANCELLED'}
