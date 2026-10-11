"""yt-dlp knowledge: where the binary lives, quality choices, and turning UI options into arguments."""
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
COOKIE_FILE = DATA_DIR / "cookies.txt"   # written by login.py from the sign-in window
YTDLP_DOWNLOAD_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# One line per progress tick. Title goes last because it may contain the separator.
PROGRESS_PREFIX = "@@P|"
PROGRESS_TEMPLATE = (
    "download:" + PROGRESS_PREFIX
    + "%(progress.downloaded_bytes)s|%(progress.total_bytes)s|%(progress.total_bytes_estimate)s|"
    "%(progress.speed)s|%(progress.eta)s|%(info.title)s"
)

TRACKS = {"both": "Video + Audio", "audio": "Audio", "video": "Video"}
GENERIC_HEIGHTS = [2160, 1440, 1080, 720, 480, 360]
GENERIC_ABR = [320, 256, 192, 160, 128, 96]
VIDEO_CONTAINERS = ["mp4", "mkv", "webm", "original"]
AUDIO_FORMATS = ["mp3", "m4a", "opus", "flac", "wav", "original"]

TEMPLATES = {
    "title": "%(title)s.%(ext)s",
    "title_id": "%(title)s [%(id)s].%(ext)s",
    "uploader_title": "%(uploader,channel|Unknown)s - %(title)s.%(ext)s",
    "date_title": "%(upload_date>%Y-%m-%d)s - %(title)s.%(ext)s",
}

# No default: people choose their own download folder (Locations) before the first download.
DEFAULT_FOLDER = ""

COOKIE_BROWSERS = ["edge", "chrome", "firefox", "brave", "opera", "vivaldi"]

URL_RE = re.compile(r"""(?:https?://|www\.)[^\s<>"'`]+""", re.IGNORECASE)


