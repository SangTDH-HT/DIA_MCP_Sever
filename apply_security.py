"""Sign-in first, and the pages that need a level: the access rules of the Silo HMI in one place.

Run:  python apply_security.py <project.dpa> <asset folder>

  start-up   the panel opens on the Login page. Nobody is signed in at power-up
             (level 0) and the X that leaves the page needs level 1, so an
             account has to sign in first.
  sign in    a correct sign-in opens the home page by itself: SIGN IN winds a
             one-second countdown (ARMED), and while it runs the panel's clock
             macro opens HOME as soon as somebody is signed in (CurrentUserLevel
             above 0). A wrong password leaves the level at 0 and the page stays.
  sign out   a sign-out button on any other page opens the Login page (After
             Execute macro), so the panel is left where the next person signs in.
  level 8    the buttons that open the recipe page, Account Management and the
             scale settings (Parameter).

How a guarded button refuses (Sang 01/10/2026: "only an error, not that box"):
the panel's own answer to a press below an element's `Level` is its Login
dialog, so the guarded buttons do not use `Level`. Each one is a Momentary
button whose macro reads CurrentUserLevel: high enough, it opens the page;
otherwise it opens the small "Not allowed" message (pop_NoRight), which says
what is needed and closes by itself or at a tap. The rules are the GUARDS table.
The panel-wide setting "do not show the password window when the level is
insufficient" is switched on as well, for elements that still carry a `Level`.

One case the countdown cannot tell apart: somebody is already signed in, opens
Login from the header and types a wrong password - the level is still above 0,
so the home page opens with the earlier account still signed in (the header
shows who).

Run it after every page script and before close_popups_on_leave.py: the page
scripts draw these buttons again as plain Goto buttons. Re-runnable: a guarded
button that is still a Goto Screen is replaced, one already replaced gets its
macro again; the message's elements ("ns_") are removed first.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

from PIL import Image

import build_silo_frame as frame
import silo_i18n as i18n
from build_clean_page import BAD, add_states, canvas, find
from build_fill_page import STOP, clear_links, picture_on, rounded
from build_silo_frame import INK, WHITE, bgr, icon
from close_popups_on_leave import popups_of
from dpa import edit, macro
from dpa.model import Project

START_SCREEN, HOME = "Login", "Home_Overview"
SIGN_IN = "ln_in"                       # Set Constant: writes 1 to the panel's `Login`
SIGN_OUT = "Logout"                     # the panel parameter every sign-out button writes 1 to
ARMED = "$255"                          # clock ticks left in which a sign-in may open HOME; inside the panel
ARMED_TICKS = 10                        # x ClockMacroDelayTime (100 ms) = one second
WHY = "$256"                            # which message pop_NoRight shows: an index into MESSAGES
PRESS = "$257.0"                        # the guarded buttons' own bit, inside the panel
SIGNED_IN, ENGINEER = 1, 8
GUARDS = {  # (screen, element) -> (level its press needs, page it opens, message when refused)
    ("Login", "ln_close"): (SIGNED_IN, HOME, 0),
    ("Home_Blend", "bl_gear"): (ENGINEER, "Set_Recipe", 1),
    ("Setting", "st_tile_1"): (ENGINEER, "Set_Parameter", 1),      # scale settings
    ("Setting", "st_tile_4"): (ENGINEER, "Set_Account", 1),
}

POPUP = "pop_NoRight"
BOX = (460, 124)                        # the message, centred on the screen
CLOSE_SECONDS = 4
TITLE = ("Not allowed", "Không đủ quyền", "Accès refusé")
MESSAGES = (
    ("Sign in first", "Hãy đăng nhập trước", "Connectez-vous d'abord"),
    (f"This page needs an account of level {ENGINEER} or higher", f"Trang này cần tài khoản cấp {ENGINEER} trở lên",
     f"Cette page exige un compte de niveau {ENGINEER} ou plus"),
)
LEFT = 33


def box_face() -> Image.Image:
    w, h = BOX
    big, d = canvas(w, h, WHITE)
    rounded(d, (0, 0, w, h), fill=WHITE, outline=BAD, radius=8)
    rounded(d, (20, (h - 56) // 2, 56, 56), fill=STOP[0], outline=STOP[0], radius=8)
    image = big.resize((w, h), Image.LANCZOS)
    image.alpha_composite(icon("lock", 30, BAD, px=2.0, cut=STOP[0]), (33, (h - 30) // 2))
    return image


def enter_macro(home_id: int) -> bytes:
    """Clock macro: while the countdown runs, open HOME once an account is signed in."""
    return macro.program(
        macro.if_statement(ARMED, ">", "0"),
        macro.arith_statement(ARMED, ARMED, "-", "1"),
        macro.if_statement("CurrentUserLevel", ">", "0"),
        macro.assign_statement(ARMED, "0"),
        macro.screen_statement(macro.OPENSCREEN, home_id),
        macro.endif_statement(),
        macro.endif_statement(),
    )


def guard_macro(level: int, page_id: int, leaving: list[int], popup_id: int, why: int) -> bytes:
    """High enough: close the page's own lists and open the page. Otherwise: say why not."""
    return macro.program(
        macro.if_statement("CurrentUserLevel", ">=", str(level)),
        *(macro.screen_statement(macro.CLOSESUBSCREEN, n) for n in leaving),
        macro.screen_statement(macro.OPENSCREEN, page_id),
        macro.else_statement(),
        macro.assign_statement(WHY, str(why)),
        macro.screen_statement(macro.OPENSCREEN, popup_id),
        macro.endif_statement(),
    )


