"""Managed studio geometry, sharing existing floor/pedestal settings and collections.

Only explicit fit/center actions sample the product bounds. Ordinary updates keep
an anchored studio in place, even after product orientation or pedestal placement.
"""
from math import sin, cos, pi
from contextlib import contextmanager
import bpy
from mathutils import Vector, Matrix
from .. import constants as c
from .geometry import compute_world_bounds
from .camera import get_or_create_render_setup_collection
from . import material_compat as compat

TAG = 'pcbstudio_environment_role'
COLLECTION = 'PCB_STUDIO_ENVIRONMENT'
FILM = 'pcbstudio_environment_original_film'
PLACEMENT = 'pcbstudio_pedestal_original_matrix'
PRESETS = {
    'WHITE_ECOMMERCE': ('White Ecommerce', 'CYCLO', (.8,.8,.8,1), .65, 'SOFT'),
    'LIGHT_GRAY': ('Light Gray Product', 'CYCLO', (.45,.45,.45,1), .65, 'SOFT'),
    'DARK_PRODUCT': ('Dark Product', 'CYCLO', (.035,.038,.045,1), .55, 'SOFT'),
    'BLACK_LUXURY': ('Black Luxury', 'CYCLO', (.008,.009,.012,1), .32, 'SOFT'),
    'GLOSSY_BLACK': ('Glossy Black', 'ACRYLIC', (.012,.012,.014,1), .19, 'GLOSSY'),
    'GLOSSY_WHITE': ('Glossy White', 'ACRYLIC', (.8,.8,.8,1), .2, 'GLOSSY'),
    'PCB_TECHNICAL': ('PCB Technical', 'CYCLO', (.5,.5,.5,1), .85, 'NONE'),
    'SOFT_GRAY': ('Soft Gray', 'MATTE', (.35,.35,.35,1), .85, 'NONE'),
    'HERO_PEDESTAL': ('Hero Pedestal', 'PEDESTAL', (.12,.13,.15,1), .6, 'SOFT'),
    'TRANSPARENT': ('Transparent Product', 'FLOATING', (.5,.5,.5,1), .7, 'NONE'),
}

@contextmanager
def batch(scene):
    previous = scene.get('pcbstudio_batch_update', False)
    scene['pcbstudio_batch_update'] = True
    try: yield
    finally: scene['pcbstudio_batch_update'] = previous

def enabled(scene):
    e = getattr(scene, 'pcb_studio_environment', None)
    return e is not None and e.active and e.studio_type != 'LEGACY'

def product_bounds(scene):
    collection = bpy.data.collections.get(c.COLLECTION_NAME)
    objects = [] if collection is None else [o for o in collection.all_objects
        if o.name in scene.objects and not o.get('pcbstudio_managed') and not o.get(TAG)
        and not o.pcb_studio_product.exclude_rotation]
    bounds = compute_world_bounds(objects)
    if not bounds.is_valid: raise ValueError('Import a PCB before creating a studio.')
    return bounds

def collection(scene):
    parent = get_or_create_render_setup_collection()
    for child in parent.children:
        if child.get(TAG) == 'collection': return child
    result = bpy.data.collections.new(COLLECTION)
    result[TAG] = 'collection'
    parent.children.link(result)
    return result

def objects(scene):
    return [o for o in scene.objects if o.get(TAG)]

def managed(scene, role):
    return next((o for o in objects(scene) if o.get(TAG) == role), None)

def ensure(scene, role, name, legacy=None):
    obj = managed(scene, role)
    if obj is None and legacy:
        candidate = bpy.data.objects.get(legacy)
        if candidate is not None and candidate.type == 'MESH' and candidate.get('pcbstudio_managed') and candidate.name in scene.objects:
            obj = candidate
    if obj is None:
        obj = bpy.data.objects.new(name, bpy.data.meshes.new(name))
    obj[TAG] = role
    obj['pcbstudio_managed'] = True
    target = collection(scene)
    if obj.name not in target.objects: target.objects.link(obj)
    # Geometry never inherits imported product transforms.
    if obj.parent is not None:
        world = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = world
    for coll in list(obj.users_collection):
        if coll != target: coll.objects.unlink(obj)
    return obj

