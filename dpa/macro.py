"""Turn a stored DOPSoft macro blob back into readable statements.

A macro blob is one record per statement, separated by CRLF.  Each record holds
a few framing bytes, then length-prefixed strings: the first is the statement as
the macro editor shows it (`BITOFF $4.1`, `OPENSCREEN 5`, `#a comment`), and the
rest are its parsed operands plus the unused Var2/Var3/Var4 slots.

Only the statement is returned - it is what a person reads and what makes the
button logic reviewable next to the PLC code.
"""

from __future__ import annotations

import struct

_MAX_PREFIX_SCAN = 24  # framing bytes before the first length-prefixed string
_MAX_STATEMENT = 300


def statements(blob: bytes | str) -> list[str]:
    if isinstance(blob, str):
        blob = blob.encode("latin1")
    out = []
    for record in blob.split(b"\r\n"):
        text = _first_string(record)
        if text:
            out.append(text)
    return out


def _first_string(record: bytes) -> str | None:
    limit = min(len(record) - 4, _MAX_PREFIX_SCAN)
    for offset in range(max(limit, 0)):
        length = struct.unpack_from("<I", record, offset)[0]
        if not 1 <= length <= _MAX_STATEMENT:
            continue
        end = offset + 4 + length
        if end > len(record):
            continue
        candidate = record[offset + 4 : end]
        if all(c >= 160 or 32 <= c < 127 for c in candidate):
            return candidate.decode("latin1").rstrip()
    return None


# Opcodes of the one-operand screen statements, read off DIAScreen's own blobs.
OPENSCREEN, CLOSESUBSCREEN = 0x84, 0x85


def screen_statement(opcode: int, screen_id: int) -> bytes:
    """One `OPENSCREEN n` / `CLOSESUBSCREEN n` record, CRLF included.

    Framing copied from DIAScreen: `02 'REV%' 02 01`, the opcode, then the
    statement, its operand and the unused Var2..Var4 slots as uint32-prefixed
    strings, four 01 flags and eight zero bytes.
    """
    word = {OPENSCREEN: "OPENSCREEN", CLOSESUBSCREEN: "CLOSESUBSCREEN"}[opcode]
    field = lambda s: struct.pack("<I", len(s)) + s.encode("latin1")
    return (b"\x02REV%\x02\x01" + bytes([opcode]) + field(f"{word} {screen_id}") + field(str(screen_id))
            + field("Var2") + field("Var3") + field("Var4") + b"\x01" * 4 + b"\x00" * 8 + b"\r\n")


def set_macro(section, key: str, blob: bytes | None) -> None:
    """Replace a `...MacroLen` entry: the byte count covers the record's own CRLF."""
    for entry in section.entries(key):
        if blob is None:
            entry.value, entry.blob, entry.blob_eol = b"0", None, True
        else:
            entry.value, entry.blob, entry.blob_eol = str(len(blob)).encode("ascii"), blob, False
