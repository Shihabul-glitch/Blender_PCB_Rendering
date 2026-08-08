# PCB Studio

Blender extension for automating PCB rendering from Altium Designer exports (OBJ/MTL).

---

## Current Milestone

**Milestone 7 — Render Presets + Turntable Animation (v0.7.0)**

Turntable video rendering with clockwise/counter-clockwise rotation, multiple duration and FPS options, video quality presets (Draft through LinkedIn Portrait), MP4 and PNG sequence output, test frame rendering, and seamless-loop 360° product videos suitable for LinkedIn and social media.

---

## Supported Blender Version

| Requirement | Value |
|---|---|
| Minimum Blender | **4.5.0** |
| Tested on | **4.5.11** |
| Extension format | `blender_manifest.toml` |

---

## Complete Workflow

### 1. Import PCB
Open panel → **Select and Import OBJ**.

### 2. Prepare Scene
Click **Prepare Scene** — centres the PCB, creates camera/lights/background, configures EEVEE.

### 3. Assign Materials
Select PCB objects, choose a preset, click **Create or Update Material**, then **Assign to Selected Objects**.

### 4. Lighting & Environment

**Studio Mode** — managed area lights with 4 presets: Bright Studio, Dark Studio, Product Shot, PCB Showcase. Controls: Lighting Intensity (0.25–2.0), Shadow Softness (0.5–2.0).

**Background Presets**: White, Black, Dark Gray, Blue Gradient (procedural).

**HDRI Mode** — load HDR/EXR files, control rotation (−180° to +180°) and brightness (0–5.0).

### 5. Camera & Composition

**Camera Presets** — reposition the managed camera:

| Preset | Description |
|---|---|
| Top | Straight product/documentation view |
| Isometric | Three-quarter product view (default) |
| 45 Degree | Lower angle, more edge visibility |
| Bottom | Underside of the PCB |
| Connector Closeup | Close-up of one selected PCB component |
| Macro | Tight macro view of one selected component |

**Connector Closeup** and **Macro** require selecting exactly one PCB mesh object in Object Mode before applying.

**Zoom to Fit PCB** — moves the camera to frame the entire PCB while preserving the current camera direction and focal length.

**Focal Length** — adjustable 20–200 mm (default 50 mm). Click **Apply Camera Settings** to set the lens and re-frame.

**Depth of Field** — enable/disable, choose focus target (PCB Center or Selected Object), adjust F-Stop (1.4–22, default 5.6). Click **Apply Camera Settings** to apply.

**Reflection Surface** — managed product-photography floor plane placed below the PCB:

| Preset | Description |
|---|---|
| Off | Hide reflection plane |
| Subtle | Soft product-table reflection (roughness ~0.35) |
| Glossy | Stronger product reflection (roughness ~0.1) |

The reflection plane is independent from the Background Preset and complements it.

### 6. Preview & Final Render
**Render Preview** for quick checks. **Render Final PNG** with Low Power/Standard/High quality presets.

### 7. Animation & Video

Enable **Enable Turntable** to show animation settings.

#### Turntable Settings

| Setting | Options | Default |
|---|---|---|
| Direction | Clockwise, Counter-Clockwise | Clockwise |
| Rotation | 180°, 360°, 720° | 360° |
| Duration | 2–30 seconds | 6 seconds |
| Frame Rate | 24, 30, 60 FPS | 30 FPS |
| Video Quality | Draft, 720p HD, 1080p Full HD, LinkedIn Square, LinkedIn Portrait | 720p HD |
| Motion | Constant, Ease In/Out | Constant |
| Start Angle | 0°–360° | 0° |
| Output Format | MP4 Video, PNG Sequence | MP4 Video |

#### Turntable Principle

Only `PCB_MODEL_ROOT` rotates around its local Z axis. The camera, lights, background, HDRI, and reflection plane all remain stationary. This creates a standard commercial product-turntable effect.

The PCB normal is assumed to be **+Z axis** after Prepare Scene centres the board.

#### Video Quality Presets

| Preset | Resolution | EEVEE Samples | Purpose |
|---|---|---|---|
| Draft | 854×480 | 16 | Fast motion/composition check |
| 720p HD | 1280×720 | 32 | Default for lower-end hardware |
| 1080p Full HD | 1920×1080 | 64 | Final LinkedIn video |
| LinkedIn Square | 1080×1080 | 64 | Social feed posts (1∶1) |
| LinkedIn Portrait | 1080×1350 | 64 | Larger feed presence (4∶5) |

#### Recommended Settings

**For laptops / lower-end GPUs (e.g., NVIDIA MX110):**
- 720p HD, 30 FPS, 4–6 seconds, 360°, Constant motion

**Final LinkedIn video:**
- 1080p Full HD, 30 FPS, 6 seconds, 360°, Clockwise, Constant motion

#### Seamless Loop

Default 360° turntable keyframes are placed so the hypothetical frame after the last rendered frame equals the starting orientation, creating a smooth loop when the video repeats. The duplicate frame is not rendered.

#### Steps

1. Configure turntable settings
2. Click **Setup Turntable**
3. Click **Preview Turntable** (or press Spacebar)
4. Click **Render Test Frame** to verify lighting/framing
5. Click **Render Turntable Video** for the final output
6. Click **Reset Turntable** to restore the PCB

#### Important Notes

- Full 1080p animation rendering takes considerably longer than a single still render
- Blender may appear unresponsive during animation rendering — this is normal
- Press **Esc** to cancel an active render (when supported)
- For full 360° turntables, Isometric or 45 Degree camera is recommended
- Connector Closeup/Macro cameras may not keep the component in frame during rotation
- PCB Center DOF focus is recommended for full turntable videos