def fit(scene, props, center=True):
    e = scene.pcb_studio_environment
    b = product_bounds(scene)
    scale = max(b.max_dimension, .0001)
    m = e.margin * (.75 if e.studio_type == 'TABLETOP' else 1.0)
    e.width = max(b.dimensions.x, scale*.6) * m * 6
    e.depth = max(b.dimensions.y, scale*.6) * m * 6
    e.height = scale*m*3
    e.radius = min(e.depth*.2, e.height*.4)
    e.pedestal_width = max(b.dimensions.x*1.35, scale*.7)
    e.pedestal_depth = max(b.dimensions.y*1.35, scale*.7)
    e.pedestal_height = scale*.15
    e.pedestal_radius = scale*.035
    e.corner_radius = scale*.04
    if center:
        e.anchor = (b.center.x, b.center.y, b.min.z-scale*.005)
        e.offset = (0,0,0)
    e.initialized = True

def center(scene):
    b = product_bounds(scene)
    e = scene.pcb_studio_environment
    e.anchor = (b.center.x, b.center.y, b.min.z-max(b.max_dimension,.0001)*.005)
    e.offset = (0,0,0)

def mesh_update(obj, vertices, faces, smooth=False, normals=None, indices=None):
    signature = repr((vertices,faces,smooth,indices))
    if obj.get('pcbstudio_geometry_signature') == signature: return
    if obj.data.users > 1: obj.data = obj.data.copy()
    obj.data.clear_geometry()
    obj.data.from_pydata(vertices, [], faces)
    obj.data.update()
    for p in obj.data.polygons:
        p.use_smooth = smooth
        if indices: p.material_index = indices[p.index]
    if normals: obj.data.normals_split_custom_set_from_vertices(normals)
    obj['pcbstudio_geometry_signature'] = signature

def sweep(obj, e):
    # Welded strips with analytic normals keep both long floor and wall planar.
    r = min(e.radius, e.depth*.45, e.height*.9)
    y = e.depth/2-r
    profile = [(-e.depth/2,0,(0,0,1)), (y,0,(0,0,1))]
    for i in range(1,65):
        a = (pi/2)*i/64
        profile.append((y+r*sin(a), r*(1-cos(a)), (0,-sin(a),cos(a))))
    profile.append((e.depth/2,e.height,(0,-1,0)))
    verts = [(x,y,z) for y,z,n in profile for x in (-e.width/2,e.width/2)]
    normals = [n for y,z,n in profile for _ in range(2)]
    faces = [(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(profile)-1)]
    mesh_update(obj,verts,faces,True,normals)

def flat(obj,e,walls=True):
    w,d,h=e.width/2,e.depth/2,e.height
    verts=[(-w,-d,0),(w,-d,0),(w,d,0),(-w,d,0)]
    if walls: verts.extend([(-w,d,h),(w,d,h)])
    faces=[(0,1,2,3)]; indices=[0]
    if walls:
        faces.append((3,2,5,4)); indices.append(1)
    if e.studio_type == 'CORNER':
        if e.side == 'LEFT':
            verts.append((-w,-d,h)); faces.append((0,3,4,6))
        else:
            verts.append((w,-d,h)); faces.append((2,1,6,5))
        indices.append(2)
    mesh_update(obj,verts,faces,indices=indices)

