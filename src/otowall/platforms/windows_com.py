"""Optional IDesktopWallpaper COM helpers (pywin32 or ole32 ctypes)."""

from __future__ import annotations

import logging
import sys

logger = logging.getLogger(__name__)

_DESKTOP_WALLPAPER_CLSID = "{C2CF3110-460E-4fc1-B9D0-8A1C0C9CC4BD}"
_IDESKTOP_WALLPAPER_IID = "{B92B56A9-8B55-4E14-9A89-0199BBB6F93B}"
_RPC_E_CHANGED_MODE = -2147417850

_monitor_device_names: dict[str, str] = {}
_monitor_rects: dict[str, tuple[int, int, int, int]] = {}
_monitor_com_paths: dict[str, str] = {}
_com_available: bool | None = None
_com_probe_detail: str = ""
_com_backend: str | None = None


def register_monitor_device(
    monitor_id: str,
    device_name: str,
    rect: tuple[int, int, int, int] | None = None,
) -> None:
    if monitor_id and device_name:
        _monitor_device_names[monitor_id] = device_name
    if monitor_id and rect:
        _monitor_rects[monitor_id] = rect


def clear_monitor_device_registry() -> None:
    _monitor_device_names.clear()
    _monitor_rects.clear()
    _monitor_com_paths.clear()


def resolve_monitor_device_path(monitor_id: str) -> str:
    if monitor_id in _monitor_com_paths:
        return _monitor_com_paths[monitor_id]

    if not idesktop_wallpaper_available():
        return _monitor_device_names.get(monitor_id, "")

    if _com_backend == "ctypes":
        from otowall.platforms import windows_com_ctypes

        try:
            interface = windows_com_ctypes.create_desktop_wallpaper_interface()
            com_list = windows_com_ctypes.get_monitor_device_paths_with_rects(interface)
            target_rect = _monitor_rects.get(monitor_id)
            if target_rect:
                for com_path, com_rect in com_list:
                    if com_rect == target_rect:
                        _monitor_com_paths[monitor_id] = com_path
                        return com_path
            if com_list:
                sorted_keys = sorted(
                    _monitor_rects.keys(),
                    key=lambda k: _monitor_rects[k][0],
                )
                if monitor_id in sorted_keys:
                    idx = sorted_keys.index(monitor_id)
                    if idx < len(com_list):
                        _monitor_com_paths[monitor_id] = com_list[idx][0]
                        return com_list[idx][0]
                _monitor_com_paths[monitor_id] = com_list[0][0]
                return com_list[0][0]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not query IDesktopWallpaper device paths: %s", exc)

    return _monitor_device_names.get(monitor_id, "")


def idesktop_wallpaper_probe_detail() -> str:
    return _com_probe_detail


def _probe_pythoncom() -> tuple[bool, str]:
    try:
        import pythoncom  # type: ignore[import-untyped]

        try:
            pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)
        except pythoncom.com_error as exc:
            if int(exc.hresult) != _RPC_E_CHANGED_MODE:
                hr = int(exc.hresult) & 0xFFFFFFFF
                return False, f"pythoncom.CoInitializeEx failed: HRESULT=0x{hr:08X} ({exc})"
        pythoncom.CoCreateInstance(
            _DESKTOP_WALLPAPER_CLSID,
            None,
            pythoncom.CLSCTX_ALL,
            _IDESKTOP_WALLPAPER_IID,
        )
        return True, "pythoncom CoCreateInstance(IDesktopWallpaper) succeeded"
    except Exception as exc:  # noqa: BLE001
        return False, f"pythoncom: {type(exc).__name__}: {exc}"


def _probe_ctypes_com() -> tuple[bool, str]:
    try:
        from otowall.platforms import windows_com_ctypes
    except ImportError as exc:
        return False, f"ctypes COM backend unavailable: {exc}"
    return windows_com_ctypes.probe_idesktop_wallpaper_ctypes()


