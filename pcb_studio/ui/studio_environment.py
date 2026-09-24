"""One adaptive Studio UI, using existing surfaces, backgrounds and card slots."""
from ..utils.studio_environment import PRESETS

def button(layout,label,action='UPDATE',preset=''):
    op=layout.operator('pcbstudio.environment',text=label)
    op.action=action; op.preset=preset

def section(layout,e,name):
    box=layout.box()
    box.prop(e,name,emboss=False,icon='TRIA_DOWN' if getattr(e,name) else 'TRIA_RIGHT')
    return box if getattr(e,name) else None

def draw(layout,context,props):
    e=context.scene.pcb_studio_environment
    layout.prop(e,'studio_type')
    if e.studio_type=='LEGACY':
        if e.active: button(layout,'Use Existing Floor / Backdrop Controls')
        return False
    presets=layout.box(); presets.label(text='Studio Presets')
    grid=presets.grid_flow(row_major=True,columns=2,even_columns=True,align=True)
    for key,(label,*_) in PRESETS.items(): button(grid,label,preset=key)
    button(layout,'Create / Update Studio')
    if e.studio_type=='FLOATING':
        layout.prop(e,'transparent'); layout.prop(e,'catcher')
        if e.catcher and context.scene.render.engine!='CYCLES':
            layout.label(text='Native shadow catching requires Cycles.',icon='INFO')
    else:
        box=section(layout,e,'show_dimensions')
        if box:
            for name in ('width','depth'): box.prop(e,name)
            if e.studio_type not in {'ACRYLIC','MATTE'}: box.prop(e,'height')
            if e.studio_type in {'CYCLO','TABLETOP','PEDESTAL'}: box.prop(e,'radius')
            if e.studio_type=='CORNER': box.prop(e,'side'); box.prop(e,'corner_radius')
            box.prop(e,'margin')
        box=section(layout,e,'show_surface')
        if box:
            box.prop(props,'floor_color',text='Studio Color' if e.studio_type not in {'FLAT','CORNER'} else 'Floor Color')
            box.prop(props,'floor_roughness',text='Surface Roughness')
            box.prop(e,'reflection')
            if e.reflection!='NONE':
                box.prop(props,'floor_reflection_strength',text='Reflection Strength')
                eevee=getattr(context.scene,'eevee',None)
                if context.scene.render.engine=='BLENDER_EEVEE_NEXT' and eevee and hasattr(eevee,'use_raytracing'):
                    box.prop(eevee,'use_raytracing',text='Eevee Raytraced Reflections')
            if e.studio_type in {'ACRYLIC','TABLETOP'}: box.prop(e,'ior')
            if e.studio_type=='TABLETOP': box.prop(e,'transmission')
            if e.studio_type in {'FLAT','CORNER'}:
                box.prop(e,'match_colors')
                if not e.match_colors:
                    box.prop(props,'wall_color',text='Back Wall Color')
                    if e.studio_type=='CORNER': box.prop(e,'side_color')
                box.prop(props,'wall_roughness')
        if e.studio_type=='PEDESTAL':
            box=layout.box(); box.label(text='Pedestal')
            box.prop(e,'pedestal_shape'); box.prop(e,'pedestal_width')
            if e.pedestal_shape!='ROUND': box.prop(e,'pedestal_depth')
            box.prop(e,'pedestal_height')
            if e.pedestal_shape!='SQUARE': box.prop(e,'pedestal_radius')
            for name in ('pedestal_color','pedestal_metallic','pedestal_roughness'): box.prop(props,name)
            button(box,'Place Product On Pedestal','PLACE')
            button(box,'Restore Product Position','RESTORE')
        background=layout.box()
        background.prop(props,'show_studio_background',text='Background / Walls',emboss=False)
        if props.show_studio_background:
            background.prop(e,'gradient')
            if e.gradient!='SOLID':
                background.prop(props,'floor_color',text='Bottom / Center Color')
                background.prop(props,'background_color_2',text='Top / Edge Color')
                background.prop(props,'background_gradient_position')
                background.prop(props,'background_gradient_strength')
                if e.gradient=='RADIAL':
                    background.prop(props,'background_halo_center_x'); background.prop(props,'background_halo_center_y')
            background.label(text='World / HDRI remains in Environment lighting.')
    backplate=layout.box()
    backplate.prop(e,'backplate_enabled')
    if e.backplate_enabled:
        backplate.template_ID(e,'backplate_image',open='image.open')
        for name in ('backplate_fit','backplate_brightness','backplate_blur'): backplate.prop(e,name)
        if e.studio_type=='FLOATING' and e.transparent:
            backplate.label(text='Disable transparency to render the backplate.',icon='INFO')
        backplate.label(text='Update Studio after moving the camera.')
        if e.studio_type!='FLOATING': backplate.label(text='Opaque studio walls may cover the image.',icon='INFO')
    cards=layout.box(); cards.prop(props,'show_light_cards',text='Reflection Cards / Flags',emboss=False)
    if props.show_light_cards:
        grid=cards.grid_flow(row_major=True,columns=2,even_columns=True,align=True)
        for label,action in (('Add Left Card','CARD_LEFT'),('Add Right Card','CARD_RIGHT'),('Add Top Card','CARD_TOP'),('Add Back Card','CARD_BACK'),('Add Black Flag','FLAG')):
            button(grid,label,action)
        cards.template_list('PCBSTUDIO_UL_light_cards','',props,'light_cards',props,'light_card_index',rows=2)
        if props.light_cards:
            card=props.light_cards[min(props.light_card_index,len(props.light_cards)-1)]
            for name in ('display_name','card_type','position','rotation','visible_render','visible_camera'): cards.prop(card,name)
            cards.prop(card,'scale',text='Thickness / Width / Height')
            if card.card_type=='WHITE':
                cards.prop(card,'color'); cards.prop(card,'brightness')
            if context.scene.render.engine!='CYCLES': cards.label(text='Camera ray visibility requires Cycles.',icon='INFO')
        button(cards,'Remove Reflection Cards','REMOVE_CARDS')
    advanced=section(layout,e,'show_advanced')
    if advanced:
        advanced.prop(e,'offset'); advanced.prop(e,'rotation')
        button(advanced,'Restore Product Position','RESTORE')
    row=layout.row(align=True)
    button(row,'Fit Studio to Product','FIT'); button(row,'Center Studio on Product','CENTER')
    row=layout.row(align=True)
    button(row,'Reset Studio','RESET'); button(row,'Remove Studio','REMOVE')
    if props.environment_status: layout.label(text=props.environment_status,icon='INFO')
    return True
