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


# --- more records, framed as DIAScreen writes them (compiled "OK" 30/09) -------------
_TAIL = b"\x01" * 4 + b"\x00" * 8
_COMPARE = {"==": 0x48, "!=": 0x49, ">": 0x4A, ">=": 0x4B, "<": 0x4C, "<=": 0x4D}   # codes read off real records


def _field(text: str) -> bytes:
    return struct.pack("<I", len(text)) + text.encode("latin1")


def if_statement(left: str, compare: str, right: str) -> bytes:
    """`IF left <compare> right`, CRLF included; close it with endif_statement().

    DIAScreen keeps the two operands in capitals next to the statement as typed
    (`{ETHERLINK1}2@DB13.DBD1916` in HMISiloFinal.dpa), so they go in that way.
    """
    return (b"\x14\x0e\x03" + bytes([_COMPARE[compare]])
            + b"".join(map(_field, (f"IF {left} {compare} {right}  ", left.upper(), right.upper(), "Var3", "Var4"))) + _TAIL + b"\r\n")


def else_statement() -> bytes:
    """`ELSE` between if_statement() and endif_statement() - bytes as in HMISiloFinal.dpa."""
    return b"\x00\x00\x00\x5c" + b"".join(map(_field, ("ELSE ", "Var1", "Var2", "Var3", "Var4"))) + _TAIL + b"\r\n"


def endif_statement() -> bytes:
    return b"\x00\x00\x00\x5d" + b"".join(map(_field, ("ENDIF", "Var1", "Var2", "Var3", "Var4"))) + _TAIL + b"\r\n"


def assign_statement(target: str, source: str) -> bytes:
    """`target = source` on one word (a constant or an address on either side), CRLF included."""
    return b"\x25\x07\x03\x1e" + b"".join(map(_field, (f"{target} = {source}", target, source, "Var3", "Var4"))) + _TAIL + b"\r\n"


def arith_statement(target: str, left: str, operator: str, right: str) -> bytes:
    """`target = left - right` or `left * right` on words, CRLF included (compiled "OK" 30/09 in build_test_trend.py)."""
    code = {"-": 1, "*": 2}[operator]
    words = (f"{target} = {left} {operator} {right}", target, left, right, "Var4")
    return b"\x04\x0f\x07" + bytes([code]) + b"".join(map(_field, words)) + _TAIL + b"\r\n"


def fmov_statement(target: str, source: str) -> bytes:
    """`target = FMOV(source) (Signed DW)`: one floating value, two words - bytes as in HMISiloFinal.dpa."""
    words = (f"{target} = FMOV({source}) (Signed DW)", target, source, "Var3", "Var4")
    return b"\x25\x01\x03\x41" + b"".join(map(_field, words)) + b"\x01" * 4 + b"\x01\x00\x00\x00" * 2 + b"\r\n"


def fillasc_statement(target: str, text: str) -> bytes:
    """`FILLASC(target,"text")`: the characters into consecutive words - bytes as in HMISiloFinal.dpa."""
    words = (f'FILLASC({target},"{text}")', target, text, "", "")
    return b"\x04\x00\x03\x21" + b"".join(map(_field, words)) + _TAIL + b"\r\n"


def program(*records: bytes) -> bytes:
    """Several statements as one macro blob; a screen_statement() brings its own header, dropped here."""
    return b"\x02REV" + b"".join(r[4:] if r.startswith(b"\x02REV") else r for r in records)
