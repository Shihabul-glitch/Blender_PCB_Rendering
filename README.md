# PCB Studio

PCB Studio is a Blender extension for importing, preparing, rendering, and animating PCB models with a simple workflow.

Current release: **PCB Studio v2.3.2 — Final Development / Stabilization Pass**.

The project is aimed at PCB designers, engineers, makers, and developers who want good-looking PCB renders without learning Blender in depth.

## Turntable Demo Video

See a sample PCB Studio turntable animation:

**[▶ Watch the PCB Turntable Demo](docs/videos/pcb_turntable.mp4)**

> Tested environments: **Blender 4.5.11 LTS (primary)** and **Blender 5.2.1 LTS (secondary)** on Windows

![PCB Studio overview](docs/images/09-final-render.png)

## Features

- Import PCB models from **OBJ**
- Automatically detect and use the linked **MTL** material file
- Automatic PCB scene preparation
- Automatic 75 mm Top camera creation and bounds-aware framing
- Manual PCB material assignment
- PCB-oriented material presets
- Studio lighting presets
- Five-light, scale-aware professional product rig with independent controls
- Two light-linked background accent lights and dual-color glow
- HDRI Visible, Lighting Only, and Lighting + Background modes
- Procedural solid, linear, radial, two-tone, and studio-gradient backgrounds
- Smooth infinity-wall cyclorama, satin/glossy/mirror/dark-glass floors, and optional pedestal
- Optional component smoothing and idempotent scale-aware micro bevels
- Shared PCB UV alignment, partial front/back PCB layer textures, trace relief, and physical silkscreen response
- EEVEE lighting previews and adaptive, denoised Cycles professional stills
- Transactional Cycles AUTO/CPU/GPU selection with backend detection and CPU fallback
- Auto Target and Manual still-camera modes with safe managed-constraint switching
- Scale-aware camera movement, pan, dolly, still orbit, roll, and product-position controls
- Fit PCB/selected, aim PCB/selected, target offsets, and save/restore/reset view
- Camera presets including Top, Front Flat, Back, Left, Right, Isometric, 45 Degree, Bottom, Close-up, and Macro
- Depth of Field
- Reflection surface
- Preview rendering
- Final still-image rendering and export
- PCB turntable animation
- Camera-orbit animation with a stationary PCB
- Cinematic Flyover camera animation with a stationary PCB and studio
- 720p and 1080p video rendering
- Animation duration, FPS, direction, and rotation controls

---

## Download

The current tested build is:

[Download PCB Studio V1.3.5](Releases/pcb_studioV1.3.5.zip).

To rebuild from source, run Blender's extension builder from this repository:

```powershell
& 'C:\Program Files\Blender Foundation\Blender 4.5\blender.exe' --background --factory-startup --command extension build --source-dir pcb_studio --output-dir Releases
```

The archive excludes Python caches and backup files.

Do **not** extract the ZIP before installing it in Blender.

---

## Requirements

- Blender **4.5.x LTS** recommended
- Windows is the primary tested platform
- OBJ PCB model
- MTL file when available
- EEVEE is recommended for faster rendering

No external Python packages are required by the Blender extension.

---

# PCB Studio 2.3.2 — Final Stabilization

Version 2.3.2 completes the still-camera workflow while retaining the established
Professional Studio, PCB Realism, PCB Turntable, Camera Orbit Animation, and
Cinematic Flyover systems.

# Professional Studio & PCB Realism

Version 1.0 upgrades the original managed camera/light/background architecture;
it does not replace the animation hierarchy. **Prepare Scene** now creates a
dimension-scaled product studio around the complete PCB bounds:

- `PCB_KEY_LIGHT` is the large neutral key softbox.
- `PCB_FILL_LIGHT` lifts black packages without flattening the image.
- `PCB_RIM_LIGHT` and `PCB_RIM_LIGHT_2` separate component and PCB edges.
- `PCB_TOP_LIGHT` is a rectangular strip for long metal and solder highlights.
- `PCB_BACKGROUND_LIGHT` and `PCB_BACKGROUND_LIGHT_2` illuminate only the
  backdrop through Blender 4.5 light-linking receiver collections.

Product brightness, background color, background glow, HDRI strength, and floor
color are independent. A blue or amber background therefore does not require
blue or amber product lighting.

