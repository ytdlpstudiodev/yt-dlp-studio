"""Small Windows helpers: clipboard, native folder/file dialogs, Explorer."""
from __future__ import annotations

import base64
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


class _Blob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]


_crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
_crypt32.CryptProtectData.argtypes = [ctypes.POINTER(_Blob), wintypes.LPCWSTR, ctypes.POINTER(_Blob),
                                      ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(_Blob)]
_crypt32.CryptUnprotectData.argtypes = [ctypes.POINTER(_Blob), ctypes.c_void_p, ctypes.POINTER(_Blob),
                                        ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(_Blob)]
_kernel32.LocalFree.argtypes = [ctypes.c_void_p]


def _dpapi(data: bytes, encrypt: bool) -> bytes:
    buf = ctypes.create_string_buffer(data, len(data))
    src, out = _Blob(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char))), _Blob()
    fn = _crypt32.CryptProtectData if encrypt else _crypt32.CryptUnprotectData
    desc = "yt-dlp Studio" if encrypt else None
    if not fn(ctypes.byref(src), desc, None, None, None, 0x1, ctypes.byref(out)):  # 0x1 = no UI
        raise OSError(ctypes.get_last_error(), "Windows couldn't encrypt/decrypt the secret")
    try:
        return ctypes.string_at(out.pbData, out.cbData)
    finally:
        _kernel32.LocalFree(out.pbData)


def protect(text: str) -> str:
    """Encrypt with Windows DPAPI: only this Windows user on this PC can decrypt it."""
    return base64.b64encode(_dpapi(text.encode("utf-8"), True)).decode()


def unprotect(blob: str) -> str:
    try:
        return _dpapi(base64.b64decode(blob), False).decode("utf-8")
    except (OSError, ValueError):
        return ""


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
elif kind == 'cookies':
    r = filedialog.askopenfilename(parent=root, initialdir=initial or None, title='Choose a cookies.txt file',
                                   filetypes=[('Cookie files', '*.txt'), ('All files', '*.*')])
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


def pick_cookies_file(initial: str = "") -> str | None:
    return _run_dialog("cookies", os.path.dirname(initial) if initial else "")


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
