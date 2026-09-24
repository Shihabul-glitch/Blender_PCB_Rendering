# FEATURES

## Shipped

Sidebar order matches this list (panels 1–9).

- [x] **1. Import & Setup** — OBJ import with automatic MTL detection; guided
      Prepare Scene dialog (centering, camera preset, studio look, engine, output
      size), undoable, safe to re-run.
- [x] **2. Materials** — 49 PCB-oriented presets in a responsive grid; manual
      base colour/metallic/roughness/coat/IOR/emission/alpha; texture map slots;
      micro-surface detail; material tools (pick, update, assign, select-same,
      make-unique); live preview toggle.
- [x] **3. PCB Realism** — angle-preserving smoothing; idempotent scale-aware
      micro bevels; shared top-down UV mapping; layered PCB surface material from
      partial front/back copper / solder-mask / silkscreen images; trace relief.
- [x] **4. Studio & Background** — 8 backdrop shapes, 12 wall looks, 10 floor
      types (standard / infinite / shadow catcher / custom / none, also offered in
      the Prepare Scene dialog) with Simple and
      Advanced modes, 6 floor presets, backdrop grain, 4 pedestal shapes,
      reflection cards,
      grounding (Ground Product / Reset Ground / Auto Ground), composition helpers.
- [x] **5. Lighting** — scale-aware rig of key, fill, 2 rims and a top strip,
      shipping three-point (key + fill + one rim); the rest are one click away
      plus 2 light-linked background lights and dual-colour glow; per-light solo;
      custom managed lights from 6 presets; complete one-click studio presets;
      HDRI in Visible / Lighting Only / Lighting + Background modes, in an
      expanded-by-default section with an .hdr/.exr-filtered file picker.
      HDRI files are supplied by the user; there is no online browser.
- [x] **6. Camera Options** — presets follow the board's own facing axis, so a
      board exported standing is framed face-on rather than edge-on;
      Auto Target vs Manual with one managed constraint;
      move/pan/dolly/still-orbit/roll at scale-aware steps; fit and aim (PCB or
      selected); target offsets; save/restore/reset view; 9 presets; Depth of
      Field sub-panel.
- [x] **7. Product Orientation** — rotate the whole product around
      `PCB_MODEL_ROOT` (Front/Back/Left/Right/Top/Bottom, ±90° steps, 180°, custom
      angles) while studio, camera and lights stay stationary; move the whole
      product on world axes (left/right, forward/back, up/down) at Fine/Normal/
      Coarse steps plus a typed Position and Reset; board override;
      board-normal axis; centre pivot; optional auto-frame.
- [x] **8. Render** — EEVEE lighting preview at 25/50/100%; Cycles professional
      still at Draft/Standard/High/Ultra adaptive samples with denoising;
      transactional AUTO/CPU/GPU device selection with backend detection and CPU
      fallback; colour look/exposure; output path handling.
- [x] **9. Animation** — PCB turntable, camera orbit, and cinematic flyover;
      direction/rotation/duration/FPS/motion style; preview, test frame, 720p and
      1080p video render; exact reset that restores camera and timeline state.

## Removed (deliberately — do not reintroduce)

- [x] "Select Board" / "Select Parts" header buttons — duplicated normal
      viewport selection.
- [x] "Select Components" (assembly-aware selector) — same reason.
- [x] "Product Turntable" — overlapped the mature camera/PCB turntable in the
      Animation panel. Backend, properties and tests removed too.
- [x] "Product Object Options" panel — `role` and `exclude_rotation` still exist
      and are honoured in code, but have no UI.

## Planned / open

- [ ] Decide the future of the adaptive studio subsystem: finish and document it,
      or retire it. It currently works but is opt-in and unmentioned in the README.
- [ ] Compositor vignette control is exposed but not wired into a node graph.
- [ ] Automatic component classification (board vs component) is heuristic only.
- [ ] KiCad/STEP import without an external conversion step.

## Known limitations

- OBJ only; STEP/KiCad users must convert first. Imported MTL materials often
  need manual adjustment.
- Material assignment and identifying the board object for layer textures are
  manual.
- PCB layer masks must share one image canvas and alignment; top-down UV
  projection assumes the board lies in local XY.
- Background-light isolation relies on Blender 4.5 light linking; Cycles bounce
  from a lit backdrop can still tint the scene slightly.
- GPU backend availability depends on the running Blender build, driver and
  hardware; unavailable GPU requests fall back to CPU.
- A `.blend` saved by an older build with an *active* product turntable is
  blocked by the orientation/prepare guards until its
  `pcbstudio_product_snapshot` custom property is deleted by hand. The guard
  messages name the property.
