"""Download queue: runs yt-dlp processes, parses their output, and reports progress."""
from __future__ import annotations

import collections
import ctypes
import itertools
import os
import re
import shutil
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import ytdlp_core as core

STAGING_NAME = ".yt-dlp-studio-tmp"
SKIP_SUFFIXES = (".part", ".ytdl", ".temp")

STAGE_PATTERNS = [
    ("[Merger]", "Merging video + audio"),
    ("[ExtractAudio]", "Converting audio"),
    ("[EmbedThumbnail]", "Embedding thumbnail"),
    ("[Metadata]", "Writing metadata"),
    ("[EmbedSubtitle]", "Embedding subtitles"),
    ("[SponsorBlock]", "Finding sponsor segments"),
    ("[ModifyChapters]", "Cutting sponsor segments"),
    ("[VideoRemuxer]", "Remuxing"),
    ("[VideoConvertor]", "Converting video"),
    ("[ThumbnailsConvertor]", "Converting thumbnail"),
    ("[SubtitlesConvertor]", "Converting subtitles"),
    ("[FixupM3u8]", "Fixing stream"),
]
ITEM_RE = re.compile(r"\[download\] Downloading (?:item|video) (\d+) of (\d+)")
FORMATS_RE = re.compile(r"Downloading \d+ format\(s\): (\S+)")


def _num(s: str):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def _hide(path: Path):
    try:
        ctypes.windll.kernel32.SetFileAttributesW(str(path), 0x2)
    except Exception:
        pass


class Job:
    _ids = itertools.count(1)

    def __init__(self, url: str, opts: dict, status: str):
        self.id = next(self._ids)
        self.url = url
        self.opts = dict(opts)
        self.status = status          # ready | queued | running | done | error | cancelled
        self.title = None
        self.uploader = None
        self.duration = None
        self.thumbnail = None
        self.is_playlist = False
        self.entries = None
        self.formats: list[dict] = []
        self.info_state = "pending"   # pending | loading | ok | failed
        self.percent = 0.0
        self.speed = None
        self.eta = None
        self.total = None
        self.stage = ""
        self.item = None              # (index, count) inside a playlist
        self.error = None
        self.files: list[str] = []
        self.log = collections.deque(maxlen=400)
        self.proc: subprocess.Popen | None = None
        self.cancel_requested = False
        self.parts = 1
        self.part_idx = -1
        self.part_sizes: dict[int, float] = {}

    @property
    def staging(self) -> Path:
        return Path(self.opts.get("folder") or core.DEFAULT_FOLDER) / STAGING_NAME / f"job-{self.id}"

    def to_dict(self) -> dict:
        preset = core.PRESET_MAP.get(self.opts.get("preset"), {})
        return {
            "id": self.id, "url": self.url, "status": self.status,
            "title": self.title, "uploader": self.uploader, "duration": self.duration,
            "thumbnail": self.thumbnail, "is_playlist": self.is_playlist, "entries": self.entries,
            "has_formats": bool(self.formats), "info_state": self.info_state,
            "percent": round(self.percent, 1), "speed": self.speed, "eta": self.eta,
            "total": self.total, "stage": self.stage, "item": self.item, "error": self.error,
            "files": self.files, "preset_label": preset.get("label", "?"),
            "preset_kind": preset.get("kind", ""), "format_override": self.opts.get("format_override", ""),
            "folder": self.opts.get("folder"),
        }


