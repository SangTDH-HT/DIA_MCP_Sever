"""Build the OTL-30-styled login screen into a Delta .dpa project.

Run:  python build_login.py <source.dpa> <output.dpa> [donor.dpa]

A brand new project has no elements to clone from, so `donor` names a project
that does. Donor and target must be the same panel, since geometry and colour
depth come from the panel.

Every element is cloned from one the project already contains, so unmapped
properties keep values DIAScreen itself wrote.  Only geometry, colour, text and
the addresses are set here.

Layout follows two constraints of the panel rather than of a web page: the
on-screen keypad covers the lower half, so both fields sit in the upper half;
and a gloved finger needs 60 px, so nothing tappable is smaller.
"""

from __future__ import annotations

import sys

from dpa import edit
from dpa.model import Project


def bgr(hex_rgb: str) -> int:
    """DOPSoft stores colours as BGR integers, the Windows way."""
    value = int(hex_rgb.lstrip("#"), 16)
    r, g, b = (value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF
    return (b << 16) | (g << 8) | r


# OTL-30 HOME palette - see the otl30-home-visual-style note. Zero rounding.
PANEL = bgr("#60656B")
PAGE = bgr("#F5F6F8")
CARD = bgr("#FFFFFF")
BORDER = bgr("#CDD0D5")
INK = bgr("#60656B")
WHITE = bgr("#FFFFFF")
ERROR = bgr("#FF4444")

SCREEN_W, SCREEN_H = 1024, 600
LEFT_W = 340
FORM_X = LEFT_W + 60
FIELD_W, FIELD_H = 420, 60
BUTTON_H = 64

# Internal panel memory. The Silo project's highest used word is $1755, so this
# block is free; check with the `addresses` tool before reusing it elsewhere.
ADDR_USER = "$1800"
ADDR_PASS = "$1820"
ADDR_LOGIN = "$1840.0"


def find_template(project: Project, *type_codes: str):
    """The first element matching any of these Type.SubType codes, in order.

    Projects differ in which button flavours they contain, so callers pass the
    kinds they can live with rather than one code that may not be there.
    """
    for wanted in type_codes:
        for screen in project.screens:
            for element in screen.elements:
                if element.type_code == wanted:
                    return element
    raise LookupError(f"no template element of type {type_codes} in this project")


def bind(element, read=None, write=None) -> None:
    """Point an element at an address, and clear what the template was wired to."""
    for key, value in (("ReadVar", read), ("WriteVar", write)):
        if value is not None and element.section.get(key) is not None:
            element.section.set(key, value)
    for key in ("InterLockVar", "VisibleVar"):
        if element.section.get(key) not in (None, "None"):
            element.section.set(key, "None")


def main(source: str, output: str, donor_path: str = "") -> None:
    project = Project(source)
    donor = Project(donor_path) if donor_path else project
    if donor_path:
        here, there = project.info(), donor.info()
        if here["panel"] != there["panel"]:
            raise SystemExit(f"panel mismatch: {here['panel']} vs donor {there['panel']}")

    rect = find_template(donor, "10.2")
    text = find_template(donor, "10.6")
    entry = find_template(donor, "6.2", "6.1")
    button = find_template(donor, "1.1", "1.3", "1.4")

    login = edit.clone_screen(project, project.screens[0], "scr_Login")
    login.section.set("BgColor", PAGE)
    login.section.set("DocSizeX", SCREEN_W)
    login.section.set("DocSizeY", SCREEN_H)

    def add_rect(x, y, w, h, fill, name, border=None):
        item = edit.clone_element(project, rect, login, x, y, w, h, name)
        item.section.set("GradFillStartColor", fill)
        item.section.set("GradFillEndColor", fill)
        item.section.set("BorderColor", border if border is not None else fill)
        item.section.set("RoundRadius", 0)
        item.section.set("EnableCustomRadius", 0)
        bind(item)
        for state in item.states:
            state.set("BgColor", fill)
            state.set("FgColor", fill)
        return item

    def add_text(x, y, w, h, vi, en, colour, size, name, bold=0):
        item = edit.clone_element(project, text, login, x, y, w, h, name)
        edit.set_state_text(item, vi, en)
        bind(item)
        for state in item.states:
            state.set("FontColor", colour)
            state.set("FontSize", size)
            state.set("FontBold", bold)
        return item

    # --- brand panel: the one bold block, everything else stays quiet -----
    add_rect(0, 0, LEFT_W, SCREEN_H, PANEL, "lg_panel")
    add_text(36, 60, 260, 56, "OTL-30", "OTL-30", WHITE, 40, "lg_brand", bold=1)
    add_text(36, 124, 260, 28, "Máy rang silo", "Silo Roaster", WHITE, 14, "lg_model")
    add_rect(36, 168, 64, 3, WHITE, "lg_accent")
    add_text(36, 500, 280, 24, "O-TESLA", "O-TESLA", WHITE, 12, "lg_company")

    # --- form, upper half, clear of the keypad ----------------------------
    add_text(FORM_X, 96, 300, 28, "Người dùng", "User", INK, 14, "lg_user_label", bold=1)
    add_rect(FORM_X, 128, FIELD_W, FIELD_H, CARD, "lg_user_box", BORDER)
    user = edit.clone_element(project, entry, login, FORM_X + 12, 140, FIELD_W - 24, 36, "lg_user")
    bind(user, read=ADDR_USER, write=ADDR_USER)
    user.section.set("DispAsterisk", 0)

    add_text(FORM_X, 216, 300, 28, "Mật khẩu", "Password", INK, 14, "lg_pass_label", bold=1)
    add_rect(FORM_X, 248, FIELD_W, FIELD_H, CARD, "lg_pass_box", BORDER)
    password = edit.clone_element(project, entry, login, FORM_X + 12, 260, FIELD_W - 24, 36, "lg_pass")
    bind(password, read=ADDR_PASS, write=ADDR_PASS)
    password.section.set("DispAsterisk", 1)

    # --- action -----------------------------------------------------------
    action = edit.clone_element(project, button, login, FORM_X, 348, FIELD_W, BUTTON_H, "lg_login")
    edit.set_state_text(action, "ĐĂNG NHẬP", "LOG IN")
    bind(action, read=ADDR_LOGIN, write=ADDR_LOGIN)
    for state in action.states:
        state.set("BgColor", PANEL)
        state.set("FgColor", PANEL)
        state.set("FontColor", WHITE)
        state.set("FontSize", 16)
        state.set("FontBold", 1)

    # --- failure message: says what to do, does not apologise -------------
    add_text(
        FORM_X, 436, FIELD_W, 26,
        "Sai mật khẩu. Thử lại.", "Wrong password. Try again.",
        ERROR, 12, "lg_error",
    )

    result = project.save(output)
    print(f"screen scr_Login id={login.id}, {len(login.elements)} elements")
    print(result)


if __name__ == "__main__":
    if not 3 <= len(sys.argv) <= 4:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) == 4 else "")