The original preset identifiers remain supported for saved scenes. Additional
one-click looks include Clean White Product, Apple-style Soft Studio, Premium
Black, Dramatic Edge, Metallic Highlight, PCB Macro, Commercial Catalog,
Cinematic Blue, and Warm Luxury.

## Custom Studio Lights and Reflection Cards

The **Lighting** panel can add managed softboxes, strips, point lights, spots,
rims, and top lights under `PCB_CUSTOM_LIGHT_*` names. Each light has independent
enable, power, color or temperature, size, position, rotation, aiming, and spot
controls. Six starting presets cover common softbox, strip, rim, overhead, and
accent arrangements. White, black, and silver cards add controlled reflections
without modifying user-created lights or objects.

## Background, Floor, Pedestal, and Shadows

The **Studio** panel provides eight bounds-aware backdrop shapes, twelve wall
looks, ten floor types, six floor presets, four pedestal shapes, and accessible
shadow controls. Studio geometry scales from the complete PCB bounds. Auto
Center, Fit, Hide, Show, Lock, and Reset operate only on PCB Studio-managed
visual objects.

## Product Photography Floor System

The **Studio > Floor / Stage** controls now offer Standard, Infinite Studio,
Shadow Catcher, Custom, and No Floor modes. Simple controls provide floor presets;
Advanced controls expose geometry, materials, reflections, and grounding.
The infinite floor uses a connected, smooth curved wall. Floor brightness,
rotation, offsets, and reflection presets remain stable when lighting changes.

Select a mesh for Custom Floor. Switching away or resetting the studio restores
its original first material slot and visibility settings. Ground Product moves
the product vertically; Reset Ground restores its saved position. Auto Ground
also responds to floor geometry and gap changes.

Native shadow catching requires Cycles. Transparent Background is restored when
disabled, when leaving Shadow Catcher, or when resetting the studio. Shadow
strength and softness use the studio lighting; arbitrary shadow tint and separate
contact-shadow density controls are not exposed. Cast Shadows is a Cycles ray
visibility control, not a switch for receiving shadows.

## HDRI Lighting Only

Load an HDR or EXR, choose **Lighting Only**, and rotate it to move reflections
across shields, pins, connectors, and gold contacts. Blender's Light Path node
separates camera rays from lighting/reflection rays, so the HDRI contributes
illumination while the camera sees the physical cyclorama or managed world
color. Manual product lights remain available at the same time.

## PCB Realism

The optional PCB Realism panel provides angle-preserving smoothing and one
managed `PCB_STUDIO_MICRO_BEVEL` modifier per selected component. The bevel
width scales from each object's bounds, is clamped against thin geometry, and
can be removed without applying or destructively changing the mesh.

For a board surface, **Setup PCB UV Mapping** creates a shared top-down UV layer
with rotation, scale, and offset. **Create PCB Surface** accepts any partial set
of front/back copper, solder-mask, and silkscreen images. Copper and solder mask
use different physical shaders, trace relief is a subtle Bump node rather than
displaced geometry, silkscreen has its own response and optional relief, and
side faces receive an FR4-like edge material.

## Professional Still Rendering

Use **Render Lighting Preview** for a 25%, 50%, or 100% EEVEE check. Use
**Render Professional Still** for Cycles Draft (64), Standard (256), High (512),
or Ultra (1024) adaptive samples with denoising. Choose AUTO, CPU, or GPU under
**Cycles Render Device**. GPU mode supports Blender-exposed CUDA, OptiX, HIP,
oneAPI, and Metal backends; AUTO prefers a usable GPU and otherwise uses CPU.
**Detect / Refresh Devices** lists devices without retaining the detection
changes. Every professional still saves and restores the scene device, compute
backend, enabled device flags, and temporary discovery entries in a `finally`
transaction—even when configuration or rendering fails. PCB Studio never saves
Blender user preferences.

## Recommended Premium Dark Recipe

| Control | Recommended value |
|---|---|
| Backdrop | Studio Gradient, graphite `#020307` to `#07080C` |
| Background glow | Cool blue, power 220, size 1.45 |
| HDRI | Studio HDRI, Lighting Only, strength 0.3-0.8 |
| Key | 5600 K, power 760, size 1.45, azimuth 42 degrees, elevation 48 degrees |
| Fill | 30% strength |
| Left / Right rim | 540 / 500 |
| Top strip | 440, neutral white |
| Floor | Satin, near-black, roughness 0.34 |
| Camera | Hero Isometric, 75-85 mm |
| DOF | Product Sharp |
| Final | Cycles High |

