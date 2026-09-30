"""Put a Goto Screen button on one screen that opens another.

Run:  python add_goto.py <project.dpa> <from screen> <to screen> [donor.dpa]

A Delta button's look comes from a bitmap in the project's picture bank
(`Picture Name` + `PIB Name`), not from a colour.  Cloning a button out of
another project therefore leaves a dangling picture reference and the button
renders blank, so any picture reference is cleared here and the button falls
back to the panel's own button drawing.

This build also places a second, experimental button over a coloured rectangle
with `Style=0`, to find out whether a button can be made to show what is behind
it.  If it can, coloured buttons are possible without touching the picture bank.
"""

from __future__ import annotations

import sys

from dpa import edit
from dpa.model import Project

PICTURE_KEYS = ("Picture Name", "PIB Name", "PictureOffset", "UsePictureCoord")


def bgr(hex_rgb: str) -> int:
    value = int(hex_rgb.lstrip("#"), 16)
    r, g, b = (value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF
    return (b << 16) | (g << 8) | r


PANEL = bgr("#60656B")
WHITE = bgr("#FFFFFF")


def strip_picture(element) -> None:
    """Drop a picture reference that means nothing in this project."""
    for state in element.states:
        for key in PICTURE_KEYS:
            if state.get(key) is not None:
                state.set(key, "" if "Name" in key else 0)


def find(project: Project, *codes: str):
    for wanted in codes:
        for screen in project.screens:
            for element in screen.elements:
                if element.type_code == wanted:
                    return element
    raise LookupError(f"no element of type {codes}")


def main(path: str, from_screen: str, to_screen: str, donor_path: str = "") -> None:
    project = Project(path)
    donor = Project(donor_path) if donor_path else project

    home = project.screen(from_screen)
    destination = project.screen(to_screen)
    goto = find(donor, "1.10")
    rect = find(donor, "10.2")
    text = find(donor, "10.6")

    def wire(button):
        button.section.set("GoToScreenID", destination.id)
        for entry in button.section.entries("GoToScreenName"):
            entry.value = destination.name.encode("latin1", "replace")
        strip_picture(button)

    # 1. the plain panel button - guaranteed to draw, default grey
    plain = edit.clone_element(project, goto, home, 80, 120, 300, 72, "nav_login_plain")
    wire(plain)
    edit.set_state_text(plain, "ĐĂNG NHẬP", "LOG IN")

    # 2. the experiment: a coloured rectangle with a Style=0 button on top
    panel = edit.clone_element(project, rect, home, 80, 260, 300, 72, "nav_login_bg")
    for key in ("GradFillStartColor", "GradFillEndColor", "BorderColor"):
        panel.section.set(key, PANEL)
    panel.section.set("RoundRadius", 0)
    for state in panel.states:
        state.set("BgColor", PANEL)
        state.set("FgColor", PANEL)

    label = edit.clone_element(project, text, home, 80, 282, 300, 28, "nav_login_label")
    edit.set_state_text(label, "ĐĂNG NHẬP", "LOG IN")
    for state in label.states:
        state.set("FontColor", WHITE)
        state.set("FontSize", 16)
        state.set("FontBold", 1)

    clear = edit.clone_element(project, goto, home, 80, 260, 300, 72, "nav_login_clear")
    wire(clear)
    clear.section.set("Style", 0)
    edit.set_state_text(clear, "", "")

    print(project.save(path))
    print(f"{home.name}: 2 buttons -> screen {destination.id} ({destination.name})")


if __name__ == "__main__":
    if not 4 <= len(sys.argv) <= 5:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
