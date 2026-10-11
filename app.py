"""yt-dlp Studio: a friendly front end for yt-dlp.

Run `python app.py` (or double-click "yt-dlp Studio.bat"). It starts a local server on
127.0.0.1 and opens the UI in a chromeless Edge window. Closing the window shuts the
server down once no downloads are running.
"""
from __future__ import annotations

import json
import mimetypes
import os
import queue
import secrets
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import ytdlp_core as core
import winutil
from jobs import JobManager
from login import LoginManager

def _port_from_args(default: int = 47815) -> int:
    if "--port" in sys.argv:
        i = sys.argv.index("--port")
        if i + 1 < len(sys.argv) and sys.argv[i + 1].isdigit():
            return int(sys.argv[i + 1])
    return default


PORT = _port_from_args()
HOST = "127.0.0.1"
WEB_DIR = core.APP_DIR / "web"
SETTINGS_FILE = core.DATA_DIR / "settings.json"
TOKEN = secrets.token_urlsafe(24)
INSTANCE = secrets.token_hex(6)
ALLOWED_HOSTS = {f"{HOST}:{PORT}", f"localhost:{PORT}"}
IDLE_EXIT_SECONDS = 40

core.DATA_DIR.mkdir(parents=True, exist_ok=True)
if sys.stdout is None:  # pythonw has no console
    sys.stdout = sys.stderr = open(core.DATA_DIR / "studio.log", "a", encoding="utf-8", buffering=1)


# ---------------------------------------------------------------- settings

DEFAULT_SETTINGS = {
    "options": core.default_options(),
    "ytdlp_path": "",
    "max_concurrent": 2,
    "js_runtime": "auto",
    "fetch_info": True,
    "clipboard_watch": False,
    "auto_start": False,
    "theme": "system",
    "notifications": True,
    "secrets": {},
    "custom_sites": [],          # your own sign-in buttons: [{"name": ..., "url": ...}]
    "recent_folders": [],
    "ui_version": 2,
}
_settings_lock = threading.Lock()


def load_settings() -> dict:
    s = json.loads(json.dumps(DEFAULT_SETTINGS))
    if SETTINGS_FILE.exists():
        try:
            saved = json.loads(SETTINGS_FILE.read_text("utf-8"))
            opts = {**s["options"], **saved.get("options", {})}
            if saved.get("ui_version") != 2:
                # Came from the preset-based layout: queue first, download when you press Download.
                saved["auto_start"] = False
                saved["ui_version"] = 2
            s.update(saved)
            s["options"] = opts
        except (OSError, ValueError) as e:
            print("settings unreadable, using defaults:", e)
    return s


SETTINGS = load_settings()


def save_settings():
    with _settings_lock:
        tmp = SETTINGS_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(SETTINGS, indent=2), "utf-8")
        os.replace(tmp, SETTINGS_FILE)


def have_folder() -> str:
    folder = (SETTINGS["options"].get("folder") or "").strip()
    return folder if folder and os.path.isabs(folder) else ""


def remember_folder(folder: str):
    if not folder:
        return
    rec = [f for f in SETTINGS.get("recent_folders", []) if os.path.normcase(f) != os.path.normcase(folder)]
    SETTINGS["recent_folders"] = [folder] + rec[:7]


# ---------------------------------------------------------------- live events

class Hub:
    def __init__(self):
        self.clients: list[queue.Queue] = []
        self.lock = threading.Lock()
        self.last_seen = time.time()
        self.ever_connected = False

    def connect(self) -> queue.Queue:
        q = queue.Queue(maxsize=2000)
        with self.lock:
            self.clients.append(q)
            self.ever_connected = True
        return q

    def disconnect(self, q):
        with self.lock:
            if q in self.clients:
                self.clients.remove(q)
            self.last_seen = time.time()

    def broadcast(self, event: str, data):
        msg = f"event: {event}\ndata: {json.dumps(data)}\n\n".encode("utf-8")
        with self.lock:
            for q in self.clients:
                try:
                    q.put_nowait(msg)
                except queue.Full:
                    pass

    def count(self) -> int:
        with self.lock:
            return len(self.clients)


