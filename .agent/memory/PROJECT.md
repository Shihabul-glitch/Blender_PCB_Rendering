# PROJECT

## Overview

PCB Studio is a Blender extension for importing, staging, rendering, and
animating printed-circuit-board models. It wraps a full product-photography
studio (lighting rig, backdrop, floor, camera, render pipeline) behind a
step-numbered sidebar.

## Goal

Let PCB designers and engineers produce commercial-quality board renders without
learning Blender. Every feature should be reachable as a labelled button in
workflow order, with safe defaults and reversible actions.

## Status

v2.3.2 — "final development / stabilization". Feature-complete and regression
tested; work is now polish, bug fixing, and UI simplification rather than new
subsystems.

Recent direction: cutting confusing/duplicate options rather than adding
features. The "adaptive studio" subsystem is finished internally but stays
opt-in and undocumented (see DECISIONS.md).

## Stack

- **Blender 4.5.11 LTS** primary target, **5.2.1 LTS** secondary. Both installed
  at `C:\Program Files\Blender Foundation\Blender <ver>\blender.exe`.
- Python 3.11 (Blender's bundled interpreter). **No external packages** — stdlib,
  `bpy`, `mathutils`, `bpy_extras` only. Keep it that way; extensions with
  dependencies are far harder to install.
- Packaged as a Blender **extension** (`blender_manifest.toml`), built with
  Blender's own `--command extension build`.
- Windows is the primary tested platform.
- Input format: Wavefront OBJ + auto-detected MTL (typically Altium exports).
  KiCad/STEP users convert externally first.
- Renderers: EEVEE Next for previews, Cycles for final stills.
- ~13.5k lines across ~55 modules. Git repo at the project root; `pcb_studio/`
  is the shipped subset.
