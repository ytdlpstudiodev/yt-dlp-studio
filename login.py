"""Site sign-ins: a private Edge/Chrome profile you log into, exported as a cookies.txt for yt-dlp.

The sign-in window is a completely normal browser window (no automation flags), so sites like
Google accept the login. Once it is closed, the same profile is opened headless with a DevTools
port just long enough to read its cookies. Reading them through the browser itself avoids the
"app-bound" cookie encryption that stops yt-dlp's --cookies-from-browser on Windows.
"""
from __future__ import annotations

import base64
import json
import os
import shutil
import socket
import struct
import subprocess
import threading
import time
import urllib.request
from pathlib import Path

import winutil
import ytdlp_core as core

PROFILE_DIR = core.DATA_DIR / "browser-profile"
COOKIE_FILE = core.COOKIE_FILE
TMP_DIR = core.DATA_DIR / "tmp"

# Edge signs new profiles in to the Windows Microsoft account and turns on sync, which would send
# Studio's browsing to your main Edge (and copy your synced data into Studio's folder). These
# switches stop that for browsers Studio launches only; your normal Edge is not affected.
NO_SIGNIN_FEATURES = [
    "msImplicitSignin", "msM365LinksImplicitSignin", "msOneAuthWAM", "msForceOneAuthWAM",
    "msBrowserLaunchSignedInMSATrigger", "msEnableProfileAADAccountSSO", "msProfileSignIn",
    "msSeamlessWebToBrowserSignIn", "msQuickAuthToBrowserSignIn", "msEnableWebToBrowserSignIn",
    "msEnableAADWebToBrowserSignIn", "msSignInWithMSAAccount", "msCombinedSyncSignIn",
    "msAutoToggleMSAPrtSSOForNonMSAProfile", "msAllowMSAPrtSSOForNonMSAProfile",
]
NO_SIGNIN_FLAGS = ["--disable-sync", "--disable-features=" + ",".join(NO_SIGNIN_FEATURES)]

QUICK_SITES = [
    ("YouTube", "https://accounts.google.com/ServiceLogin?service=youtube&continue=https%3A%2F%2Fwww.youtube.com%2F"),
    ("Vimeo", "https://vimeo.com/log_in"),
    ("Patreon", "https://www.patreon.com/login"),
    ("Twitch", "https://www.twitch.tv/login"),
    ("Instagram", "https://www.instagram.com/accounts/login/"),
    ("X / Twitter", "https://x.com/login"),
    ("Facebook", "https://www.facebook.com/login"),
    ("TikTok", "https://www.tiktok.com/login"),
    ("Reddit", "https://www.reddit.com/login/"),
    ("Nebula", "https://nebula.tv/login"),
]


def find_browser() -> str | None:
    candidates = [
        r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe",
        r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe",
        r"%ProgramFiles%\Google\Chrome\Application\chrome.exe",
        r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe",
        r"%LocalAppData%\Google\Chrome\Application\chrome.exe",
    ]
    for c in candidates:
        p = os.path.expandvars(c)
        if os.path.isfile(p):
            return p
    return shutil.which("msedge") or shutil.which("chrome")


def profile_in_use() -> bool:
    """Chromium holds <profile>/lockfile open (write-exclusive) while it runs."""
    lock = PROFILE_DIR / "lockfile"
    if not lock.exists():
        return False
    try:
        with open(lock, "a"):
            return False
    except PermissionError:
        return True
    except OSError:
        return False


def _profile_pids() -> list[int]:
    """PIDs of browser processes started with our profile folder."""
    needle = str(PROFILE_DIR).replace("'", "''")
    ps = ("Get-CimInstance Win32_Process -Filter \"Name='msedge.exe' or Name='chrome.exe'\" | "
          f"Where-Object {{ $_.CommandLine -like '*{needle}*' }} | ForEach-Object {{ $_.ProcessId }}")
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True,
                       creationflags=core.NO_WINDOW, timeout=30)
    return [int(x) for x in r.stdout.split() if x.strip().isdigit()]