HUB = Hub()
JOBS = JobManager(HUB, lambda: SETTINGS)
LOGIN = LoginManager(lambda st: HUB.broadcast("login", st))

_tool_cache: dict = {}


def tool_status(refresh: bool = False) -> dict:
    exe = core.find_ytdlp(SETTINGS)
    if refresh or _tool_cache.get("exe") != exe:
        _tool_cache.clear()
        _tool_cache.update(exe=exe, version=core.ytdlp_version(exe) if exe else None)
    return {
        "ytdlp": exe, "version": _tool_cache.get("version"),
        "ffmpeg": core.find_ffmpeg(), "js": core.detect_js_runtime(SETTINGS),
        "managed": bool(exe) and Path(exe).parent == core.BIN_DIR,
    }


def public_settings() -> dict:
    """Settings for the page: secrets are replaced by yes/no flags and never leave the server."""
    out = {k: v for k, v in SETTINGS.items() if k != "secrets"}
    sec = SETTINGS.get("secrets", {})
    out["secrets"] = {"username": sec.get("username", ""), "has_password": bool(sec.get("password")),
                      "has_video_password": bool(sec.get("video_password"))}
    return out


def full_state() -> dict:
    return {
        "settings": public_settings(), "tools": tool_status(),
        "jobs": JOBS.snapshot(), "cookie_browsers": core.COOKIE_BROWSERS,
        "video_containers": core.VIDEO_CONTAINERS, "audio_formats": core.AUDIO_FORMATS,
        "generic_qualities": core.quality_options([]),
        "default_folder": core.DEFAULT_FOLDER, "instance": INSTANCE, "login": LOGIN.state(),
    }


# ---------------------------------------------------------------- background threads

def clipboard_watcher():
    last_seq = winutil.clipboard_sequence()
    was_on = False
    while True:
        time.sleep(0.6)
        on = SETTINGS.get("clipboard_watch")
        seq = winutil.clipboard_sequence()
        if on and not was_on:
            last_seq = seq          # only react to things copied after switching it on
        was_on = on
        if not on or seq == last_seq:
            continue
        last_seq = seq
        urls = core.extract_urls(winutil.get_clipboard_text() or "")
        if urls and core.find_ytdlp(SETTINGS):
            added, _ = JOBS.add(urls, dict(SETTINGS["options"]), start=bool(SETTINGS.get("auto_start")))
            if added:
                n = len(added)
                HUB.broadcast("toast", {"kind": "ok", "text": f"{n} link{'s' if n > 1 else ''} added from the clipboard."})


def idle_watchdog(server):
    started = time.time()
    while True:
        time.sleep(5)
        if HUB.count() or JOBS.busy():
            HUB.last_seen = time.time()
            continue
        grace = IDLE_EXIT_SECONDS if HUB.ever_connected else 180
        if time.time() - max(HUB.last_seen, started) > grace:
            print("No window open and nothing downloading; exiting.")
            server.shutdown()
            return


def install_ytdlp():
    def progress(done, total):
        HUB.broadcast("install", {"done": done, "total": total})
    try:
        HUB.broadcast("install", {"done": 0, "total": 0})
        core.download_ytdlp(progress)
        SETTINGS["ytdlp_path"] = ""
        save_settings()
        HUB.broadcast("tools", tool_status(refresh=True))
        HUB.broadcast("toast", {"kind": "ok", "text": "yt-dlp installed."})
    except Exception as e:  # noqa: BLE001
        HUB.broadcast("toast", {"kind": "error", "text": f"Couldn't download yt-dlp: {e}"})
        HUB.broadcast("tools", tool_status(refresh=True))


