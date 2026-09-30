"""Screen/element view over a parsed .dpa payload.

The payload is a flat list of sections in drawing order:

    [Screen] [AuxKeyElement] [Element] [State] [State] [Element] ...

An element belongs to the screen that precedes it, and the [State] sections
after an element are that element's states.  Nothing here copies data: every
object points at the live `Section`, so edits go straight back into the
document and `Document.to_bytes()` still round-trips everything untouched.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from . import codec, macro
from .document import Document, Section

_TYPES = json.loads(Path(__file__).with_name("element_types.json").read_text(encoding="utf-8"))

# Properties that hold a PLC/internal address, e.g. {EtherLink1}2@DB13.DBX1954.1
ADDRESS_KEYS = ("ReadVar", "WriteVar", "InterLockVar", "VisibleVar")
MACRO_KEYS = (
    "ButtonOnMacroLen",
    "ButtonOffMacroLen",
    "BeforeExecMacroLen",
    "AfterExecMacroLen",
)


@dataclass
class Element:
    section: Section
    states: list[Section]
    screen_id: int
    index: int  # position within its screen, 0-based

    @property
    def type_code(self) -> str:
        return f"{self.section.get('Type', '?')}.{self.section.get('SubType', '?')}"

    @property
    def kind(self) -> str:
        return _TYPES.get(self.type_code, f"Type {self.type_code}")

    @property
    def name(self) -> str:
        found = self.section.entries("wDescTextLen0")
        return found[0].text if found else ""

    @property
    def rect(self) -> tuple[int, int, int, int]:
        get = self.section.get_int
        return (get("X", 0), get("Y", 0), get("Width", 0), get("Height", 0))

    @property
    def addresses(self) -> dict[str, str]:
        out = {}
        for key in ADDRESS_KEYS:
            value = self.section.get(key)
            if value and value not in ("None", ""):
                out[key] = value
        return out

    @property
    def caption(self) -> str:
        """The label shown on the element, taken from its first non-empty state."""
        for state in self.states:
            found = state.entries("wTextLen0") or state.entries("wTextLen")
            if found and found[0].text.strip():
                return found[0].text.strip()
        return ""

    def macros(self) -> dict[str, list[str]]:
        """Macro slots on this element, each as a list of readable statements."""
        out = {}
        for key in MACRO_KEYS:
            for entry in self.section.entries(key):
                if entry.blob:
                    lines = macro.statements(entry.blob)
                    if lines:
                        out[key[: -len("Len")]] = lines
        return out

    def summary(self) -> dict:
        x, y, w, h = self.rect
        out = {
            "index": self.index,
            "kind": self.kind,
            "type": self.type_code,
            "name": self.name,
            "x": x,
            "y": y,
            "w": w,
            "h": h,
        }
        if self.caption:
            out["caption"] = self.caption
        out.update(self.addresses)
        macros = sorted(self.macros())
        if macros:
            out["macros"] = macros
        return out


@dataclass
class Screen:
    section: Section
    elements: list[Element]

    @property
    def id(self) -> int:
        return self.section.get_int("ID", 0)

    @property
    def name(self) -> str:
        found = self.section.entries("wTextLen")
        return found[0].text if found else f"Screen_{self.id}"

    @property
    def size(self) -> tuple[int, int]:
        return (self.section.get_int("DocSizeX", 0), self.section.get_int("DocSizeY", 0))

    def summary(self) -> dict:
        w, h = self.size
        return {
            "id": self.id,
            "name": self.name,
            "width": w,
            "height": h,
            "elements": len(self.elements),
            "background": self.section.get("BgColor"),
        }


class Project:
    """A loaded .dpa, kept in memory so several tool calls can work on it."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.file = codec.read(self.path)
        self.doc = Document.parse(self.file.payload)
        self.screens = _build_screens(self.doc)

    # -- lookup ---------------------------------------------------------
    def screen(self, ref) -> Screen:
        """Find a screen by numeric ID or by name (exact, then substring)."""
        text = str(ref).strip()
        if text.isdigit():
            for screen in self.screens:
                if screen.id == int(text):
                    return screen
        for screen in self.screens:
            if screen.name == text:
                return screen
        lowered = text.lower()
        hits = [s for s in self.screens if lowered in s.name.lower()]
        if len(hits) == 1:
            return hits[0]
        if len(hits) > 1:
            raise KeyError(f"{text!r} matches {len(hits)} screens: {[s.name for s in hits]}")
        raise KeyError(f"no screen {text!r}")

    def element(self, screen_ref, index: int) -> Element:
        screen = self.screen(screen_ref)
        if not 0 <= index < len(screen.elements):
            raise KeyError(f"screen {screen.name!r} has {len(screen.elements)} elements")
        return screen.elements[index]

    def info(self) -> dict:
        app = self.doc.first("Application")
        app_d = app.as_dict() if app else {}
        return {
            "path": str(self.path),
            "hmi": app_d.get("Name"),
            "panel": app_d.get("PanelName"),
            "series": app_d.get("PanelSeries"),
            "resolution": f"{app_d.get('PanelResWidth')}x{app_d.get('PanelResHeight')}",
            "editor_version": app_d.get("Version"),
            "default_screen": app_d.get("DefaultScreen"),
            "controllers": _controllers(app_d),
            "screens": len(self.screens),
            "elements": sum(len(s.elements) for s in self.screens),
        }

    # -- writing --------------------------------------------------------
    def save(self, out_path) -> dict:
        target = Path(out_path)
        blob = codec.DpaFile(self.file.thumbnail, self.doc.to_bytes()).to_bytes()
        target.write_bytes(blob)
        return {"saved": str(target), "bytes": len(blob)}


def _build_screens(doc: Document) -> list[Screen]:
    screens: list[Screen] = []
    current: Screen | None = None
    element: Element | None = None
    for section in doc.sections:
        if section.name == "Screen":
            current = Screen(section=section, elements=[])
            screens.append(current)
            element = None
        elif section.name == "Element" and current is not None:
            element = Element(
                section=section,
                states=[],
                screen_id=current.id,
                index=len(current.elements),
            )
            current.elements.append(element)
        elif section.name == "State" and element is not None:
            element.states.append(section)
        elif section.name != "State":
            element = None
    return screens


def _controllers(app: dict) -> list[str]:
    out = []
    for i in range(8):
        name = app.get(f"ControllerName{i}")
        if not name:
            break
        link = app.get(f"CommName{i}", "")
        ip = app.get(f"PLCIP{i}")
        out.append(f"{link}: {name}" + (f" @{_ip(ip)}" if ip else ""))
    return out


def _ip(raw) -> str:
    """DOPSoft stores the PLC IP as a signed 32-bit integer, first octet high."""
    try:
        value = int(raw) & 0xFFFFFFFF
    except (TypeError, ValueError):
        return str(raw)
    return ".".join(str((value >> shift) & 0xFF) for shift in (24, 16, 8, 0))