def close_profile_browser(timeout: float = 10) -> None:
    """Ask the sign-in browser to close (like clicking X), force it only if it won't."""
    if not profile_in_use():
        return
    pids = _profile_pids()
    for pid in pids:
        subprocess.run(["taskkill", "/PID", str(pid)], capture_output=True, creationflags=core.NO_WINDOW)
    end = time.time() + timeout
    while time.time() < end:
        if not profile_in_use():
            return
        time.sleep(0.3)
    for pid in pids:
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, creationflags=core.NO_WINDOW)
    time.sleep(1)


def profile_signed_in(profile: Path = None) -> bool:
    """True if the browser has signed this profile in to an account (and may be syncing it)."""
    ls = (profile or PROFILE_DIR) / "Local State"
    if not ls.exists():
        return False
    try:
        info = json.loads(ls.read_text("utf-8", "replace")).get("profile", {}).get("info_cache", {}).get("Default", {})
    except (OSError, ValueError):
        return False
    return bool(info.get("user_name") or info.get("edge_account_type") or info.get("gaia_id"))


_COOKIE_PARAM_KEYS = ("name", "value", "domain", "path", "secure", "httpOnly", "sameSite", "priority",
                      "sourceScheme", "sourcePort", "partitionKey")


def rebuild_profile(browser: str) -> int:
    """Replace a signed-in profile with a clean one, carrying the site logins (cookies) across."""
    close_profile_browser()
    cookies = read_profile_cookies(browser) if PROFILE_DIR.exists() else []
    shutil.rmtree(PROFILE_DIR, ignore_errors=True)
    if PROFILE_DIR.exists():
        raise RuntimeError("Couldn't reset the sign-in browser profile (files in use).")
    _prepare_profile()
    params = []
    for c in cookies:
        p = {k: c[k] for k in _COOKIE_PARAM_KEYS if k in c and c[k] not in (None, "")}
        if not c.get("session") and (c.get("expires") or -1) > 0:
            p["expires"] = c["expires"]
        params.append(p)

    def work(ws, port):
        restored = 0
        for p in params:
            try:
                ws.call("Storage.setCookies", {"cookies": [p]})
                restored += 1
            except RuntimeError:
                pass   # e.g. an already-expired cookie
        return restored
    return _devtools_session(browser, work) if params else 0


def _prepare_profile() -> None:
    """Create the profile and switch off 'keep running in background' so closing the window really exits."""
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    ls = PROFILE_DIR / "Local State"
    try:
        state = json.loads(ls.read_text("utf-8")) if ls.exists() else {}
    except (OSError, ValueError):
        state = {}
    if state.get("background_mode", {}).get("enabled") is not False:
        state.setdefault("background_mode", {})["enabled"] = False
        ls.write_text(json.dumps(state), "utf-8")


# ---------------------------------------------------------------- tiny websocket client (DevTools)

