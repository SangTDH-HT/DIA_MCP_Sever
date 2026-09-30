"""MCP server for Delta DOPSoft / DIAScreen .dpa projects.

DIAScreen has no Openness-style API, so this server works on the project file
itself: a .dpa is a BMP thumbnail followed by a gzip stream whose bytes are
XOR 0x64.  Inside is an INI-like design model - screens, elements, states,
macros, alarms - which `dpa.document` reads and rewrites byte for byte.

Safety: `open_project` never locks or changes the file on disk.  Edits live in
memory until `save`, which refuses to overwrite the source unless asked and
always leaves a .bak next to an overwritten file.  Close the project in
DIAScreen before saving over it.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from mcp.server import MCPServer

from dpa import edit, editor
from dpa import macro as macro_lib
from dpa.model import ADDRESS_KEYS, Project

mcp = MCPServer(
    "delta-dpa",
    instructions=(
        "Read and edit Delta DOPSoft/DIAScreen .dpa HMI designs directly. "
        "Close the project in DIAScreen before saving over it."
    ),
)

_state: dict[str, Project] = {}
_dirty: list[str] = []


def _project() -> Project:
    if "current" not in _state:
        raise RuntimeError("no project open - call open_project first")
    return _state["current"]


def _touch(note: str) -> None:
    _dirty.append(note)


@mcp.tool()
def open_project(path: str) -> dict:
    """Load a .dpa design file. Reads only; the file on disk is left untouched."""
    project = Project(path)
    _state["current"] = project
    _dirty.clear()
    return project.info()


@mcp.tool()
def list_screens() -> list[dict]:
    """Every screen with its id, name, size and element count."""
    return [s.summary() for s in _project().screens]


@mcp.tool()
def layout(screen: str, kind: str = "") -> dict:
    """Dump one screen's elements in drawing order: position, size, text, address.

    `screen` is an id or a name. `kind` filters by element kind, e.g. "Button",
    "Numeric", "Text" (case-insensitive substring).
    """
    target = _project().screen(screen)
    items = [e.summary() for e in target.elements]
    if kind:
        needle = kind.lower()
        items = [i for i in items if needle in i["kind"].lower()]
    return {"screen": target.summary(), "elements": items}


@mcp.tool()
def element(screen: str, index: int) -> dict:
    """Every property of one element, plus its states and macros."""
    item = _project().element(screen, index)
    return {
        "summary": item.summary(),
        "properties": item.section.as_dict(),
        "states": [s.as_dict() for s in item.states],
        "macros": item.macros(),
    }


@mcp.tool()
def find(query: str, limit: int = 60) -> list[dict]:
    """Search the whole project for a PLC address, a caption or an element name.

    Matches the same way across every screen, so "DB13.DBX1954" finds every
    button wired to that bit and "Start" finds every element captioned Start.
    """
    needle = query.lower()
    hits = []
    for screen in _project().screens:
        for item in screen.elements:
            macro_text = " ".join(l for lines in item.macros().values() for l in lines)
            haystack = " ".join(
                [item.name, item.caption, *item.addresses.values(), macro_text]
            ).lower()
            if needle in haystack:
                hit = item.summary()
                hit["screen"] = screen.name
                hit["screen_id"] = screen.id
                hits.append(hit)
                if len(hits) >= limit:
                    return hits
    return hits


@mcp.tool()
def addresses() -> list[dict]:
    """Every PLC/internal address the design touches, with where it is used."""
    used: dict[str, list[str]] = {}
    for screen in _project().screens:
        for item in screen.elements:
            for key, value in item.addresses.items():
                used.setdefault(value, []).append(f"{screen.name}#{item.index}.{key}")
    return [
        {"address": addr, "uses": len(where), "where": where[:12]}
        for addr, where in sorted(used.items(), key=lambda kv: -len(kv[1]))
    ]


@mcp.tool()
def macros(screen: str = "") -> list[dict]:
    """Macro source attached to elements - the button logic of the panel.

    With no screen, returns the project's sub-macros instead.
    """
    project = _project()
    if not screen:
        section = project.doc.first("SubMacro")
        if section is None:
            return []
        return [
            {
                "sub_macro": e.key.decode("latin1").replace("Len", ""),
                "statements": macro_lib.statements(e.blob),
            }
            for e in section.items
            if getattr(e, "blob", None)
        ]
    out = []
    for item in project.screen(screen).elements:
        for slot, statements in item.macros().items():
            out.append(
                {
                    "index": item.index,
                    "name": item.name,
                    "caption": item.caption,
                    "slot": slot,
                    "statements": statements,
                }
            )
    return out


@mcp.tool()
def alarms() -> list[dict]:
    """The alarm table: trigger address and message text."""
    section = _project().doc.first("Alarm")
    if section is None:
        return []
    out = []
    for entry in section.items:
        key = getattr(entry, "key", b"").decode("latin1")
        if getattr(entry, "blob", None) and "Message" in key:
            out.append({"key": key, "text": entry.text})
    return out


@mcp.tool()
def set_property(screen: str, index: int, key: str, value: str) -> dict:
    """Change one scalar property of an element, e.g. X, Width, BgColor, ReadVar.

    The key must already exist on that element - this edits the design, it does
    not invent properties DIAScreen would not understand.
    """
    item = _project().element(screen, index)
    before = item.section.get(key)
    if before is None:
        raise KeyError(f"element has no property {key!r}")
    item.section.set(key, value)
    _touch(f"{screen}#{index}.{key}: {before} -> {value}")
    return {"element": item.summary(), "changed": {key: [before, value]}}


@mcp.tool()
def set_text(screen: str, index: int, text: str, state: int = 0) -> dict:
    """Change the caption an element shows, for one of its states."""
    item = _project().element(screen, index)
    if state >= len(item.states):
        raise KeyError(f"element has {len(item.states)} states")
    section = item.states[state]
    entries = section.entries("wTextLen0") or section.entries("wTextLen")
    if not entries:
        raise KeyError("this state carries no text")
    before = entries[0].text
    for entry in entries:
        entry.set_text(text)
    _touch(f"{screen}#{index} text[{state}]: {before!r} -> {text!r}")
    return {"element": item.summary(), "changed": {"text": [before, text]}}


@mcp.tool()
def rebind(old: str, new: str, dry_run: bool = True) -> dict:
    """Repoint every element from one PLC address to another, across all screens.

    Defaults to a dry run so the hit list can be checked before anything moves.
    """
    project = _project()
    touched = []
    for screen in project.screens:
        for item in screen.elements:
            for key in ADDRESS_KEYS:
                value = item.section.get(key)
                if value and old in value:
                    replaced = value.replace(old, new)
                    touched.append(
                        {
                            "screen": screen.name,
                            "index": item.index,
                            "key": key,
                            "from": value,
                            "to": replaced,
                        }
                    )
                    if not dry_run:
                        item.section.set(key, replaced)
    if not dry_run and touched:
        _touch(f"rebind {old} -> {new} ({len(touched)} places)")
    return {"dry_run": dry_run, "count": len(touched), "changes": touched[:80]}


@mcp.tool()
def pending_changes() -> dict:
    """What has been edited in memory but not yet written to a file."""
    return {"count": len(_dirty), "changes": list(_dirty)}


@mcp.tool()
def save(out_path: str = "", overwrite_source: bool = False, reload_editor: bool = False) -> dict:
    """Write the edited design to a .dpa file.

    Writes to `out_path` by default. Overwriting the file the project was
    loaded from needs `overwrite_source=True` and keeps a .bak copy.

    DIAScreen may hold the file open while this runs - it does not lock it. Its
    window will be stale afterwards, so pass `reload_editor=True` to close that
    window and reopen it on the new bytes. That step stops short of any dialog,
    so unsaved editor changes are never thrown away.
    """
    project = _project()
    if out_path:
        target = Path(out_path)
        if target.resolve() == project.path.resolve() and not overwrite_source:
            raise ValueError("that is the source file - pass overwrite_source=True")
    elif overwrite_source:
        target = project.path
    else:
        raise ValueError("give out_path, or pass overwrite_source=True")

    backup = None
    if target.exists():
        backup = target.with_suffix(target.suffix + ".bak")
        shutil.copy2(target, backup)
    result = project.save(target)
    result["backup"] = str(backup) if backup else None
    result["applied"] = list(_dirty)
    _dirty.clear()
    if reload_editor:
        result["editor"] = editor.reload_document(target)
    return result


@mcp.tool()
def screenshot_text(screen: str) -> str:
    """An ASCII floor plan of a screen - what sits where, for a quick read."""
    target = _project().screen(screen)
    width, height = target.size
    lines = [f"{target.name}  (id {target.id}, {width}x{height}, {len(target.elements)} elements)"]
    for item in sorted(target.elements, key=lambda e: (e.rect[1], e.rect[0])):
        x, y, w, h = item.rect
        label = item.caption or item.name
        addr = next(iter(item.addresses.values()), "")
        lines.append(f"  #{item.index:<3} {item.kind:<22} @{x:>4},{y:<4} {w:>4}x{h:<4} {label:<28} {addr}")
    return "\n".join(lines)



@mcp.tool()
def clone_element(
    from_screen: str,
    from_index: int,
    to_screen: str,
    x: int,
    y: int,
    width: int = 0,
    height: int = 0,
    name: str = "",
) -> dict:
    """Copy an element onto a screen, drawn on top of what is already there.

    New elements are always cloned from one that works, so properties this
    server has not mapped keep values DIAScreen itself wrote.
    """
    project = _project()
    source = project.element(from_screen, from_index)
    target = project.screen(to_screen)
    item = edit.clone_element(
        project,
        source,
        target,
        x=x,
        y=y,
        width=width or None,
        height=height or None,
        name=name or None,
    )
    _touch(f"cloned {from_screen}#{from_index} -> {target.name}#{item.index} at {x},{y}")
    return item.summary()


@mcp.tool()
def clone_screen(from_screen: str, name: str) -> dict:
    """Add an empty screen that copies another screen's settings and aux keys."""
    project = _project()
    screen = edit.clone_screen(project, project.screen(from_screen), name)
    _touch(f"new screen {name} (id {screen.id})")
    return screen.summary()


