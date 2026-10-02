"""Draw the sign-in page (Login) and the Account Management page (Set_Account) of the Silo HMI.

Run:  python build_account_pages.py <project.dpa> <asset folder>

Both pages work on the panel's own accounts through its internal parameters
(DIAScreen manual p.689-691, accounts must not be "simple password"):

  SetUserAccount / SetUserPassword / SetUserLevel   what the operator types
  Login, Logout                                     write 1 to do it, the panel puts 0 back
  AddUserAccount, DeleteUserAccount, ChangeUserPassword   the same, for the typed account
  ACCOUNT, CurrentUserLevel                         who is signed in
  LoginResult, AddUserAccountResult, ...            "Success" / "Fail"

  Login        a full page after OTL-30's Pop_Login: brand panel left, account and
               password in the upper half (the keypad covers the lower half),
               SIGN IN / SIGN OUT, who is signed in.
  Set_Account  session card; one form to add an account, change its password or
               delete it; and the panel's own account table for the full list -
               the panel has no parameter that lists accounts.
  header       the user menu shows the signed-in account and opens Login. The
               touch area is a transparent button ON TOP of the name, so the
               press never depends on a display letting it through.

Words are element texts in three languages (silo_i18n). Re-runnable: elements
named "ln_", "ac_" and "fr_user/fr_account" are removed first.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

from PIL import Image, ImageDraw

import build_calibration_page as cal
import build_fill_page as fill
import build_silo_frame as frame
import silo_i18n as i18n
from build_fill_page import CARD_LINE, FIELD_LINE, TILE, clear_links, picture_on, rounded
from build_setting_page import CONTENT_TOP
from build_silo_frame import INK, MUTED, NAV_INK, NAV_ON, PAGE, WHITE, bgr, icon, rgb
from dpa import edit, macro
from dpa.model import Project

OLD = r"C:\OTL\17.OTL_SILO\OTL_Silo6\HMI"
ENTRY_DONOR = (OLD + r"\FILETEST.dpa", "scr_Overview", 77)      # Character Entry 6.2
TABLE_DONOR = (OLD + r"\HMI_UPDATE.dpa", "pop_Setting", 9)      # Password Table Setting 12.2
LOGO = Path(r"C:\OTL\4.Icon_OTL\1.OTL_Logo\fulllogo_transparent_nobuffer.png")   # white wordmark
BRAND = "#2F3A45"
BRAND_SOFT = "#C9D0D8"
VALUE = "#2B3644"
LEFT, CENTRE, RIGHT = 33, 34, 36
NAME_CHARS = 24                     # the panel's limit for an account name

LOGIN = "Login"
SIDE_W = 380
EDGE_X, EDGE_Y = frame.RECT_PAD_X, frame.RECT_PAD_Y   # a Rectangle's own edge around its picture: kept inside the screen
FORM_X, FORM_W = 440, 500
USER_BOX = (FORM_X, 176, FORM_W, 50)
PASS_BOX = (FORM_X, 262, FORM_W, 50)
IN_BTN = (FORM_X, 336, 300, 52)
OUT_BTN = (FORM_X + 312, 336, FORM_W - 312, 52)
CLOSE = (960, 20, 40, 40)

ACCOUNT_PAGE = "Set_Account"
SESSION = (100, CONTENT_TOP, 916, 92)
FORM = (100, CONTENT_TOP + 102, 916, 248)
TABLE = (100, CONTENT_TOP + 360, 916, 92)
F_USER = (116, FORM[1] + 70, 320, 46)
F_PASS = (452, FORM[1] + 70, 320, 46)
F_LEVEL = (788, FORM[1] + 70, 110, 46)
ACTIONS = (  # element, parameter, result parameter, dark face, (English, Vietnamese, French)
    ("ac_add", "AddUserAccount", "AddUserAccountResult", True, ("ADD ACCOUNT", "THÊM TÀI KHOẢN", "AJOUTER")),
    ("ac_change", "ChangeUserPassword", "ChangePasswordResult", False, ("CHANGE PASSWORD", "ĐỔI MẬT KHẨU", "CHANGER MOT DE PASSE")),
    ("ac_delete", "DeleteUserAccount", "DeleteUserAccountResult", False, ("DELETE ACCOUNT", "XOÁ TÀI KHOẢN", "SUPPRIMER")),
)
ACTION_AT = [(116 + 252 * i, FORM[1] + 140, 240, 46) for i in range(3)]
USER_MENU = (1024 - 14 - 190, 11, 190, 36)       # header, right


# --- pictures (no words) -----------------------------------------------------------------

def canvas(w, h, back=PAGE):
    big = Image.new("RGBA", (w * 4, h * 4), rgb(back) + (255,))
    return big, ImageDraw.Draw(big)


def side_face() -> Image.Image:
    image = Image.new("RGBA", (SIDE_W - 2 * EDGE_X, 600 - 2 * EDGE_Y), rgb(BRAND) + (255,))
    logo = Image.open(LOGO).convert("RGBA")
    width = 250
    logo = logo.resize((width, round(logo.height * width / logo.width)), Image.LANCZOS)
    image.alpha_composite(logo, (44 - EDGE_X, 64 - EDGE_Y))
    d = ImageDraw.Draw(image)
    d.rounded_rectangle((44 - EDGE_X, 212 - EDGE_Y, 44 - EDGE_X + 44, 216 - EDGE_Y), radius=2, fill=rgb(NAV_ON))
    return image


def form_face() -> Image.Image:
    """Right side of Login: the title bar and the two field boxes."""
    w, h = 1024 - SIDE_W - 2 * EDGE_X, 600 - 2 * EDGE_Y
    ox, oy = SIDE_W + EDGE_X, EDGE_Y
    big, d = canvas(w, h)
    d.rounded_rectangle(((FORM_X - ox) * 4, (116 - oy) * 4, (FORM_X - ox + 44) * 4, (120 - oy) * 4), radius=8, fill=NAV_ON)
    for x, y, bw, bh in (USER_BOX, PASS_BOX):
        rounded(d, (x - ox, y - oy, bw, bh), fill=WHITE, outline=FIELD_LINE, radius=6)
    d.line(((FORM_X - ox) * 4, (412 - oy) * 4, (FORM_X - ox + FORM_W) * 4, (412 - oy) * 4), fill=CARD_LINE, width=4)
    return big.resize((w, h), Image.LANCZOS)


def close_face() -> Image.Image:
    _, _, w, h = CLOSE
    big, d = canvas(w, h)
    rounded(d, (0, 0, w, h), fill=WHITE, outline=FIELD_LINE, radius=6)
    image = big.resize((w, h), Image.LANCZOS)
    image.alpha_composite(icon("x", 20, NAV_INK, px=1.75, cut=WHITE), ((w - 20) // 2, (h - 20) // 2))
    return image


def card(box, glyph: str | None, wells=()) -> Image.Image:
    ox, oy, w, h = box
    big, d = canvas(w, h)
    rounded(d, (0, 0, w, h))
    if glyph:
        rounded(d, (10, 10, 34, 34), fill=TILE, outline=TILE, radius=5)
    for x, y, bw, bh in wells:
        rounded(d, (x - ox, y - oy, bw, bh), fill=WHITE, outline=FIELD_LINE, radius=6)
    image = big.resize((w, h), Image.LANCZOS)
    if glyph:
        image.alpha_composite(icon(glyph, 22, NAV_INK, px=1.5, cut=TILE), (16, 16))
    return image


def user_menu_face() -> Image.Image:
    _, _, w, h = USER_MENU
    image = Image.new("RGBA", (w, h), rgb(PAGE) + (255,))
    image.alpha_composite(icon("user", 24, NAV_INK, solid=True), (2, (h - 24) // 2))
    image.alpha_composite(icon("chevron-down", 18, NAV_INK, px=1.75), (w - 22, (h - 18) // 2))
    return image


def main(path: str, asset_dir: str) -> None:
    project = Project(path)
    i18n.ensure_languages(project)
    base = project.screen("Khung_Chung")
    home = project.screen("Home_Fill")
    page = project.screen(ACCOUNT_PAGE)

    found = [s for s in project.screens if s.name == LOGIN]
    login = found[0] if found else edit.clone_screen(project, home, LOGIN)
    login.section.set("BaseScreenID", 0)          # a page of its own: no header, no sidebar
    for slot in i18n.SLOTS:
        for entry in login.section.entries(f"wScreenDESCTextLen00{slot}"):
            entry.set_text(LOGIN)

    for screen, prefixes in ((login, ("ln_",)), (page, ("ac_",)), (base, ("fr_user", "fr_account"))):
        for element in screen.elements[::-1]:
            if element.name.startswith(prefixes):
                edit.delete_element(project, screen, element.index)

    def find(screen_name, name):
        return next(e for e in project.screen(screen_name).elements if e.name == name)

    tpl_rect, tpl_text = find("Home_Fill", "fl_process"), find("Home_Fill", "fl_status_bar_txt1")
    tpl_num, tpl_name = find("Home_Fill", "fl_rate"), find("Home_Fill", "fl_silo_name")
    tpl_push, tpl_goto = find("Set_Calibration", "cal_apply"), find("Home_Fill", "nav_home")
    tpl_level = find("Set_Parameter", "pr_1_1")
    tpl_const = find("pop_Silo", "fl_row_1")
    tpl_entry = Project(ENTRY_DONOR[0]).element(*ENTRY_DONOR[1:])
    tpl_table = Project(TABLE_DONOR[0]).element(*TABLE_DONOR[1:])
    frame.prune_bank(project)

    folder = Path(asset_dir)
    folder.mkdir(parents=True, exist_ok=True)
    faces = {
        "ln_side": side_face(), "ln_form": form_face(), "ln_close": close_face(),
        "ac_session": card(SESSION, "user"), "ac_form": card(FORM, "users", (F_USER, F_PASS, F_LEVEL)),
        "ac_table": card(TABLE, "database"), "fr_user_face": user_menu_face(),
    }
    sizes = {(240, 46), (IN_BTN[2], IN_BTN[3]), (OUT_BTN[2], OUT_BTN[3]), (150, 44), (220, 44)}
    for w, h in sizes:
        for dark in (False, True):
            for p in (0, 1):
                faces[f"btn_{w}x{h}_{int(dark)}_{p}"] = cal.button_face(w, h, "", dark, bool(p))
    bank = frame.Bank(project)
    for key, image in faces.items():
        image.save(folder / f"{key}.png")
        bank.add(key, folder / f"{key}.png")
    bank.commit()

    def style(item, size, colour, bold=False, align=LEFT):
        for state in item.states:
            state.set("FontColor", bgr(colour))
            state.set("FontBold", 1 if bold else 0)
            state.set("FontAlign", align)
            for slot in i18n.SLOTS:
                state.set(f"FontName{slot}", "Arial")
                state.set(f"FontSize{slot}", size)

    def picture(screen, key, x, y, back=PAGE):
        _, _, w, h = bank.where[key]
        item = edit.clone_element(project, tpl_rect, screen, 0, 0, 10, 10, key)
        clear_links(item)
        frame.face(item, bank, key)
        frame.flat(item, back)
        for state in item.states:
            state.set("TransColor", bgr(back))
        frame.picture_rect(item, x, y, w, h)

    def text(screen, name, box, texts, size=14, colour=INK, bold=False, align=LEFT):
        item = edit.clone_element(project, tpl_text, screen, *box, name)
        style(item, size, colour, bold, align)
        i18n.words(item, texts, size)
        return item

    def shown(screen, name, box, parameter, chars, size=16, colour=INK, bold=True, align=LEFT):
        """Character Display of an internal parameter."""
        item = edit.clone_element(project, tpl_name, screen, *box, name)
        clear_links(item)
        item.section.set("ReadVar", parameter)
        item.section.set("StringLen", chars)
        style(item, size, colour, bold, align)
        return item

    def entry(screen, name, box, parameter, secret=False):
        x, y, w, h = box
        item = edit.clone_element(project, tpl_entry, screen, x + 10, y + 6, w - 20, h - 12, name)
        i18n.ensure_languages(project)            # the donor has two language slots
        clear_links(item)
        for key in ("ReadVar", "WriteVar"):
            item.section.set(key, parameter)
        for key, value in (("StringLen", NAME_CHARS), ("DispAsterisk", 1 if secret else 0), ("Style", 3),
                           ("AutoResizeByText", 0), ("Level", 0)):
            item.section.set(key, value)
        for state in item.states:
            for colour_key in ("FgColor", "BgColor"):
                state.set(colour_key, bgr(WHITE))
        style(item, 18, VALUE, True)
        i18n.words(item, "")
        return item

    def push(screen, name, box, parameter, texts, dark, size=14):
        """Set Constant 1 on a trigger parameter; the panel puts it back to 0 when it is done.

        Internal parameters take word elements only: a bit button on one does not
        compile ("Element address input error").
        """
        x, y, w, h = box
        item = edit.clone_element(project, tpl_const, screen, x, y, w, h, name)
        clear_links(item)
        item.section.set("WriteVar", parameter)
        item.section.set("SetValue", 1)
        item.section.set("Style", 3)
        macro.set_macro(item.section, "BeforeExecMacroLen", None)
        macro.set_macro(item.section, "AfterExecMacroLen", None)
        # Set Constant keeps no picture keys; a pushbutton state has them
        item.states[0].items = copy.deepcopy(tpl_push.states[0].items)
        picture_on(item, 0, bank, f"btn_{w}x{h}_{int(dark)}_0", x, y, w, h, WHITE)
        item.states[0].set("FontColor", bgr(WHITE if dark else INK))
        item.states[0].set("FontBold", 1)
        item.states[0].set("FontAlign", CENTRE)
        i18n.words(item, texts, size, state=0, margin=16)
        return item

    def goto(screen, name, box, destination, key=None, texts="", size=14, colour=INK, bold=True):
        x, y, w, h = box
        item = edit.clone_element(project, tpl_goto, screen, x, y, w, h, name)
        item.section.set("GoToScreenID", destination.id)
        for goto_name in item.section.entries("GoToScreenName"):
            goto_name.value = destination.name.encode("latin1")
        if key:
            frame.face(item, bank, key)
            frame.flat(item)
        else:        # a touch area only: Style 3 and no picture draws nothing
            frame.flat(item)
            for state in item.states:
                state.items = [i for i in state.items if getattr(i, "key", b"").decode("latin1") not in frame.PICTURE_KEYS]
                state.set("PictureStretch", 0)
        style(item, size, colour, bold, CENTRE)
        i18n.words(item, texts, size, margin=16)
        return item

    # --- header: who is signed in, and the way to Login ------------------------------
    ux, uy, uw, uh = USER_MENU
    picture(base, "fr_user_face", ux, uy)
    shown(base, "fr_account", (ux + 32, uy + 6, uw - 58, 24), "ACCOUNT", NAME_CHARS, 16, NAV_INK, False)
    goto(base, "fr_user", USER_MENU, login)

    # --- Login -------------------------------------------------------------------------
    picture(login, "ln_side", EDGE_X, EDGE_Y, BRAND)
    picture(login, "ln_form", SIDE_W + EDGE_X, EDGE_Y)
    text(login, "ln_t_model", (44, 164, 290, 36), "SILO 6", 28, WHITE, True)
    text(login, "ln_t_about", (44, 232, 300, 21),
         ("Sign in to run the silo system", "Đăng nhập để vận hành hệ silo", "Connectez-vous pour piloter les silos"), 14, BRAND_SOFT)
    text(login, "ln_t_company", (44, 540, 310, 18), "O TESLA INDUSTRIAL CO., LTD", 12, BRAND_SOFT)
    text(login, "ln_t_web", (44, 560, 310, 18), "www.otlpro.com", 12, BRAND_SOFT)

    text(login, "ln_t_title", (FORM_X - 4, 58, 420, 51), ("Sign in", "Đăng nhập", "Connexion"), 36, INK, True)
    text(login, "ln_t_user", (FORM_X - 4, USER_BOX[1] - 26, 300, 21), ("Account", "Tài khoản", "Compte"), 14, MUTED)
    entry(login, "ln_user", USER_BOX, "SetUserAccount")
    text(login, "ln_t_pass", (FORM_X - 4, PASS_BOX[1] - 26, 300, 21), ("Password", "Mật khẩu", "Mot de passe"), 14, MUTED)
    entry(login, "ln_pass", PASS_BOX, "SetUserPassword", secret=True)
    sign_in = push(login, "ln_in", IN_BTN, "Login", ("SIGN IN", "ĐĂNG NHẬP", "SE CONNECTER"), True, 16)
    # signed in -> the main page; a wrong password leaves the level at 0 and the page open
    macro.set_macro(sign_in.section, "AfterExecMacroLen", macro.program(
        macro.if_statement("CurrentUserLevel", ">", "0"),
        macro.screen_statement(macro.OPENSCREEN, home.id),
        macro.endif_statement()))
    push(login, "ln_out", OUT_BTN, "Logout", ("SIGN OUT", "ĐĂNG XUẤT", "DÉCONNEXION"), False)
    text(login, "ln_t_now", (FORM_X - 4, 428, 150, 21), ("Signed in as", "Đang đăng nhập", "Connecté"), 14, MUTED)
    shown(login, "ln_now", (FORM_X + 150, 426, 220, 24), "ACCOUNT", NAME_CHARS, 16, VALUE)
    text(login, "ln_t_level", (FORM_X + 372, 428, 70, 21), ("Level", "Cấp", "Niveau"), 14, MUTED, align=RIGHT)
    level = edit.clone_element(project, tpl_num, login, FORM_X + 446, 426, 40, 24, "ln_level")
    clear_links(level)
    level.section.set("ReadVar", "CurrentUserLevel")
    level.section.set("IntNum", 2)
    level.section.set("DotNum", 0)
    style(level, 16, VALUE, True, LEFT)
    text(login, "ln_t_result", (FORM_X - 4, 460, 150, 21), ("Last sign-in", "Lần vừa rồi", "Dernier essai"), 14, MUTED)
    shown(login, "ln_result", (FORM_X + 150, 458, 220, 24), "LoginResult", 8, 16, VALUE)
    goto(login, "ln_close", CLOSE, home, "ln_close")

    # --- Set_Account ---------------------------------------------------------------------
    sx, sy = SESSION[0], SESSION[1]
    picture(page, "ac_session", sx, sy)
    text(page, "ac_t_session", (sx + 52, sy + 17, 260, 21), ("SIGNED IN", "ĐANG ĐĂNG NHẬP", "SESSION"), 14, INK, True)
    shown(page, "ac_now", (sx + 16, sy + 54, 300, 26), "ACCOUNT", NAME_CHARS, 18, VALUE)
    text(page, "ac_t_level", (sx + 330, sy + 58, 70, 21), ("Level", "Cấp", "Niveau"), 14, MUTED, align=RIGHT)
    level = edit.clone_element(project, tpl_num, page, sx + 404, sy + 55, 40, 26, "ac_level")
    clear_links(level)
    level.section.set("ReadVar", "CurrentUserLevel")
    level.section.set("IntNum", 2)
    level.section.set("DotNum", 0)
    style(level, 18, VALUE, True, LEFT)
    goto(page, "ac_signin", (sx + SESSION[2] - 16 - 150 - 12 - 150, sy + 24, 150, 44), login, "btn_150x44_1_0",
         ("SIGN IN", "ĐĂNG NHẬP", "CONNEXION"), 14, WHITE)
    push(page, "ac_signout", (sx + SESSION[2] - 16 - 150, sy + 24, 150, 44), "Logout", ("SIGN OUT", "ĐĂNG XUẤT", "DÉCONNEXION"), False)

    fx, fy = FORM[0], FORM[1]
    picture(page, "ac_form", fx, fy)
    text(page, "ac_t_form", (fx + 52, fy + 17, 700, 21),
         ("ADD, CHANGE PASSWORD, DELETE", "THÊM, ĐỔI MẬT KHẨU, XOÁ", "AJOUTER, CHANGER LE MOT DE PASSE, SUPPRIMER"), 14, INK, True)
    text(page, "ac_t_user", (F_USER[0] - 4, F_USER[1] - 24, 300, 21), ("Account", "Tài khoản", "Compte"), 14, MUTED)
    entry(page, "ac_user", F_USER, "SetUserAccount")
    text(page, "ac_t_pass", (F_PASS[0] - 4, F_PASS[1] - 24, 300, 21), ("Password", "Mật khẩu", "Mot de passe"), 14, MUTED)
    entry(page, "ac_pass", F_PASS, "SetUserPassword", secret=True)
    text(page, "ac_t_lvl", (F_LEVEL[0] - 4, F_LEVEL[1] - 24, 190, 21), ("Level (0–9)", "Cấp (0–9)", "Niveau (0–9)"), 14, MUTED)
    lx, ly, lw, lh = F_LEVEL
    lvl = edit.clone_element(project, tpl_level, page, lx + 10, ly + 6, lw - 20, lh - 12, "ac_lvl")
    clear_links(lvl)
    for key in ("ReadVar", "WriteVar"):
        lvl.section.set(key, "SetUserLevel")
    for key, value in (("IntNum", 1), ("DotNum", 0), ("MinValue", "0.0"), ("MaxValue", "9.0")):
        lvl.section.set(key, value)
    style(lvl, 18, VALUE, True, CENTRE)
    for (name, parameter, result, dark, texts), box in zip(ACTIONS, ACTION_AT):
        push(page, name, box, parameter, texts, dark)
        shown(page, f"{name}_result", (box[0] + 4, box[1] + box[3] + 6, box[2] - 8, 20), result, 8, 12, MUTED, False, CENTRE)
    text(page, "ac_t_rule", (fx + 16, fy + FORM[3] - 30, FORM[2] - 32, 18),
         ("Only accounts below your own level can be added or deleted.",
          "Chỉ thêm / xoá được tài khoản có cấp thấp hơn cấp đang đăng nhập.",
          "Seuls les comptes d'un niveau inférieur au vôtre peuvent être ajoutés ou supprimés."), 12, MUTED)

    tx, ty = TABLE[0], TABLE[1]
    picture(page, "ac_table", tx, ty)
    text(page, "ac_t_table", (tx + 52, ty + 17, 500, 21), ("ALL ACCOUNTS", "TẤT CẢ TÀI KHOẢN", "TOUS LES COMPTES"), 14, INK, True)
    text(page, "ac_t_table2", (tx + 16, ty + 56, 600, 21),
         ("The full list is the panel's own account table.", "Danh sách đầy đủ nằm ở bảng tài khoản của màn hình.",
          "La liste complète est la table des comptes du pupitre."), 14, MUTED)
    bx, by, bw, bh = tx + TABLE[2] - 16 - 220, ty + 24, 220, 44
    table = edit.clone_element(project, tpl_table, page, bx, by, bw, bh, "ac_open_table")
    i18n.ensure_languages(project)
    table.section.set("Style", 3)
    table.section.set("AutoResizeByText", 0)
    for macro_key in ("BeforeExecMacroLen", "AfterExecMacroLen"):
        macro.set_macro(table.section, macro_key, None)
    picture_on(table, 0, bank, "btn_220x44_0_0", bx, by, bw, bh, WHITE)
    style(table, 14, INK, True, CENTRE)
    i18n.words(table, ("ACCOUNT TABLE", "BẢNG TÀI KHOẢN", "TABLE DES COMPTES"), 14, margin=16)

    i18n.ensure_languages(project)
    print(project.save(path))
    print(f"{LOGIN} (id {login.id}): {len(login.elements)} elements; {ACCOUNT_PAGE}: {len(page.elements)} elements")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
