"""Shared constants for the PCB Studio Blender extension."""

EXTENSION_NAME: str = "PCB Studio"
EXTENSION_VERSION: str = "2.3.2"
EXTENSION_ID: str = "pcb_studio"

SIDEBAR_CATEGORY: str = "PCB Studio"
PANEL_LABEL: str = "PCB Studio"
PANEL_ID: str = "PCBSTUDIO_PT_main_panel"

OPERATOR_ID_SYSTEM_CHECK: str = "pcbstudio.system_check"
OPERATOR_ID_IMPORT_OBJ: str = "pcbstudio.import_obj"
OPERATOR_ID_PREPARE_SCENE: str = "pcbstudio.prepare_scene"
OPERATOR_ID_RENDER_PREVIEW: str = "pcbstudio.render_preview"
OPERATOR_ID_CREATE_MATERIAL: str = "pcbstudio.create_or_update_material"
OPERATOR_ID_ASSIGN_MATERIAL: str = "pcbstudio.assign_material"
OPERATOR_ID_PREVIEW_MATERIALS: str = "pcbstudio.preview_materials"
OPERATOR_ID_RENDER_FINAL: str = "pcbstudio.render_final"
OPERATOR_ID_APPLY_LIGHTING: str = "pcbstudio.apply_lighting_preset"
OPERATOR_ID_APPLY_BACKGROUND: str = "pcbstudio.apply_background"
OPERATOR_ID_LOAD_HDRI: str = "pcbstudio.load_hdri"
OPERATOR_ID_APPLY_HDRI: str = "pcbstudio.apply_hdri"
OPERATOR_ID_REMOVE_HDRI: str = "pcbstudio.remove_hdri"
OPERATOR_ID_APPLY_CAMERA_PRESET: str = "pcbstudio.apply_camera_preset"
OPERATOR_ID_SET_BOARD_AXIS_FROM_VIEW: str = "pcbstudio.set_board_axis_from_view"
OPERATOR_ID_ALIGN_CAMERA_TO_VIEW: str = "pcbstudio.align_camera_to_view"
OPERATOR_ID_APPLY_CAMERA_SETTINGS: str = "pcbstudio.apply_camera_settings"
OPERATOR_ID_ZOOM_TO_FIT: str = "pcbstudio.zoom_to_fit"
OPERATOR_ID_CAMERA_NUDGE: str = "pcbstudio.camera_nudge"
OPERATOR_ID_SET_CAMERA_MODE: str = "pcbstudio.set_camera_control_mode"
OPERATOR_ID_AIM_CAMERA_PCB: str = "pcbstudio.aim_camera_at_pcb"
OPERATOR_ID_AIM_CAMERA_SELECTED: str = "pcbstudio.aim_camera_at_selected"
OPERATOR_ID_RESET_CAMERA_TARGET: str = "pcbstudio.reset_camera_target"
OPERATOR_ID_FIT_CAMERA_SELECTED: str = "pcbstudio.fit_camera_selected"
OPERATOR_ID_SAVE_CAMERA_VIEW: str = "pcbstudio.save_camera_view"
OPERATOR_ID_RESTORE_CAMERA_VIEW: str = "pcbstudio.restore_camera_view"
OPERATOR_ID_RESET_CAMERA: str = "pcbstudio.reset_camera"
OPERATOR_ID_APPLY_REFLECTION: str = "pcbstudio.apply_reflection_plane"
OPERATOR_ID_SETUP_TURNTABLE: str = "pcbstudio.setup_turntable"
OPERATOR_ID_RESET_TURNTABLE: str = "pcbstudio.reset_turntable"
OPERATOR_ID_PREVIEW_TURNTABLE: str = "pcbstudio.preview_turntable"
OPERATOR_ID_RENDER_TEST_FRAME: str = "pcbstudio.render_test_frame"
OPERATOR_ID_RENDER_TURNTABLE: str = "pcbstudio.render_turntable"
OPERATOR_ID_UPDATE_STUDIO: str = "pcbstudio.update_professional_studio"
OPERATOR_ID_RESET_STUDIO: str = "pcbstudio.reset_professional_studio"
OPERATOR_ID_RENDER_LIGHTING_PREVIEW: str = "pcbstudio.render_lighting_preview"
OPERATOR_ID_RENDER_PROFESSIONAL: str = "pcbstudio.render_professional_still"
OPERATOR_ID_SOLO_LIGHT: str = "pcbstudio.solo_studio_light"
OPERATOR_ID_RESTORE_LIGHTS: str = "pcbstudio.restore_studio_lights"
OPERATOR_ID_ADD_CUSTOM_LIGHT: str = "pcbstudio.add_custom_studio_light"
OPERATOR_ID_DELETE_CUSTOM_LIGHT: str = "pcbstudio.delete_custom_studio_light"
OPERATOR_ID_APPLY_CUSTOM_LIGHT_PRESET: str = "pcbstudio.apply_custom_light_preset"
OPERATOR_ID_ADD_LIGHT_CARD: str = "pcbstudio.add_light_card"
OPERATOR_ID_REMOVE_LIGHT_CARD: str = "pcbstudio.remove_light_card"
OPERATOR_ID_APPLY_FLOOR_PRESET: str = "pcbstudio.apply_floor_preset"
OPERATOR_ID_STUDIO_HELPER: str = "pcbstudio.studio_helper"
OPERATOR_ID_FLOOR_ACTION: str = "pcbstudio.floor_action"
OPERATOR_ID_SMOOTH_SELECTED: str = "pcbstudio.smooth_selected_components"
OPERATOR_ID_SMOOTH_ALL: str = "pcbstudio.smooth_all_components"
OPERATOR_ID_APPLY_MICRO_BEVEL: str = "pcbstudio.apply_micro_bevel"
OPERATOR_ID_REMOVE_MICRO_BEVEL: str = "pcbstudio.remove_micro_bevel"
OPERATOR_ID_CREATE_PCB_SURFACE: str = "pcbstudio.create_pcb_surface_material"
OPERATOR_ID_SETUP_PCB_UV: str = "pcbstudio.setup_pcb_uv_mapping"
OPERATOR_ID_REFRESH_CYCLES_DEVICES: str = "pcbstudio.refresh_cycles_devices"
OPERATOR_ID_PICK_MATERIAL_PRESET: str = "pcbstudio.pick_material_preset"
OPERATOR_ID_RESET_MATERIAL_VALUES: str = "pcbstudio.reset_material_values"
OPERATOR_ID_PICK_ACTIVE_MATERIAL: str = "pcbstudio.pick_active_material"
OPERATOR_ID_UPDATE_ACTIVE_MATERIAL: str = "pcbstudio.update_active_material"
OPERATOR_ID_ASSIGN_ACTIVE_MATERIAL: str = "pcbstudio.assign_active_material"
OPERATOR_ID_SELECT_SAME_MATERIAL: str = "pcbstudio.select_same_material"
OPERATOR_ID_MAKE_MATERIAL_UNIQUE: str = "pcbstudio.make_material_unique"

