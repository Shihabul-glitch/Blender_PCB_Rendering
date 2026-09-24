# DECISIONS

Things that look wrong or accidental but are deliberate. Review this file before
changing defaults, error handling, or shared helpers.

## Errors are message-string prefixes, not exceptions

`utils/` functions return a status string; failure is encoded as the prefix
`"Cannot"`, `"No "`, or `"Unknown"`, which operators test to choose
`ERROR`/`CANCELLED` vs `INFO`/`FINISHED`.

It's fragile — a wording change can flip success and failure — but it is used
consistently across ~40 operators and lets one generic operator base class handle
every managed-studio action. **Don't half-migrate it to exceptions.** If it ever
changes, it changes everywhere in one pass, with tests updated together.

Corollary: never embed a callee's message inside a success sentence
(`f"{preset} applied. {result}"`) without first checking `result` for a failure
prefix — that swallows the failure. This bug has been fixed three times.

## Test the failure prefix, never whitelist a success string

`update_professional_studio` has four possible returns: the legacy success
sentence, the adaptive studio's own success sentence, and two `Cannot ...`
failures. `operators/professional_render.py` and `operators/professional_studio.py`
used to check `result.startswith("Professional studio updated")` and treat
everything else as fatal, so with any non-LEGACY adaptive studio active, Render
Professional Still and Render Lighting Preview reported the *success* message
`Studio updated; product, camera and lights preserved.` as an ERROR and
cancelled. Both now use `startswith(("Cannot", "No ", "Unknown"))`.

Whitelisting one sentence is the mirror image of the swallowed-failure bug in
this file: it turns every unrecognised success into a failure, and it breaks the
moment a callee gains a second success path. **Always test for the failure
prefix.** `blender_professional_studio_smoke_test.py` now renders once per
adaptive studio type to keep that crossing covered.

## Floor placement is product-relative and re-seeded

`floor_height` is a **fraction of `bounds.max_dimension`**, not absolute Blender
units. It used to be added as absolute units in `floor.py` while the legacy path
in `studio.py` scaled it, so the default -0.005 was sub-millimetre on a real
board and the floor z-fought through the underside of the PCB.

The floor's Z is still cached in `pcbstudio_floor_base_z`, because Ground Product
moves the product down onto the floor and a floor that chased the product would
never settle. But `floor._floor_base_z` now re-seeds that cache when it is at or
above the product's lowest point, or more than one product-length below it.
Caching it forever was the bug: Prepare Scene re-centres the assembly, so a floor
built for an earlier position stayed put and sliced through the new board.
`ground_product` uses the same scaling, so grounding and placement agree.

## The default light rig is three-point on purpose

Prepare Scene creates nine light objects but only **key, fill and one rim** emit.
The second rim, the overhead strip and both front fills exist, are one click
away, and ship disabled. Previously every `*_enabled` defaulted True, which put
four broad sources (key, fill, front-left, front-right) inside a ~90 degree arc —
flat, cross-lit and shadowless, the opposite of the "Premium Dark" name.

Objects are created regardless of enable state, so the nine-name existence
assertions in `blender_professional_studio_smoke_test.py` still hold. Presets now
state their own rig explicitly rather than inheriting, so a preset can opt into
more lights (`DRAMATIC_RIM` keeps both rims, `MACRO_DETAIL` keeps the top strip)
without every other preset silently inheriting them.

## EEVEE shadow quality is set from `update_professional_studio`

The product shadow was invisible in the viewport while rendering correctly in
Cycles. `configure_eevee_preview` set no shadow settings at all and wrote only
`taa_render_samples`, which does nothing for viewport shading; the one function
that enabled EEVEE shadows pinned them at their floor and was reachable only from
a Prepare Scene run whose engine stage defaults to KEEP on every re-run.

`render.configure_eevee_shadows` now owns those settings and is called from
`configure_render_settings`, `configure_eevee_preview` **and**
`update_professional_studio`. The last one is deliberate: it is the only path
that runs often enough to keep the viewport correct. It writes global scene state
outside a render operator, which the rest of the codebase avoids, but it touches
only EEVEE shadow quality, is idempotent, and is inert under Cycles.

Key and fill emitters were also shrunk below the product's size (`key_size` 1.35
to 0.55). An area light larger than the product casts almost no shadow; Cycles
resolved it with hundreds of samples, EEVEE got one shadow ray and showed
nothing. **Don't raise the default emitter sizes above ~1.0 without checking the
viewport shadow.**

## Board orientation is declared, not guessed

Camera presets are authored in a canonical board frame -- board flat, face
normal +Z, canonical -Y toward a viewer standing at the front edge -- and
`geometry.board_direction` maps that into world space.

How that frame is found is the user's choice, in `board_orientation_mode`:

- **AUTO** keeps the original heuristic in `geometry.board_normal_axis`: the
  thinnest dimension of the product bounds is the face normal, with a near-cubic
  box falling back to +Z. It is still the default, so every existing scene opens
  unchanged, and there is a test asserting a flat board yields the world axes.
