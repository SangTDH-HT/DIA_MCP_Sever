"""Byte-faithful reader/writer for the plain text payload inside a .dpa.

The payload looks like an INI file, but two kinds of entries carry raw bytes
that must not be touched:

    wTextLen0=28          a UTF-16LE string of 28 bytes, then a CRLF separator
    ButtonOnMacroLen=842  842 bytes of macro source whose own CRLF ends the run
    Size=2689151          the whole picture bank, on the next line

So the payload is parsed length-driven rather than line-driven, and every entry
keeps its original bytes. Anything the parser does not understand is stored
verbatim, which lets `Document.to_bytes()` reproduce the input exactly.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

EOL = b"\r\n"
_SECTION = re.compile(rb"^\[([A-Za-z0-9_. \-]{2,40})\]$")
# A few headers carry leftover binary in front of them, e.g. "...,N[d[Application]".
_SECTION_TAIL = re.compile(rb"^(.*)(\[[A-Za-z0-9_. \-]{2,40}\])$", re.S)
_ENTRY = re.compile(rb"^([A-Za-z_][A-Za-z0-9_.\- ]{0,60})=(.*)$", re.S)
# Keys whose value is a byte count for the blob that follows on the next line:
# every `...Len` variant, plus the bare `Size` of a picture bank.
#
# `Size` must NOT match as a suffix. `FontSize1=16` is an ordinary number, but
# reading it as a length swallows the 16 bytes after it - which happens to be
# the whole `FontRatio1=100` line. Round-tripping still produced identical
# bytes, so only a font that refused to change gave it away.
_BLOB_KEY = re.compile(rb"(Len[0-9]{0,3}(-[0-9]{1,3})?|^Size)$")


@dataclass
class Entry:
    """One `key=value` line, plus the raw blob that follows it when there is one."""

    key: bytes
    value: bytes
    blob: bytes | None = None
    blob_eol: bool = True  # False when the byte count already covers the CRLF

    def to_bytes(self) -> bytes:
        out = self.key + b"=" + self.value + EOL
        if self.blob is not None:
            out += self.blob + (EOL if self.blob_eol else b"")
        return out

    @property
    def text(self) -> str:
        """The blob decoded as UTF-16LE, without the trailing NUL."""
        if self.blob is None:
            return ""
        return self.blob.decode("utf-16le", "replace").rstrip("\x00")

    def set_text(self, value: str) -> None:
        """Replace the blob and keep the byte-count key in step."""
        blob = value.encode("utf-16le") + b"\x00\x00"
        self.blob = blob
        self.value = str(len(blob)).encode("ascii")

    @property
    def source(self) -> str:
        """The blob read as macro/ANSI source rather than as UTF-16LE text."""
        return "" if self.blob is None else self.blob.decode("latin1")


@dataclass
class Raw:
    """A line the parser makes no claim about; re-emitted unchanged."""

    data: bytes

    def to_bytes(self) -> bytes:
        return self.data + EOL


@dataclass
class Section:
    name: str
    items: list = field(default_factory=list)
    prefix: bytes = b""  # stray bytes that sit in front of the header on its line

    def to_bytes(self) -> bytes:
        head = b""
        if self.name:
            head = self.prefix + b"[" + self.name.encode("latin1") + b"]" + EOL
        return head + b"".join(i.to_bytes() for i in self.items)

    def entries(self, key: str) -> list[Entry]:
        k = key.encode("latin1")
        return [i for i in self.items if isinstance(i, Entry) and i.key == k]

    def get(self, key: str, default: str | None = None) -> str | None:
        found = self.entries(key)
        return found[0].value.decode("latin1") if found else default

    def get_int(self, key: str, default: int | None = None) -> int | None:
        value = self.get(key)
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def set(self, key: str, value) -> bool:
        """Overwrite an existing scalar. Returns False when the key is absent."""
        found = self.entries(key)
        if not found:
            return False
        found[0].value = str(value).encode("latin1")
        found[0].blob = None if found[0].blob is None else found[0].blob
        return True

    def as_dict(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for item in self.items:
            if isinstance(item, Entry):
                key = item.key.decode("latin1")
                out[key] = item.text if item.blob is not None else item.value.decode("latin1")
        return out


class Document:
    """The parsed payload: an ordered list of sections."""

    def __init__(self, sections: list[Section]):
        self.sections = sections

    @classmethod
    def parse(cls, payload: bytes) -> "Document":
        sections = [Section(name="")]
        pos = 0
        size = len(payload)
        while pos < size:
            end = payload.find(EOL, pos)
            if end < 0:
                sections[-1].items.append(Raw(payload[pos:]))
                break
            line = payload[pos:end]
            pos = end + 2

            match = _SECTION.match(line)
            if match:
                sections.append(Section(name=match.group(1).decode("latin1")))
                continue

            match = _ENTRY.match(line)
            if not match:
                tail = _SECTION_TAIL.match(line)
                if tail:
                    name = tail.group(2)[1:-1].decode("latin1")
                    sections.append(Section(name=name, prefix=tail.group(1)))
                    continue
            if not match:
                sections[-1].items.append(Raw(line))
                continue

            key, value = match.group(1), match.group(2)
            entry = Entry(key=key, value=value)
            length = _blob_length(key, value)
            framing = _blob_framing(payload, pos, length)
            if framing is not None:
                entry.blob = payload[pos : pos + length]
                entry.blob_eol = framing
                pos += length + (2 if framing else 0)
            sections[-1].items.append(entry)
        return cls(sections)

    def to_bytes(self) -> bytes:
        return b"".join(s.to_bytes() for s in self.sections)

    def named(self, name: str) -> list[Section]:
        return [s for s in self.sections if s.name == name]

    def first(self, name: str) -> Section | None:
        found = self.named(name)
        return found[0] if found else None


def _blob_length(key: bytes, value: bytes) -> int | None:
    if not _BLOB_KEY.search(key):
        return None
    try:
        length = int(value)
    except ValueError:
        return None
    return length if length > 0 else None


def _blob_framing(payload: bytes, pos: int, length: int | None) -> bool | None:
    """Decide whether a blob follows, and how it is terminated.

    Returns True when the count excludes the trailing CRLF (text blobs), False
    when the count includes it (macro blobs), and None when no blob follows -
    which is the case for a plain scalar such as `StringLen=16`.
    """
    if length is None:
        return None
    end = pos + length
    if end > len(payload):
        return None
    if payload[end : end + 2] == EOL:
        return True
    if payload[end - 2 : end] == EOL and _starts_entry(payload, end):
        return False
    return None


def _starts_entry(payload: bytes, pos: int) -> bool:
    end = payload.find(EOL, pos)
    line = payload[pos : end if end >= 0 else len(payload)]
    return bool(_SECTION.match(line) or _ENTRY.match(line))