COLLECTION_NAME: str = "PCB_MODEL"
RENDER_SETUP_COLLECTION: str = "PCB_RENDER_SETUP"

ROOT_EMPTY_NAME: str = "PCB_MODEL_ROOT"
CAMERA_NAME: str = "PCB_RENDER_CAMERA"
CAMERA_TARGET_NAME: str = "PCB_CAMERA_TARGET"
CAMERA_TARGET_CONSTRAINT_NAME: str = "PCB Studio Targeting"
CAMERA_ORBIT_ROOT_NAME: str = "PCB_CAMERA_ORBIT_ROOT"
CAMERA_ORBIT_MOUNT_NAME: str = "PCB_CAMERA_ORBIT_MOUNT"
CAMERA_FLYOVER_ROOT_NAME: str = "PCB_CAMERA_FLYOVER_ROOT"
DOF_TARGET_NAME: str = "PCB_DOF_TARGET"
REFLECTION_PLANE_NAME: str = "PCB_REFLECTION_PLANE"
REFLECTION_MATERIAL_NAME: str = "PCB_REFLECTION_MATERIAL"
KEY_LIGHT_NAME: str = "PCB_KEY_LIGHT"
FILL_LIGHT_NAME: str = "PCB_FILL_LIGHT"
RIM_LIGHT_NAME: str = "PCB_RIM_LIGHT"
RIM_LIGHT_2_NAME: str = "PCB_RIM_LIGHT_2"
FRONT_LIGHT_LEFT_NAME: str = "PCB_FRONT_LIGHT_LEFT"
FRONT_LIGHT_RIGHT_NAME: str = "PCB_FRONT_LIGHT_RIGHT"