---

# Installation

## 1. Open Blender

Start Blender.

![Blender startup](docs/images/01-blender-start.png)

Click **General** to open the normal 3D workspace.

![Blender default scene](docs/images/02-default-scene.png)

The default scene normally contains a Cube, Camera, and Light.

You may delete the default cube by selecting it and pressing `X`, but this is optional.

## 2. Install PCB Studio

In Blender, open:

`Edit → Preferences → Get Extensions`

Open the menu in the upper-right corner and choose:

`Install from Disk`

Select:

`pcb_studioV1.3.5.zip`

Enable **PCB Studio** if Blender asks you to enable it.

## 3. Open PCB Studio

Return to the 3D Viewport.

Move the mouse over the viewport and press:

`N`

The right sidebar will appear.

Select the **PCB Studio** tab.

![PCB Studio sidebar](docs/images/03-pcb-studio-panel.png)

Before a PCB is imported, several controls are disabled. This is normal.

---

# Preparing Your PCB File

## Altium Designer

The recommended workflow is to export the PCB as:

```text
MyBoard.obj
MyBoard.mtl
```

Keep both files in the same folder:

```text
PCB_Export/
├── MyBoard.obj
└── MyBoard.mtl
```

You only need to select the `.obj` file in PCB Studio.

The OBJ normally references the material library internally, for example:

```text
mtllib MyBoard.mtl
```

PCB Studio imports the OBJ and Blender loads the linked MTL materials automatically.

You do **not** need to select the MTL file separately.

## KiCad / STEP Users

PCB Studio currently expects an OBJ file.

If your PCB workflow gives you a STEP file instead, convert the STEP model to OBJ first using a tool such as:

- FreeCAD
- Fusion 360
- another CAD or mesh-conversion tool

A typical workflow is:

```text
KiCad / STEP
     ↓
FreeCAD / Fusion 360
     ↓
OBJ
     ↓
PCB Studio
```

Material and object separation can vary depending on the conversion tool.

---

# Basic Workflow

```text
Import PCB
    ↓
Prepare Scene
    ↓
Assign Materials
    ↓
Choose Lighting / HDRI
    ↓
Choose Background
    ↓
Choose Camera
    ↓
Preview Render
    ↓
Final Still Render
      or
Turntable Animation
```

---

# Importing the PCB

Click:

**Select and Import OBJ**

Choose the PCB `.obj` file.

PCB Studio will:

1. Read the OBJ file.
2. Detect the referenced MTL file when available.
3. Import the PCB geometry.
4. Load the available MTL materials.
5. Organize the imported PCB objects.
6. Report the number of imported objects and materials.

![PCB imported](docs/images/04-pcb-imported.png)

After a successful import, the remaining PCB Studio tools become available.

---

# Prepare the Scene

Click **Prepare Scene...** to choose the setup before applying it:

- **Center PCB at Origin** moves the complete assembly to the origin. Disable
  it to preserve the imported placement and orientation.
- **Set Up Camera** creates or reframes the managed camera. Choose Top, Front
  Flat, Back, Left, Right, Isometric, 45 Degree, Hero Isometric, Hero Low, or
  Product Straight, plus a framing margin. Fitting uses the chosen output aspect
  ratio.
- **Set Up Lighting and Background** applies the selected complete studio look.
  Disable it to preserve your existing lights, background, floor, and world.
- **Render Setup** offers Keep Current Settings, EEVEE Preview, and Cycles Still.
  Cycles uses the quality selected in the Render panel without changing GPU
  preferences.
- **Output Size** offers Keep Current Resolution, 720p, 1080p, square, portrait,
  4K, and custom dimensions. Explicit size choices also update the still-render
  output settings.

The first preparation defaults to a centered PCB, Top camera, studio
lighting, and a 720p EEVEE setup. Reopening the dialog after preparation defaults
to preserving existing placement, camera, studio, engine, and resolution;
missing camera or studio elements can still be created. Cancel closes the dialog
without changing the scene. Preparation is undoable, and repeated centering
keeps the assembly at the origin.