#### Output Handling

MP4 videos are saved with H.264 codec in MPEG-4 container. PNG sequences are saved to a dedicated folder (`filename_frames`). Existing output is protected unless **Overwrite Existing** is enabled.

---

## Managed Objects

| Name | Type |
|---|---|
| PCB_KEY_LIGHT | Area Light |
| PCB_FILL_LIGHT | Area Light |
| PCB_RIM_LIGHT | Area Light |
| PCB_RIM_LIGHT_2 | Area Light |
| PCB_TOP_LIGHT | Area Light |
| PCB_BACKGROUND | Mesh Plane |
| PCB_BACKGROUND_MATERIAL | Material |
| PCB_STUDIO_WORLD | World |
| PCB_RENDER_CAMERA | Camera |
| PCB_CAMERA_TARGET | Empty |
| PCB_DOF_TARGET | Empty |
| PCB_REFLECTION_PLANE | Mesh Plane |
| PCB_REFLECTION_MATERIAL | Material |
| PCB_RENDER_SETUP | Collection |
| PCB_MODEL_ROOT | Empty (animated for turntable) |

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Extension not visible | ZIP root must contain blender_manifest.toml |
| Panel missing | Press N in 3D Viewport |
| Button error | Window → Toggle System Console |
| Camera not found | Run Prepare Scene first |
| Connector Closeup/Macro fails | Select exactly one PCB mesh object |
| Reflection plane not visible | Ensure it is not hidden; check PCB_RENDER_SETUP collection |
| DOF not working | Enable Depth of Field and click Apply Camera Settings |
| Turntable not rotating | Click Setup Turntable first |
| Setup Turntable fails | Run Prepare Scene first (creates PCB_MODEL_ROOT) |
| MP4 output fails | Try PNG Sequence instead; verify FFmpeg is available |
| PCB wobbles during turntable | Ensure Prepare Scene was run to centre the board |
| Blender appears frozen | Normal during animation rendering; monitor system console |

---

## ZIP Packaging

From the parent directory of `pcb_studio/`:

**PowerShell:**
```powershell
Compress-Archive -Path pcb_studio\* -DestinationPath pcb_studio_v0.7.0.zip
```

**Command Prompt:**
```cmd
tar -a -cf pcb_studio_v0.7.0.zip -C pcb_studio .
```

Install via **Edit → Preferences → Extensions → Install from Disk**.

---

## Manual Testing Checklist

### Existing features (regression)

| # | Test | Expected |
|---|---|---|
| 1 | System Check | Reports Blender version |
| 2 | OBJ/MTL import | PCB objects + materials imported |
| 3 | Manual materials | Presets work, assign to objects |
| 4 | Lighting presets | Bright Studio, Dark Studio, Product Shot, PCB Showcase |
| 5 | HDRI | Load, rotate, brightness, remove |
| 6 | Camera presets | Top, Isometric, 45°, Bottom, Connector Closeup, Macro |
| 7 | DOF | Enable, PCB Center/Selected Object focus, F-Stop |
| 8 | Reflection plane | Off, Subtle, Glossy |
| 9 | Still preview render | No errors |
| 10 | Final still PNG render | Saved correctly |

### Turntable

| # | Test | Expected |
|---|---|---|
| 11 | Setup Turntable | Keyframes created; "Turntable set up" message |
| 12 | 360° animation | PCB rotates full revolution |
| 13 | Clockwise | PCB rotates clockwise |
| 14 | Counter-clockwise | PCB rotates counter-clockwise |
| 15 | 180° rotation | Half revolution |
| 16 | 720° rotation | Two revolutions |
| 17 | Duration changes frame count | 6s × 30fps = 180 frames displayed |
| 18 | 24 FPS | Timeline and render use 24 FPS |
| 19 | 30 FPS | Timeline and render use 30 FPS |
| 20 | 60 FPS | Timeline and render use 60 FPS |
| 21 | Constant motion | Linear interpolation, constant speed |
| 22 | Ease In/Out | Bezier interpolation, smooth accel/decel |
| 23 | Start angle | Turbo starts from chosen angle |
| 24 | Seamless loop | Duplicate 360° frame not rendered |
| 25 | PCB rotates around centre | No wobbling |
| 26 | Camera stationary | Only PCB_ROOT moves |
| 27 | Lighting stationary | Lights do not rotate |
| 28 | Reflection plane stationary | Plane does not rotate |
| 29 | Background stationary | Background does not rotate |
| 30 | HDRI unchanged | HDRI not modified |

### Output

| # | Test | Expected |
|---|---|---|
| 31 | Draft resolution | 854×480 |
| 32 | 720p | 1280×720 |
| 33 | 1080p | 1920×1080 |
| 34 | LinkedIn Square | 1080×1080 |
| 35 | LinkedIn Portrait | 1080×1350 |
| 36 | Preview Turntable | Playback starts or safe message shown |
| 37 | Render Test Frame | One frame rendered |
| 38 | MP4 animation renders | H.264 MP4 file created |
| 39 | MP4 uses correct resolution/FPS | Matches settings |
| 40 | PNG sequence renders | Folder with frame_0001.png etc. |
| 41 | Output files saved to chosen location | Files exist |
| 42 | Existing files protected | Error if overwrite disabled |
| 43 | Reset Turntable | PCB restored, timeline reset |
| 44 | Repeated Setup | No duplicate keyframes/errors |
| 45 | Unrelated animation untouched | User animations preserved |
| 46 | No Blender traceback | Clean console |
| 47 | Disable + re-enable extension | No errors |
| 48 | Reinstall extension | Works cleanly |

---

*PCB Studio v0.7.0 — Render Presets + Turntable Animation*