TOP_LIGHT_NAME: str = "PCB_TOP_LIGHT"
BACKGROUND_LIGHT_NAME: str = "PCB_BACKGROUND_LIGHT"
BACKGROUND_LIGHT_2_NAME: str = "PCB_BACKGROUND_LIGHT_2"
LIGHT_TARGET_NAME: str = "PCB_LIGHT_TARGET"
BACKGROUND_NAME: str = "PCB_BACKGROUND"
BACKGROUND_MATERIAL_NAME: str = "PCB_BACKGROUND_MATERIAL"
PCB_STUDIO_WORLD_NAME: str = "PCB_STUDIO_WORLD"
BACKGROUND_RECEIVER_COLLECTION: str = "PCB_BACKGROUND_RECEIVERS"
PEDESTAL_NAME: str = "PCB_STAGE_PEDESTAL"
PEDESTAL_MATERIAL_NAME: str = "PCB_STAGE_MATERIAL"
CUSTOM_LIGHT_PREFIX: str = "PCB_CUSTOM_LIGHT_"
LIGHT_CARD_PREFIX: str = "PCB_STUDIO_CARD_"
LIGHT_CARD_MATERIAL_PREFIX: str = "PCB_STUDIO_CARD_MAT_"
BACKGROUND_FLOOR_MATERIAL_NAME: str = "PCB_BACKGROUND_FLOOR_MATERIAL"
PCB_SURFACE_MATERIAL_NAME: str = "PCB_STUDIO_SURFACE"
PCB_EDGE_MATERIAL_NAME: str = "PCB_STUDIO_EDGE"
OPERATOR_ID_PRODUCT_ORIENTATION: str = "pcbstudio.product_orientation"
OPERATOR_ID_PRODUCT_MOVE: str = "pcbstudio.product_move"
MICRO_BEVEL_MODIFIER_NAME: str = "PCB_STUDIO_MICRO_BEVEL"
PCB_UV_LAYER_NAME: str = "PCB_STUDIO_UV"
MANAGED_COMPOSITOR_TAG: str = "pcbstudio_finishing_node"

#: Quarter-circle segments in a cyclorama floor-to-wall sweep.  The sweep is a
#: welded strip carrying analytic custom split normals, so this only controls
#: the silhouette, not the shading; 64 matches ``studio_environment.sweep``.
CYCLORAMA_CURVE_SEGMENTS: int = 64

MATERIAL_NAME_PREFIX: str = "PCBSTUDIO_MAT_"

PROP_GROUP_ID: str = "PCBSTUDIO_PG_import_state"
PROP_SCENE_ATTR: str = "pcb_studio_import"

# --- Material preset enum items ---
# The preset enum itself is generated from the single source of truth in
# ``utils.materials.PRESET_DATA`` (as MATERIAL_PRESET_ITEMS) so preset values
# and enum labels can never drift apart.  Only the pure UI enums live here.
#: Micro surface detail modes.  Values map to utils.material_nodes.MICRO_PROFILES.
MATERIAL_MICRO_DETAIL_ITEMS: list[tuple[str, str, str]] = [
    ("OFF", "Off", "No micro surface detail"),
    ("SOLDER_MASK", "PCB Solder Mask", "Very fine sprayed solder mask texture"),
    ("IC_PLASTIC", "IC Plastic", "Fine moulded plastic grain for IC packages"),
    ("FINE_PLASTIC", "Fine Plastic", "Slightly larger grain for moulded parts"),
    ("FINE_CERAMIC", "Fine Ceramic", "Sintered ceramic surface variation"),
    ("BRUSHED_METAL", "Brushed Metal", "Directional brushed metal streaks"),
]

# --- Render quality preset items ---
RENDER_QUALITY_ITEMS: list[tuple[str, str, str]] = [
    ("LOW_POWER", "Low Power", "1280×720, 32 samples"),
    ("STANDARD", "Standard", "1920×1080, 64 samples"),
    ("HIGH", "High", "2560×1440, 128 samples"),
]

# --- Lighting mode ---
LIGHTING_MODE_ITEMS: list[tuple[str, str, str]] = [
    ("STUDIO", "Studio", "Use managed studio area lights"),
    ("HDRI", "HDRI", "Use environment HDRI for lighting"),
]

# --- Studio lighting presets ---
STUDIO_PRESET_ITEMS: list[tuple[str, str, str]] = [
    ("BRIGHT_STUDIO", "Bright Studio", "Bright, even, low-contrast"),
    ("DARK_STUDIO", "Dark Studio", "Dramatic premium product lighting"),
    ("PRODUCT_SHOT", "Product Shot", "Balanced catalog/product photography"),
    ("PCB_SHOWCASE", "PCB Showcase", "Emphasise PCB materials and geometry"),
    ("PREMIUM_DARK", "Premium Dark", "Neutral product lighting on a premium graphite set"),
    ("CLEAN_COMMERCIAL", "Clean Commercial", "Bright catalog lighting with soft contact shadows"),
    ("ELECTRIC_BLUE", "Electric Blue", "Neutral product light with a controlled blue background halo"),
    ("WARM_AMBER", "Warm Amber", "Neutral-warm product light with an amber background halo"),
    ("DRAMATIC_RIM", "Dramatic Rim", "Strong edge separation for dark electronics"),
    ("MACRO_DETAIL", "Macro Detail", "Tight highlights for component close-ups"),
    ("CLEAN_WHITE_PRODUCT", "Clean White Product", "Crisp neutral product lighting on white"),
    ("APPLE_SOFT_STUDIO", "Apple-style Soft Studio", "Large soft sources and gentle tonal separation"),
    ("PREMIUM_BLACK", "Premium Black", "Controlled premium lighting on a black set"),
    ("DRAMATIC_EDGE", "Dramatic Edge", "Strong rim separation with restrained fill"),
    ("METALLIC_HIGHLIGHT", "Metallic Highlight", "Long specular highlights for metal parts"),
    ("PCB_MACRO", "PCB Macro", "Compact detailed light for PCB close-ups"),
    ("COMMERCIAL_CATALOG", "Commercial Catalog", "Even repeatable catalog lighting"),
    ("CINEMATIC_BLUE", "Cinematic Blue", "Cool cinematic edge and backdrop accents"),
    ("WARM_LUXURY", "Warm Luxury", "Warm premium product lighting"),
]