def update_ytdlp():
    exe = core.find_ytdlp(SETTINGS)
    if not exe:
        return install_ytdlp()
    HUB.broadcast("toast", {"kind": "info", "text": "Checking for yt-dlp updates…"})
    r = subprocess.run([exe, "-U"], capture_output=True, creationflags=core.NO_WINDOW, env=core.child_env())
    out = (r.stdout + r.stderr).decode("utf-8", "replace").strip().splitlines()
    last = out[-1] if out else "done"
    HUB.broadcast("tools", tool_status(refresh=True))
    HUB.broadcast("toast", {"kind": "ok" if r.returncode == 0 else "error", "text": last})


# ---------------------------------------------------------------- HTTP

class Handler(BaseHTTPRequestHandler):
    server_version = "yt-dlp-studio"

    def log_message(self, fmt, *args):  # quiet
        pass

    # helpers
    def _send(self, code: int, body: bytes, ctype: str = "application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, data, code: int = 200):
        self._send(code, json.dumps(data).encode("utf-8"))

    def _host_ok(self) -> bool:
        # Blocks DNS-rebinding: only answer to our own loopback address.
        return self.headers.get("Host", "") in ALLOWED_HOSTS

    def _authed(self, query: dict | None = None) -> bool:
        tok = self.headers.get("X-Token") or (query or {}).get("token", [""])[0]
        return self._host_ok() and secrets.compare_digest(tok, TOKEN)

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if not n:
            return {}
        return json.loads(self.rfile.read(n).decode("utf-8"))

    # routes
    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if not self._host_ok():
            return self._send(403, b"forbidden", "text/plain")
        if u.path == "/api/ping":
            return self._json({"app": "yt-dlp-studio", "instance": INSTANCE})
        if u.path == "/api/events":
            if not self._authed(q):
                return self._send(403, b"forbidden", "text/plain")
            return self._events()
        if u.path.startswith("/api/"):
            if not self._authed(q):
                return self._json({"error": "forbidden"}, 403)
            return self._json({"error": "not found"}, 404)
        return self._static(u.path)

    def do_POST(self):
        u = urlparse(self.path)
        if not self._authed():
            return self._json({"error": "forbidden"}, 403)
        try:
            body = self._body()
            result = self._dispatch(u.path, body)
        except Exception as e:  # noqa: BLE001 - report to the UI instead of dropping the connection
            return self._json({"error": str(e)}, 500)
        if result is None:
            return self._json({"error": "not found"}, 404)
        return self._json(result)

    def _dispatch(self, path: str, b: dict):
        if path == "/api/state":
            return full_state()
        if path == "/api/preview":
            opts = {**SETTINGS["options"], **b.get("options", {})}
            return {"command": core.preview_command(opts, core.extract_urls(b.get("text", "")), SETTINGS)}
        if path == "/api/options":
            SETTINGS["options"] = {**SETTINGS["options"], **b.get("options", {})}
            save_settings()
            return {"ok": True}
        if path == "/api/settings":
            allowed = {"ytdlp_path", "max_concurrent", "js_runtime", "fetch_info", "clipboard_watch", "auto_start",
                       "theme", "notifications"}
            for k, v in b.items():
                if k in allowed:
                    SETTINGS[k] = v
            save_settings()
            JOBS.wake.set()
            return {"settings": public_settings(), "tools": tool_status(refresh="ytdlp_path" in b)}
        if path == "/api/add":
            urls = core.extract_urls(b.get("text", ""))
            if not urls:
                return {"added": 0, "dupes": 0, "error": "No links found."}
            if not core.find_ytdlp(SETTINGS):
                return {"added": 0, "dupes": 0, "error": "yt-dlp isn't installed yet."}
            opts = {**SETTINGS["options"], **b.get("options", {})}
            opts.pop("format_override", None)
            SETTINGS["options"] = dict(opts)
            remember_folder(opts.get("folder", ""))
            save_settings()
            start = bool(b.get("start", SETTINGS.get("auto_start"))) and bool(have_folder())
            added, dupes = JOBS.add(urls, opts, start=start)
            return {"added": len(added), "dupes": dupes, "recent_folders": SETTINGS["recent_folders"]}
        if path == "/api/start":
            if not have_folder():
                return {"need_folder": True, "error": "Choose where to save downloads first (Locations)."}
            JOBS.start(b.get("id"))
            return {"ok": True}
        if path == "/api/cancel":
            JOBS.cancel(int(b["id"]))
            return {"ok": True}
        if path == "/api/pause":
            JOBS.cancel(int(b["id"]), pause=True)
            return {"ok": True}
        if path == "/api/cancel-all":
            JOBS.cancel_all(pause=bool(b.get("pause")))
            return {"ok": True}
        if path == "/api/clear":
            JOBS.clear(b.get("which", "all"))
            return {"ok": True}
        if path == "/api/job-options":
            JOBS.set_options(int(b["id"]), b.get("options", {}))
            return {"ok": True}
        if path == "/api/apply-all":
            patch = {k: b[k] for k in ("track", "quality") if k in b}
            SETTINGS["options"].update(patch)
            save_settings()
            JOBS.apply_all(patch)
            return {"ok": True}
        if path == "/api/open-url":
            url = b.get("url", "")
            if not url.lower().startswith(("http://", "https://")):
                return {"error": "Not a web link."}
            os.startfile(url)
            return {"ok": True}
        if path == "/api/secrets":
            sec = SETTINGS.setdefault("secrets", {})
            if "username" in b:
                sec["username"] = (b.get("username") or "").strip()
            for k in ("password", "video_password"):
                if k in b:   # "" clears it; omitted keeps the saved one
                    sec[k] = winutil.protect(b[k]) if b[k] else ""
            save_settings()
            return {"settings": public_settings()}
        if path == "/api/pick-cookies":
            chosen = winutil.pick_cookies_file(b.get("initial", ""))
            return {"path": chosen}
        if path == "/api/remove":
            JOBS.remove(int(b["id"]))
            return {"ok": True}
        if path == "/api/clear-finished":
            JOBS.clear("done")
            return {"ok": True}
        if path == "/api/format":
            JOBS.set_options(int(b["id"]), {"format_override": b.get("format", "")})
            return {"ok": True}
        if path == "/api/job":
            j = JOBS.get(int(b["id"]))
            if not j:
                return {"error": "gone"}
            return {"job": j.to_dict(), "log": list(j.log), "formats": j.formats, "meta": j.meta,
                    "command": core.preview_command(j.opts, [j.url], SETTINGS)}
        if path == "/api/pick-folder":
            chosen = winutil.pick_folder(b.get("initial") or SETTINGS["options"].get("folder", ""))
            if chosen:
                remember_folder(chosen)
                SETTINGS["options"]["folder"] = chosen
                save_settings()
            return {"path": chosen, "recent_folders": SETTINGS["recent_folders"]}
        if path == "/api/forget-folder":
            SETTINGS["recent_folders"] = [f for f in SETTINGS["recent_folders"] if f != b.get("path")]
            save_settings()
            return {"recent_folders": SETTINGS["recent_folders"]}
        if path == "/api/pick-exe":
            chosen = winutil.pick_exe(b.get("initial", ""))
            if chosen:
                SETTINGS["ytdlp_path"] = chosen
                save_settings()
            return {"path": chosen, "tools": tool_status(refresh=True)}
        if path == "/api/open-folder":
            target = b.get("path") or SETTINGS["options"].get("folder")
            if not target:
                return {"error": "No download folder chosen yet."}
            winutil.open_folder(target)
            return {"ok": True}
        if path == "/api/reveal":
            winutil.reveal_file(b["path"])
            return {"ok": True}
        if path == "/api/open-file":
            winutil.open_file(b["path"])
            return {"ok": True}
        if path == "/api/clipboard":
            return {"text": winutil.get_clipboard_text() or ""}
        if path == "/api/ytdlp/install":
            threading.Thread(target=install_ytdlp, daemon=True).start()
            return {"ok": True}
        if path == "/api/ytdlp/update":
            threading.Thread(target=update_ytdlp, daemon=True).start()
            return {"ok": True}
        if path == "/api/tools":
            return tool_status(refresh=True)
        if path == "/api/login/state":
            return LOGIN.state()
        if path == "/api/login/open":
            LOGIN.open_window(b.get("url", ""))
            return LOGIN.state()
        if path == "/api/login/save":
            threading.Thread(target=LOGIN.save, daemon=True).start()
            return {"ok": True}
        if path == "/api/login/forget":
            site = (b.get("site") or "").strip().lower()
            if not site:
                return {"error": "Which site?"}
            threading.Thread(target=LOGIN.forget, args=(site,), daemon=True).start()
            return {"ok": True}
        if path == "/api/login/sites":
            sites = SETTINGS.setdefault("custom_sites", [])
            url = (b.get("url") or "").strip()
            if url and "://" not in url:
                url = "https://" + url
            if b.get("action") == "add":
                if not url.lower().startswith(("http://", "https://")):
                    return {"error": "That doesn't look like a website address."}
                name = (b.get("name") or "").strip()[:40] or urlparse(url).hostname or url
                sites[:] = [s for s in sites if s["url"] != url] + [{"name": name, "url": url}]
            elif b.get("action") == "remove":
                sites[:] = [s for s in sites if s["url"] != url]
            save_settings()
            return {"custom_sites": sites}
        if path == "/api/login/clear":
            LOGIN.clear()
            return LOGIN.state()
        return None

    def _events(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        q = HUB.connect()
        try:
            self.wfile.write(f"event: hello\ndata: {json.dumps(full_state())}\n\n".encode("utf-8"))
            self.wfile.flush()
            while True:
                try:
                    msg = q.get(timeout=15)
                except queue.Empty:
                    msg = b": ping\n\n"
                self.wfile.write(msg)
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
            pass
        finally:
            HUB.disconnect(q)

    def _static(self, path: str):
        if path in ("", "/"):
            path = "/index.html"
        target = (WEB_DIR / path.lstrip("/")).resolve()
        if WEB_DIR.resolve() not in target.parents or not target.is_file():
            return self._send(404, b"not found", "text/plain")
        data = target.read_bytes()
        if target.name == "index.html":
            data = data.replace(b"{{TOKEN}}", TOKEN.encode()).replace(b"{{INSTANCE}}", INSTANCE.encode())
        ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript",):
            ctype += "; charset=utf-8"
        self._send(200, data, ctype)


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False


# ---------------------------------------------------------------- launch

def open_window(url: str):
    if "--no-window" in sys.argv:
        return
    edge_paths = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
    ]
    edge = next((p for p in edge_paths if os.path.isfile(p)), None) or shutil.which("msedge")
    if edge:
        # Its own profile keeps Studio out of your normal Edge history and makes uninstalling clean.
        profile = core.DATA_DIR / "window-profile"
        subprocess.Popen([edge, f"--app={url}", "--window-size=1360,900", f"--user-data-dir={profile}",
                          "--no-first-run", "--no-default-browser-check"])
    else:
        webbrowser.open(url)


def already_running() -> bool:
    try:
        with urllib.request.urlopen(f"http://{HOST}:{PORT}/api/ping", timeout=2) as r:
            return json.loads(r.read()).get("app") == "yt-dlp-studio"
    except Exception:  # noqa: BLE001
        return False


def main():
    mimetypes.add_type("application/javascript", ".js")
    mimetypes.add_type("text/css", ".css")
    url = f"http://{HOST}:{PORT}/"
    try:
        server = Server((HOST, PORT), Handler)
    except OSError:
        if already_running():
            open_window(url)
            return
        raise
    threading.Thread(target=clipboard_watcher, daemon=True).start()
    if "--stay" not in sys.argv:
        threading.Thread(target=idle_watchdog, args=(server,), daemon=True).start()
    print(f"yt-dlp Studio running at {url}")
    open_window(url)
    server.serve_forever()


if __name__ == "__main__":
    main()
