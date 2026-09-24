"""Studio environment controls; geometry is updated explicitly, without lighting edits."""
import bpy

STUDIO_TYPES = [(k, label, '') for k, label in (
    ('CYCLO', 'Seamless Cyclorama'), ('TABLETOP', 'Tabletop Sweep'),
    ('FLAT', 'Flat Studio'), ('CORNER', 'Corner Studio'), ('ACRYLIC', 'Glossy Acrylic'),
    ('MATTE', 'Matte Studio'), ('PEDESTAL', 'Pedestal Studio'), ('FLOATING', 'Floating / Transparent'),
    ('LEGACY', 'Existing Floor / Backdrop Controls'))]

def reflection_changed(self, context):
    if context is None or context.scene.get('pcbstudio_batch_update', False): return
    props=context.scene.pcb_studio_import
    from .utils.studio_environment import batch
    with batch(context.scene):
        props.floor_roughness={'NONE':.85,'SOFT':.55,'GLOSSY':.19}[self.reflection]

class PCBSTUDIO_PG_environment(bpy.types.PropertyGroup):
    studio_type: bpy.props.EnumProperty(name='Studio Type', items=STUDIO_TYPES, default='LEGACY')
    active: bpy.props.BoolProperty(default=False, options={'HIDDEN'})
    removed: bpy.props.BoolProperty(default=False, options={'HIDDEN'})
    initialized: bpy.props.BoolProperty(default=False, options={'HIDDEN'})
    width: bpy.props.FloatProperty(name='Width', default=1, min=.0001, subtype='DISTANCE', unit='LENGTH')
    depth: bpy.props.FloatProperty(name='Depth', default=1, min=.0001, subtype='DISTANCE', unit='LENGTH')
    height: bpy.props.FloatProperty(name='Backdrop Height', default=.6, min=.0001, subtype='DISTANCE', unit='LENGTH')
    radius: bpy.props.FloatProperty(name='Sweep Radius', default=.15, min=.00001, subtype='DISTANCE', unit='LENGTH')
    margin: bpy.props.FloatProperty(name='Fit Margin', default=2.0, min=1.1, max=10)
    anchor: bpy.props.FloatVectorProperty(size=3, options={'HIDDEN'})
    offset: bpy.props.FloatVectorProperty(name='Studio Offset', size=3, subtype='TRANSLATION')
    rotation: bpy.props.FloatProperty(name='Studio Rotation Z', subtype='ANGLE')
    match_colors: bpy.props.BoolProperty(name='Match All Colors', default=True)
    side: bpy.props.EnumProperty(name='Side Wall', items=[('LEFT','Left',''),('RIGHT','Right','')])
    corner_radius: bpy.props.FloatProperty(name='Corner Softness', default=.01, min=0, subtype='DISTANCE', unit='LENGTH')
    side_color: bpy.props.FloatVectorProperty(name='Side Wall Color', size=4, subtype='COLOR', min=0, max=1, default=(.45,.45,.45,1))
    transmission: bpy.props.FloatProperty(name='Sweep Transmission', default=0, min=0, max=1)
    ior: bpy.props.FloatProperty(name='Surface IOR', default=1.46, min=1, max=2.5)
    reflection: bpy.props.EnumProperty(name='Reflection Mode', items=[('NONE','None',''),('SOFT','Soft',''),('GLOSSY','Glossy','')], default='SOFT', update=reflection_changed)
    transparent: bpy.props.BoolProperty(name='Transparent Render Background', default=True)
    catcher: bpy.props.BoolProperty(name='Shadow Catcher', default=False)
    pedestal_width: bpy.props.FloatProperty(name='Width / Diameter', default=.3, min=.0001, subtype='DISTANCE', unit='LENGTH')
    pedestal_depth: bpy.props.FloatProperty(name='Depth', default=.25, min=.0001, subtype='DISTANCE', unit='LENGTH')
    pedestal_height: bpy.props.FloatProperty(name='Height', default=.05, min=.0001, subtype='DISTANCE', unit='LENGTH')
    pedestal_radius: bpy.props.FloatProperty(name='Corner Radius', default=.01, min=0, subtype='DISTANCE', unit='LENGTH')
    pedestal_shape: bpy.props.EnumProperty(name='Pedestal Shape', items=[('ROUND','Round',''),('SQUARE','Square',''),('ROUNDED','Rounded Square','')])
    gradient: bpy.props.EnumProperty(name='Background Surface', items=[('SOLID','Solid Color',''),('VERTICAL','Vertical Gradient',''),('RADIAL','Radial Gradient','')])
    backplate_enabled: bpy.props.BoolProperty(name='Background Image / Backplate', default=False)
    backplate_image: bpy.props.PointerProperty(name='Image', type=bpy.types.Image)
    backplate_fit: bpy.props.EnumProperty(name='Fit Mode', items=[('FIT','Fit',''),('FILL','Fill','')], default='FILL')
    backplate_brightness: bpy.props.FloatProperty(name='Image Brightness', default=1, min=0, max=5)
    backplate_blur: bpy.props.FloatProperty(name='Image Blur', default=0, min=0, max=.02, precision=3)
    show_dimensions: bpy.props.BoolProperty(name='Dimensions', default=True)
    show_surface: bpy.props.BoolProperty(name='Surface', default=True)
    show_advanced: bpy.props.BoolProperty(name='Advanced', default=False)