Reset an active PCB turntable, camera orbit, or flyover before preparing again.
Moving the PCB or changing output aspect while keeping the camera can change
its framing; the dialog shows a reminder for those combinations.

After confirming the options, use **Render Lighting Preview** to check the result.

If Blender looks temporarily unresponsive while rendering, wait for the render to finish. Rendering time depends on PCB complexity, render resolution, lighting, HDRI size, and hardware.

---

# Assigning Materials

Material assignment should be done in **Object Mode**.

Look at the mode selector in the upper-left corner of the 3D Viewport.

It should say:

`Object Mode`

If Blender is in Edit Mode, press:

`Tab`

to return to Object Mode.

Select a PCB object.

PCB Studio should show something similar to:

```text
Active object: ComponentBody.116
Selected PCB objects: 1
```

![Material assignment](docs/images/05-materials.png)

Choose a material preset and adjust the available controls.

Typical controls include:

- **Base Color** — visible material color
- **Metallic** — `0` for non-metals, approximately `1` for metals
- **Roughness** — lower values are shinier, higher values are more matte
- **Coat Weight** — additional coated/glossy appearance where supported

Possible PCB Studio material presets include solder mask, plastic, ceramic, copper, gold, tin/silver, and silkscreen materials.

Click:

**Create or Update Material**

then:

**Assign to Selected Objects**

To assign the same material to several PCB components, hold `Shift` while selecting multiple objects.

## Previewing Materials

Move the mouse over the 3D Viewport and press:

`Z`

Choose:

**Material Preview**

For a more accurate result using the configured lights and camera, use:

**Render Preview**

---

# Lighting & Environment

PCB Studio includes one-click studio lighting presets.

Typical presets include:

### Bright Studio

Clean, bright, low-contrast lighting for documentation and catalog-style images.

### Dark Studio

More dramatic lighting with stronger edge highlights and contrast.

### Product Shot

A balanced general-purpose commercial product look.

### PCB Showcase

Designed to emphasize PCB surfaces, metallic pads, connectors, component edges, and silkscreen.

![Lighting and HDRI controls](docs/images/06-lighting-hdri.png)

Depending on the build, you can also adjust:

- Lighting Intensity
- Shadow Softness

---

# HDRI Lighting

PCB Studio can use HDRI environment lighting.

Supported formats include:

```text
.hdr
.exr
```

