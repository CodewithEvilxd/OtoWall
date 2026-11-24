"""Local OS media session playback."""

from __future__ import annotations

import sys

from otowall.sources.local.base import LocalPlaybackProvider


def build_local_provider() -> LocalPlaybackProvider:
    if sys.platform == "win32":
        from otowall.sources.local.windows_smtc import WindowsSmtcProvider

        return WindowsSmtcProvider()
    if sys.platform == "linux":
        from otowall.sources.local.linux_mpris import LinuxMprisProvider

        return LinuxMprisProvider()
    if sys.platform == "darwin":
        from otowall.sources.local.macos_spotify import MacOsSpotifyProvider

        return MacOsSpotifyProvider()
    from otowall.sources.local.unsupported import UnsupportedLocalProvider

    return UnsupportedLocalProvider(sys.platform)
