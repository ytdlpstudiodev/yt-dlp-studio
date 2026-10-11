"""Small Windows helpers: clipboard, native folder/file dialogs, Explorer."""
from __future__ import annotations

import ctypes
import os
import subprocess
import sys
import time
from ctypes import wintypes

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
CF_UNICODETEXT = 13

_user32 = ctypes.WinDLL("user32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_user32.OpenClipboard.argtypes = [wintypes.HWND]
_user32.OpenClipboard.restype = wintypes.BOOL
_user32.CloseClipboard.restype = wintypes.BOOL
_user32.IsClipboardFormatAvailable.argtypes = [wintypes.UINT]
_user32.IsClipboardFormatAvailable.restype = wintypes.BOOL
_user32.GetClipboardData.argtypes = [wintypes.UINT]
_user32.GetClipboardData.restype = wintypes.HANDLE
_user32.GetClipboardSequenceNumber.restype = wintypes.DWORD
_kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
_kernel32.GlobalLock.restype = ctypes.c_void_p
_kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]


def clipboard_sequence() -> int:
    return _user32.GetClipboardSequenceNumber()


def get_clipboard_text() -> str | None:
    for _ in range(10):
        if _user32.OpenClipboard(None):
            break
        time.sleep(0.03)          # another app has it open; try again shortly
    else:
        return None
    try:
        if not _user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
            return ""
        h = _user32.GetClipboardData(CF_UNICODETEXT)
        if not h:
            return ""
        p = _kernel32.GlobalLock(h)
        if not p:
            return ""
        try:
            return ctypes.wstring_at(p)
        finally:
            _kernel32.GlobalUnlock(h)
    finally:
        _user32.CloseClipboard()


_DIALOG_SCRIPT = r"""
import sys, tkinter as tk
from tkinter import filedialog
root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
kind, initial = sys.argv[1], sys.argv[2]
if kind == 'folder':
    r = filedialog.askdirectory(parent=root, initialdir=initial or None, title='Choose where to save downloads', mustexist=False)
else:
    r = filedialog.askopenfilename(parent=root, initialdir=initial or None, title='Locate yt-dlp.exe',
                                   filetypes=[('yt-dlp', 'yt-dlp*.exe'), ('Programs', '*.exe')])
sys.stdout.write(r or '')
"""


def _run_dialog(kind: str, initial: str) -> str | None:
    """Tk dialogs run in their own process so they never fight with the server's threads."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    exe = sys.executable
    if exe.lower().endswith("pythonw.exe"):
        exe = exe[:-5] + ".exe" if os.path.exists(exe[:-5] + ".exe") else exe
    r = subprocess.run([exe, "-c", _DIALOG_SCRIPT, kind, initial or ""], capture_output=True,
                       env=env, creationflags=NO_WINDOW)
    path = r.stdout.decode("utf-8", "replace").strip()
    return os.path.normpath(path) if path else None


def pick_folder(initial: str = "") -> str | None:
    return _run_dialog("folder", initial if initial and os.path.isdir(initial) else "")


def pick_exe(initial: str = "") -> str | None:
    return _run_dialog("file", initial)


def open_folder(path: str):
    os.makedirs(path, exist_ok=True)
    os.startfile(path)


def reveal_file(path: str):
    if os.path.exists(path):
        subprocess.Popen(f'explorer /select,"{os.path.normpath(path)}"')
    else:
        open_folder(os.path.dirname(path))


def open_file(path: str):
    os.startfile(path)