def material(obj, role, color, roughness, reflection, metallic=0, ior=1.46, transmission=0, gradient=None, props=None):
    mat = next((m for m in obj.data.materials if m and m.get(TAG)==role), None)
    if mat is None:
        mat = next((m for m in bpy.data.materials if m.get(TAG)==role and m.get('pcbstudio_environment_object')==obj.name),None)
    if mat is None:
        mat=bpy.data.materials.new('PCB Studio '+role.title())
        mat[TAG]=role
        mat['pcbstudio_environment_object']=obj.name
    mat.use_nodes=True
    nodes=mat.node_tree.nodes; links=mat.node_tree.links
    graph = gradient or 'SOLID'
    if mat.get('pcbstudio_graph') != graph:
        nodes.clear()
        shader=nodes.new('ShaderNodeBsdfPrincipled'); shader.name='Surface'
        out=nodes.new('ShaderNodeOutputMaterial'); links.new(shader.outputs['BSDF'],out.inputs['Surface'])
        if graph != 'SOLID':
            tex=nodes.new('ShaderNodeTexCoord')
            separate=nodes.new('ShaderNodeSeparateXYZ'); separate.name='Coordinates'
            links.new(tex.outputs['Generated'],separate.inputs[0])
            ramp=nodes.new('ShaderNodeValToRGB'); ramp.name='Gradient'
            if graph == 'VERTICAL': links.new(separate.outputs['Z'],ramp.inputs[0])
            else:
                combine=nodes.new('ShaderNodeCombineXYZ')
                links.new(separate.outputs['X'],combine.inputs['X']); links.new(separate.outputs['Z'],combine.inputs['Y'])
                distance=nodes.new('ShaderNodeVectorMath'); distance.operation='DISTANCE'; distance.name='Gradient Center'
                links.new(combine.outputs[0],distance.inputs[0]); distance.inputs[1].default_value=(.5,.5,0)
                links.new(distance.outputs['Value'],ramp.inputs[0])
            links.new(ramp.outputs['Color'],shader.inputs['Base Color'])
        mat['pcbstudio_graph']=graph
    shader=nodes['Surface']
    for key,value in (('base_color',color),('roughness',roughness),('metallic',metallic),('ior',ior),('transmission_weight',transmission),('specular',reflection)):
        compat.set_value(shader,key,value)
    mat.diffuse_color=color
    if graph != 'SOLID':
        ramp=nodes['Gradient'].color_ramp
        low=max(0,min(.98,props.background_gradient_position-props.background_gradient_strength*.5))
        high=max(low+.01,min(1,props.background_gradient_position+props.background_gradient_strength*.5))
        ramp.elements[0].position=low; ramp.elements[1].position=high
        ramp.elements[0].color=color; ramp.elements[1].color=props.background_color_2
        if graph=='RADIAL': nodes['Gradient Center'].inputs[1].default_value=(props.background_halo_center_x,props.background_halo_center_y,0)
    return mat

def film(scene,e):
    transparent=e.studio_type=='FLOATING' and e.transparent
    if transparent:
        if FILM not in scene: scene[FILM]=scene.render.film_transparent
        scene.render.film_transparent=True
    elif FILM in scene:
        scene.render.film_transparent=bool(scene[FILM]); del scene[FILM]

