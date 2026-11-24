# System Architecture

OtoWall is a real-time, cross-platform wallpaper compositor that listens to current media playback and updates the desktop background with customized album art and visualizations.

---

## High-Level Data Flow

```
┌─────────────────────────┐
│ Media Playback Sessions │  (Spotify Desktop, Web API, Windows SMTC, Linux MPRIS)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Playback Event Poller  │  (Single-instance mutex, active track deduplication)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Album Art Resolution   │  (SMTC / MPRIS thumbnail -> iTunes Search API fallback)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Wallpaper Compositor   │  (Retro CRT TV Engine OR Frosted Glass Engine)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│   OS Wallpaper Driver   │  (Windows COM IDesktopWallpaper, Linux D-Bus, macOS AppKit)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│    Desktop Display      │  (Multi-monitor, high-DPI scaling, original restore on pause)
└─────────────────────────┘
```

---

## Core Components

### 1. Playback Source Providers (`src/otowall/sources/`)
- **Windows SMTC**: Reads playback title, artist, playback state, and embedded stream thumbnails via WinRT `GlobalSystemMediaTransportControlsSessionManager`.
- **Linux MPRIS**: Connects to the user's D-Bus session and queries `org.mpris.MediaPlayer2.*` services.
- **macOS AppleScript**: Communicates with the Spotify desktop application via AppleScript automation.
- **Spotify Web API**: Connects to Spotify's REST endpoints using PKCE OAuth authorization.

### 2. High-Resolution Art Resolution (`src/otowall/art_resolution.py`)
- Extracts thumbnail image bytes from the local media session.
- If the thumbnail is missing or low-resolution ($<600\times600$), queries the **Apple iTunes Search API** asynchronously to fetch uncompressed $1000\times1000$ cover artwork.
- Employs disk caching in `%APPDATA%\otowall\cache` with hashed query keys to eliminate redundant network roundtrips.

### 3. Retro CRT Television Engine (`src/otowall/ascii_composer.py`)
- **NumPy Vectorized Barrel Bulge**:
  $$r_{\text{distorted}} = r \times (1 + k \cdot r^2) \quad \text{where } k = 0.08$$
  Simulates the spherical curvature of physical cathode ray tube glass.
- **Aperture Grille Triads**:
  Applies alternating vertical RGB phosphor attenuation masks.
- **Scanlines**:
  Modulates horizontal raster retrace lines with a sinusoidal luminance falloff.
- **Specular Highlights & Inner Shadow**:
  Renders curved glass reflections and a multi-stop 24px inner cavity shadow.
- **Curated Cloudscape Backgrounds**:
  1. *Pop-Art Halftone Screen Clouds*: Variable dot radius modulated by luminosity.
  2. *Manga Screentone Clouds*: Dense 45-degree dot screening with dual-layer cloud shading.
  3. *Retro ASCII Bayer Dither Clouds*: 8x8 Bayer ordered threshold dithering.

### 4. Platform Wallpaper Drivers (`src/otowall/platforms/`)
- **Windows (`windows.py`, `windows_com.py`)**:
  Interacts with `IDesktopWallpaper` COM interface supporting multi-monitor display topologies and virtual span modes. Falls back to `SystemParametersInfoW`.
- **Linux (`linux.py`)**:
  Interacts with GNOME `gsettings`, KDE Plasma `plasma-apply-wallpaperimage`, XFCE `xfconf-query`, or `feh`/`swaybg`.
- **macOS (`macos.py`)**:
  Controls per-display desktop backgrounds via Cocoa AppKit or `osascript`.

### 5. Session State & Restoration (`src/otowall/runner.py`)
- Captures an immutable snapshot of the user's pre-session desktop wallpaper at startup.
- Employs OS-level mutexes (`Local\otowall-run` on Windows, PID lockfile on Linux/macOS) to prevent multiple conflicting daemons.
- Registers graceful exit handlers (`SIGINT`, `SIGTERM`, atexit) to restore the original wallpaper whenever playback is paused or the process terminates.