# --- Background presets ---
BACKGROUND_PRESET_ITEMS: list[tuple[str, str, str]] = [
    ("WHITE", "White", "Neutral off-white background"),
    ("BLACK", "Black", "Near-black background"),
    ("DARK_GRAY", "Dark Gray", "Neutral dark charcoal gray"),
    ("BLUE_GRADIENT", "Blue Gradient", "Procedural dark-blue gradient"),
    ("CUSTOM_SOLID", "Custom Solid", "Use the custom background color"),
    ("CUSTOM_GRADIENT", "Custom Gradient", "Blend two custom colors"),
    ("RADIAL_GRADIENT", "Radial Gradient", "Radial two-color background"),
    ("TWO_TONE", "Two-Tone", "Controlled split-color background"),
    ("STUDIO_GRADIENT", "Studio Gradient", "Soft commercial studio gradient"),
    ("PURE_WHITE", "Pure White", "Bright clean white wall"),
    ("SOFT_WHITE", "Soft White", "Warm off-white studio wall"),
    ("LIGHT_GRAY", "Light Gray", "Neutral light-gray wall"),
    ("GRAPHITE", "Graphite", "Premium graphite wall"),
    ("MATTE_BLACK", "Matte Black", "Low-reflectance black wall"),
    ("MIDNIGHT_BLUE", "Midnight Blue", "Deep muted blue wall"),
    ("WARM_GRAY", "Warm Gray", "Warm neutral gray wall"),
    ("DARK_NAVY", "Dark Navy", "Very dark navy wall"),
    ("CONCRETE", "Concrete", "Procedural concrete-like neutral wall"),
    ("SOFT_GRADIENT", "Soft Gradient", "Subtle neutral procedural gradient"),
    ("WARM_GRADIENT", "Warm Gradient", "Warm procedural gradient"),
]

# --- Board orientation ---
#: How the board's own frame is established before a preset is aimed.
BOARD_ORIENTATION_MODE_ITEMS: list[tuple[str, str, str]] = [
    ("AUTO", "Automatic", "Guess the board face from the thinnest dimension of the product bounds"),
    ("MANUAL", "Declare Faces", "State which world axis the top face and front edge point along"),
]

#: The six signed world axes, used for both the top face and the front edge.
BOARD_AXIS_ITEMS: list[tuple[str, str, str]] = [
    ("POS_X", "+X", "Toward positive world X"),
    ("NEG_X", "-X", "Toward negative world X"),
    ("POS_Y", "+Y", "Toward positive world Y"),
    ("NEG_Y", "-Y", "Toward negative world Y"),
    ("POS_Z", "+Z", "Toward positive world Z"),
    ("NEG_Z", "-Z", "Toward negative world Z"),
]

# --- Camera presets ---
CAMERA_PRESET_ITEMS: list[tuple[str, str, str]] = [
    ("TOP", "Top", "Straight down at the component side of the board"),
    ("FRONT_FLAT", "Front Flat", "Level elevation of the board's front edge"),
    ("BACK", "Back", "Level elevation of the edge opposite the front"),
    ("LEFT", "Left", "Level elevation of the board's left edge"),
    ("RIGHT", "Right", "Level elevation of the board's right edge"),
    ("ISOMETRIC", "Isometric", "Three-quarter product view"),
    ("45_DEGREE", "45 Degree", "Lower angle, more edge visibility"),
    ("BOTTOM", "Bottom", "Straight up at the solder side of the board"),
    ("CONNECTOR_CLOSEUP", "Connector Closeup", "Close-up of selected component"),
    ("MACRO", "Macro", "Tight macro view of selected component"),
    ("HERO_ISOMETRIC", "Hero Isometric", "Long-lens commercial three-quarter view"),
    ("HERO_LOW", "Hero Low", "Low commercial product angle"),
    ("PRODUCT_STRAIGHT", "Product Straight", "Clean straight product composition"),
]

CAMERA_CONTROL_MODE_ITEMS: list[tuple[str, str, str]] = [
    ("AUTO_TARGET", "Auto Target", "Keep the camera aimed at the PCB Studio target"),
    ("MANUAL", "Manual", "Unlock the managed target for free camera rotation"),
]

