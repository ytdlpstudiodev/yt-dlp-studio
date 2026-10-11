"""yt-dlp knowledge: where the binary lives, presets, and turning UI options into arguments."""
from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import urllib.request
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
BIN_DIR = APP_DIR / "bin"
DATA_DIR = APP_DIR / "data"
YTDLP_DOWNLOAD_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# One line per progress tick. Title goes last because it may contain the separator.
PROGRESS_PREFIX = "@@P|"
PROGRESS_TEMPLATE = (
    "download:" + PROGRESS_PREFIX
    + "%(progress.downloaded_bytes)s|%(progress.total_bytes)s|%(progress.total_bytes_estimate)s|"
    "%(progress.speed)s|%(progress.eta)s|%(info.title)s"
)

SUB_LANGS = "en.*,-live_chat"

PRESETS = [
    {"id": "video-mp4", "kind": "video", "icon": "film", "label": "Best video",
     "sub": "MP4 · highest resolution",
     "args": ["-S", "res,ext:mp4:m4a", "--merge-output-format", "mp4"]},
    {"id": "video-1080", "kind": "video", "icon": "film", "label": "1080p",
     "sub": "MP4 · up to 1080p",
     "args": ["-S", "res:1080,ext:mp4:m4a", "--merge-output-format", "mp4"]},
    {"id": "video-720", "kind": "video", "icon": "film", "label": "720p",
     "sub": "MP4 · smaller files",
     "args": ["-S", "res:720,ext:mp4:m4a", "--merge-output-format", "mp4"]},
    {"id": "video-max", "kind": "video", "icon": "spark", "label": "Max quality",
     "sub": "MKV · any codec (AV1/VP9)",
     "args": ["-f", "bv*+ba/b", "--merge-output-format", "mkv"]},
    {"id": "audio-mp3", "kind": "audio", "icon": "music", "label": "MP3",
     "sub": "Best quality VBR",
     "args": ["-f", "ba/b", "-x", "--audio-format", "mp3", "--audio-quality", "0"]},
    {"id": "audio-m4a", "kind": "audio", "icon": "music", "label": "M4A",
     "sub": "AAC · phone friendly",
     "args": ["-f", "ba[ext=m4a]/ba/b", "-x", "--audio-format", "m4a"]},
    {"id": "audio-best", "kind": "audio", "icon": "wave", "label": "Original audio",
     "sub": "No re-encoding",
     "args": ["-f", "ba/b", "-x"]},
    {"id": "subs", "kind": "extra", "icon": "captions", "label": "Subtitles only",
     "sub": "SRT · English",
     "args": ["--skip-download", "--write-subs", "--write-auto-subs",
              "--sub-langs", SUB_LANGS, "--convert-subs", "srt"]},
    {"id": "thumb", "kind": "extra", "icon": "image", "label": "Thumbnail only",
     "sub": "JPG",
     "args": ["--skip-download", "--write-thumbnail", "--convert-thumbnails", "jpg"]},
    {"id": "custom", "kind": "custom", "icon": "terminal", "label": "Custom",
     "sub": "Only your extra arguments",
     "args": []},
]
PRESET_MAP = {p["id"]: p for p in PRESETS}

TEMPLATES = {
    "title": "%(title)s.%(ext)s",
    "title_id": "%(title)s [%(id)s].%(ext)s",
    "uploader_title": "%(uploader,channel|Unknown)s - %(title)s.%(ext)s",
    "date_title": "%(upload_date>%Y-%m-%d)s - %(title)s.%(ext)s",
}

# No default: people pick their own download folder the first time.
DEFAULT_FOLDER = ""

COOKIE_BROWSERS = ["edge", "chrome", "firefox", "brave", "opera", "vivaldi"]

URL_RE = re.compile(r"""(?:https?://|www\.)[^\s<>"'`]+""", re.IGNORECASE)


def default_options() -> dict:
    return {
        "preset": "video-mp4",
        "folder": DEFAULT_FOLDER,
        "on_exists": "keep_both",
        "template": "title",
        "template_custom": "%(title)s.%(ext)s",
        "playlist": "single",
        "playlist_items": "",
        "playlist_folder": True,
        "embed_thumbnail": True,
        "embed_metadata": True,
        "embed_chapters": True,
        "embed_subs": False,
        "sponsorblock": False,
        "archive": False,
        "restrict_names": False,
        "cookies": "",
        "rate_limit": "",
        "extra": "",
    }


def extract_urls(text: str) -> list[str]:
    """Pull every link out of arbitrary pasted text, in order, without duplicates."""
    seen, out = set(), []
    for m in URL_RE.finditer(text or ""):
        url = m.group(0).rstrip(".,;:!?)]}>'\"")
        if url.lower().startswith("www."):
            url = "https://" + url
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out


