# -*- coding: utf-8 -*-
"""
Style & Theming Engine - Antigravity Conversation Renamer
Provides QSS stylesheet loading and Windows DWM title bar customization.
"""
import ctypes
import os
import sys

# DWM constants for Windows title bar styling
DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19
DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_BORDER_COLOR = 34
DWMWA_CAPTION_COLOR = 35
DWMWA_TEXT_COLOR = 36


def get_stylesheet_path() -> str:
    """Discovers theme.qss across frozen runtime bundle, resources, and project root."""
    if getattr(sys, "frozen", False):
        p = os.path.join(sys._MEIPASS, "resources", "styles", "theme.qss")
        if os.path.exists(p):
            return p
        p_flat = os.path.join(sys._MEIPASS, "theme.qss")
        if os.path.exists(p_flat):
            return p_flat

    candidates = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "styles", "theme.qss"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "styles", "theme.qss"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "theme.qss"),
        os.path.join("resources", "styles", "theme.qss"),
        "theme.qss"
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return ""


def load_theme_qss() -> str:
    """Loads Ocean Dark QSS from external stylesheet file."""
    qss_path = get_stylesheet_path()
    if qss_path and os.path.exists(qss_path):
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"[Warning] Failed to read stylesheet {qss_path}: {e}")
    return ""


def apply_dark_window_titlebar(window):
    """
    Applies native Windows title bar dark theming via Windows DWM API:
    - DWMWA_USE_IMMERSIVE_DARK_MODE (20 & 19): Windows 10 & 11 native dark mode
    - DWMWA_CAPTION_COLOR (35): Ocean Dark background (#0c1a3a -> 0x003A1A0C)
    - DWMWA_TEXT_COLOR (36): Soft white title text (#f8fafc -> 0x00FCFAF8)
    - DWMWA_BORDER_COLOR (34): Subtle blue border (#1e3a8a -> 0x008A3A1E)
    """
    if sys.platform != "win32":
        return
    try:
        hwnd = int(window.winId())
        if not hwnd:
            return

        # 1. Immersive Dark Mode (Windows 10 Build 17763+ & Windows 11)
        val = ctypes.c_int(1)
        for attr in [DWMWA_USE_IMMERSIVE_DARK_MODE, DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1]:
            res = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, attr, ctypes.byref(val), ctypes.sizeof(val)
            )
            if res == 0:
                break

        # 2. Custom Title Bar Background Color (Windows 11 Build 22000+)
        # #0c1a3a -> 0x003A1A0C (COLORREF format 0x00BBGGRR)
        caption_color = ctypes.c_int(0x003A1A0C)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_CAPTION_COLOR, ctypes.byref(caption_color), ctypes.sizeof(caption_color)
        )

        # 3. Custom Title Bar Text Color (Windows 11 Build 22000+)
        # #f8fafc -> 0x00FCFAF8
        text_color = ctypes.c_int(0x00FCFAF8)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_TEXT_COLOR, ctypes.byref(text_color), ctypes.sizeof(text_color)
        )

        # 4. Custom Border Color (Windows 11 Build 22000+)
        # #1e3a8a -> 0x008A3A1E
        border_color = ctypes.c_int(0x008A3A1E)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_BORDER_COLOR, ctypes.byref(border_color), ctypes.sizeof(border_color)
        )
    except Exception:
        pass


# Pre-loaded theme stylesheet singleton
OCEAN_THEME_QSS = load_theme_qss()