CAMERA_MOVE_STEP_ITEMS: list[tuple[str, str, str]] = [
    ("FINE", "Fine", "Move 1.5% of the PCB size per click"),
    ("NORMAL", "Normal", "Move 5% of the PCB size per click"),
    ("COARSE", "Coarse", "Move 12% of the PCB size per click"),
]

PRODUCT_MOVE_STEP_ITEMS: list[tuple[str, str, str]] = [
    ("FINE", "Fine", "Move the product 1.5% of its size per click"),
    ("NORMAL", "Normal", "Move the product 5% of its size per click"),
    ("COARSE", "Coarse", "Move the product 12% of its size per click"),
]

#: Product translation directions, in world axes.  Left/Right is world X,
#: Forward/Back is world Y (the backdrop sits at +Y), Up/Down is world Z.
PRODUCT_MOVE_ACTION_ITEMS: list[tuple[str, str, str]] = [
    ("LEFT", "Left", "Move the product left along world -X"),
    ("RIGHT", "Right", "Move the product right along world +X"),
    ("FORWARD", "Forward", "Move the product away from the camera along world +Y"),
    ("BACK", "Back", "Move the product toward the camera along world -Y"),
    ("UP", "Up", "Move the product up along world +Z"),
    ("DOWN", "Down", "Move the product down along world -Z"),
    ("RESET", "Reset Position", "Return the product to its original position"),
]

# --- Focus target modes ---
FOCUS_TARGET_ITEMS: list[tuple[str, str, str]] = [
    ("PCB_CENTER", "PCB Center", "Focus on the PCB bounding-box centre"),
    ("SELECTED_OBJECT", "Selected Object", "Focus on the selected PCB object"),
]

# --- Reflection surface presets ---
REFLECTION_SURFACE_ITEMS: list[tuple[str, str, str]] = [
    ("OFF", "Off", "Hide reflection plane"),
    ("SUBTLE", "Subtle", "Soft product-table reflection"),
    ("GLOSSY", "Glossy", "Stronger product reflection"),
    ("SATIN", "Satin", "Controlled commercial floor reflection"),
    ("MIRROR", "Mirror", "Highly reflective floor"),
    ("DARK_GLASS", "Dark Glass", "Dark coated glass floor"),
    ("CUSTOM", "Custom", "Use manual floor controls"),
    ("MATTE", "Matte", "Diffuse non-reflective product floor"),
    ("FROSTED", "Frosted", "Soft frosted reflective floor"),
    ("CONCRETE", "Concrete", "Rough neutral concrete floor"),
    ("ACRYLIC", "Acrylic", "Clean coated acrylic floor"),
    ("METALLIC", "Metallic", "Brushed metallic product floor"),
]

BACKDROP_TYPE_ITEMS: list[tuple[str, str, str]] = [
    ("INFINITY_CYCLORAMA", "Infinity Cyclorama", "Floor-to-wall seamless sweep"),
    ("CURVED_WALL", "Curved Wall", "Curved rear studio wall"),
    ("FLAT_WALL", "Flat Wall", "Simple vertical rear wall"),
    ("FLOOR_BACK_WALL", "Floor + Back Wall", "Separate floor and rear wall surfaces"),
    ("THREE_WALL", "Three-wall Studio", "Floor, rear wall, and both side walls"),
    ("CORNER_STUDIO", "Corner Studio", "Floor, rear wall, and one side wall"),
    ("SEAMLESS_PAPER", "Seamless Paper", "Narrow seamless paper sweep"),
    ("GRADIENT_CYCLORAMA", "Gradient Cyclorama", "Seamless sweep with procedural gradient"),
]

FLOOR_PRESET_ITEMS: list[tuple[str, str, str]] = [
    ("WHITE_ACRYLIC", "White Acrylic", "Glossy clean white floor"),
    ("BLACK_ACRYLIC", "Black Acrylic", "Glossy black acrylic floor"),
    ("PREMIUM_SATIN", "Premium Satin", "Controlled premium satin floor"),
    ("MIRROR_BLACK", "Mirror Black", "Near-mirror black floor"),
    ("MATTE_GRAY", "Matte Gray", "Neutral matte gray floor"),
    ("DARK_GLASS", "Dark Glass", "Dark coated-glass floor"),
]

FLOOR_MODE_ITEMS: list[tuple[str, str, str]] = [
    ("NONE", "No Floor", "Show the product floating without creating a floor"),
    ("STANDARD", "Standard Floor", "Flat product-photography floor"),
    ("SHADOW_CATCHER", "Shadow Catcher", "Cycles-compatible compositing receiver"),
    ("INFINITE", "Infinite Studio", "Seamless curved floor and backdrop"),
    ("CUSTOM", "Custom Floor", "Use a user-selected mesh as the floor"),
]