def update(scene, props):
    e=scene.pcb_studio_environment
    if e.studio_type=='LEGACY':
        remove(scene,props)
        e.active=False
        e.removed=False
        from .studio import update_professional_studio
        return update_professional_studio(scene,props)
    if e.removed: return 'Studio removed. Use Create / Update Studio to restore it.'
    if not e.initialized: fit(scene,props)
    e.active=True
    # Hide existing floor implementations; restore any borrowed user floor.
    from . import floor
    for obj in (floor._managed('plane'),floor._managed('infinite')):
        floor._set_visible(obj,False)
    if props.floor_custom_object: floor._restore_custom_floor(props.floor_custom_object)
    old=bpy.data.objects.get(c.PEDESTAL_NAME)
    if old and old.get('pcbstudio_managed'): old.hide_render=old.hide_viewport=True
    if 'pcbstudio_floor_film_transparent' in scene:
        scene.render.film_transparent=bool(scene['pcbstudio_floor_film_transparent']); del scene['pcbstudio_floor_film_transparent']
    film(scene,e)
    for obj in objects(scene):
        if obj.get(TAG)!='card': obj.hide_render=obj.hide_viewport=True
    visible=e.studio_type!='FLOATING' or (e.catcher and scene.render.engine=='CYCLES')
    if not visible:
        old=bpy.data.objects.get(c.BACKGROUND_NAME)
        if old and old.get('pcbstudio_managed'): old.hide_render=old.hide_viewport=True
        update_backplate(scene,props)
        return 'Floating studio active.' + (' Native shadow catching requires Cycles.' if e.catcher and scene.render.engine!='CYCLES' else '')
    shell=ensure(scene,'shell','PCB_Studio_Cyclorama',c.BACKGROUND_NAME)
    shell.hide_render=shell.hide_viewport=False
    shell.location=Vector(e.anchor)+Vector(e.offset)
    shell.rotation_euler=(0,0,e.rotation); shell.scale=(1,1,1)
    shell.is_shadow_catcher=e.studio_type=='FLOATING' and e.catcher and scene.render.engine=='CYCLES'
    curved=e.studio_type in {'CYCLO','TABLETOP','PEDESTAL'}
    if curved: sweep(shell,e)
    else: flat(shell,e,e.studio_type in {'FLAT','CORNER'})
    thickness=shell.modifiers.get('PCB Studio Sweep Thickness')
    if e.studio_type=='TABLETOP' and e.transmission>0:
        if thickness is None: thickness=shell.modifiers.new('PCB Studio Sweep Thickness','SOLIDIFY')
        thickness.thickness=min(e.width,e.depth)*.002
    elif thickness: shell.modifiers.remove(thickness)
    bevel=shell.modifiers.get('PCB Studio Corner')
    if e.studio_type=='CORNER' and e.corner_radius>0:
        if bevel is None: bevel=shell.modifiers.new('PCB Studio Corner','BEVEL')
        bevel.width=min(e.corner_radius,e.width*.1,e.depth*.1,e.height*.1)
        bevel.segments=8; bevel.limit_method='ANGLE'
    elif bevel: shell.modifiers.remove(bevel)
    strength=0 if e.reflection=='NONE' else props.floor_reflection_strength
    roughness=props.floor_roughness
    color=tuple(props.floor_color)
    surface=material(shell,'surface',color,roughness,strength,ior=e.ior,
        transmission=e.transmission if e.studio_type=='TABLETOP' else 0,gradient=e.gradient,props=props)
    mats=[surface]
    if e.studio_type in {'FLAT','CORNER'}:
        mats.append(material(shell,'wall',color if e.match_colors else tuple(props.wall_color),props.wall_roughness,strength,gradient=e.gradient,props=props))
        if e.studio_type=='CORNER': mats.append(material(shell,'side',color if e.match_colors else tuple(e.side_color),props.wall_roughness,strength))
    shell.data.materials.clear()
    for mat in mats: shell.data.materials.append(mat)
    if e.studio_type in {'FLAT','CORNER'}:
        for polygon in shell.data.polygons: polygon.material_index=polygon.index
    if e.studio_type=='PEDESTAL':
        podium=ensure(scene,'pedestal','PCB_Studio_Pedestal',c.PEDESTAL_NAME)
        podium.hide_render=podium.hide_viewport=False
        from .studio import _cylinder_geometry, _cube_geometry
        signature=repr((e.pedestal_shape,e.pedestal_width,e.pedestal_depth,e.pedestal_height))
        if podium.get('pcbstudio_shape')!=signature:
            if podium.data.users>1: podium.data=podium.data.copy()
            if e.pedestal_shape=='ROUND': _cylinder_geometry(podium.data,96)
            else: _cube_geometry(podium.data)
            width=e.pedestal_width; depth=width if e.pedestal_shape=='ROUND' else e.pedestal_depth
            for vertex in podium.data.vertices:
                vertex.co.x*=width; vertex.co.y*=depth; vertex.co.z*=e.pedestal_height
            # Existing cube helper has inward winding; correct for native shading.
            if e.pedestal_shape!='ROUND':
                import bmesh
                bm=bmesh.new(); bm.from_mesh(podium.data)
                bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(podium.data); bm.free()
            for polygon in podium.data.polygons: polygon.use_smooth=e.pedestal_shape=='ROUND' and len(polygon.vertices)==4
            podium['pcbstudio_shape']=signature
        podium.scale=(1,1,1); podium.rotation_euler=(0,0,e.rotation)
        podium.location=Vector(e.anchor)+Vector(e.offset)+Vector((0,0,e.pedestal_height/2))
        bevel=podium.modifiers.get('PCB_STUDIO_STAGE_BEVEL')
        if bevel is None: bevel=podium.modifiers.new('PCB_STUDIO_STAGE_BEVEL','BEVEL')
        bevel.width=0 if e.pedestal_shape=='SQUARE' else min(e.pedestal_radius,e.pedestal_height*.45,e.pedestal_width*.2,e.pedestal_depth*.2)
        bevel.segments=8; bevel.limit_method='ANGLE'
        mat=material(podium,'pedestal',tuple(props.pedestal_color),props.pedestal_roughness,.5,props.pedestal_metallic)
        podium.data.materials.clear(); podium.data.materials.append(mat)
    bpy.context.view_layer.update()
    update_backplate(scene,props)
    return 'Studio updated; product, camera and lights preserved.'

