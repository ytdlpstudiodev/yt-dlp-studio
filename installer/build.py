"""Build dist/yt-dlp Studio Setup.exe using only what ships with Windows (the .NET C# compiler).

    python installer/build.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
APP = HERE.parent
BUILD = HERE / "build"
DIST = APP / "dist"
CSC = Path(r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe")

APP_FILES = ["app.py", "jobs.py", "login.py", "ytdlp_core.py", "winutil.py"]
REFS = ["System.dll", "System.Core.dll", "System.Drawing.dll", "System.Windows.Forms.dll", "System.Management.dll"]

sys.path.insert(0, str(HERE))
import make_icon  # noqa: E402


def csc(out: Path, sources: list[str], extra: list[str] = (), refs: list[str] = ()) -> None:
    cmd = [str(CSC), "/nologo", "/target:winexe", "/optimize+", "/codepage:65001", f"/out:{out}",
           f"/win32icon:{BUILD / 'icon.ico'}"] + [f"/r:{r}" for r in REFS + list(refs)] + list(extra) + \
          [str(HERE / s) for s in sources]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout, r.stderr)
        raise SystemExit(f"compile failed: {out.name}")
    print(f"compiled {out.name} ({out.stat().st_size // 1024} KB)")


def main() -> None:
    if not CSC.exists():
        raise SystemExit("The .NET Framework C# compiler wasn't found at " + str(CSC))
    BUILD.mkdir(exist_ok=True)
    DIST.mkdir(exist_ok=True)
    make_icon.build(BUILD / "icon.ico")

    launcher = BUILD / "yt-dlp Studio.exe"
    uninstaller = BUILD / "Uninstall yt-dlp Studio.exe"
    csc(launcher, ["Launcher.cs", "Common.cs"])
    csc(uninstaller, ["Uninstall.cs", "Common.cs"], refs=["System.Web.Extensions.dll"])

    payload = BUILD / "payload.zip"
    with zipfile.ZipFile(payload, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in APP_FILES:
            z.write(APP / f, f)
        for f in sorted((APP / "web").iterdir()):
            if f.is_file():
                z.write(f, f"web/{f.name}")
        ytdlp = APP / "bin" / "yt-dlp.exe"
        if ytdlp.exists():                      # bundle it so Studio works offline right after install
            z.write(ytdlp, "bin/yt-dlp.exe")
        z.write(BUILD / "icon.ico", "icon.ico")
        z.write(launcher, launcher.name)
        z.write(uninstaller, uninstaller.name)
    print(f"payload.zip: {len(zipfile.ZipFile(payload).namelist())} files, {payload.stat().st_size // 1024} KB")

    setup = DIST / "yt-dlp Studio Setup.exe"
    csc(setup, ["Setup.cs", "Common.cs"],
        extra=[f"/resource:{payload},payload.zip", f"/resource:{BUILD / 'icon.ico'},icon.ico"],
        refs=["System.IO.Compression.dll", "System.IO.Compression.FileSystem.dll"])
    print(f"\nInstaller ready: {setup}")


if __name__ == "__main__":
    main()