def main(path: str, asset_dir: str) -> None:
    project = Project(path)
    i18n.ensure_languages(project)
    login, home = project.screen(START_SCREEN), project.screen(HOME)
    for element in login.elements[::-1]:
        if element.name == "sc_enter":      # the "go to home" button of the first version: the page opens by itself now
            edit.delete_element(project, login, element.index)

    existing = [s for s in project.screens if s.name == POPUP]
    popup = existing[0] if existing else edit.clone_screen(project, project.screen("pop_Silo"), POPUP)
    for element in popup.elements[::-1]:
        edit.delete_element(project, popup, element.index)
    w, h = BOX
    for key, value in (("Width", w), ("Height", h), ("DocSizeX", w), ("DocSizeY", h), ("CenterSubScreen", 1),
                       ("AutoCloseTime", CLOSE_SECONDS), ("BgColor", bgr(WHITE))):
        popup.section.set(key, value)
    for slot in i18n.SLOTS:
        for entry in popup.section.entries(f"wScreenDESCTextLen00{slot}"):
            entry.set_text(POPUP)

    tpl_push = find(project, "Home_Fill", "fl_start")
    tpl_text, tpl_ind = find(project, "Home_Fill", "fl_status_bar_txt1"), find(project, "Home_Fill", "fl_fill_mode")
    tpl_close = find(project, "pop_Silo", "fl_silo_close")
    frame.prune_bank(project)
    folder = Path(asset_dir)
    folder.mkdir(parents=True, exist_ok=True)
    box_face().save(folder / "ns_box.png")
    bank = frame.Bank(project)
    bank.add("ns_box", folder / "ns_box.png")
    bank.commit()

    def style(item, size, colour, bold):
        for state in item.states:
            state.set("FontColor", bgr(colour))
            state.set("FontBold", 1 if bold else 0)
            state.set("FontAlign", LEFT)
            for slot in i18n.SLOTS:
                state.set(f"FontName{slot}", "Arial")
                state.set(f"FontSize{slot}", size)

    # --- the message: the whole box is one button that closes it; the words lie on top -----
    box = edit.clone_element(project, tpl_close, popup, 0, 0, w, h, "ns_close")
    clear_links(box)
    for key in ("ReadVar", "WriteVar"):
        box.section.set(key, PRESS)
    macro.set_macro(box.section, "ButtonOnMacroLen", macro.program(macro.screen_statement(macro.CLOSESUBSCREEN, popup.id)))
    for n in range(len(box.states)):
        picture_on(box, n, bank, "ns_box", 0, 0, w, h, WHITE)
    i18n.words(box, "")
    title = edit.clone_element(project, tpl_text, popup, 96, 30, w - 116, 27, "ns_title")
    style(title, 18, BAD, True)
    i18n.words(title, TITLE, 18)
    why = edit.clone_element(project, tpl_ind, popup, 96, 64, w - 116, 26, "ns_why")
    clear_links(why)
    why.section.set("ReadVar", WHY)
    why.section.set("MemLen", 1)            # a word: the state is the message's index
    why.section.set("AutoResizeByText", 0)
    add_states(project, why, len(MESSAGES))
    style(why, 14, INK, False)
    for n, texts in enumerate(MESSAGES):
        i18n.words(why, texts, 14, state=n)

    # --- start-up, the sign-in that opens HOME, the sign-out that opens Login ----------------
    application = project.doc.first("Application")
    application.set("DefaultScreen", login.id)
    application.set("LevelPromptNWnd", 1)       # no password window on a press below an element's Level
    macro.set_macro(application, "ClockMacroLen", enter_macro(home.id))
    macro.set_macro(find(project, START_SCREEN, SIGN_IN).section, "AfterExecMacroLen",
                    macro.program(macro.assign_statement(ARMED, str(ARMED_TICKS))))
    back = macro.program(macro.screen_statement(macro.OPENSCREEN, login.id))
    for screen in project.screens:
        for element in screen.elements:
            if element.section.get("WriteVar") == SIGN_OUT and screen is not login:
                macro.set_macro(element.section, "AfterExecMacroLen", back)

    # --- the guarded buttons ----------------------------------------------------------------
    floating = {s.id for s in project.screens if s.section.get("IsSubScreen") == "1"}
    for (screen_name, name), (level, target, message) in GUARDS.items():
        screen = project.screen(screen_name)
        old = find(project, screen_name, name)
        if old.type_code == "1.10":             # a plain Goto: put a Momentary with its face and words in its place
            box_ = tuple(old.section.get_int(k) for k in ("X", "Y", "Width", "Height"))
            button = edit.clone_element(project, tpl_push, screen, *box_, name)
            clear_links(button)
            for n, state in enumerate(button.states):
                value = state.get("Value")
                state.items = copy.deepcopy(old.states[0].items)
                state.set("Value", value if value is not None else n)
            for key in ("Style", "BorderColor", "AutoResizeByText"):
                button.section.set(key, old.section.get(key))
            edit.delete_element(project, screen, old.index)
        else:
            button = old
        for key in ("ReadVar", "WriteVar"):
            button.section.set(key, PRESS)
        button.section.set("Level", 0)
        leaving = [n for n in popups_of(screen) if n in floating and n != popup.id]
        macro.set_macro(button.section, "ButtonOnMacroLen",
                        guard_macro(level, project.screen(target).id, leaving, popup.id, message))

    i18n.ensure_languages(project)
    print(project.save(path))
    print(f"start-up screen {START_SCREEN} (id {login.id}); a sign-in opens {HOME} (id {home.id}); message {POPUP} (id {popup.id})")
    for (screen_name, name), (level, target, _) in GUARDS.items():
        button = find(project, screen_name, name)
        print(f"  {screen_name}/{name} [{button.type_code}] level {level} -> {target}:",
              macro.statements(button.section.entries("ButtonOnMacroLen")[0].blob))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