FLOOR_MATERIAL_ITEMS: list[tuple[str, str, str]] = [
    ("MATTE_WHITE", "Matte White", "Neutral matte white"),
    ("MATTE_BLACK", "Matte Black", "Neutral matte black"),
    ("LIGHT_GRAY", "Light Gray", "Light neutral gray"),
    ("DARK_GRAY", "Dark Gray", "Dark neutral gray"),
    ("WARM_GRAY", "Warm Gray", "Warm neutral gray"),
    ("GLOSSY_WHITE", "Glossy White", "Glossy white product surface"),
    ("GLOSSY_BLACK", "Glossy Black", "Glossy black product surface"),
    ("CONCRETE", "Concrete", "Procedural rough concrete"),
    ("SOFT_STUDIO", "Soft Studio", "Soft low-contrast studio finish"),
    ("METALLIC", "Metallic", "Brushed metallic finish"),
    ("CUSTOM", "Custom", "Use the manual material controls"),
]

FLOOR_STUDIO_PRESET_ITEMS: list[tuple[str, str, str]] = [
    ("CLEAN_WHITE", "Clean White Ecommerce", "Clean matte white catalog floor"),
    ("APPLE_SOFT", "Apple-Style Soft White", "Soft white reflective studio"),
    ("DARK_LUXURY", "Dark Luxury", "Deep glossy luxury floor"),
    ("GRAY_STUDIO", "Gray Product Studio", "Balanced neutral gray floor"),
    ("GLOSSY_PRODUCT", "Glossy Product Floor", "Strong clean reflection"),
    ("SOFT_REFLECTIVE", "Soft Reflective Floor", "Broad subtle reflection"),
    ("MATTE_PRODUCT", "Matte Product Floor", "Non-distracting matte floor"),
    ("FLOATING", "Floating Product / No Floor", "Disable all managed floor geometry"),
]

FLOOR_REFLECTION_PRESET_ITEMS: list[tuple[str, str, str]] = [
    ("MATTE", "Matte", "Disable visible reflections"),
    ("SOFT", "Soft Reflection", "Broad soft reflection"),
    ("PRODUCT", "Product Photography", "Balanced commercial reflection"),
    ("GLOSSY", "Glossy", "Strong glossy reflection"),
    ("MIRROR", "Mirror", "Sharp mirror-like reflection"),
]

INFINITE_STUDIO_PRESET_ITEMS: list[tuple[str, str, str]] = [
    ("WHITE", "White Infinity Studio", "White seamless sweep"),
    ("GRAY", "Gray Infinity Studio", "Gray seamless sweep"),
    ("BLACK", "Black Infinity Studio", "Black seamless sweep"),
    ("SOFT_GRADIENT", "Soft Gradient Studio", "Softly graded seamless sweep"),
]

PEDESTAL_SHAPE_ITEMS: list[tuple[str, str, str]] = [
    ("CIRCULAR", "Circular", "Round product pedestal"),
    ("ROUNDED_SQUARE", "Rounded Square", "Soft-corner square pedestal"),
    ("RECTANGULAR", "Rectangular", "Rectangular product pedestal"),
    ("LOW_PLATFORM", "Low Platform", "Thin low-profile platform"),
]

CUSTOM_LIGHT_TYPE_ITEMS: list[tuple[str, str, str]] = [
    ("AREA", "Area / Softbox", "Large soft area source"),
    ("STRIP", "Strip Light", "Long narrow area source"),
    ("POINT", "Point Light", "Omnidirectional point source"),
    ("SPOT", "Spot Light", "Focused cone source"),
    ("RIM", "Rim Light", "Edge-separation strip source"),
    ("TOP", "Top Light", "Overhead area source"),
]

CUSTOM_LIGHT_PRESET_ITEMS: list[tuple[str, str, str]] = [
    ("LARGE_SOFTBOX", "Large Softbox", "Large soft key source"),
    ("SIDE_STRIP", "Side Strip", "Vertical side highlight"),
    ("TOP_STRIP", "Top Strip", "Long overhead highlight"),
    ("EDGE_RIM", "Edge Rim", "Rear edge-separation light"),
    ("OVERHEAD", "Overhead", "Broad overhead fill"),
    ("ACCENT_SPOT", "Accent Spot", "Focused accent light"),
]

LIGHT_CARD_TYPE_ITEMS: list[tuple[str, str, str]] = [
    ("WHITE", "White Card", "Bright diffuse reflection card"),
    ("BLACK", "Black Card", "Negative-fill reflection card"),
    ("SILVER", "Silver Card", "Strong metallic highlight card"),
]

