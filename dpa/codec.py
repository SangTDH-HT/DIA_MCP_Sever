"""Container codec for Delta DOPSoft / DIAScreen .dpa project files.

Layout of a .dpa file:

    offset 0    'BM'                      - Windows bitmap magic (preview thumbnail)
    offset 2    uint32 = 14               - bogus bfSize, always 0x0000000E
    offset 6    'PDAB'                    - Delta marker, overwrites bfReserved
    offset 10   uint32 = 54               - bfOffBits
    offset 14   BITMAPINFOHEADER (40 B)   - biSizeImage at +34 gives the pixel size
    offset 54   thumbnail pixels
    then        gzip stream               - deflate level 6, mtime 0, OS byte 0x0b
    inside      every byte XOR 0x64       - the plain project text

Re-encoding an unmodified payload reproduces the original file byte for byte,
which is what makes writing back to .dpa safe.
"""

from __future__ import annotations

import gzip
import io
import struct
from dataclasses import dataclass
from pathlib import Path

XOR_KEY = 0x64
BMP_MAGIC = b"BM"
DELTA_MARKER = b"PDAB"
GZIP_MAGIC = b"\x1f\x8b\x08"


class DpaFormatError(ValueError):
    """The file is not a .dpa container we recognise."""


@dataclass
class DpaFile:
    """A decoded .dpa: the thumbnail bytes kept verbatim plus the plain payload."""

    thumbnail: bytes
    payload: bytes

    def to_bytes(self) -> bytes:
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=6, mtime=0) as gz:
            gz.write(bytes(b ^ XOR_KEY for b in self.payload))
        blob = bytearray(buf.getvalue())
        blob[9] = 0x0B  # DOPSoft stamps OS = FAT; keep the byte identical
        return self.thumbnail + bytes(blob)


def _thumbnail_size(data: bytes) -> int:
    if data[:2] != BMP_MAGIC or data[6:10] != DELTA_MARKER:
        raise DpaFormatError("missing 'BM'/'PDAB' header - not a Delta .dpa file")
    if len(data) < 54:
        raise DpaFormatError("file truncated inside the bitmap header")
    return 54 + struct.unpack_from("<I", data, 34)[0]


def decode(data: bytes) -> DpaFile:
    end = _thumbnail_size(data)
    if data[end : end + 3] != GZIP_MAGIC:
        raise DpaFormatError(f"no gzip stream at offset {end}")
    raw = gzip.decompress(data[end:])
    return DpaFile(thumbnail=data[:end], payload=bytes(b ^ XOR_KEY for b in raw))


def read(path: str | Path) -> DpaFile:
    return decode(Path(path).read_bytes())


def write(path: str | Path, dpa: DpaFile) -> None:
    Path(path).write_bytes(dpa.to_bytes())
