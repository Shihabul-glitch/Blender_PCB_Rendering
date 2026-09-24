# Floor completion checkpoint — 2026-09-05

Continued the existing 2.3.2 source and September 4 floor-system work. The new
installable artifact is `Releases/pcb_studio-2.3.2.zip`; the older archive in
`Haiku_update/` predates this floor work.

Completed floor integration with lighting refresh, connected infinity geometry,
brightness and rotation, preset reflection values, automatic grounding updates,
custom-floor material/visibility restoration, and shadow-catcher transparency
restoration. Fixed studio reset for Blender 5.2's compositor property. Removed
nonfunctional shadow-tint/contact-density controls from the floor UI while
retaining their stored properties for existing scenes.

Passed in Blender 4.5.11 LTS:

- Floor regression checks, including auto grounding and preset values.
- Professional studio/realism/render regression suite, including still renders
  and turntable/orbit/flyover preservation; rerun after integration fixes.
- Camera controls, animation, and Cycles-device acceptance suites.
- Built ZIP registration/unregistration and native extension manifest validation.

Blender 5.2.1 LTS: floor/reset checks and built ZIP registration passed. The full
professional-render suite was only run on 4.5; this is not full 5.2 certification.

The ZIP excludes caches and `.bak` files. Existing unrelated working-tree changes
were preserved. `git diff --check` still reports two pre-existing trailing-space
lines in `pcb_studio/utils/lighting.py` (110 and 116).

Install the ZIP directly using Blender > Preferences > Get Extensions > Install
from Disk. No installation into the user's Blender profile was performed.

## Product/material continuation ? 2026-09-06

Product tests now cover orientation, selection, stationary studio geometry,
turntable action protection, save/reopen, hierarchy, auto framing, and undo/redo.
The material/UI test covers all presets, manual controls, panel drawing, and
registration cycles. See the current product documentation for supported features.

Passed in Blender 4.5.11 and 5.2.1: product smoke, geometry/hierarchy,
actual undo/redo, and material/UI checks (49 entries including Custom).
Passed in Blender 4.5.11: camera, animation, and floor regression suites.
Python compilation passed. No obsolete component-animation references remain
in source, tests or documentation; historical ZIP archives were retained.
Existing lighting.py trailing whitespace is outside this change.

Changed source files in this continuation:
- pcb_studio/__init__.py, constants.py, properties.py, product_properties.py
- pcb_studio/operators/product.py
- pcb_studio/ui/main_panel.py, ui/product.py
- pcb_studio/utils/animation.py, utils/product.py, utils/materials.py

Updated documentation: README.md, pcb_studio/README.md,
pcb_studio/PRODUCT_PRESENTATION.md, and this validation record.
Updated product smoke, geometry, undo and package registration tests;
added blender_material_ui_smoke_test.py.

The installable Releases/pcb_studio-2.3.2-material-grid.zip passed isolated
registration/unregistration on both Blender versions (56 package files).
All 53 addon modules passed AST parsing and duplicate-definition checks.
The broader professional-studio suite also passed on Blender 4.5.11, including
actual Eevee preview and Cycles still rendering, realism, lighting, studio reset,
and animation preservation. Manually verify camera alignment from a real
viewport, preset highlights on your PCB, and grid readability at your preferred
sidebar width.