- **MANUAL** reads `board_top_axis` and `board_front_axis` through
  `utils.board_orientation.declared_board_frame`. This exists because the guess
  can only ever find a *face*: it has no way to know which edge is the front, so
  the roll and the left/right side of every angled preset were arbitrary, and a
  small board with tall connectors defeated the guess outright.

The two declared axes must be perpendicular. The property update callbacks snap
an invalid pair, and `declared_board_frame` returns `None` for one anyway, so a
degenerate basis can never reach the camera. **Declaring an orientation never
moves geometry** -- it only changes where a preset puts the camera.

`CameraPreset.board_relative` marks which presets take part. Face-referenced
shots -- Top, Bottom, the four edge elevations, Isometric, 45 Degree and the
close-ups -- are board relative. The hero and product shots are **not**: they are
composed against the studio floor and the world up axis, so they stay in world
axes whatever the export.

Preset names describe their directions. `TOP` looks down the board's face normal
and `FRONT_FLAT` is a level elevation of the declared front edge, with `BACK`,
`LEFT` and `RIGHT` alongside it. Before this, `FRONT_FLAT` pointed at the face --
a top view under a front name -- and `TOP` ignored the board entirely.

## Camera roll and framing are computed, not inherited

`composition._aim_camera_at` takes an `up_hint` and builds the rotation from an
explicit orthonormal basis: the board's face normal for an elevation or angled
shot, the board's in-plane up when looking straight at the face (where the
normal is degenerate), and world +Z for the floor-relative studio shots.
DAMPED_TRACK rotates minimally about the aim axis, so that roll survives the
constraint.

It must be given a settled transform. `apply_camera_preset` calls
`view_layer.update()` after moving the camera and before aiming, because
`matrix_world` is otherwise still the *previous* shot's -- the roll was
previously derived from the old position and then patched up by the constraint,
which is how presets ended up tilted by tens of degrees.

`geometry.required_camera_distance` frames by projecting the eight bounding-box
corners onto the camera's own axes, and `geometry.camera_field_of_view` supplies
the field of view for the **render** aspect rather than the sensor's own shape.
Both matter: framing from the world X/Y extents mis-sizes any edge-on view of a
thin board, and `Camera.angle_x`/`angle_y` describe the sensor alone, so a 16:9
or portrait output frames the wrong axis. `fit_camera_to_bounds`,
`apply_camera_preset` and `setup_scene._fit_prepared_camera` all go through
these two, which is why the fit is now exact and identical at every aspect.

`_fit_prepared_camera` used `Object.camera_fit_coords` before. That can return a
location off the camera-to-target ray, which the managed track constraint then
aims away from, silently undoing the fit -- it clipped the board on a 1920x1080
output. Moving along the ray keeps the aim and the framing consistent.

## Backdrop grain is surface detail, not a compositor effect

`backdrop_grain` drives a Noise -> Bump -> Normal chain plus a Map Range into
Roughness on the backdrop material, built by `studio._apply_backdrop_grain`.
It exists because a perfectly smooth sweep does not read as a physical surface;
real seamless paper has a fine tooth, which is the grain users like watching
resolve in a Cycles render.

It is deliberately **not** a compositor film-grain pass: baked into the surface
it survives any sample count, renders identically in EEVEE and Cycles, and
leaves the product itself clean. Only Noise, Bump and Map Range are used, all
stable across 4.5 and 5.2. The graph is rebuilt from scratch on every material
update, so node counts stay stable -- a test asserts that.

## Adaptive studio defaults to LEGACY

`studio_properties.PCBSTUDIO_PG_environment.studio_type` defaults to `'LEGACY'`.

The adaptive studio (cyclorama/tabletop/acrylic/pedestal shells in
`utils/studio_environment.py` + `ui/studio_environment.py`) is a newer, working,
tested alternative to the floor/backdrop system — but it is undocumented in the
README and was never finished as a product-facing feature. It previously
defaulted to `'CYCLO'`, which silently replaced the entire documented Studio &
Background panel for every new scene.

`enabled()` requires `active AND studio_type != 'LEGACY'`, and the panel's
`draw()` returns early for non-LEGACY types, so this default is the only thing
keeping the documented UI visible. **Don't change it** without also documenting
the adaptive studio and updating the README.

## `SNAPSHOT` is kept as a legacy-data marker

`utils/product.py:SNAPSHOT` ("pcbstudio_product_snapshot") is written by nothing
now — the product turntable that created it was removed. It stays because guards
in `validate_static`, `center_pivot`, `operators/setup_scene.py` and
`utils/animation._product_presentation_active()` still refuse to act on objects
carrying it, so a `.blend` from an older build can't be silently corrupted.

`utils/animation.py` matches the string literal rather than importing the
constant; that's intentional decoupling of the legacy camera subsystem. Guard
messages name the property literally so users can delete it by hand — that is
their only recovery path now that Clear Turntable is gone.

## Panel order via `bl_order`, not registration order

Sidebar order used to fall out of the order classes were registered, which put
the product panel at the bottom because it registers from a different tuple.
Splicing the tuples together would force `ui/main_panel.py` to import
`ui/product.py` and spread the ordering contract across three files.

