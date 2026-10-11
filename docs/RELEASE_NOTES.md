## Download

**[yt-dlp-Studio-Setup.exe](https://github.com/ytdlpstudiodev/yt-dlp-studio/releases/latest/download/yt-dlp-Studio-Setup.exe)** for Windows 10/11 (listed under *Assets* below).

1. Run the installer. If Windows shows **"Windows protected your PC"**, click **More info → Run anyway**. The installer isn't code-signed.
2. Choose the install location, tick **Create a desktop shortcut** if you want one, and click **Install**. No admin rights needed.
3. Needs **Python 3.10+** ([python.org](https://www.python.org/downloads/windows/)); Setup tells you if it's missing.
   **ffmpeg** (`winget install Gyan.FFmpeg`) and **Deno** (`winget install DenoLand.Deno`) are recommended.
4. On first use, click the **folder icon** in the bottom bar and choose where downloads should go.

`SHA256SUMS.txt` lets you check that the installer is genuine.

## What's new in 2.1.1

- **Fix:** Studio's browser windows no longer get signed in to your Microsoft account by Edge, so they don't sync and
  their history stays out of your main Edge. Already-affected Studio profiles are reset automatically (saved site
  logins are kept).
- If you used an earlier version, consider deleting synced entries via `edge://history` in your normal Edge.

## What's new in 2.1

- The sign-in window now opens **in front** of other windows (Windows could hide it before)
- **Delete one saved login** with the × next to it under *Saved logins*
- **Add your own site buttons** to the sign-in list (type a login page, click **Save to list**)

Updating from 2.0: just run the new installer. Your settings and logins are kept.

## What's new in 2.0

- Windows **installer and uninstaller** (Start menu, optional desktop shortcut, removes every trace except your downloads)
- **New interface** inspired by Open Video Downloader: a card per link with track and quality pickers, sizes and durations
- **Sign in to sites** inside the app (members-only, private, age-restricted and paid content), plus cookies.txt and passwords
- **Pause and resume**, plus pause, resume or cancel all
- **Subtitles** page: languages, auto-generated captions, embedding
- MP4/MKV/WebM and MP3/M4A/Opus/FLAC/WAV, a proxy setting, themes and notifications
- Locations and Settings now apply to items when you press Download

*This is an AI-generated app (written with Claude). It isn't affiliated with yt-dlp or Open Video Downloader. Built automatically by GitHub Actions from this release's source code, with the latest official yt-dlp bundled.*
