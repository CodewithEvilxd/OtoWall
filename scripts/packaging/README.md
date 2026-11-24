# Windows Packaging & Executable Build

Specifications and scripts for packaging OtoWall as a standalone, zero-dependency Windows executable.

---

## Files

- **`otowall-windows.spec`**:
  Full PyInstaller specification for the production Windows release.
  - Bundles WinRT System Media Transport Controls (SMTC) dependencies.
  - Embeds bundled fonts (`assets/fonts/`) and cloud reference textures (`assets/`).
  - Sets application icons, metadata, and runtime hooks.
  - Enables DPI awareness on Windows 10/11.

- **`otowall-smoke.spec`**:
  Lightweight specification for CI smoke testing to quickly verify executable generation without bundling optional dependencies.

- **`pyinstaller_win_entry.py`**:
  Dedicated runtime bootstrap entry point. Configures high-DPI scaling policies before any UI or COM subsystem initializes and launches `otowall.cli.main_windows()`.

---

## Building the Windows Executable

Ensure development and Windows packaging dependencies are installed:

```powershell
pip install -e ".[dev,windows]"
```

Run PyInstaller using the production spec:

```powershell
pyinstaller scripts/packaging/otowall-windows.spec
```

The resulting standalone executable will be placed in `dist/OtoWall-windows.exe`.