def apply_preset(scene,props,key):
    label,kind,color,rough,reflection=PRESETS[key]
    e=scene.pcb_studio_environment
    e.removed=False
    with batch(scene):
        e['applied_type']=kind
        e.studio_type=kind; e.gradient='SOLID'; e.match_colors=True
        e.reflection=reflection; e.transmission=0; e.catcher=False; e.transparent=True
        props.floor_color=props.wall_color=color
        props.floor_roughness=props.wall_roughness=rough
        props.floor_reflection_strength=.5
    return update(scene,props)

def place(scene):
    from .product import ensure_root, validate_static
    from .animation import _matrix_to_list
    e=scene.pcb_studio_environment
    if e.studio_type!='PEDESTAL' or not managed(scene,'pedestal'): raise ValueError('Create a pedestal first.')
    root=ensure_root(bpy.context); validate_static(root)
    bounds=product_bounds(scene)
    if PLACEMENT not in root: root[PLACEMENT]=_matrix_to_list(root.matrix_world)
    root.matrix_world.translation.z += e.anchor[2]+e.offset[2]+e.pedestal_height-bounds.min.z
    bpy.context.view_layer.update()
    return 'Product placed on pedestal; original position retained.'

def restore_placement(scene):
    from .animation import _list_to_matrix
    from .product import validate_static
    roots=[o for o in scene.objects if PLACEMENT in o]
    for obj in roots: validate_static(obj)
    for obj in roots:
        # Restore translation only: keep orientation changes made on the podium.
        obj.matrix_world.translation=_list_to_matrix(obj[PLACEMENT]).translation
        del obj[PLACEMENT]
    bpy.context.view_layer.update()
    return 'Original product position restored.'

def remove(scene,props):
    restore_placement(scene)
    remove_cards(scene,props)
    for obj in list(objects(scene)):
        data=obj.data
        bpy.data.objects.remove(obj,do_unlink=True)
        if isinstance(data,bpy.types.Mesh) and data.users==0: bpy.data.meshes.remove(data)
    for mat in list(bpy.data.materials):
        if mat.get(TAG) and mat.users==0: bpy.data.materials.remove(mat)
    if FILM in scene: scene.render.film_transparent=bool(scene[FILM]); del scene[FILM]
    scene.pcb_studio_environment.active=True
    scene.pcb_studio_environment.removed=True
    return 'Studio geometry removed; camera, lights and user objects preserved.'

