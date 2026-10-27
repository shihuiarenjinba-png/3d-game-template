# 3D Game Template — Godot 4.3

Minimal **working 3D starter** for the 3D Factory. This repository is a source template, not a completed game, signed MSIX, Store submission, or GPU-qualified release.

## Source layout

- `project.godot`: Godot 4.3 project (GL Compatibility renderer, 1024×768)
- `scenes/main.tscn`: camera, directional light, and rotating 3D cube
- `scripts/main.gd`: tiny frame-update script
- `tests/test_template.py`: offline structural checks
- `.github/workflows/godot-smoke.yml`: offline checks plus **real Godot 4.3 headless import and launch** on Ubuntu CI

## Validate locally

```bash
python -m unittest discover -s tests -v
godot --headless --editor --path . --import
godot --headless --path . --quit-after 5
```

The headless launch is **not** Windows GUI/GPU QA. This template now includes `export_presets.cfg` and `.github/workflows/windows-export.yml`. GitHub Actions downloads official Godot 4.3 export templates, builds a real **Windows x64 EXE/PCK pair**, validates the PE header and file hashes, and uploads a seven-day `godot-3d-windows-x64-qa-unsigned` Artifact containing `build-evidence.json` with the exact source SHA. It does **not** produce an MSIX, sign the package, validate a Store Identity, or run Windows GUI/GPU QA. The artifact is a reproducible **QA_UNSIGNED_EXPORT** only, not a finished product. A product Factory must supply original playable game content; the Windows MSIX/Identity/Store workflow is a separate validated stage. Keep binaries, exported builds, caches and large source assets outside ordinary Git history; use Git LFS or external artifact storage after checking quotas and permissions.

The **120-hour creation gate** is owned by `3d-game-factory`, not this template. Do not schedule or create a new game from this repository automatically. Identity, Store ID, Publisher, price and security declarations must never be inferred.