class _WebSocket:
    def __init__(self, port: int, path: str, timeout: float = 30):
        self.sock = socket.create_connection(("127.0.0.1", port), timeout=timeout)
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall((f"GET {path} HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nUpgrade: websocket\r\n"
                           f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        self.buf = bytearray()
        while b"\r\n\r\n" not in self.buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("DevTools closed the connection")
            self.buf += chunk
        head, _, rest = bytes(self.buf).partition(b"\r\n\r\n")
        if b" 101 " not in head.split(b"\r\n", 1)[0]:
            raise ConnectionError("DevTools refused the connection: " + head.split(b"\r\n", 1)[0].decode("latin-1"))
        self.buf = bytearray(rest)
        self.next_id = 0

    def _read(self, n: int) -> bytes:
        while len(self.buf) < n:
            chunk = self.sock.recv(1 << 16)
            if not chunk:
                raise ConnectionError("DevTools connection closed")
            self.buf += chunk
        out = bytes(self.buf[:n])
        del self.buf[:n]
        return out

    def _send_frame(self, opcode: int, data: bytes) -> None:
        hdr = bytearray([0x80 | opcode])
        n = len(data)
        if n < 126:
            hdr.append(0x80 | n)
        elif n < 65536:
            hdr.append(0x80 | 126)
            hdr += struct.pack(">H", n)
        else:
            hdr.append(0x80 | 127)
            hdr += struct.pack(">Q", n)
        mask = os.urandom(4)
        masked = bytes(b ^ mask[i & 3] for i, b in enumerate(data))
        self.sock.sendall(bytes(hdr) + mask + masked)

    def _recv_text(self) -> str:
        parts = []
        while True:
            b1, b2 = self._read(2)
            opcode, fin = b1 & 0x0F, b1 & 0x80
            n = b2 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._read(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._read(8))[0]
            payload = self._read(n)
            if opcode == 0x8:
                raise ConnectionError("DevTools closed the connection")
            if opcode == 0x9:
                self._send_frame(0xA, payload)
                continue
            if opcode in (0x0, 0x1, 0x2):
                parts.append(payload)
                if fin:
                    return b"".join(parts).decode("utf-8", "replace")

    def call(self, method: str, params: dict | None = None) -> dict:
        self.next_id += 1
        self._send_frame(0x1, json.dumps({"id": self.next_id, "method": method, "params": params or {}}).encode())
        while True:
            msg = json.loads(self._recv_text())
            if msg.get("id") == self.next_id:
                if "error" in msg:
                    raise RuntimeError(msg["error"].get("message", "DevTools error"))
                return msg.get("result", {})

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


def read_profile_cookies(browser: str, start_url: str = "about:blank", settle: float = 0) -> list[dict]:
    """Open the profile headless, read every cookie through DevTools, then shut it down."""
    def work(ws, port):
        if settle:
            time.sleep(settle)
        return ws.call("Storage.getCookies").get("cookies", [])
    return _devtools_session(browser, work, start_url)


def remove_site_cookies(browser: str, site: str) -> list[dict]:
    """Delete one site's cookies inside the sign-in profile; returns the cookies that remain."""
    def work(ws, port):
        doomed = [c for c in ws.call("Storage.getCookies").get("cookies", []) if _base_domain(c.get("domain", "")) == site]
        pages = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=10))
        page = next((p for p in pages if p.get("type") == "page"), None)
        if page is None:
            raise RuntimeError("Couldn't open the sign-in profile to remove the login.")
        pws = _WebSocket(port, "/devtools/page/" + page["id"])
        try:
            for c in doomed:
                pws.call("Network.deleteCookies", {"name": c["name"], "domain": c["domain"], "path": c.get("path") or "/"})
        finally:
            pws.close()
        return ws.call("Storage.getCookies").get("cookies", [])
    return _devtools_session(browser, work)


def _devtools_session(browser: str, work, start_url: str = "about:blank"):
    """Run work(browser_ws, port) against the sign-in profile opened headless, then shut it down."""
    port_file = PROFILE_DIR / "DevToolsActivePort"
    port_file.unlink(missing_ok=True)
    proc = subprocess.Popen([browser, "--headless=new", f"--user-data-dir={PROFILE_DIR}",
                             "--remote-debugging-port=0", "--no-first-run", "--no-default-browser-check",
                             "--disable-extensions", *NO_SIGNIN_FLAGS, start_url],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=core.NO_WINDOW)
    try:
        end = time.time() + 25
        lines = []
        while time.time() < end:
            if port_file.exists():
                lines = port_file.read_text().split()
                if len(lines) >= 2:
                    break
            if proc.poll() is not None:
                raise RuntimeError("The browser closed before Studio could read the login.")
            time.sleep(0.2)
        if len(lines) < 2:
            raise RuntimeError("Timed out waiting for the browser.")
        ws = _WebSocket(int(lines[0]), lines[1])
        try:
            result = work(ws, int(lines[0]))
            try:
                ws.call("Browser.close")
            except (ConnectionError, OSError):
                pass
        finally:
            ws.close()
        return result
    finally:
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True,
                           creationflags=core.NO_WINDOW)
        # Edge's helper processes can hold the profile for a few seconds after the main one exits.
        end = time.time() + 12
        while profile_in_use() and time.time() < end:
            time.sleep(0.3)
        if profile_in_use():
            for pid in _profile_pids():
                subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True,
                               creationflags=core.NO_WINDOW)
            time.sleep(0.5)


