"""Windows DWM acrylic / blur effects via ctypes.

Adapted from zhiyiYo/PyQt-Frameless-Window's window_effect.py for PySide6.
"""

import ctypes
from ctypes import POINTER, c_bool, c_int, c_uint, c_ulong, pointer, sizeof
from ctypes.wintypes import DWORD

_ACCENT_STATE_DISABLED = 0
_ACCENT_STATE_ACRYLIC = 4
_WCA_ACCENT_POLICY = 19


class _ACCENT_POLICY(ctypes.Structure):
    _fields_ = [
        ("AccentState", c_uint),
        ("AccentFlags", c_uint),
        ("GradientColor", c_uint),
        ("AnimationId", c_uint),
    ]


class _WCA_DATA(ctypes.Structure):
    _fields_ = [
        ("Attribute", c_int),
        ("Data", POINTER(_ACCENT_POLICY)),
        ("SizeOfData", c_ulong),
    ]


_user32 = ctypes.windll.user32
_set_comp_attr = _user32.SetWindowCompositionAttribute
_set_comp_attr.restype = c_bool
_set_comp_attr.argtypes = [c_int, POINTER(_WCA_DATA)]


def set_acrylic_effect(
    hwnd: int,
    gradient_color: str = "12121299",
    enable_shadow: bool = True,
) -> None:
    """Apply acrylic blur behind a window (Win10+).

    Parameters
    ----------
    hwnd : int
        Native window handle (``int(widget.winId())``).
    gradient_color : str
        8-char hex string in RRGGBBAA order.
    enable_shadow : bool
        Show the native window shadow.
    """
    # RRGGBBAA  →  AABBGGRR  (Win32 GDI DWORD order)
    reversed_gc = "".join(
        gradient_color[i : i + 2] for i in range(6, -1, -2)
    )
    accent_flags = DWORD(0x20 | 0x40 | 0x80 | 0x100) if enable_shadow else DWORD(0)

    accent = _ACCENT_POLICY()
    accent.AccentState = _ACCENT_STATE_ACRYLIC
    accent.GradientColor = DWORD(int(reversed_gc, 16))
    accent.AccentFlags = accent_flags
    accent.AnimationId = DWORD(0)

    data = _WCA_DATA()
    data.Attribute = _WCA_ACCENT_POLICY
    data.SizeOfData = sizeof(accent)
    data.Data = pointer(accent)

    _set_comp_attr(hwnd, pointer(data))


def remove_background_effect(hwnd: int) -> None:
    """Remove any acrylic / blur effect from a window."""
    accent = _ACCENT_POLICY()
    accent.AccentState = _ACCENT_STATE_DISABLED

    data = _WCA_DATA()
    data.Attribute = _WCA_ACCENT_POLICY
    data.SizeOfData = sizeof(accent)
    data.Data = pointer(accent)

    _set_comp_attr(hwnd, pointer(data))
