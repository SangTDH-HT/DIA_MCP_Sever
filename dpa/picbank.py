"""Read and extend a project's picture bank - where Delta keeps every bitmap.

The bank is the `[Picture]` section's blob:

    'DOP-100IMAGE1.0'                        15-byte magic
    repeated:  uint32 length                 bytes that follow for this image
               BITMAPINFOHEADER (40 bytes)   32 bits per pixel, no compression
               pixels                        BGRA, bottom-up

There are no names inside it. An element names a bitmap as `Picture Name`
(e.g. `NewHMI00007`) plus `PIB Name` (which bank), and the trailing digits are
the image's 1-based position in this sequence - confirmed by counting: a bank of
168 images is referenced by exactly the indices 1..168.

So adding an icon is appending one record, and the index it lands at is its name.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

MAGIC = b"DOP-100IMAGE1.0"
BITMAPINFOHEADER = 40


@dataclass
class Picture:
    index: int      # 1-based, this is what the element's name refers to
    width: int
    height: int
    record: bytes   # length-prefixed, exactly as stored


def read(blob: bytes) -> list[Picture]:
    if not blob.startswith(MAGIC):
        if not blob or blob == b"0":
            return []
        raise ValueError("not a DOP-100 picture bank")
    out: list[Picture] = []
    pos = len(MAGIC)
    while pos + 4 <= len(blob):
        size = struct.unpack_from("<I", blob, pos)[0]
        if size == 0 or pos + 4 + size > len(blob):
            break
        _, width, height = struct.unpack_from("<Iii", blob, pos + 4)
        out.append(Picture(len(out) + 1, width, abs(height), blob[pos : pos + 4 + size]))
        pos += 4 + size
    return out


def write(pictures: list[Picture]) -> bytes:
    return MAGIC + b"".join(p.record for p in pictures)


def encode(path: str | Path, background: tuple[int, int, int] | None = None) -> bytes:
    """Turn an image file into one bank record: a bottom-up 32-bit BGRA DIB.

    Delta panels do not composite alpha, so a transparent PNG is flattened onto
    `background` - pass the colour of whatever it will sit on, or leave it None
    to keep the alpha channel as stored.
    """
    image = Image.open(path).convert("RGBA")
    if background is not None:
        flat = Image.new("RGBA", image.size, (*background, 255))
        flat.alpha_composite(image)
        image = flat

    width, height = image.size
    rows = image.tobytes("raw", "BGRA")
    stride = width * 4
    pixels = b"".join(rows[y * stride : (y + 1) * stride] for y in range(height - 1, -1, -1))

    header = struct.pack(
        "<IiiHHIIiiII",
        BITMAPINFOHEADER,
        width,
        height,
        1,      # planes
        32,     # bits per pixel
        0,      # BI_RGB
        len(pixels),
        0, 0, 0, 0,
    )
    body = header + pixels
    return struct.pack("<I", len(body)) + body


def append(blob: bytes, files, background=None) -> tuple[bytes, list[Picture]]:
    """Add image files to a bank. Returns the new bank and the pictures added."""
    pictures = read(blob)
    added = []
    for path in files:
        record = encode(path, background)
        _, width, height = struct.unpack_from("<Iii", record, 4)
        picture = Picture(len(pictures) + 1, width, abs(height), record)
        pictures.append(picture)
        added.append(picture)
    return write(pictures), added