PCB Studio does not download HDRIs for you. Get free CC0 ones from
[Poly Haven](https://polyhaven.com/hdris) and save them locally.

For lower-end GPUs, start with **1K or 2K HDRIs**.

Open:

`Sidebar → PCB Studio → 5. Lighting → HDRI Environment`

Pick a **Mode**, click **Load HDRI**, choose your `.hdr` or `.exr`, then adjust
Rotation and Environment Lighting Strength and press **Apply**.

| Mode | Effect |
|---|---|
| Off | No HDRI; the managed studio lighting alone |
| Visible Environment | HDRI lights the scene and is the camera background |
| Lighting Only | HDRI lights the scene; the camera sees the flat World Color |
| Lighting + Background | HDRI lights the scene and stays visible but dimmed behind the studio backdrop |

Then adjust:

- **HDRI Rotation** — changes the direction of the environment and reflections
- **HDRI Brightness** — changes environment intensity

HDRI rotation is useful for controlling reflections on metallic pads, pins, connectors, and solder-mask surfaces.

---

# Background Presets

PCB Studio provides several background options, depending on the current build.

Typical presets include:

- White
- Black
- Dark Gray
- Blue Gradient

The background can be changed independently from the lighting.

For example:

```text
PCB Showcase Lighting
+
Dark Gray Background
```

or:

```text
Bright Studio
+
White Background
```

---

# Camera & Composition

**Prepare Scene** starts with a product-oriented **Top** view: the managed
camera sits on the board's face normal, looks straight at the component side,
uses a 75 mm lens, and fits the complete PCB with a modest margin. Existing
Isometric and other presets remain available.

## Board Orientation

Camera presets are authored for a board lying flat with its component side up
and its front edge toward the viewer. CAD exports do not agree on which way that
is, so the **Board Orientation** block at the top of the Camera panel decides how
the board's own frame is found:

- **Automatic** guesses the facing axis from the thinnest dimension of the
  product bounds and reports what it found. It cannot know which edge is the
  front, and a board with tall connectors can defeat the guess entirely.
- **Declare Faces** lets you state it. Pick the world axis the **Top Face**
  (component side) points along and the axis the **Front Edge** faces -- where a
  viewer stands to read the silkscreen the right way up. **From View** next to
  each reads the angle you are currently orbited to and snaps it to the nearest
  world axis, so you can simply look at a face and claim it.

The two axes must be perpendicular; choosing a front edge that lies along the
top face is corrected rather than stored. Declaring an orientation only changes
where the camera goes -- your geometry is never rotated.

![Camera and composition controls](docs/images/07-camera-composition.png)

## Auto Target and Manual Modes

**Auto Target** keeps local camera -Z aimed at `PCB_CAMERA_TARGET`. PCB Studio
owns one constraint named `PCB Studio Targeting`; switching modes only mutes or
enables that constraint. It does not delete or change user-authored camera
constraints. Use **Manual** to unlock free camera rotation, and **Auto Target**
to re-enable managed aiming.

All panel movement buttons are still-camera operations. They do not insert
keyframes, including when Blender auto-key is enabled:

- **Move Camera**: Left, Right, Up, and Down in camera-local axes.
- **Forward / Back** and **Dolly In / Out**: translate along the viewing axis;
  dolly does not change focal length.
- **Pan**: moves the camera and target together, retaining the composition.
- **Still Orbit**: rotates the camera around the target at constant distance.
- **Roll**: rotates around the view axis; Reset Roll returns to zero.

Fine, Normal, and Coarse steps scale from the current PCB dimensions, so the
buttons remain useful for both small modules and large boards.

## Framing, Aiming, and Product Controls

- **Fit PCB** frames the full board while preserving viewing direction and lens.
- **Fit Selected** frames exactly one selected PCB mesh component.
- **Aim at PCB** and **Aim at Selected** change the target without changing
  camera position.
- Live Target X/Y/Z values offset the target from the PCB center; **Reset
  Target** returns all offsets to zero.
- Advanced Azimuth, Elevation, Distance, and Roll values update the product view
  live.
- **Save View** stores transform, target, lens, and control mode in the scene;
  **Restore View** recalls them. **Reset Camera** restores Top, 75 mm,
  Auto Target, and fits the PCB.

Still-camera controls are disabled while a **Camera Orbit Animation** or
**Cinematic Flyover** rig is active. Use **Reset Animation** before adjusting a
still composition.

## Camera Presets

Every preset below is aimed in the board's own frame, so it shows the face it
names whichever way the board was exported. See **Board Orientation** above.

| Preset | Purpose |
|---|---|
| Top | Default 75 mm view straight down at the component side |
| Front Flat | 75 mm level elevation of the board's front edge |
| Back | 75 mm elevation of the edge opposite the front |
| Left / Right | 75 mm elevations of the side edges |
| Isometric | Three-quarter product view |
| 45 Degree | Lower angle with more edge visibility |
| Bottom | Straight up at the solder side |
| Connector Closeup | Long-lens framing of one selected PCB component |
| Macro | Tight framing of one selected PCB component |
| Hero Isometric | 80 mm commercial three-quarter view |
| Hero Low | 85 mm low product angle |
| Product Straight | 75 mm clean straight-on composition |

Connector Closeup and Macro require exactly one selected PCB mesh in Object
Mode.

# Camera Focal Length

Focal length changes the look of the shot.

Typical ranges:

```text
24–35 mm   Wide perspective
50–75 mm   General product photography
85–120 mm  Close-up / macro style
```

After changing focal length, click **Apply Camera Settings** to update the lens
and fit the PCB with the current Fit Margin.

---

# Depth of Field

Depth of Field can keep one part of the PCB sharp while blurring the foreground or background.

Possible focus targets include:

- PCB Center
- Selected Object

Lower F-Stop values create stronger blur.

Examples:

```text
f/1.8 – f/2.8   Strong blur
f/4 – f/5.6     Moderate product-photo blur
f/8 and higher  More of the PCB remains sharp
```

For full-board renders, moderate values are usually easier to use.

---

# Reflection Surface

PCB Studio can create a managed reflection surface beneath the PCB.

Typical options include:

- Off
- Subtle
- Glossy

**Subtle** creates a softer product-table reflection.

**Glossy** creates a stronger reflection.

The reflection surface is separate from the PCB geometry.

---

# Rendering a Still Image

Before the final render:

```text
Check Materials
    ↓
Choose Lighting / HDRI
    ↓
Choose Background
    ↓
Choose Camera
    ↓
Render Preview
```

When the preview looks correct, select your output settings and run the final render.

PCB Studio can render and save the image automatically.

![Final PCB render](docs/images/09-final-render.png)

---

# PCB Turntable, Camera Orbit Animation, and Cinematic Flyover

PCB Studio provides three product-animation styles:

- **PCB Turntable** keeps the camera stationary while the PCB rotates.
- **Camera Orbit Animation** creates a temporary keyed rig and keeps the PCB
  stationary while the camera circles it.
- **Cinematic Flyover** keeps the PCB stationary while the camera physically
  travels across a dimension-scaled product-shot path and tracks the PCB centre.

Choose the required style from **Animation Type** before clicking
**Setup Animation**.

This is distinct from the **Still Orbit (No Keyframes)** buttons in Camera &
Composition. Still Orbit makes one immediate composition adjustment; Camera
Orbit Animation creates timeline keyframes. While an orbit/flyover rig exists,
still-camera controls remain locked until **Reset Animation** restores the saved
camera and target state.

The intended behavior is:

```text
Camera stays still
Lighting stays still
Background stays still
PCB rotates
```

This creates a commercial product-turntable effect.

In Camera Orbit mode, PCB Studio creates a temporary pivot at the calculated
PCB centre and an offset mount at the camera's current position. Rotating the
pivot physically carries the mounted camera around a circular path while the
camera continues to point at the PCB. The PCB, lights, background, HDRI, and
reflection surfaces remain stationary.

![Turntable controls](docs/images/08-turntable.png)

Recommended full-board camera presets:

- Isometric
- 45 Degree

## Cinematic Flyover

Choose **Cinematic Flyover** to move only the managed render camera. The PCB,
lights, background, HDRI/world, and reflection plane remain stationary.

**Flyover Style** offers Side Sweep, Front-to-Back, and Diagonal Reveal.
**Flyover Height** offers Low, Medium, and High elevations. All offsets and
heights are derived from the current PCB world-space bounding box, so the same
presets scale to different board sizes and positions. Diagonal Reveal, Medium
height, 6 seconds, 30 FPS, and Ease In/Out are recommended for a product shot.

The camera uses the existing `PCB_CAMERA_TARGET` at the calculated PCB centre.
**Reset Animation** removes the temporary `PCB_CAMERA_FLYOVER_ROOT`, removes
only a tracking constraint created by the flyover (if any), and restores the
camera matrix, parent, parent inverse, lens, target, and prior timeline range.
Setting up another animation mode first performs the same managed cleanup.

Flyover testing checklist: verify changing camera XYZ at start/25%/50%/75%/end,
a stationary `PCB_MODEL_ROOT` and studio, centred tracking, distinct styles and
heights, correct duration × FPS, eased motion, repeated setup, mode switching,
exact reset, a midpoint test frame, and a short Draft render.

---

# Animation Settings

## Direction

Choose:

- Clockwise
- Counter-Clockwise

## Rotation

Typical choices:

- 180°
- 360°
- 720°

For normal product videos, use:

`360°`

## Duration

Choose the animation length in seconds.

Examples:

- 4 seconds
- 6 seconds
- 8 seconds

## Frame Rate

Typical options include:

- 24 FPS
- 30 FPS
- 60 FPS

For LinkedIn and YouTube, **30 FPS** is a good default.

---

# Recommended Video Settings

## Fast Preview

```text
Resolution: 1280 × 720
FPS: 30
Duration: 4 seconds
Rotation: 360°
Engine: EEVEE
```

Use this first to verify that the animation, camera, materials, and lighting are correct.

## Final LinkedIn / YouTube Video

```text
Resolution: 1920 × 1080
FPS: 30
Duration: 6 seconds
Rotation: 360°
Output: MP4 / H.264
```

This provides a good balance between quality, file size, and render time.

---

# Preview Animation

Click:

**Setup Animation**

then:

**Preview Animation**

This lets you inspect the rotation before rendering every frame.

If automatic playback does not start, press:

`Spacebar`

to preview the timeline animation.

---

# Render Test Frame

Before rendering the complete video, use:

**Render Test Frame**

This renders only one frame.

Check:

- Camera
- Lighting
- Materials
- HDRI
- Reflection
- Depth of Field
- Background

If the test frame looks correct, continue to the full animation.

---

# Render Animation

Select the required video quality, output directory, and filename.

Then click:

**Render Animation**

For slower computers, start with:

```text
720p
30 FPS
4 seconds
```

before trying 1080p.

Full animation rendering can take much longer than still-image rendering.

Blender may appear temporarily unresponsive during a long render. This does not necessarily mean Blender has crashed.

---

# Performance Tips

If rendering is slow:

- Use EEVEE.
- Start with 720p.
- Use 30 FPS instead of 60 FPS.
- Use 1K or 2K HDRIs while testing.
- Render one test frame before a full animation.
- Start with a 4-second turntable.
- Close unnecessary applications while rendering.
- Move to 1080p only after the scene has been verified.

---

# Troubleshooting

## PCB Studio tab is not visible

Make sure the extension is enabled.

Move the mouse over the 3D Viewport and press:

`N`

Then select the **PCB Studio** tab.

## MTL is not detected

Keep the OBJ and MTL files in the same folder.

Check that the OBJ references the correct MTL filename.

## Material assignment does not work

Make sure Blender is in **Object Mode**.

Select a valid PCB mesh object before assigning the material.

## Camera view looks wrong

Click **Reset Camera** for the 75 mm Top baseline, then use **Fit PCB**.
For a free viewport-derived angle, switch to **Manual** before adjusting camera
rotation. Use **Auto Target** when the camera should remain aimed at its target.

If the panel says still controls are locked, click **Reset Animation** first.

## HDRI is slow

Use a 1K or 2K HDRI instead of a very high-resolution HDRI.

## Animation is very slow

Start with:

```text
1280 × 720
30 FPS
4 seconds
EEVEE
```

and only move to 1080p after the animation is working correctly.

---

# Known Limitations

PCB Studio is still an experimental project.

Current limitations may include:

- CAD programs can export OBJ geometry differently.
- Some imported MTL materials may need manual adjustment.
- KiCad STEP workflows currently require conversion to OBJ.
- Automatic component classification is not included.
- Material assignment and identifying the board object for PCB layer textures remain manual.
- PCB layer masks are expected to share the same image canvas and alignment.
- Top-down UV projection assumes the board surface is aligned to local XY.
- Automatic component targets assume the prepared PCB convention (+Z is top);
  unusual component orientations may be better handled with Selected Faces.
- Current View projection needs an open 3D Viewport. Selected Faces and all six
  directional projections are independent of editor context.
- Backend availability is determined by the running Blender build, operating
  system, driver, and hardware; unavailable GPU requests can fall back to CPU.
- Background-light isolation uses Blender 4.5 light linking; colored Cycles
  bounce from a lit physical backdrop can still contribute subtly to the scene.
- Vignette is exposed as a reserved finishing control but is not injected into
  a custom compositor graph; existing user compositor nodes are always preserved.
- Very complex PCB models can take longer to import and render.
- High-resolution HDRIs use more GPU memory.
- 1080p animation can take significant time on older GPUs.
- Extreme closeups and unusually shaped boards may still benefit from Manual
  mode and a custom Fit Margin.

Always keep a copy of your original PCB export.

---

# Tested Environment

```text
Blender: 4.5.11 LTS
Operating System: Windows
Renderer: EEVEE Next and Cycles
Primary Input: Altium Designer OBJ + MTL
```

Testing on other operating systems, Blender versions, and PCB export workflows is welcome.

---

# Feedback and Bug Reports

If you encounter a problem, open a GitHub Issue and include:

- PCB Studio version
- Blender version
- Operating system
- What you were doing when the problem occurred
- Screenshot of the problem
- Blender system-console traceback when available

Please do not upload proprietary PCB design files unless you have permission to share them.

---

# Project Status

PCB Studio is an experimental project under active development.

The goal is to make attractive PCB product renders and animations accessible to engineers and PCB designers without requiring deep Blender experience.

Feedback, testing, bug reports, and suggestions are welcome.

Product orientation controls are documented in
[Product Presentation](pcb_studio/PRODUCT_PRESENTATION.md), including animation
safety, object classification, and tested limitations.