def write_cookie_file(cookies: list[dict], path: Path = COOKIE_FILE) -> int:
    """Netscape cookies.txt, the format yt-dlp's --cookies reads."""
    lines = ["# Netscape HTTP Cookie File", "# Written by yt-dlp Studio. Contains your sign-ins: keep it private.", ""]
    n = 0
    for c in cookies:
        name, value, domain = c.get("name", ""), c.get("value", ""), c.get("domain", "")
        if not domain or any(ch in f"{name}{value}" for ch in "\t\r\n"):
            continue
        exp = c.get("expires", -1)
        exp = 0 if (c.get("session") or exp is None or exp < 0) else int(exp)
        lines.append("\t".join([
            domain, "TRUE" if domain.startswith(".") else "FALSE", c.get("path") or "/",
            "TRUE" if c.get("secure") else "FALSE", str(exp), name, value,
        ]))
        n += 1
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text("\n".join(lines) + "\n", "utf-8")
    os.replace(tmp, path)
    return n


def _base_domain(d: str) -> str:
    parts = d.lstrip(".").lower().split(".")
    if len(parts) >= 3 and len(parts[-1]) == 2 and parts[-2] in ("co", "com", "net", "org", "ac", "gov", "edu"):
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def saved_sites() -> list[dict]:
    if not COOKIE_FILE.exists():
        return []
    counts: dict[str, int] = {}
    for line in COOKIE_FILE.read_text("utf-8", "replace").splitlines():
        if not line or line.startswith("#"):
            continue
        d = line.split("\t", 1)[0]
        b = _base_domain(d)
        counts[b] = counts.get(b, 0) + 1
    return [{"site": s, "cookies": n} for s, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]


def cookie_copy(tag: str, src: str | Path | None = None) -> str | None:
    """Each yt-dlp run gets its own copy, since yt-dlp writes the file back when it exits."""
    src = Path(src) if src else COOKIE_FILE
    if not src.exists():
        return None
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    dst = TMP_DIR / f"cookies-{tag}.txt"
    shutil.copyfile(src, dst)
    return str(dst)


# ---------------------------------------------------------------- manager used by the server

