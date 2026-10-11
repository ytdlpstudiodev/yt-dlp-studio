"""Draw the yt-dlp Studio icon (green rounded square, white download arrow) as a multi-size .ico.

Pure Python: shapes are rasterised with 4x4 supersampling, small sizes are stored as classic
32-bit bitmaps and 256px as PNG, which is what Windows expects in an .ico.
"""
from __future__ import annotations

import math
import struct
import sys
import zlib
from pathlib import Path

SIZES = [16, 20, 24, 32, 40, 48, 64, 128, 256]
TOP, BOTTOM = (0x45, 0xC7, 0x6E), (0x26, 0x9E, 0x4D)   # subtle vertical gradient around #32b45c
WHITE = (255, 255, 255)
# Arrow strokes in a 32x32 design grid (same shape as the app's favicon).
SEGMENTS = [((16, 8), (16, 19)), ((16, 19), (11, 14)), ((16, 19), (21, 14)), ((9, 24), (23, 24))]
STROKE = 3.0
RADIUS = 7.5


def _seg_dist(px, py, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _in_rounded(px, py, size=32.0, r=RADIUS):
    cx = min(max(px, r), size - r)
    cy = min(max(py, r), size - r)
    return (px - cx) ** 2 + (py - cy) ** 2 <= r * r and 0 <= px <= size and 0 <= py <= size


def render(n: int) -> list[tuple[int, int, int, int]]:
    """RGBA pixels, row-major, top-down."""
    ss = 4
    scale = 32.0 / n
    # Thicker strokes at tiny sizes keep the arrow readable.
    stroke = STROKE * (1.25 if n <= 20 else 1.1 if n <= 32 else 1.0)
    out = []
    for y in range(n):
        for x in range(n):
            r = g = b = a = 0.0
            for sy in range(ss):
                for sx in range(ss):
                    px = (x + (sx + 0.5) / ss) * scale
                    py = (y + (sy + 0.5) / ss) * scale
                    if not _in_rounded(px, py):
                        continue
                    if any(_seg_dist(px, py, s0, s1) <= stroke / 2 for s0, s1 in SEGMENTS):
                        c = WHITE
                    else:
                        t = py / 32.0
                        c = tuple(TOP[i] + (BOTTOM[i] - TOP[i]) * t for i in range(3))
                    r += c[0]; g += c[1]; b += c[2]; a += 1
            k = ss * ss
            if a:
                out.append((round(r / a), round(g / a), round(b / a), round(255 * a / k)))
            else:
                out.append((0, 0, 0, 0))
    return out


def png_bytes(n: int, px) -> bytes:
    raw = b"".join(b"\x00" + bytes(c for p in px[y * n:(y + 1) * n] for c in p) for y in range(n))

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def dib_bytes(n: int, px) -> bytes:
    header = struct.pack("<IiiHHIIiiII", 40, n, n * 2, 1, 32, 0, 0, 0, 0, 0, 0)
    rows = []
    for y in range(n - 1, -1, -1):                       # bottom-up BGRA
        rows.append(b"".join(bytes((p[2], p[1], p[0], p[3])) for p in px[y * n:(y + 1) * n]))
    mask_row = ((n + 31) // 32) * 4
    return header + b"".join(rows) + b"\x00" * (mask_row * n)


def build(out: Path) -> None:
    images = []
    for n in SIZES:
        px = render(n)
        images.append((n, png_bytes(n, px) if n >= 256 else dib_bytes(n, px)))
        if n == 256:
            out.with_suffix(".png").write_bytes(png_bytes(n, px))
    offset = 6 + 16 * len(images)
    head = struct.pack("<HHH", 0, 1, len(images))
    entries, blobs = b"", b""
    for n, data in images:
        entries += struct.pack("<BBBBHHII", n % 256, n % 256, 0, 0, 1, 32, len(data), offset + len(blobs))
        blobs += data
    out.write_bytes(head + entries + blobs)
    print(f"wrote {out} ({len(images)} sizes, {out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    build(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("icon.ico"))