HDRI_MODE_ITEMS: list[tuple[str, str, str]] = [
    ("OFF", "Off", "Disable HDRI while retaining the physical studio"),
    ("VISIBLE_ENVIRONMENT", "Visible Environment", "Use the HDRI for lighting and camera background"),
    ("LIGHTING_ONLY", "Lighting Only", "Use HDRI lighting/reflections with a hidden HDRI image"),
    ("LIGHTING_BACKGROUND", "Lighting + Background", "Use HDRI lighting behind the physical studio backdrop"),
]

BACKGROUND_LIGHT_MODE_ITEMS: list[tuple[str, str, str]] = [
    ("OFF", "Off", "Disable managed background accents"),
    ("CENTER_GLOW", "Center Glow", "Centered backdrop glow"),
    ("LEFT_GLOW", "Left Glow", "Glow from the left"),
    ("RIGHT_GLOW", "Right Glow", "Glow from the right"),
    ("BOTTOM_GLOW", "Bottom Glow", "Low backdrop glow"),
    ("DUAL_GLOW", "Dual Glow", "Independent left and right accents"),
]

STAGE_TYPE_ITEMS: list[tuple[str, str, str]] = [
    ("NONE", "None", "No floor or pedestal"),
    ("FLOOR", "Floor", "Use the managed reflection floor"),
    ("ROUNDED_PEDESTAL", "Rounded Pedestal", "Rounded product plinth"),
    ("RAISED_PLATFORM", "Raised Platform", "Low raised stage"),
]

PROFESSIONAL_RENDER_ENGINE_ITEMS: list[tuple[str, str, str]] = [
    ("FAST_PREVIEW", "Fast Preview — EEVEE", "Fast still and look-development rendering"),
    ("PROFESSIONAL_FINAL", "Professional Final — Cycles", "Adaptive denoised Cycles still rendering"),
]

CYCLES_QUALITY_ITEMS: list[tuple[str, str, str]] = [
    ("DRAFT", "Draft", "64 adaptive samples"),
    ("STANDARD", "Standard", "256 adaptive samples"),
    ("HIGH", "High", "512 adaptive samples"),
    ("ULTRA", "Ultra", "1024 adaptive samples"),
]

CYCLES_RENDER_DEVICE_ITEMS: list[tuple[str, str, str]] = [
    ("AUTO", "Auto", "Prefer an available Cycles GPU, otherwise use the CPU"),
    ("CPU", "CPU", "Render the professional Cycles still on the CPU"),
    ("GPU", "GPU", "Render the professional Cycles still on a compatible GPU"),
]

CYCLES_GPU_BACKEND_ITEMS: list[tuple[str, str, str]] = [
    ("AUTO", "Auto", "Choose an available Cycles GPU backend automatically"),
    ("CUDA", "CUDA", "NVIDIA CUDA compute backend"),
    ("OPTIX", "OptiX", "NVIDIA OptiX compute backend"),
    ("HIP", "HIP", "AMD HIP compute backend"),
    ("ONEAPI", "oneAPI", "Intel oneAPI compute backend"),
    ("METAL", "Metal", "Apple Metal compute backend"),
]

STILL_FORMAT_ITEMS: list[tuple[str, str, str]] = [
    ("HD_LANDSCAPE", "1080p Landscape", "1920 × 1080"),
    ("INSTAGRAM_SQUARE", "Instagram Square", "1080 × 1080"),
    ("INSTAGRAM_PORTRAIT", "Instagram Portrait 4:5", "1080 × 1350"),
    ("STORY", "Story 9:16", "1080 × 1920"),
    ("PORTRAIT_1600", "1600 × 2000 Portrait", "1600 × 2000"),
    ("FOUR_K", "4K Landscape", "3840 × 2160"),
    ("CUSTOM", "Custom", "Use custom width and height"),
]

PREVIEW_RESOLUTION_ITEMS: list[tuple[str, str, str]] = [
    ("25", "25%", "Fast lighting check"),
    ("50", "50%", "Balanced preview"),
    ("100", "100%", "Full-resolution preview"),
]

MICRO_BEVEL_PRESET_ITEMS: list[tuple[str, str, str]] = [
    ("OFF", "Off", "Disable micro bevel"),
    ("SUBTLE", "Subtle", "Very small edge highlight"),
    ("REALISTIC", "Realistic", "Scale-aware commercial edge softening"),
    ("STRONG", "Strong", "More visible edge treatment"),
    ("CUSTOM", "Custom", "Use manual bevel settings"),
]

PCB_COLOR_PRESET_ITEMS: list[tuple[str, str, str]] = [
    ("GREEN", "Green", "Traditional green solder mask"),
    ("BLACK", "Black", "Premium black solder mask"),
    ("BLUE", "Blue", "Blue solder mask"),
    ("RED", "Red", "Red solder mask"),
    ("PURPLE", "Purple", "Purple solder mask"),
    ("WHITE", "White", "White solder mask"),
    ("CUSTOM", "Custom", "Use custom solder-mask color"),
]

