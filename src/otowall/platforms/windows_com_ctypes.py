"""IDesktopWallpaper via ``ole32`` (no pywin32 required)."""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

if sys.platform != "win32":
    raise ImportError("windows_com_ctypes is Windows-only")

ole32 = ctypes.OleDLL("ole32")
kernel32 = ctypes.windll.kernel32

CLSID_DESKTOP_WALLPAPER = "{C2CF3110-460E-4fc1-B9D0-8A1C0C9CC4BD}"
IID_IDESKTOP_WALLPAPER = "{B92B56A9-8B55-4E14-9A89-0199BBB6F93B}"

CLSCTX_ALL = 0x17
COINIT_APARTMENTTHREADED = 0x2
RPC_E_CHANGED_MODE = 0x80010106
S_OK = 0
DWPOS_CENTER = 0
DWPOS_TILE = 1
DWPOS_STRETCH = 2
DWPOS_FIT = 3
DWPOS_FILL = 4
DWPOS_SPAN = 5

_VTABLE_SET_WALLPAPER = 3
_VTABLE_GET_WALLPAPER = 4
_VTABLE_GET_MONITOR_DEVICE_PATH_AT = 5
_VTABLE_GET_MONITOR_DEVICE_PATH_COUNT = 6
_VTABLE_GET_MONITOR_RECT = 7
_VTABLE_SET_POSITION = 10


class _COM_RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]
_VTABLE_GET_WALLPAPER = 4

_com_initialized = False


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8),
    ]


def _hresult_string(hr: int) -> str:
    if hr == 0:
        return "S_OK"
    if hr < 0:
        return f"HRESULT=0x{hr & 0xFFFFFFFF:08X}"
    return f"HRESULT={hr}"


def _guid_from_string(value: str) -> GUID:
    guid = GUID()
    hr = ole32.CLSIDFromString(value, ctypes.byref(guid))
    if hr < 0:
        raise OSError(f"CLSIDFromString failed for {value!r}: {_hresult_string(hr)}")
    return guid


def _ensure_com_apartment() -> None:
    global _com_initialized
    if _com_initialized:
        return
    hr = ole32.CoInitializeEx(None, COINIT_APARTMENTTHREADED)
    if hr < 0 and hr != RPC_E_CHANGED_MODE:
        raise OSError(f"CoInitializeEx failed: {_hresult_string(hr)}")
    _com_initialized = True


def _com_method(interface: int, slot: int, restype, argtypes):
    iface = ctypes.c_void_p(interface)
    vtable = ctypes.cast(iface, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)))[0]
    vtable_entries = ctypes.cast(vtable, ctypes.POINTER(ctypes.c_void_p))
    prototype = ctypes.CFUNCTYPE(restype, ctypes.c_void_p, *argtypes)
    return prototype(vtable_entries[slot])


def _create_desktop_wallpaper() -> int:
    _ensure_com_apartment()
    clsid = _guid_from_string(CLSID_DESKTOP_WALLPAPER)
    iid = _guid_from_string(IID_IDESKTOP_WALLPAPER)
    interface = ctypes.c_void_p()
    hr = ole32.CoCreateInstance(
        ctypes.byref(clsid),
        None,
        CLSCTX_ALL,
        ctypes.byref(iid),
        ctypes.byref(interface),
    )
    if hr < 0:
        raise OSError(f"CoCreateInstance(IDesktopWallpaper) failed: {_hresult_string(hr)}")
    return interface.value


def probe_idesktop_wallpaper_ctypes() -> tuple[bool, str]:
    try:
        interface = _create_desktop_wallpaper()
        if interface:
            return True, "CoCreateInstance(IDesktopWallpaper) via ole32 succeeded"
    except OSError as exc:
        return False, str(exc)
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"
    return False, "CoCreateInstance returned null interface"


def create_desktop_wallpaper_interface() -> int:
    return _create_desktop_wallpaper()


def set_wallpaper_on_device(
    interface: int,
    device: str | None,
    path: str,
    position: int = DWPOS_FILL,
) -> None:
    set_position = _com_method(interface, _VTABLE_SET_POSITION, ctypes.c_long, [ctypes.c_int])
    hr = set_position(interface, position)
    if hr < 0:
        raise OSError(f"IDesktopWallpaper.SetPosition failed: {_hresult_string(hr)}")
    set_wallpaper = _com_method(
        interface,
        _VTABLE_SET_WALLPAPER,
        ctypes.c_long,
        [wintypes.LPCWSTR, wintypes.LPCWSTR],
    )
    dev_arg = wintypes.LPCWSTR(device) if device else None
    hr = set_wallpaper(interface, dev_arg, path)
    if hr < 0:
        raise OSError(f"IDesktopWallpaper.SetWallpaper failed: {_hresult_string(hr)}")


def set_wallpaper_all(interface: int, path: str, span: bool = False) -> None:
    pos = DWPOS_SPAN if span else DWPOS_FILL
    set_wallpaper_on_device(interface, None, path, position=pos)


def get_wallpaper_for_device(interface: int, device: str) -> str:
    get_wallpaper = _com_method(
        interface,
        _VTABLE_GET_WALLPAPER,
        ctypes.c_long,
        [wintypes.LPCWSTR, ctypes.POINTER(wintypes.LPCWSTR)],
    )
    out = wintypes.LPCWSTR()
    hr = get_wallpaper(interface, device, ctypes.byref(out))
    if hr < 0:
        raise OSError(f"IDesktopWallpaper.GetWallpaper failed: {_hresult_string(hr)}")
    return str(out.value if out.value else "")


def get_monitor_device_paths_with_rects(
    interface: int,
) -> list[tuple[str, tuple[int, int, int, int]]]:
    get_count = _com_method(
        interface,
        _VTABLE_GET_MONITOR_DEVICE_PATH_COUNT,
        ctypes.c_long,
        [ctypes.POINTER(ctypes.c_uint)],
    )
    get_path = _com_method(
        interface,
        _VTABLE_GET_MONITOR_DEVICE_PATH_AT,
        ctypes.c_long,
        [ctypes.c_uint, ctypes.POINTER(wintypes.LPWSTR)],
    )
    get_rect = _com_method(
        interface,
        _VTABLE_GET_MONITOR_RECT,
        ctypes.c_long,
        [wintypes.LPCWSTR, ctypes.POINTER(_COM_RECT)],
    )
    count = ctypes.c_uint()
    hr = get_count(interface, ctypes.byref(count))
    if hr < 0:
        return []
    results: list[tuple[str, tuple[int, int, int, int]]] = []
    for i in range(count.value):
        path = wintypes.LPWSTR()
        hr = get_path(interface, i, ctypes.byref(path))
        if hr < 0 or not path.value:
            continue
        rect = _COM_RECT()
        hr = get_rect(interface, path.value, ctypes.byref(rect))
        if hr < 0:
            continue
        results.append(
            (
                str(path.value),
                (int(rect.left), int(rect.top), int(rect.right), int(rect.bottom)),
            )
        )
    return results