# ---------------------------------------------------------------- binaries

def find_ytdlp(settings: dict) -> str | None:
    custom = (settings.get("ytdlp_path") or "").strip()
    if custom and os.path.isfile(custom):
        return custom
    local = BIN_DIR / "yt-dlp.exe"
    if local.is_file():
        return str(local)
    return shutil.which("yt-dlp")


def find_ffmpeg() -> str | None:
    local = BIN_DIR / "ffmpeg.exe"
    if local.is_file():
        return str(local)
    return shutil.which("ffmpeg")


def detect_js_runtime(settings: dict) -> str | None:
    """yt-dlp needs a JS runtime for full YouTube support. Deno is on by default; others must be enabled."""
    choice = settings.get("js_runtime", "auto")
    if choice == "none":
        return None
    if choice != "auto":
        return choice
    for rt in ("deno", "node", "bun"):
        if shutil.which(rt):
            return rt
    return None


def ytdlp_version(exe: str) -> str | None:
    try:
        r = subprocess.run([exe, "--version"], capture_output=True, text=True,
                           timeout=30, creationflags=NO_WINDOW)
        return r.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def download_ytdlp(progress_cb=None) -> str:
    """Fetch the official yt-dlp.exe from GitHub releases into ./bin."""
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    dest = BIN_DIR / "yt-dlp.exe"
    part = dest.with_suffix(".exe.part")
    req = urllib.request.Request(YTDLP_DOWNLOAD_URL, headers={"User-Agent": "yt-dlp-studio"})
    with urllib.request.urlopen(req, timeout=60) as resp, open(part, "wb") as f:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        while True:
            chunk = resp.read(256 * 1024)
            if not chunk:
                break
            f.write(chunk)
            done += len(chunk)
            if progress_cb:
                progress_cb(done, total)
    os.replace(part, dest)
    return str(dest)


# ---------------------------------------------------------------- arguments

def _strip_flags(args: list[str], flags: set[str]) -> list[str]:
    out, skip = [], False
    for a in args:
        if skip:
            skip = False
            continue
        if a in flags:
            skip = True
            continue
        out.append(a)
    return out


PLAYLIST_URL_RE = re.compile(r"[?&]list=|/playlist|/channel/|/@[^/]+/?(?:videos|streams|shorts)?/?$|/c/|/user/|/sets/|/album/", re.I)


def looks_like_playlist(url: str) -> bool:
    return bool(PLAYLIST_URL_RE.search(url or ""))


def output_template(opts: dict, is_playlist: bool = False) -> str:
    key = opts.get("template", "title")
    tpl = (opts.get("template_custom") or "").strip() if key == "custom" else TEMPLATES.get(key)
    tpl = tpl or TEMPLATES["title"]
    if opts.get("playlist") == "all":
        # The index only appears for playlist entries; single videos keep the plain name.
        tpl = "%(playlist_index&{} - |)s" + tpl
        # yt-dlp strips "/" produced inside a field, so the folder has to be a literal
        # path part, which is only safe when we know the link really is a playlist.
        if opts.get("playlist_folder") and is_playlist:
            tpl = "%(playlist_title,playlist_id|Playlist)s/" + tpl
    return tpl


def split_extra(extra: str) -> list[str]:
    extra = (extra or "").strip()
    if not extra:
        return []
    # Keep Windows backslashes intact while still honouring quotes.
    return shlex.split(extra.replace("\\", "\\\\"))


def network_args(opts: dict, settings: dict) -> list[str]:
    """Arguments that affect what yt-dlp can see, shared by downloads and info lookups."""
    a = ["--yes-playlist" if opts.get("playlist") == "all" else "--no-playlist"]
    if opts.get("cookies") in COOKIE_BROWSERS:
        a += ["--cookies-from-browser", opts["cookies"]]
    rt = detect_js_runtime(settings)
    if rt and rt != "deno":
        a += ["--js-runtimes", rt]
    return a


