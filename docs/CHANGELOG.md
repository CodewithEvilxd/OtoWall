# Changelog

All notable changes to the OtoWall project are documented in this file.

---

## [1.1.0] - 2026-11-24

### Added
- **3D Retro CRT Television Engine (`ascii_composer.py`)**:
  - Vectorized NumPy barrel bulge distortion simulating physical curved glass bulb geometry.
  - RGB phosphor aperture grille vertical micro-stripes and horizontal electron scanlines.
  - Specular glass reflections, 24px recessed inner bezel drop shadow, and phosphor OSD display (`CH-04 STEREO  ● PLAY`).
  - Smoked acrylic translucent song card with typography hierarchy.
- **Curated Cloudscape Backgrounds**:
  - Style 0: *Pop-Art Halftone Screen Clouds* (variable-radius dot matrix sampling album palette).
  - Style 1: *Manga Screentone Dither Clouds* (dense diagonal screening with high-contrast cloud rims).
  - Style 2: *Retro ASCII Bayer Dither Clouds* (8x8 Bayer ordered threshold dithering).
- **Showcase Wallpapers**:
  - High-resolution 1080p sample renders in `docs/wallpapers/`.
  - Automated wallpaper generation utility `scripts/generate_showcase_wallpapers.py`.
- **Project Structure Overhaul**:
  - Reorganized workspace into clean `docs/`, `scripts/`, `src/`, and `tests/` directories.
  - Consolidated PyInstaller packaging pipeline into `scripts/packaging/`.
  - Relocated Pytest cache to `.venv/.pytest_cache` to keep root pristine.
  - Configured workspace exclusions in `.vscode/settings.json`.

### Fixed
- Fixed COM `IDesktopWallpaper` mocking in `tests/test_platforms_windows.py` to prevent desktop wallpaper mutation during testing.
- Added explicit `numpy>=1.26.0,<3` requirement in `pyproject.toml`.
- Resolved mutex busy collisions in background daemon execution.

---

## [1.0.1] - 2026-11-22

### Added
- Background album artwork upgrader with iTunes Search API integration.
- Linux MPRIS and macOS AppleScript local playback providers.

---

## [1.0.0] - 2026-11-19

### Initial Release
- Frosted glass wallpaper compositor for Spotify Web API and local media players.
- Windows SMTC playback session monitoring.
- Multi-monitor wallpaper spanning with `IDesktopWallpaper`.
