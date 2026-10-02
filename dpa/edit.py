"""Create new screens and elements by cloning ones DIAScreen already wrote.

Nothing here invents a section from scratch.  A real `[Element]` carries dozens
of properties whose defaults we have not mapped, so a new element starts as a
deep copy of one that works, and only the properties we understand are changed.
That keeps every unknown field at a value DIAScreen itself produced.

Two pieces of bookkeeping the format needs:

* `nPartsID` is unique per screen - the editor numbers elements 1..N as they are
  drawn, so a clone takes the next free number on its destination screen.
* section order is drawing order, so an element inserted last draws on top, and
  its `[State]` sections must stay immediately behind it.
"""

from __future__ import annotations

import copy

from .document import Document, Entry, Section
from .model import Element, Project, Screen


def clone_element(
    project: Project,
    source: Element,
    target: Screen,
    x: int | None = None,
    y: int | None = None,
    width: int | None = None,
    height: int | None = None,
    name: str | None = None,
) -> Element:
    """Copy an element onto a screen, on top of whatever is already there."""
    section = copy.deepcopy(source.section)
    states = [copy.deepcopy(s) for s in source.states]

    section.set("nPartsID", _next_part_id(target))
    for key, value in (("X", x), ("Y", y), ("Width", width), ("Height", height)):
        if value is not None:
            section.set(key, int(value))
    if name is not None:
        for key in ("wDescTextLen0", "wDescTextLen1"):
            for entry in section.entries(key):
                entry.set_text(name)

    _insert_after_last(project.doc, target, [section, *states])

    element = Element(
        section=section,
        states=states,
        screen_id=target.id,
        index=len(target.elements),
    )
    target.elements.append(element)
    return element


def set_state_text(element: Element, text: str, english: str | None = None, state: int = 0) -> None:
    """Write the caption of one state.

    A state carries one text per language slot: slot 0 is the first language,
    slot 1 the second.  On OTL-30 that is Vietnamese then English, so `english`
    fills the second slot; left out, both slots get the same words.
    """
    if state >= len(element.states):
        raise KeyError(f"element has {len(element.states)} states")
    section = element.states[state]
    entries = [
        e
        for e in section.items
        if isinstance(e, Entry) and e.blob is not None and e.key.startswith(b"wText")
    ]
    if not entries:
        raise KeyError("this state carries no text")
    for entry in entries:
        second = entry.key.endswith(b"1") and english is not None
        entry.set_text(english if second else text)


def clone_screen(project: Project, source: Screen, name: str, screen_id: int | None = None) -> Screen:
    """Copy a screen's frame - its settings and aux keys - without its elements."""
    section = copy.deepcopy(source.section)
    new_id = screen_id if screen_id is not None else max(s.id for s in project.screens) + 1
    section.set("ID", new_id)
    for key in ("wTextLen", "wScreenDESCTextLen000", "wScreenDESCTextLen001"):
        for entry in section.entries(key):
            entry.set_text(name)

    aux = copy.deepcopy(_aux_of(project.doc, source)) if _aux_of(project.doc, source) else None
    block = [section] + ([aux] if aux else [])

    last = _last_section_index(project.doc, project.screens[-1])
    project.doc.sections[last + 1 : last + 1] = block

    screen = Screen(section=section, elements=[])
    project.screens.append(screen)
    return screen


def delete_screen(project: Project, target: Screen) -> None:
    """Remove a screen with everything on it. Check first that no Goto or macro opens it."""
    start = project.doc.sections.index(target.section)
    end = _last_section_index(project.doc, target)
    del project.doc.sections[start : end + 1]
    project.screens[:] = [s for s in project.screens if s is not target]


def delete_element(project: Project, target: Screen, index: int) -> None:
    element = target.elements[index]
    # By identity, not by value: `list.remove` takes the first *equal* section,
    # and two elements with identical states (two matching divider lines) would
    # lose each other's [State] - DIAScreen then calls the screen corrupt.
    doomed = {id(section) for section in [element.section, *element.states]}
    project.doc.sections[:] = [s for s in project.doc.sections if id(s) not in doomed]
    target.elements.pop(index)
    for position, remaining in enumerate(target.elements):
        remaining.index = position


def _next_part_id(target: Screen) -> int:
    used = {e.section.get_int("nPartsID", 0) for e in target.elements}
    candidate = 1
    while candidate in used:
        candidate += 1
    return candidate


def _aux_of(doc: Document, screen: Screen) -> Section | None:
    start = doc.sections.index(screen.section)
    nxt = doc.sections[start + 1] if start + 1 < len(doc.sections) else None
    return nxt if nxt is not None and nxt.name == "AuxKeyElement" else None


def _last_section_index(doc: Document, screen: Screen) -> int:
    """The index of the last section that belongs to this screen."""
    start = doc.sections.index(screen.section)
    end = start
    for position in range(start + 1, len(doc.sections)):
        if doc.sections[position].name in ("Element", "State", "AuxKeyElement"):
            end = position
        else:
            break
    return end


def _insert_after_last(doc: Document, screen: Screen, block: list[Section]) -> None:
    at = _last_section_index(doc, screen) + 1
    doc.sections[at:at] = block
