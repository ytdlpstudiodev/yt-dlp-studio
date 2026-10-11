# yt-dlp Studio

> [!NOTE]
> **This is an AI-generated app.** The code, UI and this README were written by an AI model
> (Anthropic's Claude) through Claude Code, then tested by running it. Review it as you would any code from the
> internet before trusting it with your files.

A friendly Windows desktop front end for [**yt-dlp**](https://github.com/yt-dlp/yt-dlp), the open-source
command-line video downloader. Paste links, click a preset, and you're done. No command line, and no Python packages to install.

yt-dlp Studio is **not affiliated with the yt-dlp project** or with any website it can download from. It is a separate
graphical shell that runs the official `yt-dlp.exe` for you.

---

## Features

**Easy links**
- Paste any text and every link in it is picked up automatically: one per line, mixed into a sentence, whatever.
- Paste anywhere in the window, or drag links straight in from your browser.
- **Watch clipboard** mode: copy a link anywhere in Windows and it appears in the list.
- `Ctrl+Enter` starts downloading.

**Presets instead of command-line flags**

| Video | Audio | Other |
|---|---|---|
| Best video (MP4) | MP3 (best VBR) | Subtitles only (SRT) |
| 1080p (MP4) | M4A (AAC) | Thumbnail only (JPG) |
| 720p (MP4) | Original audio (no re-encode) | Custom (your own arguments) |
| Max quality (MKV, any codec) | | |

Save any combination of preset, folder and options as **your own one-click preset**.

**File names that never collide**
- Choose a naming style: *Title*, *Title [ID]*, *Channel - Title*, *Upload date - Title*, or your own yt-dlp template.
- **If the file name already exists**:
  - **Keep both** (default): saves `Title (2).mp4`, `Title (3).mp4`, and so on. Existing files are never touched, and subtitles or
    thumbnails get the same number as their video.
  - **Skip**: doesn't download it again.
  - **Overwrite**: replaces the old file.

**Queue**
- Thumbnails, titles, duration, progress bar, speed and time remaining.
- Several downloads at once (1 to 5, configurable).
- Stop, retry (resumes partial downloads), open the file, or show it in Explorer.
- **Pick formats**: choose exact video and audio streams for any item.
- Playlists: download only the linked video or the whole playlist, optionally a range (`1-10`), into its own folder.

**Transparent**
- A live **command preview** shows the exact `yt-dlp` command your choices produce, with a copy button. It's a good way
  to learn yt-dlp.
- A per-item **log** shows yt-dlp's full output.

**Self-maintaining**
- Downloads the official `yt-dlp.exe` from yt-dlp's GitHub releases on first run (you click to confirm), and updates it
  with one click.

**Extras (optional)**: embed thumbnail, metadata and chapters, embed subtitles, remove sponsor segments
(SponsorBlock), skip videos you've already downloaded, ASCII-only file names, speed limit, browser cookies for
content you have access to, and any extra yt-dlp arguments.

---

## Requirements

- **Windows 10 or 11**
- **Python 3.10 or newer** ([python.org](https://www.python.org/downloads/)). Only the standard library is used.
- **ffmpeg** (strongly recommended): needed to merge HD video with audio and to convert audio.
  Install with: `winget install Gyan.FFmpeg`
- **Deno or Node.js** (recommended for YouTube): recent yt-dlp versions need a JavaScript runtime to get every
  format from YouTube. Studio detects either one automatically.
  Install with `winget install DenoLand.Deno` or `winget install OpenJS.NodeJS.LTS`
- Microsoft Edge (built into Windows) is used to show the app in its own window. Any browser works as a fallback.

## Getting started

1. Download this repository (green **Code** button → **Download ZIP**) and unzip it anywhere.
2. Double-click **`yt-dlp Studio.bat`**.
3. The first time, click **Download yt-dlp** in the banner (or point Studio at a `yt-dlp.exe` you already have).
4. Click **Browse…** next to *Save to* and **choose the folder where downloads should go**. There is no default
   folder, so you have to pick one before the first download.
5. Paste a link, pick a preset, and press **Download**.

Closing the window stops the app about 40 seconds later, but only once nothing is downloading.

You can also run it from a terminal: `python app.py` (add `--port 50000` to use another port).

---

## How it works

- `app.py` starts a small web server bound to `127.0.0.1` only (not reachable from other computers) and opens the
  UI in an Edge "app" window. API calls require a random per-launch token, and requests with a foreign `Host` header
  are rejected, so web pages you visit can't drive the app.
- Each download runs `yt-dlp.exe` as a separate process. Progress comes from yt-dlp's `--progress-template`
  output.
- **Keep both** works by downloading into a hidden `.yt-dlp-studio-tmp` folder inside your chosen folder, then
  moving the finished files out under a free name. If you stop a download, its partial file stays there so
  **Retry** can resume it.

| Path | Contents |
|---|---|
| `app.py` | Local server, settings, window launch |
| `jobs.py` | Download queue, progress parsing, keep-both file placement |
| `ytdlp_core.py` | Presets, option-to-argument mapping, yt-dlp detection |
| `winutil.py` | Clipboard, native folder picker, Explorer helpers |
| `web/` | The user interface (plain HTML/CSS/JS) |
| `bin/` | Created on first run: the managed `yt-dlp.exe` (not in this repo) |
| `data/` | Created on first run: your settings, presets and recent folders (not in this repo) |

---

## Responsible use

yt-dlp Studio is a general-purpose tool. **You are responsible for how you use it.** Only download content that you
own, that is in the public domain or under a license that allows it, or that you otherwise have permission to
download, and follow the terms of service of the sites you use. Downloading copyrighted material without
permission may be illegal where you live.

This project does not circumvent DRM and does not include or distribute yt-dlp, ffmpeg or any media. It only
runs the tools you install.

## License

Released into the public domain under [The Unlicense](LICENSE), the same license yt-dlp uses. Do whatever you
like with it.

The software is provided "as is", without warranty of any kind. See the license for details.