class LoginManager:
    def __init__(self, on_change):
        self.on_change = on_change
        self.lock = threading.Lock()
        self.watching = False      # we opened a sign-in window and will save when it closes
        self.seen_open = False
        self.opened_at = 0.0
        self.busy = False
        self.error = None
        self.last_count = None
        self.notice = None
        threading.Thread(target=self._watch, daemon=True).start()
        threading.Thread(target=self.repair_if_signed_in, daemon=True).start()

    def state(self) -> dict:
        saved_at = COOKIE_FILE.stat().st_mtime if COOKIE_FILE.exists() else None
        return {
            "browser": find_browser(), "window_open": self.watching and profile_in_use(),
            "waiting": self.watching, "busy": self.busy, "error": self.error,
            "saved_at": saved_at, "sites": saved_sites(), "quick_sites": QUICK_SITES,
            "last_count": self.last_count, "notice": self.notice,
        }

    def _changed(self):
        try:
            self.on_change(self.state())
        except Exception as e:  # noqa: BLE001
            print("login state broadcast failed:", e)

    def open_window(self, url: str) -> None:
        browser = find_browser()
        if not browser:
            raise RuntimeError("Signing in needs Microsoft Edge or Google Chrome.")
        url = (url or "").strip()
        if url and "://" not in url:
            url = "https://" + url
        if not profile_in_use():
            self.repair_if_signed_in()
            _prepare_profile()
        subprocess.Popen([browser, f"--user-data-dir={PROFILE_DIR}", "--no-first-run",
                          "--no-default-browser-check", "--new-window", "--window-size=1100,820",
                          *NO_SIGNIN_FLAGS, url or "about:blank"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with self.lock:
            self.watching, self.seen_open, self.opened_at, self.error = True, False, time.time(), None
        self._changed()
        threading.Thread(target=self._raise_window, daemon=True).start()

    @staticmethod
    def _raise_window():
        """Windows keeps windows opened by background programs behind the active one; pull it forward."""
        end = time.time() + 15
        while time.time() < end:
            time.sleep(0.5)
            pids = set(_profile_pids())
            wins = winutil.windows_of(pids) if pids else []
            if wins:
                time.sleep(0.4)            # let it finish drawing
                for hwnd in winutil.windows_of(pids)[:1]:
                    winutil.bring_to_front(hwnd)
                return

    def repair_if_signed_in(self) -> bool:
        """Undo Edge's automatic Microsoft-account sign-in on Studio's profile, keeping site logins."""
        if not PROFILE_DIR.exists() or not profile_signed_in() or profile_in_use():
            return False
        browser = find_browser()
        if not browser:
            return False
        with self.lock:
            self.busy = True
        self._changed()
        try:
            n = rebuild_profile(browser)
            self.notice = (f"Studio's sign-in browser had been signed in to your Microsoft account by Edge. "
                           f"It has been reset to a private, signed-out profile; {n} saved site cookies were kept.")
            print(self.notice)
            return True
        except Exception as e:  # noqa: BLE001
            self.error = f"Couldn't reset the sign-in profile: {e}"
            return False
        finally:
            self.busy = False
            self._changed()

    def forget(self, site: str) -> None:
        """Sign out of one site: remove its cookies from the profile and the saved file."""
        with self.lock:
            if self.busy:
                return
            self.busy, self.error, self.watching = True, None, False
        self._changed()
        try:
            browser = find_browser()
            if not browser:
                raise RuntimeError("Removing a login needs Microsoft Edge or Google Chrome.")
            if PROFILE_DIR.exists():
                close_profile_browser()
                remaining = remove_site_cookies(browser, site)
            else:
                remaining = []
            if remaining or COOKIE_FILE.exists():
                write_cookie_file(remaining)
            if not remaining:
                COOKIE_FILE.unlink(missing_ok=True)
            self.last_count = None
        except Exception as e:  # noqa: BLE001
            self.error = str(e)
        finally:
            self.busy = False
            self._changed()

    def save(self) -> None:
        """Close the sign-in window if needed and export cookies. Runs in a worker thread."""
        with self.lock:
            if self.busy:
                return
            self.busy, self.error = True, None
            self.watching = False
        self._changed()
        try:
            browser = find_browser()
            if not browser:
                raise RuntimeError("Signing in needs Microsoft Edge or Google Chrome.")
            if not PROFILE_DIR.exists():
                raise RuntimeError("Sign in to a site first.")
            close_profile_browser()
            cookies = read_profile_cookies(browser)
            self.last_count = write_cookie_file(cookies)
        except Exception as e:  # noqa: BLE001
            self.error = str(e)
        finally:
            self.busy = False
            self._changed()

    def clear(self) -> None:
        close_profile_browser()
        self.watching = False
        shutil.rmtree(PROFILE_DIR, ignore_errors=True)
        COOKIE_FILE.unlink(missing_ok=True)
        if TMP_DIR.exists():
            for p in TMP_DIR.glob("cookies-*.txt"):
                p.unlink(missing_ok=True)
        self.error, self.last_count = None, None
        self._changed()

    def _watch(self):
        """Save automatically once the sign-in window we opened has been closed."""
        while True:
            time.sleep(1.2)
            if not self.watching or self.busy:
                continue
            running = profile_in_use()
            if running and not self.seen_open:
                self.seen_open = True
                self._changed()
            elif not running and (self.seen_open or time.time() - self.opened_at > 20):
                self.save()