def default_options() -> dict:
    return {
        # what to download
        "track": "both",
        "quality": "best",
        "video_container": "mp4",
        "audio_format": "mp3",
        # where & how it's named
        "folder": DEFAULT_FOLDER,
        "on_exists": "keep_both",
        "template": "title",
        "template_custom": "%(title)s.%(ext)s",
        "playlist": "single",
        "playlist_items": "",
        "playlist_folder": True,
        # extras
        "embed_thumbnail": True,
        "embed_metadata": True,
        "embed_chapters": True,
        "sponsorblock": False,
        "archive": False,
        "restrict_names": False,
        # subtitles
        "subtitles": False,
        "sub_langs": ["en"],
        "sub_all": False,
        "sub_auto": True,
        "sub_embed": True,
        "sub_format": "srt",
        # login: "" | "studio" | "file" | a browser name
        "cookies": "",
        "cookies_file": "",
        # network
        "rate_limit": "",
        "proxy": "",
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


# ---------------------------------------------------------------- quality choices

def _parse_quality(q: str) -> tuple[int | None, int | None, int | None]:
    """'h1080f60' -> (1080, 60, None); 'h720' -> (720, None, None); 'a160' -> (None, None, 160)."""
    m = re.fullmatch(r"h(\d+)(?:f(\d+))?", q or "")
    if m:
        return int(m.group(1)), int(m.group(2)) if m.group(2) else None, None
    m = re.fullmatch(r"a(\d+)", q or "")
    if m:
        return None, None, int(m.group(1))
    return None, None, None


def quality_label(track: str, q: str) -> str:
    h, fps, abr = _parse_quality(q)
    if h:
        return f"{h}p{fps}" if fps else f"{h}p"
    if abr:
        return f"{abr}kbps"
    return "Best"


def quality_options(formats: list[dict]) -> dict:
    """Choices for the per-item quality dropdown, with an estimated download size for each."""
    audio_only = [f for f in formats if f.get("vcodec") in (None, "none") and f.get("acodec") not in (None, "none")]
    video = [f for f in formats if f.get("vcodec") not in (None, "none") and f.get("height")]
    best_audio = max((f.get("size") or 0 for f in audio_only), default=0)

    by_res: dict[tuple, int] = {}
    for f in video:
        fps = int(round(f["fps"])) if f.get("fps") else None
        key = (f["height"], fps)
        by_res[key] = max(by_res.get(key, 0), f.get("size") or 0)
    res_keys = sorted(by_res, key=lambda k: (k[0], k[1] or 0), reverse=True)

    def vopt(key, add_audio):
        h, fps = key
        size = by_res[key] + (best_audio if add_audio else 0)
        return {"value": f"h{h}f{fps}" if fps else f"h{h}", "label": f"{h}p{fps}" if fps else f"{h}p",
                "size": size or None}

    by_abr: dict[int, int] = {}
    for f in audio_only:
        abr = f.get("abr") or f.get("tbr")
        if abr:
            by_abr[int(round(abr))] = max(by_abr.get(int(round(abr)), 0), f.get("size") or 0)

    if res_keys:
        top = by_res[res_keys[0]]
        both = [{"value": "best", "label": "Best", "size": (top + best_audio) or None}] + [vopt(k, True) for k in res_keys]
        vid = [{"value": "best", "label": "Best", "size": top or None}] + [vopt(k, False) for k in res_keys]
    else:
        both = [{"value": "best", "label": "Best", "size": None}] + \
               [{"value": f"h{h}", "label": f"{h}p", "size": None} for h in GENERIC_HEIGHTS]
        vid = [dict(o) for o in both]
    if by_abr:
        aud = [{"value": "best", "label": "Best", "size": best_audio or None}] + \
              [{"value": f"a{a}", "label": f"{a}kbps", "size": by_abr[a] or None} for a in sorted(by_abr, reverse=True)]
    else:
        aud = [{"value": "best", "label": "Best", "size": None}] + \
              [{"value": f"a{a}", "label": f"{a}kbps", "size": None} for a in GENERIC_ABR]
    return {"both": both, "video": vid, "audio": aud}


def format_args(opts: dict) -> tuple[list[str], str]:
    """Track + quality (or exact streams picked in Preferences) -> yt-dlp format arguments."""
    track = opts.get("track", "both")
    h, fps, abr = _parse_quality(opts.get("quality", "best"))
    exact = (opts.get("format_override") or "").strip()

    if track == "audio":
        f = exact or (f"ba[abr<={abr}]/ba/b" if abr else "ba/b")
        a = ["-f", f, "-x"]
        af = opts.get("audio_format", "mp3")
        if af in AUDIO_FORMATS and af != "original":
            a += ["--audio-format", af, "--audio-quality", "0"]
        return a, "audio"

    if exact:
        f = exact
    elif not h:
        f = "bv*+ba/b" if track == "both" else "bv*/b"
    else:
        fps_f = f"[fps<={fps + 1}]" if fps else ""
        if track == "both":
            f = f"bv*[height={h}]{fps_f}+ba/bv*[height={h}]+ba/b[height={h}]/bv*[height<={h}]+ba/b[height<={h}]/b"
        else:
            f = (f"bv*[height={h}]{fps_f}/" if fps else "") + f"bv*[height={h}]/bv*[height<={h}]/b"
    a = ["-f", f]
    vc = opts.get("video_container", "mp4")
    if vc == "mp4":
        a += ["-S", "res,fps,ext:mp4:m4a"]
    if vc in ("mp4", "mkv", "webm") and track == "both":
        a += ["--merge-output-format", vc]
    if vc in ("mp4", "mkv", "webm") and track == "video":
        a += ["--remux-video", vc]
    return a, "video"


def describe(opts: dict) -> str:
    """Short label for a queue item, e.g. 'Video + Audio · 1080p · MP4'."""
    track = opts.get("track", "both")
    parts = [TRACKS.get(track, track), quality_label(track, opts.get("quality", "best"))]
    if opts.get("format_override"):
        parts[1] = f"-f {opts['format_override']}"
    fmt = opts.get("audio_format") if track == "audio" else opts.get("video_container")
    if fmt and fmt != "original":
        parts.append(fmt.upper())
    return " · ".join(parts)


# ---------------------------------------------------------------- arguments

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


def cookie_source(opts: dict) -> str | None:
    """The cookies.txt this item should use (Studio sign-ins or a file the user picked)."""
    if opts.get("cookies") == "studio":
        return str(COOKIE_FILE) if COOKIE_FILE.exists() else None
    if opts.get("cookies") == "file":
        p = (opts.get("cookies_file") or "").strip()
        return p if p and os.path.isfile(p) else None
    return None


def network_args(opts: dict, settings: dict, cookie_file: str | None = None,
                 secrets: dict | None = None) -> list[str]:
    """Arguments that affect what yt-dlp can see, shared by downloads and info lookups.

    cookie_file: a private copy of cookie_source(opts) for this run.
    secrets: decrypted {"username", "password", "video_password"}; None in previews.
    """
    a = ["--yes-playlist" if opts.get("playlist") == "all" else "--no-playlist"]
    if opts.get("cookies") in ("studio", "file") and cookie_file:
        a += ["--cookies", cookie_file]
    elif opts.get("cookies") in COOKIE_BROWSERS:
        a += ["--cookies-from-browser", opts["cookies"]]
    sec = settings.get("secrets", {}) if secrets is None else secrets
    masked = secrets is None
    if sec.get("username") and (sec.get("password") or sec.get("has_password")):
        a += ["--username", sec["username"], "--password", "********" if masked else sec.get("password", "")]
    if sec.get("video_password") or sec.get("has_video_password"):
        a += ["--video-password", "********" if masked else sec.get("video_password", "")]
    if (opts.get("proxy") or "").strip():
        a += ["--proxy", opts["proxy"].strip()]
    rt = detect_js_runtime(settings)
    if rt and rt != "deno":
        a += ["--js-runtimes", rt]
    return a


def build_args(opts: dict, urls: list[str], settings: dict, internal: bool = False,
               print_file: str | None = None, staging: str | None = None,
               is_playlist: bool | None = None, cookie_file: str | None = None,
               secrets: dict | None = None) -> list[str]:
    """UI options -> yt-dlp argument list (without the executable).

    internal=True adds the machine-readable progress flags the app needs; the
    preview shown to the user leaves them out so it is a command they could run.
    staging: download into this folder instead (the app moves files out afterwards
    so an existing file with the same name never blocks or gets overwritten).
    """
    fargs, kind = format_args(opts)

    a: list[str] = []
    if internal:
        a += ["--newline", "--encoding", "utf-8", "--progress-template", PROGRESS_TEMPLATE]
        if print_file:
            a += ["--print-to-file", "after_move:%(filepath)s", print_file]
    a += fargs
    if is_playlist is None:
        is_playlist = any(looks_like_playlist(u) for u in urls)
    a += ["-P", staging or opts.get("folder") or DEFAULT_FOLDER or "<choose a folder>", "-o", output_template(opts, is_playlist)]
    if opts.get("on_exists") == "overwrite":
        a.append("--force-overwrites")
    a += network_args(opts, settings, cookie_file, secrets)
    if opts.get("playlist") == "all" and (opts.get("playlist_items") or "").strip():
        a += ["-I", opts["playlist_items"].strip()]

    if opts.get("embed_metadata"):
        a.append("--embed-metadata")
    if opts.get("embed_thumbnail"):
        a.append("--embed-thumbnail")
    if kind == "video" and opts.get("embed_chapters"):
        a.append("--embed-chapters")
    if opts.get("subtitles"):
        # "en" should also catch regional/original variants like en-US, en-GB and en-orig.
        langs = "all,-live_chat" if opts.get("sub_all") else             ",".join(f"{c},{c}-.*" for c in (opts.get("sub_langs") or ["en"]))
        a += ["--write-subs", "--sub-langs", langs]
        if opts.get("sub_auto"):
            a.append("--write-auto-subs")
        if opts.get("sub_format") in ("srt", "vtt", "ass"):
            a += ["--convert-subs", opts["sub_format"]]
        if kind == "video" and opts.get("sub_embed"):
            a.append("--embed-subs")
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
    cmd = subprocess.list2cmdline(["yt-dlp"] + build_args(opts, shown, settings, cookie_file=cookie_source(opts)))
    if len(urls) > 1:
        cmd += f"  (+{len(urls) - 1} more)"
    return cmd


# ---------------------------------------------------------------- info lookup

def fetch_info(exe: str, url: str, opts: dict, settings: dict, cookie_file: str | None = None,
               secrets: dict | None = None) -> dict:
    args = [exe, "-J", "--flat-playlist", "--no-warnings", "--encoding", "utf-8"]
    args += network_args(opts, settings, cookie_file, secrets or {}) + ["--", url]
    r = subprocess.run(args, capture_output=True, timeout=120, creationflags=NO_WINDOW,
                       env=child_env())
    if r.returncode != 0:
        err = r.stderr.decode("utf-8", "replace").strip().splitlines()
        msg = next((l for l in reversed(err) if l.startswith("ERROR")), err[-1] if err else "lookup failed")
        raise RuntimeError(msg.replace("ERROR: ", "", 1))
    d = json.loads(r.stdout.decode("utf-8", "replace"))
    info = {"title": d.get("title") or url, "uploader": d.get("uploader") or d.get("channel"),
            "duration": d.get("duration"), "thumbnail": d.get("thumbnail"),
            "is_playlist": d.get("_type") == "playlist", "entries": None, "formats": [],
            "meta": {k: d.get(k) for k in ("webpage_url", "extractor_key", "upload_date", "view_count",
                                          "like_count", "channel", "uploader", "description", "id")}}
    if info["meta"].get("description"):
        info["meta"]["description"] = info["meta"]["description"][:4000]
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
                "tbr": f.get("tbr"), "abr": f.get("abr"), "note": f.get("format_note") or "",
                "hdr": f.get("dynamic_range") not in (None, "SDR"),
            })
    return info


def child_env() -> dict:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["NO_COLOR"] = "1"
    return env