SURFACE_IMPERFECTION_ITEMS: list[tuple[str, str, str]] = [
    ("OFF", "Off", "Perfectly clean managed material"),
    ("CLEAN", "Clean", "Barely visible roughness variation"),
    ("SUBTLE", "Subtle", "Restrained commercial surface variation"),
    ("USED", "Used", "More visible but non-damaged variation"),
]

COLOR_LOOK_ITEMS: list[tuple[str, str, str]] = [
    ("NATURAL", "Natural", "Neutral AgX response"),
    ("PRODUCT", "Product", "Medium-high product contrast"),
    ("HIGH_CONTRAST", "High Contrast", "Strong supported AgX contrast"),
    ("MOODY", "Moody", "Dark restrained contrast"),
]

DOF_PRESET_ITEMS: list[tuple[str, str, str]] = [
    ("OFF", "Off", "Disable depth of field"),
    ("PRODUCT_SHARP", "Product Sharp", "Keep board detail readable"),
    ("SUBTLE", "Subtle", "Gentle product-photo depth of field"),
    ("MACRO", "Macro", "Shallow close-up focus"),
]

# --- Turntable direction ---
ANIMATION_TYPE_ITEMS: list[tuple[str, str, str]] = [
    (
        "PCB_TURNTABLE",
        "PCB Turntable",
        "Keep the camera stationary while the PCB rotates",
    ),
    (
        "CAMERA_ORBIT",
        "Camera Orbit Animation",
        "Keep the PCB stationary while the camera orbits around it",
    ),
    (
        "CINEMATIC_FLYOVER",
        "Cinematic Flyover",
        "Move the camera through space while it tracks the stationary PCB",
    ),
]

FLYOVER_STYLE_ITEMS: list[tuple[str, str, str]] = [
    ("SIDE_SWEEP", "Side Sweep", "Travel from the left side of the PCB to the right"),
    ("FRONT_TO_BACK", "Front-to-Back", "Travel from the front edge toward the rear"),
    ("DIAGONAL_REVEAL", "Diagonal Reveal", "Travel diagonally across the PCB"),
]

FLYOVER_HEIGHT_ITEMS: list[tuple[str, str, str]] = [
    ("LOW", "Low", "Low product-shot elevation"),
    ("MEDIUM", "Medium", "Balanced cinematic elevation"),
    ("HIGH", "High", "High overview elevation"),
]

# --- Animation direction ---
TURNTABLE_DIRECTION_ITEMS: list[tuple[str, str, str]] = [
    ("CLOCKWISE", "Clockwise", "Rotate clockwise"),
    ("COUNTER_CLOCKWISE", "Counter-Clockwise", "Rotate counter-clockwise"),
]

# --- Turntable rotation amount ---
TURNTABLE_ROTATION_ITEMS: list[tuple[str, str, str]] = [
    ("180", "180 Degrees", "Half revolution"),
    ("360", "360 Degrees", "Full revolution (seamless loop)"),
    ("720", "720 Degrees", "Two full revolutions"),
]

# --- Turntable FPS ---
TURNTABLE_FPS_ITEMS: list[tuple[str, str, str]] = [
    ("24", "24 FPS", "Cinematic frame rate"),
    ("30", "30 FPS", "Recommended for product videos"),
    ("60", "60 FPS", "Smooth motion (~2× frames vs 30 FPS)"),
]

# --- Turntable video resolution ---
TURNTABLE_RESOLUTION_ITEMS: list[tuple[str, str, str]] = [
    ("DRAFT", "Draft", "854×480 — fast testing"),
    ("HD_720P", "720p HD", "1280×720 — recommended for laptops"),
    ("FULL_HD_1080P", "1080p Full HD", "1920×1080 — final LinkedIn"),
    ("LINKEDIN_SQUARE", "LinkedIn Square", "1080×1080 — social feed"),
    ("LINKEDIN_PORTRAIT", "LinkedIn Portrait", "1080×1350 — 4∶5 feed"),
]

# --- Turntable motion style ---
TURNTABLE_MOTION_ITEMS: list[tuple[str, str, str]] = [
    ("CONSTANT", "Constant", "Linear constant-speed rotation"),
    ("EASE_IN_OUT", "Ease In/Out", "Smooth acceleration and deceleration"),
]

# --- Animation output format ---
ANIMATION_FORMAT_ITEMS: list[tuple[str, str, str]] = [
    ("MP4", "MP4 Video", "H.264 MPEG-4 video file"),
    ("PNG_SEQUENCE", "PNG Sequence", "Folder of numbered PNG frames"),
]

DEFAULT_OUTPUT_FILENAME: str = "pcb_final_render"
DEFAULT_ANIMATION_FILENAME: str = "pcb_turntable"