`bl_order` is Blender's native mechanism, keeps ordering on the same line as the
label it must agree with, and is immune to registration-list edits. Keep each
panel's `bl_order` in sync with its numeric label prefix.

## Managed objects are tagged, never name-matched

Every generated object carries `pcbstudio_managed` / `pcbstudio_role` /
`pcbstudio_floor` / `pcbstudio_environment_role`. Resets and helpers act only on
tagged objects so user geometry always survives. The one deliberate exception is
adopting the add-on's own known legacy reflection plane in `floor._managed()`.

**Never** delete or transform an object because its name matches a pattern.

## Cycles device changes are transactional

`professional_render` saves the scene device, compute backend, enabled-device
flags and temporary discovery entries, and restores them in `finally` even when
rendering fails. PCB Studio deliberately **never writes Blender user
preferences** — a render must not permanently change the user's setup.

## Idempotent update functions

`update_professional_studio`, `update_floor_system` and friends create-or-update;
calling them repeatedly must not duplicate objects or materials. Tests assert
exact object and material counts across repeated updates. Preserve this when
adding studio elements.

## Removed features stay removed

Select Board / Select Parts / Select Components / Product Turntable / Product
Object Options were removed on purpose to reduce UI confusion, after evaluating
their dependencies. See FEATURES.md. `role` and `exclude_rotation` survive as
properties because `protected()` and the studio bounds code read them.

## Cyclorama sweeps are welded strips with analytic normals

Every floor-to-wall sweep (`studio._update_backdrop_geometry`,
`floor._infinite_geometry`, `studio_environment.sweep`) is built as a **welded**
quad strip — two vertices per profile point, shared by the faces on both sides —
and then given explicit per-vertex normals via
`normals_split_custom_set_from_vertices`.

Both halves are load-bearing. Smooth shading averages normals across *shared*
vertices, so an unwelded strip renders faceted no matter what `use_smooth` says;
that was a real bug, since the backdrop emitted four fresh vertices per quad.
The custom normals are what keep the long flat floor and the rear wall exactly
planar instead of letting the smoothing bend their shading into the curve.

Do **not** "fix" faceting here with Subdivision Surface or Bevel modifiers. The
strip is already exact at its vertices, a Subsurf would shrink the profile away
from the requested radius, and any modifier that regenerates geometry discards
the custom normals. Raise `constants.CYCLORAMA_CURVE_SEGMENTS` instead — it only
affects the silhouette, and the shading is already continuous.

Cyclorama-shaped backdrops use **one** material across floor, curve and wall: a
second floor material draws a hard colour line exactly at the start of the curve,
which is the thing a cyclorama exists to avoid. The flat shapes (Flat Wall, Three
Wall, Corner Studio) keep the two-material split, because their corners are meant
to read as corners.

## Material edits are copy-on-write; assignment stays shared

`materials.ensure_editable` copies a material, and swaps the copy onto just the
objects being edited, when the material is either a hand-built shader network or
**shared with an object outside the edit target**. Anything already exclusive is
edited in place, so the ordinary case creates no duplicate.

This exists because an OBJ import creates one datablock per `usemtl` name shared
across many layer objects (this is why recolouring "PCB top paste" used to
recolour its neighbours), and because the live-preview sliders used to write to
`props.current_material_name` — a scene-global string unrelated to the selection,
so dragging a colour edited whatever material was last created or picked.
`materials.live_preview_target` now resolves the active object's own material.

**Copies happen only in operators.** `mat.copy()` is reachable from
`update_active_material` and `make_material_unique`, which are
`bl_options = {'REGISTER', 'UNDO'}` operators - Blender's sanctioned place to
create or remove a datablock, and the only place the copy lands in the undo
stack. The live-preview property update callback deliberately creates nothing:
`materials.live_preview_target` resolves a material only when writing to it is
safe (exclusive to the active object, and not a hand-built shader network) and
returns `None` otherwise. `None` is the normal "don't write" signal, not a
failure, so it carries no status-message prefix; the Materials panel shows the
sharing box with a Make Unique button instead. An update callback runs inside
RNA property assignment, can fire during file load, undo and animation
evaluation, and gets no undo push, so creating an ID there risks a stray
datablock that Ctrl+Z cannot remove. **Don't move copying back into a callback**,
and don't reach for `bpy.app.timers` to sneak around this - the deferred copy
would still land outside the undo stack.

Consequence worth knowing: with a shared material selected, the colour sliders
do nothing until Make Unique is clicked. Editing a shared preset for all of its
users at once is still done with *Create or Update Material*.

**Assignment is deliberately still shared.** `assign_material`,
`assign_active_material` and `create_or_update_material` keep handing one
datablock to many objects — that is the point of those buttons, it is what
`Select Same Material` walks, and per-object copies would mean one datablock per
component. Independence is enforced at *edit* time, not at assign time.

## Not decided

Whether the adaptive studio is finished-and-documented or retired. Until that's
resolved it stays opt-in.
