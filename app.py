"""yt-dlp Studio: a friendly front end for yt-dlp.

Run `python app.py` (or double-click "yt-dlp Studio.bat"). It starts a local server on
127.0.0.1 (port 47815; change with --port N) and opens the UI in a chromeless Edge window. Closing the window shuts the
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

def _port_from_args(default: int = 47815) -> int:
    if "--port" in sys.argv:
        i = sys.argv.index("--port")
        if i + 1 < len(sys.argv) and sys.argv[i + 1].isdigit():
            return int(sys.argv[i + 1])
    return int(os.environ.get("STUDIO_PORT", default))


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
    "auto_start": True,
    "user_presets": [],
    "recent_folders": [],
}
_settings_lock = threading.Lock()


def load_settings() -> dict:
    s = json.loads(json.dumps(DEFAULT_SETTINGS))
    if SETTINGS_FILE.exists():
        try:
            saved = json.loads(SETTINGS_FILE.read_text("utf-8"))
            opts = {**s["options"], **saved.get("options", {})}
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


def full_state() -> dict:
    return {
        "settings": SETTINGS, "presets": core.PRESETS, "tools": tool_status(),
        "jobs": JOBS.snapshot(), "cookie_browsers": core.COOKIE_BROWSERS,
        "default_folder": core.DEFAULT_FOLDER, "instance": INSTANCE,
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
        if urls:
            HUB.broadcast("clip", {"urls": urls})


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
            allowed = {"ytdlp_path", "max_concurrent", "js_runtime", "fetch_info", "clipboard_watch", "auto_start"}
            for k, v in b.items():
                if k in allowed:
                    SETTINGS[k] = v
            save_settings()
            JOBS.wake.set()
            return {"settings": SETTINGS, "tools": tool_status(refresh="ytdlp_path" in b)}
        if path == "/api/add":
            urls = core.extract_urls(b.get("text", ""))
            if not urls:
                return {"added": 0, "dupes": 0, "error": "No links found."}
            if not core.find_ytdlp(SETTINGS):
                return {"added": 0, "dupes": 0, "error": "yt-dlp isn't installed yet."}
            opts = {**SETTINGS["options"], **b.get("options", {})}
            folder = (opts.get("folder") or "").strip()
            if not folder or not os.path.isabs(folder):
                return {"added": 0, "dupes": 0, "need_folder": True,
                        "error": "Choose where to save downloads first (click Browse…)."}
            opts.pop("format_override", None)
            SETTINGS["options"] = dict(opts)
            remember_folder(opts.get("folder", ""))
            save_settings()
            added, dupes = JOBS.add(urls, opts, start=bool(b.get("start", True)))
            return {"added": len(added), "dupes": dupes, "recent_folders": SETTINGS["recent_folders"]}
        if path == "/api/start":
            JOBS.start(b.get("id"))
            return {"ok": True}
        if path == "/api/cancel":
            JOBS.cancel(int(b["id"]))
            return {"ok": True}
        if path == "/api/remove":
            JOBS.remove(int(b["id"]))
            return {"ok": True}
        if path == "/api/clear-finished":
            JOBS.clear_finished()
            return {"ok": True}
        if path == "/api/format":
            JOBS.set_format(int(b["id"]), b.get("format", ""))
            return {"ok": True}
        if path == "/api/job":
            j = JOBS.get(int(b["id"]))
            if not j:
                return {"error": "gone"}
            return {"job": j.to_dict(), "log": list(j.log), "formats": j.formats,
                    "command": core.preview_command(j.opts, [j.url], SETTINGS)}
        if path == "/api/presets/save":
            name = (b.get("name") or "").strip()[:40] or "My preset"
            p = {"id": "user-" + secrets.token_hex(4), "label": name,
                 "options": {k: v for k, v in b.get("options", {}).items() if k != "format_override"}}
            SETTINGS["user_presets"].append(p)
            save_settings()
            return {"user_presets": SETTINGS["user_presets"]}
        if path == "/api/presets/delete":
            SETTINGS["user_presets"] = [p for p in SETTINGS["user_presets"] if p["id"] != b.get("id")]
            save_settings()
            return {"user_presets": SETTINGS["user_presets"]}
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
                return {"error": "No folder chosen yet."}
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
        subprocess.Popen([edge, f"--app={url}", "--window-size=1360,900"])
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
