# ARCHITECTURE

## Folders

```
PCB_Studio/                 repo root (git, dev docs — not shipped)
├── pcb_studio/             the extension package (this is what ships)
│   ├── __init__.py         registration: _REGISTERED_CLASSES, register/unregister
│   ├── constants.py        operator IDs, managed object names, enum item lists
│   ├── properties.py       PCBSTUDIO_PG_import_state — the main scene state (~1000 lines)
│   ├── studio_properties.py    adaptive-studio state (opt-in subsystem)
│   ├── product_properties.py   product orientation state (scene + per-object)
│   ├── operators/          thin bpy.types.Operator wrappers
│   ├── utils/              all real logic
│   └── ui/                 panels only
├── tests/                  standalone Blender scripts + VALIDATION.md
└── Releases/               built ZIPs
```

## Layering

**`ui/` → `operators/` → `utils/`**, one direction only.

- `ui/` reads properties and draws buttons. No logic, no `utils` mutation.
- `operators/` validate context, call one `utils` function, store its returned
  message on a status property, report INFO/ERROR. Most wrap `execute()` in
  try/except that prints a traceback and reports a generic failure.
- `utils/` holds everything real and is import-safe from anywhere. Modules do not
  import `operators/` or `ui/`.

Cross-module calls inside `utils/` are common and are usually done as **local
imports inside the function** to avoid circular imports (e.g. `floor.py` importing
`studio_environment` inside `update_floor_system`). Follow that pattern.

## Communication

- **State** lives in `PropertyGroup`s on `bpy.types.Scene`:
  - `scene.pcb_studio_import` (`PROP_SCENE_ATTR`) — the big one: import, material,
    lighting, floor, camera, render, animation settings, plus `show_*` UI toggles.
  - `scene.pcb_studio_environment` — adaptive studio.
  - `scene.pcb_studio_product` / `Object.pcb_studio_product` — product orientation.
- **Results** flow back as **status strings**, not exceptions. Failure is signalled
  by the message prefix `"Cannot"` / `"No "` / `"Unknown"`. See DECISIONS.md.
- **Identity** of generated objects is by custom-property tag, never by name
  matching: `pcbstudio_managed`, `pcbstudio_role`, `pcbstudio_floor`,
  `pcbstudio_environment_role`. Resets only remove tagged objects.
- Some properties carry `update=` callbacks that live-apply changes; batch edits
  suppress them with the `scene["pcbstudio_batch_update"]` flag (context manager
  `studio_environment.batch`).

## Key modules

| Module | Role |
|---|---|
| `utils/studio.py` | The professional studio: lights, backdrop, cards, pedestal, presets. `update_professional_studio` is the central idempotent rebuild, and `_update_backdrop_geometry` owns the backdrop **mesh** (`render.setup_background_plane` only creates the object, its collection, position and wall material). |
| `utils/floor.py` | Floor/stage system: standard, infinite, shadow catcher, custom. |
| `utils/studio_environment.py` | Alternative "adaptive studio" (cyclorama/tabletop/etc). Opt-in. |
| `utils/lighting.py`, `environment.py` | Legacy lighting/background presets, HDRI world. |
| `utils/camera.py`, `camera_controls.py`, `composition.py` | Camera creation, still-camera moves, presets/framing. |
| `utils/animation.py` | Legacy camera subsystem: PCB turntable, camera orbit, cinematic flyover. |
| `utils/product.py` | Product orientation around `PCB_MODEL_ROOT`. |
| `utils/materials.py`, `material_nodes.py`, `material_compat.py` | Presets, shader graphs, cross-version input-name fallbacks. |
| `utils/professional_render.py`, `cycles_devices.py`, `render.py` | Render config + transactional GPU/CPU device selection. |
| `utils/geometry.py`, `collections.py`, `obj_mtl.py` | Bounds math, `PCB_MODEL`/`PCB_RENDER_SETUP` collections, MTL detection. |

## Scene objects it creates

`PCB_MODEL` (imported board) and `PCB_RENDER_SETUP` (everything generated).
Named singletons from `constants.py`: `PCB_RENDER_CAMERA`, `PCB_CAMERA_TARGET`,
`PCB_KEY_LIGHT` / `FILL` / `RIM` / `RIM_2` / `TOP` / `BACKGROUND_LIGHT(_2)`,
`PCB_BACKGROUND`, `PCB_REFLECTION_PLANE`, `PCB_STAGE_PEDESTAL`,
`PCB_MODEL_ROOT`, plus `PCB_CUSTOM_LIGHT_*` / `PCB_STUDIO_CARD_*` prefixes.

## UI architecture

One root panel `PCBSTUDIO_PT_main_panel` (sidebar category "PCB Studio") with
nine numbered children; `Depth of Field` is nested under Camera Options.

**Order is set by `bl_order` on each child panel** (1–9), *not* registration
order — so `PANEL_CLASSES` and `PRODUCT_PANEL_CLASSES` can register separately in
`__init__.py` while still interleaving correctly in the sidebar. Keep each
panel's `bl_order` and its numeric label prefix in sync.

Collapsible sections inside a panel use the `_disclosure()` helper backed by
`show_*` boolean properties.

## Rendering pipeline

1. `_validate_scene` checks geometry + camera, then calls
   `update_professional_studio` so the studio matches the UI.
2. `snapshot_render_settings` saves scene render state.
3. EEVEE preview: `configure_eevee_preview`. Cycles still: `configure_cycles_final`
   plus `configure_requested_cycles_device` (AUTO/CPU/GPU with backend detection
   and CPU fallback).
4. Render, then **`finally`** restores render settings and Cycles device state —
   including temporary discovery entries. User preferences are never written.
