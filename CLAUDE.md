# CLAUDE.md — PCB Studio

Blender extension that turns PCB CAD exports (Altium OBJ+MTL) into professional
product renders and animations, for engineers who don't know Blender.

**Before coding, always read the relevant files inside `.agent/memory`.**

Start with `.agent/memory/ARCHITECTURE.md` for anything structural, and
`.agent/memory/DECISIONS.md` before changing defaults or error handling — several
things that look wrong are deliberate.

## Layout

| Path | What it is |
|---|---|
| `pcb_studio/` | The extension package — **this alone ships in the ZIP** |
| `pcb_studio/__init__.py` | Single registration list `_REGISTERED_CLASSES` |
| `pcb_studio/constants.py` | Every operator ID, object name, and enum item list |
| `pcb_studio/operators/` | Thin `bpy.types.Operator` wrappers; error handling only |
| `pcb_studio/utils/` | All real logic; no operator or UI imports |
| `pcb_studio/ui/` | Panels only; no logic |
| `tests/` | Standalone Blender scripts, each prints `*_PASSED` |
| `.agent/memory/`, `LOG.md`, `CLAUDE.md` | Dev docs — outside the shipped package |

## Conventions

- **Operators don't contain logic.** They call a `utils/` function, store the
  returned message on a property, and report it. Put new logic in `utils/`.
- **Errors travel as message strings, not exceptions.** A `utils/` function
  signals failure by returning a string starting with `"Cannot"`, `"No "`, or
  `"Unknown"`; operators test that prefix to choose `ERROR`/`CANCELLED`. If you
  add a failure path, match that prefix or it will be reported as success.
- **Never concatenate a status message into a success string** without checking
  the prefix first — that silently swallows failures.
- **Managed objects are tagged**, not name-matched: `obj["pcbstudio_managed"]`,
  `pcbstudio_role`, `pcbstudio_floor`. Only ever delete/modify tagged objects —
  user objects must survive every reset.
- **Update functions are idempotent.** Calling `update_professional_studio` twice
  must not create a second light or material.
- **Save and restore anything global** you touch (render engine, device, film
  transparency) in a `finally` block. Never write Blender user preferences.
- New IDs and enum item lists go in `constants.py`, not inline.

## Blender rules

- Extension (`blender_manifest.toml`), not a legacy addon — relative imports only.
- Register in `_REGISTERED_CLASSES`; unregister walks it reversed, so order stays
  symmetric automatically. Parent panels must register before their children.
- Sidebar order comes from **`bl_order`** on each panel, not registration order.
- Target Blender 4.5 LTS; 5.2 must also pass. Guard version-specific API with
  `hasattr` (see `utils/material_compat.py`).

## Testing

Always clear stale bytecode first — removed symbols can resolve from `.pyc`:

```bash
find . -name "__pycache__" -type d -exec rm -rf {} +
"/c/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
    --background --factory-startup --python tests/<file>.py
```

Each test prints a `*_PASSED` sentinel. Run the full `tests/` suite before
declaring work done, and repeat on Blender 5.2 for anything touching the API.
See `.agent/memory/WORKFLOW.md` for the full loop and the ZIP rebuild command.

## Safe modification

- Don't rewrite working subsystems to "clean them up" — this codebase is stable
  and heavily tested. Prefer surgical edits.
- Deleting a symbol? Grep `pcb_studio/` **and** `tests/` first. Several
  innocuous-looking helpers (`SNAPSHOT`, `validate_static`, `ensure_root`) are
  load-bearing across subsystems.
- Changing a status-message string? Check whether a test asserts on its prefix.
- Don't touch `Releases/*.zip` by hand; rebuild with the documented command.