@mcp.tool()
def delete_element(screen: str, index: int) -> dict:
    """Remove an element and its states from a screen."""
    project = _project()
    target = project.screen(screen)
    gone = target.elements[index].summary()
    edit.delete_element(project, target, index)
    _touch(f"deleted {target.name}#{index} ({gone['kind']})")
    return {"deleted": gone, "remaining": len(target.elements)}


@mcp.tool()
def set_state_text(screen: str, index: int, text: str, english: str = "", state: int = 0) -> dict:
    """Set an element's caption in both language slots at once.

    Slot 0 takes `text`, slot 1 takes `english` - OTL-30 keeps every label
    bilingual, Vietnamese first.
    """
    item = _project().element(screen, index)
    edit.set_state_text(item, text, english or None, state)
    _touch(f"{screen}#{index} text[{state}] -> {text!r}/{english!r}")
    return item.summary()


@mcp.tool()
def editor_windows() -> list[dict]:
    """Which projects DIAScreen currently has open, by window title."""
    return [
        {"title": title, "pid": pid}
        for _, pid, _, title in editor._windows()
        if title.startswith("DIAScreen")
    ]


@mcp.tool()
def close_in_editor(path: str = "") -> dict:
    """Close DIAScreen on this project BEFORE rewriting it; a save prompt is answered Yes.

    Order of work: close_in_editor -> open_project/edit/save -> open_in_editor.
    Closing first puts the user's own edits on disk, so the rewrite keeps them.
    A dialog already open means the user is mid-edit, and the window is left alone.
    """
    target = path or str(_project().path)
    return editor.close_document(target)


@mcp.tool()
def open_in_editor(path: str = "") -> dict:
    """Open the project in DIAScreen so the user sees the result."""
    target = path or str(_project().path)
    return editor.open_document(target)


@mcp.tool()
def reload_in_editor(path: str = "") -> dict:
    """Make the open DIAScreen window show the file as it is on disk now.

    DIAScreen reads a .dpa at open and never looks again, so after a save its
    window is stale. This closes that document window and reopens the editor on
    the file. It never answers a dialog: if DIAScreen asks about unsaved
    changes, it stops and hands the question back, because those changes were
    typed by the user and are not this server's to discard.
    """
    target = path or str(_project().path)
    return editor.reload_document(target)


if __name__ == "__main__":
    mcp.run()
