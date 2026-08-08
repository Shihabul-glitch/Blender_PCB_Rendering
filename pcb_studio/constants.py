"""Shared constants for the PCB Studio Blender extension."""

EXTENSION_NAME: str = "PCB Studio"
EXTENSION_VERSION: str = "0.7.0"
EXTENSION_ID: str = "pcb_studio"

SIDEBAR_CATEGORY: str = "PCB Studio"
PANEL_LABEL: str = "PCB Studio"
PANEL_ID: str = "PCBSTUDIO_PT_main_panel"

OPERATOR_ID_SYSTEM_CHECK: str = "pcbstudio.system_check"
OPERATOR_ID_IMPORT_OBJ: str = "pcbstudio.import_obj"
OPERATOR_ID_PREPARE_SCENE: str = "pcbstudio.prepare_scene"
OPERATOR_ID_RENDER_PREVIEW: str = "pcbstudio.render_preview"
OPERATOR_ID_ASSIGN_MATERIAL: str = "pcbstudio.assign_material"
OPERATOR_ID_PREVIEW_MATERIALS: str = "pcbstudio.preview_materials"
OPERATOR_ID_RENDER_FINAL: str = "pcbstudio.render_final"
OPERATOR_ID_APPLY_LIGHTING: str = "pcbstudio.apply_lighting_preset"
OPERATOR_ID_APPLY_BACKGROUND: str = "pcbstudio.apply_background"
OPERATOR_ID_LOAD_HDRI: str = "pcbstudio.load_hdri"
OPERATOR_ID_APPLY_HDRI: str = "pcbstudio.apply_hdri"
OPERATOR_ID_REMOVE_HDRI: str = "pcbstudio.remove_hdri"
OPERATOR_ID_APPLY_CAMERA_PRESET: str = "pcbstudio.apply_camera_preset"
OPERATOR_ID_APPLY_CAMERA_SETTINGS: str = "pcbstudio.apply_camera_settings"
OPERATOR_ID_ZOOM_TO_FIT: str = "pcbstudio.zoom_to_fit"
OPERATOR_ID_APPLY_REFLECTION: str = "pcbstudio.apply_reflection_plane"
OPERATOR_ID_SETUP_TURNTABLE: str = "pcbstudio.setup_turntable"
OPERATOR_ID_RESET_TURNTABLE: str = "pcbstudio.reset_turntable"
OPERATOR_ID_PREVIEW_TURNTABLE: str = "pcbstudio.preview_turntable"
OPERATOR_ID_RENDER_TEST_FRAME: str = "pcbstudio.render_test_frame"
OPERATOR_ID_RENDER_TURNTABLE: str = "pcbstudio.render_turntable"

COLLECTION_NAME: str = "PCB_MODEL"
RENDER_SETUP_COLLECTION: str = "PCB_RENDER_SETUP"

ROOT_EMPTY_NAME: str = "PCB_MODEL_ROOT"
CAMERA_NAME: str = "PCB_RENDER_CAMERA"
CAMERA_TARGET_NAME: str = "PCB_CAMERA_TARGET"
DOF_TARGET_NAME: str = "PCB_DOF_TARGET"
REFLECTION_PLANE_NAME: str = "PCB_REFLECTION_PLANE"
REFLECTION_MATERIAL_NAME: str = "PCB_REFLECTION_MATERIAL"
KEY_LIGHT_NAME: str = "PCB_KEY_LIGHT"
FILL_LIGHT_NAME: str = "PCB_FILL_LIGHT"
RIM_LIGHT_NAME: str = "PCB_RIM_LIGHT"
RIM_LIGHT_2_NAME: str = "PCB_RIM_LIGHT_2"
TOP_LIGHT_NAME: str = "PCB_TOP_LIGHT"
BACKGROUND_NAME: str = "PCB_BACKGROUND"
BACKGROUND_MATERIAL_NAME: str = "PCB_BACKGROUND_MATERIAL"
PCB_STUDIO_WORLD_NAME: str = "PCB_STUDIO_WORLD"

MATERIAL_NAME_PREFIX: str = "PCBSTUDIO_MAT_"

PROP_GROUP_ID: str = "PCBSTUDIO_PG_import_state"
PROP_SCENE_ATTR: str = "pcb_studio_import"

# --- Material preset enum items ---
MATERIAL_PRESET_ITEMS: list[tuple[str, str, str]] = [
    ("SOLDER_MASK_GREEN", "Green Solder Mask", "Green solder mask material"),
    ("SOLDER_MASK_BLUE", "Blue Solder Mask", "Blue solder mask material"),
    ("SOLDER_MASK_RED", "Red Solder Mask", "Red solder mask material"),
    ("SOLDER_MASK_BLACK", "Black Solder Mask", "Black solder mask material"),
    ("FR4", "FR4 Substrate", "FR4 substrate material"),
    ("PLASTIC_BLACK", "Black Plastic", "Black plastic material"),
    ("PLASTIC_DARK_GRAY", "Dark Gray Plastic", "Dark gray plastic material"),
    ("PLASTIC_LIGHT_GRAY", "Light Gray Plastic", "Light gray plastic material"),
    ("CERAMIC_WHITE", "White Ceramic", "White ceramic material"),
    ("COPPER", "Copper", "Copper metal material"),
    ("GOLD", "Gold", "Gold metal material"),
    ("TIN", "Tin or Silver", "Tin or silver metal material"),
    ("SILKSCREEN_WHITE", "White Silkscreen", "White silkscreen material"),
    ("SILKSCREEN_BLACK", "Black Silkscreen", "Black silkscreen material"),
    ("CUSTOM", "Custom", "User-defined custom material"),
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
]

# --- Background presets ---
BACKGROUND_PRESET_ITEMS: list[tuple[str, str, str]] = [
    ("WHITE", "White", "Neutral off-white background"),
    ("BLACK", "Black", "Near-black background"),
    ("DARK_GRAY", "Dark Gray", "Neutral dark charcoal gray"),
    ("BLUE_GRADIENT", "Blue Gradient", "Procedural dark-blue gradient"),
]

# --- Camera presets ---
CAMERA_PRESET_ITEMS: list[tuple[str, str, str]] = [
    ("TOP", "Top", "Straight product/documentation view"),
    ("ISOMETRIC", "Isometric", "Three-quarter product view"),
    ("45_DEGREE", "45 Degree", "Lower angle, more edge visibility"),
    ("BOTTOM", "Bottom", "Underside of the PCB"),
    ("CONNECTOR_CLOSEUP", "Connector Closeup", "Close-up of selected component"),
    ("MACRO", "Macro", "Tight macro view of selected component"),
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
]

# --- Turntable direction ---
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