def idesktop_wallpaper_probe() -> tuple[bool, str]:
    """Return availability and a human-readable probe trace (for ``diag``)."""
    global _com_available, _com_probe_detail, _com_backend
    if _com_available is not None:
        return _com_available, _com_probe_detail

    if sys.platform != "win32":
        _com_available = False
        _com_probe_detail = "non-win32"
        _com_backend = None
        return False, _com_probe_detail

    py_ok, py_detail = _probe_pythoncom()
    if py_ok:
        _com_available = True
        _com_probe_detail = py_detail
        _com_backend = "pythoncom"
        return True, py_detail

    ct_ok, ct_detail = _probe_ctypes_com()
    if ct_ok:
        _com_available = True
        _com_probe_detail = f"{py_detail}; fallback {ct_detail}"
        _com_backend = "ctypes"
        return True, _com_probe_detail

    _com_available = False
    _com_probe_detail = f"{py_detail}; {ct_detail}"
    _com_backend = None
    return False, _com_probe_detail


def idesktop_wallpaper_available() -> bool:
    available, _detail = idesktop_wallpaper_probe()
    return available


def _desktop_wallpaper_interface_pythoncom():
    import pythoncom  # type: ignore[import-untyped]

    try:
        pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)
    except pythoncom.com_error as exc:
        if int(exc.hresult) != _RPC_E_CHANGED_MODE:
            raise
    return pythoncom.CoCreateInstance(
        _DESKTOP_WALLPAPER_CLSID,
        None,
        pythoncom.CLSCTX_ALL,
        _IDESKTOP_WALLPAPER_IID,
    )


_DWPOS_FILL = 4
_DWPOS_SPAN = 5


def set_wallpaper_all(path: str, span: bool = False) -> None:
    if not idesktop_wallpaper_available():
        raise OSError("IDesktopWallpaper is not available")
    pos = _DWPOS_SPAN if span else _DWPOS_FILL
    if _com_backend == "ctypes":
        from otowall.platforms import windows_com_ctypes

        interface = windows_com_ctypes.create_desktop_wallpaper_interface()
        windows_com_ctypes.set_wallpaper_all(interface, path, span=span)
    else:
        wallpaper = _desktop_wallpaper_interface_pythoncom()
        wallpaper.SetPosition(pos)
        wallpaper.SetWallpaper(None, path)
    logger.debug(
        "IDesktopWallpaper.SetWallpaper(ALL, %s, span=%s)",
        path,
        span,
    )


def set_wallpaper_for_monitor(monitor_id: str, path: str) -> None:
    if not idesktop_wallpaper_available():
        raise OSError("IDesktopWallpaper is not available")
    device = resolve_monitor_device_path(monitor_id)
    if not device:
        raise OSError(f"No device name registered for monitor {monitor_id}")
    if _com_backend == "ctypes":
        from otowall.platforms import windows_com_ctypes

        interface = windows_com_ctypes.create_desktop_wallpaper_interface()
        windows_com_ctypes.set_wallpaper_on_device(interface, device, path)
    else:
        wallpaper = _desktop_wallpaper_interface_pythoncom()
        wallpaper.SetPosition(_DWPOS_FILL)
        wallpaper.SetWallpaper(device, path)
    logger.debug(
        "IDesktopWallpaper.SetPosition(FILL) SetWallpaper(%s, %s)",
        device,
        path,
    )


def get_wallpaper_for_monitor(monitor_id: str) -> str | None:
    if not idesktop_wallpaper_available():
        return None
    device = resolve_monitor_device_path(monitor_id)
    if not device:
        return None
    if _com_backend == "ctypes":
        from otowall.platforms import windows_com_ctypes

        interface = windows_com_ctypes.create_desktop_wallpaper_interface()
        return windows_com_ctypes.get_wallpaper_for_device(interface, device)
    wallpaper = _desktop_wallpaper_interface_pythoncom()
    return str(wallpaper.GetWallpaper(device))