def add_card(scene,props,action):
    from .studio import sync_light_card_slot
    b=product_bounds(scene); scale=max(b.max_dimension,.0001)
    slot=props.light_cards.add()
    slot.card_type='BLACK' if action=='FLAG' else 'WHITE'
    direction={'CARD_LEFT':(-1.3,0,.7),'CARD_RIGHT':(1.3,0,.7),'CARD_TOP':(0,0,1.6),'CARD_BACK':(0,1.3,.7),'FLAG':(-1.1,0,.5)}[action]
    slot.display_name={'CARD_LEFT':'Left Reflection Card','CARD_RIGHT':'Right Reflection Card','CARD_TOP':'Top Reflection Card','CARD_BACK':'Back Reflection Card','FLAG':'Black Flag'}[action]
    slot.position=tuple(b.center+Vector(direction)*scale)
    # Thin local X dimension: aim the card's local X normal toward the product.
    slot.rotation=(b.center-Vector(slot.position)).to_track_quat('X','Z').to_euler()
    slot.scale=(scale*.01,scale*.9,scale*1.2)
    slot.visible_camera=False
    base='PCB_Studio_'+slot.display_name.replace(' ','_')
    name=base; index=1
    while bpy.data.objects.get(name):
        name=f'{base}_{index:02d}'; index+=1
    slot.object_name=name
    props.light_card_index=len(props.light_cards)-1
    obj=sync_light_card_slot(scene,slot)
    parent=collection(scene)
    target=next((coll for coll in parent.children if coll.get(TAG)=='cards'),None)
    if target is None:
        target=bpy.data.collections.new('PCB_STUDIO_REFLECTION_CARDS')
        target[TAG]='cards'; parent.children.link(target)
    if obj.name not in target.objects: target.objects.link(obj)
    for coll in list(obj.users_collection):
        if coll!=target: coll.objects.unlink(obj)
    obj[TAG]='card'
    return 'Added '+slot.display_name+'.'

def remove_cards(scene,props):
    from .studio import _remove_managed_object
    for slot in props.light_cards:
        obj=bpy.data.objects.get(slot.object_name)
        if obj is not None and obj.name in scene.objects and obj.get('pcbstudio_role')=='light_card':
            materials=list(obj.data.materials)
            _remove_managed_object(obj.name,'light_card')
            for mat in materials:
                if mat and mat.users==0 and mat.get('pcbstudio_role')=='light_card_material': bpy.data.materials.remove(mat)
    props.light_cards.clear(); props.light_card_index=0
    return 'Reflection cards removed.'

