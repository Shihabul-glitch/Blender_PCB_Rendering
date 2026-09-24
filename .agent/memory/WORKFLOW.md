# WORKFLOW

## Safe modification loop

1. **Read before cutting.** Grep the symbol across `pcb_studio/` *and* `tests/`.
   Helpers with turntable-ish or product-ish names are often shared with the
   studio or Prepare Scene.
2. Make the edit in `utils/` (logic) — `operators/` and `ui/` should only need
   wiring changes.
3. Compile: `python -m py_compile $(find pcb_studio -name "*.py")`.
4. Run the affected test(s), then the whole suite.
5. Re-run anything API-shaped on Blender 5.2 as well.
6. Rebuild the ZIP and run the packaged-registration test if you touched
   registration, the manifest, or module layout.
7. Add a one-line entry to `LOG.md`.

## Testing

```bash
cd c:/Users/USER/Documents/Python_1/PCB_Studio
find . -name "__pycache__" -type d -exec rm -rf {} +      # ALWAYS do this first

B45="/c/Program Files/Blender Foundation/Blender 4.5/blender.exe"
B52="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"

"$B45" --background --factory-startup --python tests/blender_product_smoke_test.py
```

Every test is standalone and prints a `*_PASSED` sentinel (or a "passed"
sentence) on success; failures raise. There is no test runner — loop over the
files. Note tests **do not** set a non-zero exit code by default, so grep the
output for the sentinel rather than trusting `$?`.

Suite map:

| Test | Covers |
|---|---|
| `blender_package_registration_smoke_test.py` | Built ZIP registers/unregisters. Needs a ZIP path after `--`. |
| `blender_material_ui_smoke_test.py` | All material presets, panel draw, duplicate-class/idname checks |
| `blender_product_smoke_test.py` | Orientation, stationary studio, save/reload. Exports `cube`/`close`/`reject` used by other tests — don't break its top half. |
| `blender_product_geometry_test.py` | Board detection, hierarchy, auto-frame |
| `blender_product_undo_test.py` | Real undo/redo stack |
| `blender_studio_environment_smoke_test.py` | Adaptive studio, all types, idempotency |
| `blender_prepare_scene_smoke_test.py` | Prepare Scene option matrix |
| `blender_professional_studio_smoke_test.py` | Studio + realism + actual renders |
| `blender_floor_system_smoke_test.py` | Floor modes, grounding, presets |
| `blender_camera_controls_smoke_test.py` | Still-camera moves |
| `blender_animation_smoke_test.py` | Orbit + flyover setup/reset |
| `blender_cycles_devices_smoke_test.py` | Device selection and restore |

Useful ad-hoc check: register the extension in background Blender and call each
panel's `draw()` with a fake layout that asserts `hasattr(data, propname)` — this
catches missing properties without a GUI. `blender_material_ui_smoke_test.py`
already does this; copy its stub.

## Rebuild the installable ZIP

```bash
"$B45" --background --factory-startup --command extension build \
    --source-dir pcb_studio --output-dir Releases
```

Builds `Releases/pcb_studio-<version>.zip`, excluding `__pycache__`, `*.pyc`,
`*.bak`, `.git`. Version comes from `blender_manifest.toml` (keep it in sync with
`constants.EXTENSION_VERSION` — a test asserts the value).

## Reloading in the Blender GUI

Background scripts are the fast loop and cover almost everything. For real GUI
checks (panel order, layout, widget spacing) install the built ZIP via
`Edit → Preferences → Get Extensions → Install from Disk`, and **restart
Blender** after reinstalling — hot-reloading an extension leaves stale classes
registered.

## Common mistakes

- **Stale `.pyc`.** Deleted symbols keep resolving from `__pycache__` until you
  clear it. First suspect for "impossible" test results.
- **Forgetting the message-prefix contract.** A new failure return that doesn't
  start with `Cannot` / `No ` / `Unknown` gets reported as success.
- **Concatenating a status message** into a success sentence — swallows the
  failure prefix. Check the prefix first, return the raw message on failure.
- **Registration order.** A child panel registered before its `bl_parent_id`
  fails. Add new classes to `_REGISTERED_CLASSES` only; unregister is derived.
- **Panel order.** Set `bl_order`, and keep it consistent with the label's number
  prefix. Reordering the tuples alone no longer changes anything.
- **Non-idempotent updates.** Re-running an update must not duplicate objects or
  materials; the studio test asserts exact object/material counts.
- **Leaving global state changed.** Restore render engine/device/film settings in
  `finally`.
- **Touching `utils/animation.py`** when you meant product orientation — that
  module is the separate legacy camera turntable/orbit/flyover subsystem.
