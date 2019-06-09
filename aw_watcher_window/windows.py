from typing import Optional

import wmi
import win32gui
import win32process
import ctypes
from ctypes import Structure, POINTER, WINFUNCTYPE, windll  # type: ignore
from ctypes.wintypes import BOOL, UINT, DWORD  # type: ignore

c = wmi.WMI()

"""
Much of this derived from: http://stackoverflow.com/a/14973422/965332
"""

def get_app_path(hwnd) -> Optional[str]:
    """Get application path given hwnd."""
    path = None
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    for p in c.query('SELECT ExecutablePath FROM Win32_Process WHERE ProcessId = %s' % str(pid)):
        path = p.ExecutablePath
        break
    return path

def get_app_name(hwnd) -> Optional[str]:
    """Get application filename given hwnd."""
    name = None
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    for p in c.query('SELECT Name FROM Win32_Process WHERE ProcessId = %s' % str(pid)):
        name = p.Name
        break
    return name

def get_window_title(hwnd):
    return win32gui.GetWindowText(hwnd)

def get_active_window_handle():
    hwnd = win32gui.GetForegroundWindow()
    return hwnd

class LastInputInfo(Structure):
    _fields_ = [
        ("cbSize", UINT),
        ("dwTime", DWORD)
    ]


def _getLastInputTick() -> int:
    prototype = WINFUNCTYPE(BOOL, POINTER(LastInputInfo))
    paramflags = ((1, "lastinputinfo"), )
    c_GetLastInputInfo = prototype(("GetLastInputInfo", ctypes.windll.user32), paramflags)  # type: ignore

    l = LastInputInfo()
    l.cbSize = ctypes.sizeof(LastInputInfo)
    assert 0 != c_GetLastInputInfo(l)
    return l.dwTime


def _getTickCount() -> int:
    prototype = WINFUNCTYPE(DWORD)
    paramflags = ()
    c_GetTickCount = prototype(("GetTickCount", ctypes.windll.kernel32), paramflags)  # type: ignore
    return c_GetTickCount()


def seconds_since_last_input():
    seconds_since_input = (_getTickCount() - _getLastInputTick()) / 1000
    return seconds_since_input


if __name__ == "__main__":
    hwnd = get_active_window_handle()
    print("Title:", get_window_title(hwnd))
    print("App:", get_app_name(hwnd))