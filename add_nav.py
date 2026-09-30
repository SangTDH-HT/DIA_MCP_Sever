"""Wire navigation between screens, drawn the same way as every other button.

Run:  python add_nav.py <project.dpa> <donor.dpa> [more donors]

A Delta button takes its face from a bitmap, so a coloured button is really
three objects: a filled rectangle, a label, and a picture-less Goto Screen
button laid over both to take the touch. The overlay keeps the donor's `Style` -
`Style=0` makes the panel draw its own grey body over the top of the others.
"""

from __future__ import annotations

import sys

from dpa import edit
from dpa.model import Project

LEFT, CENTRE = 33, 34  # FontAlign: 32 vertical centre, +1 left, +2 centre


def bgr(hex_rgb: str) -> int:
    value = int(hex_rgb.lstrip("#"), 16)
    r, g, b = (value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF
    return (b << 16) | (g << 8) | r


PANEL = bgr("#60656B")
WHITE = bgr("#FFFFFF")


def find(donors, *codes):
    for wanted in codes:
        for donor in donors:
            for screen in donor.screens:
                for element in screen.elements:
                    if element.type_code == wanted:
                        return element
    raise LookupError(codes)


def clear(element):
    for key in ("ReadVar", "WriteVar", "InterLockVar", "VisibleVar"):
        if element.section.get(key) not in (None, "None"):
            element.section.set(key, "None")
    for state in element.states:
        for key in ("Picture Name", "PIB Name"):
            if state.get(key) is not None:
                state.set(key, "")


def nav_button(project, donors, screen, destination, x, y, w, h, vi, en, key, size=14):
    """One Goto Screen element, coloured and captioned - not three objects.

    A Goto Screen strips of its picture still draws a body of its own, so a
    rectangle placed behind it is simply hidden. Colour the button itself
    instead and let it carry its own label.
    """
    goto = find(donors, "1.10")
    hit = edit.clone_element(project, goto, screen, x, y, w, h, f"{key}_hit")
    clear(hit)
    hit.section.set("GoToScreenID", destination.id)
    for entry in hit.section.entries("GoToScreenName"):
        entry.value = destination.name.encode("latin1", "replace")
    edit.set_state_text(hit, vi, en)
    for state in hit.states:
        state.set("BgColor", PANEL)
        state.set("FgColor", PANEL)
        state.set("FontColor", WHITE)
        state.set("FontBold", 1)
        state.set("FontAlign", CENTRE)
        for slot in (0, 1):
            state.set(f"FontSize{slot}", size)
            state.set(f"FontName{slot}", "Arial")
    return hit


def main(path: str, *donor_paths: str) -> None:
    project = Project(path)
    donors = [Project(p) for p in donor_paths]

    home = project.screen("Screen_1")
    roast = project.screen("scr_Roast")

    nav_button(project, donors, home, roast, 80, 380, 300, 72, "MÀN RANG", "ROASTING", "nav_roast")

    # Back out of the roasting screen from its header, where the eye already is.
    # The profile label sits at the right end of that bar, so move it aside
    # rather than stacking two things in the same place.
    for element in roast.elements:
        if element.name == "hd_profile":
            element.section.set("X", 620)
            element.section.set("Width", 200)
    nav_button(project, donors, roast, home, 1024 - 24 - 130, 12, 130, 32,
               "Trang chủ", "Home", "nav_home", size=12)

    print(project.save(path))
    print(f"{home.name} -> {roast.name} (id {roast.id}), and back from the header")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