def build_args(opts: dict, urls: list[str], settings: dict, internal: bool = False,
               print_file: str | None = None, staging: str | None = None,
               is_playlist: bool | None = None) -> list[str]:
    """UI options -> yt-dlp argument list (without the executable).

    internal=True adds the machine-readable progress flags the app needs; the
    preview shown to the user leaves them out so it is a command they could run.
    staging: download into this folder instead (the app moves files out afterwards
    so an existing file with the same name never blocks or gets overwritten).
    """
    preset = PRESET_MAP.get(opts.get("preset")) or PRESETS[0]
    pargs = list(preset["args"])
    fmt = (opts.get("format_override") or "").strip()
    if fmt:
        pargs = _strip_flags(pargs, {"-f", "-S", "--format", "--format-sort"}) + ["-f", fmt]
    skip_dl = "--skip-download" in pargs
    kind = preset["kind"]

    a: list[str] = []
    if internal:
        a += ["--newline", "--encoding", "utf-8", "--progress-template", PROGRESS_TEMPLATE]
        if print_file:
            a += ["--print-to-file", "after_move:%(filepath)s", print_file]
    a += pargs
    if is_playlist is None:
        is_playlist = any(looks_like_playlist(u) for u in urls)
    folder = staging or opts.get("folder") or DEFAULT_FOLDER
    a += ["-P", folder or "<choose a folder>", "-o", output_template(opts, is_playlist)]
    if opts.get("on_exists") == "overwrite":
        a.append("--force-overwrites")
    a += network_args(opts, settings)
    if opts.get("playlist") == "all" and (opts.get("playlist_items") or "").strip():
        a += ["-I", opts["playlist_items"].strip()]

    if not skip_dl and kind != "custom":
        if opts.get("embed_metadata"):
            a.append("--embed-metadata")
        if opts.get("embed_thumbnail"):
            a.append("--embed-thumbnail")
        if kind == "video" and opts.get("embed_chapters"):
            a.append("--embed-chapters")
        if kind == "video" and opts.get("embed_subs"):
            a += ["--embed-subs", "--sub-langs", SUB_LANGS]
        if opts.get("sponsorblock"):
            a += ["--sponsorblock-remove", "sponsor,selfpromo,interaction"]
    if opts.get("archive"):
        a += ["--download-archive", str(DATA_DIR / "archive.txt")]
    if opts.get("restrict_names"):
        a.append("--restrict-filenames")
    if (opts.get("rate_limit") or "").strip():
        a += ["-r", opts["rate_limit"].strip()]
    ff = BIN_DIR / "ffmpeg.exe"
    if ff.is_file():
        a += ["--ffmpeg-location", str(ff)]
    a += split_extra(opts.get("extra", ""))
    a += ["--"] + list(urls)
    return a


def preview_command(opts: dict, urls: list[str], settings: dict) -> str:
    shown = urls[:1] if urls else ["<URL>"]
    cmd = subprocess.list2cmdline(["yt-dlp"] + build_args(opts, shown, settings))
    if len(urls) > 1:
        cmd += f"  (+{len(urls) - 1} more)"
    return cmd


# ---------------------------------------------------------------- info lookup

def fetch_info(exe: str, url: str, opts: dict, settings: dict) -> dict:
    args = [exe, "-J", "--flat-playlist", "--no-warnings", "--encoding", "utf-8"]
    args += network_args(opts, settings) + ["--", url]
    r = subprocess.run(args, capture_output=True, timeout=120, creationflags=NO_WINDOW,
                       env=child_env())
    if r.returncode != 0:
        err = r.stderr.decode("utf-8", "replace").strip().splitlines()
        msg = next((l for l in reversed(err) if l.startswith("ERROR")), err[-1] if err else "lookup failed")
        raise RuntimeError(msg.replace("ERROR: ", "", 1))
    d = json.loads(r.stdout.decode("utf-8", "replace"))
    info = {"title": d.get("title") or url, "uploader": d.get("uploader") or d.get("channel"),
            "duration": d.get("duration"), "thumbnail": d.get("thumbnail"),
            "is_playlist": d.get("_type") == "playlist", "entries": None, "formats": []}
    if info["is_playlist"]:
        entries = d.get("entries") or []
        info["entries"] = d.get("playlist_count") or len(entries)
        thumbs = d.get("thumbnails") or []
        if not info["thumbnail"] and thumbs:
            info["thumbnail"] = thumbs[-1].get("url")
        if not info["thumbnail"] and entries:
            et = (entries[0] or {}).get("thumbnails") or []
            info["thumbnail"] = et[-1].get("url") if et else None
    else:
        for f in d.get("formats") or []:
            if f.get("format_id") is None or f.get("protocol") == "mhtml":
                continue
            info["formats"].append({
                "id": f.get("format_id"), "ext": f.get("ext"),
                "res": f.get("resolution") or ("audio only" if f.get("vcodec") == "none" else ""),
                "height": f.get("height"), "fps": f.get("fps"),
                "vcodec": f.get("vcodec"), "acodec": f.get("acodec"),
                "size": f.get("filesize") or f.get("filesize_approx"),
                "tbr": f.get("tbr"), "note": f.get("format_note") or "",
                "hdr": f.get("dynamic_range") not in (None, "SDR"),
            })
    return info


def child_env() -> dict:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["NO_COLOR"] = "1"
    return env
