import sys
import getpass
from typing import Optional


def get_current_window_linux() -> Optional[dict]:
    from . import xlib
    window = xlib.get_current_window()

    if window is None:
        cls = "unknown"
        name = "unknown"
        user = "unknown"
    else:
        cls = xlib.get_window_class(window)
        name = xlib.get_window_name(window)
        user = xlib.get_window_user(window)


    return {"appname": cls, "title": name, "user": user}


def get_current_window_macos() -> Optional[dict]:
    from . import macos
    info = macos.getInfo()
    app = macos.getApp(info)
    title = macos.getTitle(info)

    return {"title": title, "appname": app, "user": getpass.getuser()}


def get_current_window_windows() -> Optional[dict]:
    from . import windows
    window_handle = windows.get_active_window_handle()
    app = windows.get_app_name(window_handle)
    title = windows.get_window_title(window_handle)
    user = getpass.getuser()

    if app is None:
        app = "unknown"
    if title is None:
        title = "unknown"

    return {"appname": app, "title": title, "user": user}


def get_current_window() -> Optional[dict]:
    if sys.platform.startswith("linux"):
        return get_current_window_linux()
    elif sys.platform == "darwin":
        return get_current_window_macos()
    elif sys.platform in ["win32", "cygwin"]:
        return get_current_window_windows()
    else:
        raise Exception("Unknown platform: {}".format(sys.platform))
