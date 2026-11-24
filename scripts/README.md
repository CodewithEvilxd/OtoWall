# Developer Scripts

Utility and automation scripts for development, benchmarking, and asset generation.

---

## Available Scripts & Tools

### 1. Convenience Commands (Windows PowerShell)
- **`run.ps1`**: Runs the live daemon with local playback and retro CRT TV style:
  ```powershell
  .\scripts\run.ps1
  ```
- **`test.ps1`**: Executes the test suite via pytest:
  ```powershell
  .\scripts\test.ps1
  ```
- **`build.ps1`**: Builds the standalone Windows `.exe` using PyInstaller:
  ```powershell
  .\scripts\build.ps1
  ```

---

### 2. `generate_showcase_wallpapers.py`
Automates the retrieval of high-resolution album cover art from the Apple iTunes Search API and renders 1080p showcase wallpapers across all 3 curated cloud background styles.

- **Outputs**:
  - `docs/wallpapers/wallpaper_liggi_ritviz.png` (Style 0: Pop-Art Halftone Clouds)
  - `docs/wallpapers/wallpaper_uff_bang_bang.png` (Style 1: Manga Screentone Clouds)
  - `docs/wallpapers/wallpaper_senorita_znmd.png` (Style 2: Retro ASCII Bayer Dither Clouds)
- **Features**:
  - Connection pooling with `requests.Session` and resilient timeout handling.
  - Automated fallback cache check to skip redundant re-renders.
  - High-res cover resolution (upscaling 100x100 thumbnails to 600x600 uncompressed album art).
- **Usage**:
  ```bash
  python scripts/generate_showcase_wallpapers.py
  ```

---

### 3. `profile_compose.py`
Benchmarks wallpaper composition performance at high-DPI laptop resolution ($2496 \times 1664$).
- **Usage**:
  ```bash
  python scripts/profile_compose.py
  ```

---

### 4. `packaging/`
Windows standalone executable packaging pipeline via PyInstaller.
- **`packaging/otowall-windows.spec`**: Production standalone bundle with WinRT SMTC dependencies, assets, and metadata.
- **`packaging/otowall-smoke.spec`**: Lean CI smoke build spec.
- **`packaging/pyinstaller_win_entry.py`**: High-DPI Windows runtime bootstrap entry point.
- **`packaging/README.md`**: Dedicated packaging and build instructions.

---

### 5. `requirements-lock.txt`
Pinned dependency lock file for reproducible builds across development and release environments.