def update_backplate(scene,props):
    e=scene.pcb_studio_environment
    obj=managed(scene,'backplate')
    enabled=e.backplate_enabled and e.backplate_image is not None and scene.camera is not None
    enabled=enabled and not (e.studio_type=='FLOATING' and e.transparent)
    if not enabled:
        if obj: obj.hide_render=obj.hide_viewport=True
        return
    camera=scene.camera; source=e.backplate_image
    if camera.data.type not in {'PERSP','ORTHO'}: raise ValueError('Backplates support perspective and orthographic cameras.')
    if source.size[0]==0 or source.size[1]==0: raise ValueError('Load a valid backplate image first.')
    b=product_bounds(scene)
    depth=-(camera.matrix_world.inverted() @ b.center).z+max(b.max_dimension,.001)*2
    if depth<=camera.data.clip_start or depth>=camera.data.clip_end:
        raise ValueError('Backplate lies outside camera clipping; adjust camera clipping first.')
    frame=camera.data.view_frame(scene=scene)
    corners=[Vector((v.x*(depth/-v.z if camera.data.type=='PERSP' else 1),
                     v.y*(depth/-v.z if camera.data.type=='PERSP' else 1),-depth)) for v in frame]
    # Use a consistent bottom-left, bottom-right, top-right, top-left order.
    x0=min(v.x for v in corners); x1=max(v.x for v in corners)
    y0=min(v.y for v in corners); y1=max(v.y for v in corners)
    obj=ensure(scene,'backplate','PCB_Studio_Backplate')
    mesh_update(obj,[(x0,y0,-depth),(x1,y0,-depth),(x1,y1,-depth),(x0,y1,-depth)],[(0,1,2,3)])
    obj.matrix_world=camera.matrix_world.copy()
    obj.hide_render=obj.hide_viewport=False
    for attr in ('visible_shadow','visible_diffuse','visible_glossy','visible_transmission'):
        if hasattr(obj,attr): setattr(obj,attr,False)
    screen=(x1-x0)/(y1-y0); aspect=source.size[0]/source.size[1]
    u=v=1.0
    if e.backplate_fit=='FILL':
        if screen>aspect: v=aspect/screen
        else: u=screen/aspect
    else:
        if screen>aspect: u=screen/aspect
        else: v=aspect/screen
    uv=obj.data.uv_layers.active or obj.data.uv_layers.new(name='Backplate UV')
    for loop,coords in zip(uv.data,((.5-u/2,.5-v/2),(.5+u/2,.5-v/2),(.5+u/2,.5+v/2),(.5-u/2,.5+v/2))): loop.uv=coords
    mat=next((m for m in obj.data.materials if m and m.get(TAG)=='backplate'),None)
    if mat is None:
        mat=bpy.data.materials.new('PCB Studio Backplate'); mat[TAG]='backplate'
        obj.data.materials.clear(); obj.data.materials.append(mat)
    mat.use_nodes=True
    signature=repr((source.name,e.backplate_brightness,e.backplate_blur,tuple(props.wall_color)))
    if mat.get('pcbstudio_graph')==signature: return
    nodes=mat.node_tree.nodes; links=mat.node_tree.links; nodes.clear()
    texcoord=nodes.new('ShaderNodeTexCoord')
    total=None; central=None
    samples=[(0,0,1)] if e.backplate_blur==0 else [(x,y,(2 if x==0 else 1)*(2 if y==0 else 1)/16) for y in (-1,0,1) for x in (-1,0,1)]
    for x,y,weight in samples:
        image=nodes.new('ShaderNodeTexImage'); image.image=source; image.extension='CLIP'; image.interpolation='Cubic'
        offset=nodes.new('ShaderNodeVectorMath'); offset.operation='ADD'
        links.new(texcoord.outputs['UV'],offset.inputs[0]); offset.inputs[1].default_value=(x*e.backplate_blur,y*e.backplate_blur*aspect,0)
        links.new(offset.outputs[0],image.inputs['Vector'])
        if x==0 and y==0: central=image
        weighted=nodes.new('ShaderNodeMixRGB'); weighted.blend_type='MULTIPLY'; weighted.inputs[0].default_value=1
        links.new(image.outputs['Color'],weighted.inputs[1]); weighted.inputs[2].default_value=(weight,weight,weight,1)
        if total is None: total=weighted.outputs[0]
        else:
            add=nodes.new('ShaderNodeMixRGB'); add.blend_type='ADD'; add.inputs[0].default_value=1
            links.new(total,add.inputs[1]); links.new(weighted.outputs[0],add.inputs[2]); total=add.outputs[0]
    mix=nodes.new('ShaderNodeMixRGB'); mix.inputs[1].default_value=props.wall_color
    links.new(central.outputs['Alpha'],mix.inputs[0]); links.new(total,mix.inputs[2])
    emission=nodes.new('ShaderNodeEmission'); emission.inputs['Strength'].default_value=e.backplate_brightness
    links.new(mix.outputs[0],emission.inputs['Color'])
    output=nodes.new('ShaderNodeOutputMaterial'); links.new(emission.outputs[0],output.inputs['Surface'])
    mat['pcbstudio_graph']=signature