class JobManager:
    def __init__(self, hub, settings_ref):
        self.hub = hub
        self.settings = settings_ref      # callable returning the live settings dict
        self.jobs: dict[int, Job] = {}
        self.lock = threading.RLock()
        self.wake = threading.Event()
        self.dirty: set[int] = set()
        self.info_pool = ThreadPoolExecutor(max_workers=3)
        threading.Thread(target=self._scheduler, daemon=True).start()
        threading.Thread(target=self._ticker, daemon=True).start()

    # ------------------------------------------------------------ public API

    def add(self, urls: list[str], opts: dict, start: bool) -> tuple[list[Job], int]:
        added, dupes = [], 0
        with self.lock:
            active = {j.url for j in self.jobs.values() if j.status in ("ready", "queued", "running")}
            for url in urls:
                if url in active:
                    dupes += 1
                    continue
                job = Job(url, opts, "queued" if start else "ready")
                self.jobs[job.id] = job
                active.add(url)
                added.append(job)
        for job in added:
            self._emit(job)
            if self.settings().get("fetch_info", True):
                self._fetch_info_async(job)
        self.wake.set()
        return added, dupes

    def start(self, job_id: int | None = None):
        with self.lock:
            if job_id is None:
                targets = list(self.jobs.values())
            else:
                targets = [self.jobs[job_id]] if job_id in self.jobs else []
            for j in targets:
                if j.status in ("ready", "error", "cancelled"):
                    self._reset(j)
                    j.status = "queued"
                    self._emit(j)
        self.wake.set()

    def cancel(self, job_id: int):
        with self.lock:
            j = self.jobs.get(job_id)
            if not j:
                return
            if j.status == "running" and j.proc:
                j.cancel_requested = True
                subprocess.run(["taskkill", "/PID", str(j.proc.pid), "/T", "/F"],
                               capture_output=True, creationflags=core.NO_WINDOW)
            elif j.status == "queued":
                j.status = "ready"
                self._emit(j)

    def remove(self, job_id: int):
        with self.lock:
            j = self.jobs.get(job_id)
        if not j:
            return
        if j.status == "running":
            self.cancel(job_id)
            for _ in range(50):
                if j.status != "running":
                    break
                time.sleep(0.1)
        with self.lock:
            self.jobs.pop(job_id, None)
        self._clean_staging(j)
        self.hub.broadcast("removed", {"id": job_id})

    def clear_finished(self):
        with self.lock:
            gone = [j for j in self.jobs.values() if j.status in ("done", "cancelled", "error")]
        for j in gone:
            self.remove(j.id)

    def set_format(self, job_id: int, fmt: str):
        with self.lock:
            j = self.jobs.get(job_id)
            if j and j.status != "running":
                j.opts["format_override"] = fmt
                self._emit(j)

    def get(self, job_id: int) -> Job | None:
        return self.jobs.get(job_id)

    def snapshot(self) -> list[dict]:
        with self.lock:
            return [j.to_dict() for j in self.jobs.values()]

    def busy(self) -> bool:
        with self.lock:
            return any(j.status in ("queued", "running") for j in self.jobs.values())

    # ------------------------------------------------------------ internals

    def _emit(self, job: Job, now: bool = True):
        if now:
            self.hub.broadcast("job", job.to_dict())
        else:
            self.dirty.add(job.id)

    def _ticker(self):
        while True:
            time.sleep(0.25)
            with self.lock:
                ids, self.dirty = self.dirty, set()
                payload = [self.jobs[i].to_dict() for i in ids if i in self.jobs]
            for d in payload:
                self.hub.broadcast("job", d)

    def _reset(self, j: Job):
        j.percent, j.speed, j.eta, j.total, j.stage = 0.0, None, None, None, ""
        j.error, j.item, j.files, j.cancel_requested = None, None, [], False
        j.parts, j.part_idx, j.part_sizes = 1, -1, {}

    def _fetch_info_async(self, job: Job):
        exe = core.find_ytdlp(self.settings())
        if not exe:
            return
        job.info_state = "loading"
        self._emit(job)

        def work():
            try:
                info = core.fetch_info(exe, job.url, job.opts, self.settings())
                for k in ("title", "uploader", "duration", "thumbnail", "is_playlist", "entries", "formats"):
                    if k == "title" and job.title:   # a running download may already know it
                        continue
                    setattr(job, k, info[k])
                job.info_state = "ok"
            except Exception as e:  # noqa: BLE001 - surface anything to the UI
                job.info_state = "failed"
                job.log.append(f"[studio] Info lookup failed: {e}")
            self._emit(job)

        self.info_pool.submit(work)

    def _scheduler(self):
        while True:
            self.wake.wait(1.0)
            self.wake.clear()
            with self.lock:
                limit = max(1, int(self.settings().get("max_concurrent", 2)))
                running = sum(1 for j in self.jobs.values() if j.status == "running")
                for j in self.jobs.values():
                    if running >= limit:
                        break
                    if j.status == "queued":
                        j.status = "running"
                        j.stage = "Starting"
                        running += 1
                        self._emit(j)
                        threading.Thread(target=self._run, args=(j,), daemon=True).start()

    def _run(self, job: Job):
        settings = self.settings()
        exe = core.find_ytdlp(settings)
        if not exe:
            job.status, job.error = "error", "yt-dlp is not installed"
            self._emit(job)
            return

        keep_both = job.opts.get("on_exists", "keep_both") == "keep_both"
        if not (job.opts.get("folder") or "").strip():
            job.status, job.error = "error", "No download folder chosen"
            self._emit(job)
            return
        dest = Path(job.opts["folder"])
        staging = job.staging if keep_both else None
        try:
            dest.mkdir(parents=True, exist_ok=True)
            if staging:
                staging.mkdir(parents=True, exist_ok=True)
                _hide(staging.parent)
        except OSError as e:
            job.status, job.error = "error", f"Can't use folder: {e}"
            self._emit(job)
            return

        core.DATA_DIR.mkdir(parents=True, exist_ok=True)
        print_file = core.DATA_DIR / f"files-{job.id}.txt"
        print_file.unlink(missing_ok=True)
        args = [exe] + core.build_args(job.opts, [job.url], settings, internal=True,
                                       print_file=str(print_file),
                                       staging=str(staging) if staging else None,
                                       is_playlist=job.is_playlist if job.info_state == "ok" else None)
        job.log.append("[studio] " + subprocess.list2cmdline(args))
        try:
            job.proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        stdin=subprocess.DEVNULL, creationflags=core.NO_WINDOW,
                                        env=core.child_env())
        except OSError as e:
            job.status, job.error = "error", f"Couldn't start yt-dlp: {e}"
            self._emit(job)
            return

        for raw in job.proc.stdout:
            for line in raw.decode("utf-8", "replace").replace("\r", "\n").split("\n"):
                line = line.rstrip()
                if line:
                    self._parse_line(job, line)
        rc = job.proc.wait()
        job.proc = None

        main_files = []
        if print_file.exists():
            main_files = [l.strip() for l in print_file.read_text("utf-8", "replace").splitlines() if l.strip()]
            print_file.unlink(missing_ok=True)

        if job.cancel_requested:
            # Staging is kept so a retry resumes the partial download.
            job.status, job.stage = "cancelled", "Cancelled"
        elif rc == 0 or main_files:
            if staging:
                try:
                    main_files = self._place_files(staging, dest, main_files)
                    self._clean_staging(job)
                except OSError as e:
                    rc = rc or 1
                    job.error = f"Downloaded, but moving out of the temp folder failed: {e}"
            job.files = main_files
            job.speed = job.eta = None
            if rc == 0:
                job.status, job.percent = "done", 100.0
                if job.stage not in ("Already downloaded", "Skipped (already in archive)"):
                    job.stage = "Done"
            else:
                # e.g. a playlist where some entries failed: keep what worked, report the rest.
                job.status = "error"
                job.error = f"Partly done ({len(main_files)} saved): {job.error or f'exit code {rc}'}"
        else:
            job.status = "error"
            job.error = job.error or f"yt-dlp exited with code {rc}"
        self._emit(job)
        self.wake.set()

    def _parse_line(self, job: Job, line: str):
        if line.startswith(core.PROGRESS_PREFIX):
            parts = line[len(core.PROGRESS_PREFIX):].split("|", 5)
            if len(parts) == 6:
                done, total, est, speed, eta, title = parts
                done, total = _num(done), _num(total) or _num(est)
                if total and done is not None:
                    frac = min(done / total, 1.0)
                    job.percent = (max(job.part_idx, 0) + frac) / max(job.parts, 1) * 100
                if total:
                    job.part_sizes[max(job.part_idx, 0)] = total
                    job.total = sum(job.part_sizes.values())
                job.speed = _num(speed)
                job.eta = _num(eta)
                if title and title != "NA" and not job.is_playlist:
                    job.title = job.title or title
                job.stage = "Downloading"
                self._emit(job, now=False)
            return

        job.log.append(line)
        m = ITEM_RE.search(line)
        if m:
            job.item = (int(m.group(1)), int(m.group(2)))
            job.part_idx, job.parts, job.percent, job.part_sizes = -1, 1, 0.0, {}
        m = FORMATS_RE.search(line)
        if m:
            job.parts = m.group(1).count("+") + 1
            job.part_idx = -1
        if line.startswith("[download] Destination:"):
            job.part_idx = min(job.part_idx + 1, job.parts - 1)
        elif "has already been downloaded" in line:
            job.stage, job.percent = "Already downloaded", 100.0
        elif "has already been recorded in the archive" in line:
            job.stage = "Skipped (already in archive)"
        elif line.startswith("ERROR:"):
            job.error = line[6:].strip()
        else:
            for tag, label in STAGE_PATTERNS:
                if line.startswith(tag):
                    job.stage = label
                    break
        self._emit(job, now=False)

    @staticmethod
    def _place_files(staging: Path, dest: Path, main_files: list[str]) -> list[str]:
        """Move everything from the staging folder into dest, numbering names that already exist.

        A video and its sidecar files (subtitles, thumbnail) share one number so they stay matched:
        "Title (2).mp4" + "Title (2).en.srt".
        """
        files = [p for p in staging.rglob("*") if p.is_file() and not p.name.endswith(SKIP_SUFFIXES)]
        mains = []
        for m in main_files:
            try:
                mains.append(Path(m).resolve().relative_to(staging.resolve()))
            except ValueError:
                pass
        groups: dict[tuple, list[Path]] = {}
        for p in files:
            rel = p.relative_to(staging)
            stem = None
            for m in mains:
                if rel.parent == m.parent and rel.name.startswith(m.stem) and (stem is None or len(m.stem) > len(stem)):
                    stem = m.stem
            stem = stem or rel.stem
            groups.setdefault((rel.parent, stem), []).append(rel)

        moved: dict[Path, Path] = {}
        for (parent, stem), rels in groups.items():
            n = 1
            while True:
                suffix = f" ({n})" if n > 1 else ""
                targets = [dest / parent / (stem + suffix + r.name[len(stem):]) for r in rels]
                if not any(t.exists() for t in targets):
                    break
                n += 1
            for r, t in zip(rels, targets):
                t.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(staging / r), str(t))
                moved[r] = t
        out = []
        for m in main_files:
            try:
                rel = Path(m).resolve().relative_to(staging.resolve())
                out.append(str(moved.get(rel, dest / rel)))
            except ValueError:
                out.append(m)
        return out

    @staticmethod
    def _clean_staging(job: Job):
        st = job.staging
        if st.exists():
            shutil.rmtree(st, ignore_errors=True)
        try:
            st.parent.rmdir()     # only succeeds when no other job is using it
        except OSError:
            pass
