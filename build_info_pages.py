"""Draw the About page (Set_About) and the scale settings page (Set_Parameter).

Run:  python build_info_pages.py <project.dpa> <asset folder>

About       everything on it is fixed text, so the page is one picture plus an
            X that goes back to Settings.
Parameter   "CAI DAT BON CAN": three cards - discharge, filling, general and
            speed - of six settings each. A setting is a label, its range
            under it and a numeric entry limited to that range.

Back link and title come from build_setting_page.py, like every sub-page; this script
draws the content from CONTENT_TOP down and leaves the st_ elements alone. Entries are one signed word, value x10, like every number on
this HMI. No PLC addresses exist yet: ADDRESSES is the list to rebind.
Re-runnable: elements named "ab_" / "pr_" are removed first.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

import build_fill_page as fill
import build_silo_frame as frame
from build_fill_page import CARD_LINE, FIELD_LINE, RIGHT, clear_links, rounded, text_style
from build_setting_page import CONTENT_TOP
from build_silo_frame import INK, MUTED, NAV_INK, PAGE, TAB_LINE, WHITE, bgr, font, icon, rgb
from dpa import edit
from dpa.model import Project

LOGO = Path(r"C:\OTL\LOGO_OTESLA\OTL\OTL-logo-square-01.png")
BLUE = TAB_LINE          # section titles, the web link
VALUE = "#2B3644"


# --- Parameter page ----------------------------------------------------------------
CARDS = (
    ("CÀI ĐẶT XẢ LIỆU", "arrow-down-to-line", (
        ("Trễ mở van xả bồn", 1, 30, "s"),
        ("Thời gian mở van xả phễu", 2, 60, "s"),
        ("Thời gian hút tối đa mỗi mẻ", 30, 600, "s"),
        ("Thời gian chuyển bồn", 5, 45, "s"),
        ("Mở GHFV – trễ chạy động cơ", 1, 5, "s"),
        ("Tắt động cơ – trễ đóng GHFV", 5, 10, "s"),
    )),
    ("CÀI ĐẶT NẠP LIỆU", "arrow-up-from-line", (
        ("Ổn định đường ống", 5, 60, "s"),
        ("Tổng thời gian nạp mỗi mẻ", 60, 900, "s"),
        ("Nạp ngắt quãng – van mở", 2, 60, "s"),
        ("Nạp ngắt quãng – nghỉ", 2, 60, "s"),
        ("Chuyển bồn – đóng van phễu", 5, 60, "s"),
        ("Trễ đóng van bồn", 1, 30, "s"),
    )),
    ("CÀI ĐẶT CHUNG & TỐC ĐỘ", "settings", (
        ("Trọng lượng tối đa", 500, 800, "kg"),
        ("Giới hạn áp suất", 0, 50, "Pa"),
        ("Thời gian xả đường ống", 5, 120, "s"),
        ("Nạp ngắt quãng – van mở", 20, 100, "%"),
        ("Nạp ngắt quãng – nghỉ", 0, 50, "%"),
        ("Xả / phối trộn – tốc độ biến tần", 20, 100, "%"),
    )),
)
ADDRESSES = {f"pr_{c + 1}_{r + 1}": f"${700 + 6 * c + r}" for c in range(3) for r in range(6)}  # value x10

CARD_Y, CARD_H, CARD_W, GAP = CONTENT_TOP, 472, 297, 12
ROW_TOP, ROW_H = 52, 70
BOX_W, BOX_H = 80, 40


def card_x(c: int) -> int:
    return 100 + c * (CARD_W + GAP)


def fit_label(t: ImageDraw.ImageDraw, words: str, room: int):
    """One line at 14 or 13 px; otherwise two balanced lines at 13, broken at the dash if there is one."""
    for size in (14, 13):
        face = font("arial.ttf", size)
        if t.textlength(words, font=face) <= room:
            return face, [words]
    face = font("arial.ttf", 13)
    if " – " in words:
        head, tail = words.split(" – ", 1)
        return face, [head + " –", tail]
    parts = words.split(" ")
    best = min(range(1, len(parts)), key=lambda i: abs(t.textlength(" ".join(parts[:i]), font=face)
                                                    - t.textlength(" ".join(parts[i:]), font=face)))
    return face, [" ".join(parts[:best]), " ".join(parts[best:])]


def parameter_face() -> Image.Image:
    w, h = 916, CARD_H
    s = 4
    big = Image.new("RGBA", (w * s, h * s), rgb(PAGE) + (255,))
    d = ImageDraw.Draw(big)
    oy = CARD_Y
    for c, (_, _, rows) in enumerate(CARDS):
        x = card_x(c) - 100
        y = CARD_Y - oy
        rounded(d, (x, y, CARD_W, CARD_H))
        d.line(((x + 14) * s, (y + 46) * s, (x + CARD_W - 14) * s, (y + 46) * s), fill=CARD_LINE, width=s)
        for r in range(len(rows)):
            ry = y + ROW_TOP + ROW_H * r
            if r:
                d.line(((x + 14) * s, ry * s, (x + CARD_W - 14) * s, ry * s), fill=CARD_LINE, width=s)
            rounded(d, (x + CARD_W - 14 - BOX_W, ry + (ROW_H - BOX_H) // 2, BOX_W, BOX_H), outline=FIELD_LINE)
    image = big.resize((w, h), Image.LANCZOS)
    t = ImageDraw.Draw(image)
    for c, (title, name, rows) in enumerate(CARDS):
        x = card_x(c) - 100
        y = CARD_Y - oy
        image.alpha_composite(icon(name, 24, BLUE, px=2.0, cut=WHITE), (x + 14, y + 11))
        t.text((x + 46, y + 23), title, font=font("arialbd.ttf", 15), fill=BLUE, anchor="lm")
        room = CARD_W - 28 - BOX_W - 8
        for r, (words, low, high, unit) in enumerate(rows):
            ry = y + ROW_TOP + ROW_H * r
            face, lines = fit_label(t, words, room)
            top = ry + (ROW_H - 18 * len(lines) - 16) / 2
            for i, line in enumerate(lines):
                t.text((x + 14, top + 9 + 18 * i), line, font=face, fill=INK, anchor="lm")
            t.text((x + 14, top + 18 * len(lines) + 8), f"{low} – {high} {unit}", font=font("arial.ttf", 12),
                   fill=MUTED, anchor="lm")
    return image


# --- About page ---------------------------------------------------------------------
PRODUCT = (0, 0, 916, 100)       # inside the page picture, which starts at 100, CONTENT_TOP
DY = 58                          # every other y below was laid out with the product card at 58
CONTACTS = (("phone", "Mobile", "(+84) 936 198 938"), ("globe", "Website", "https://www.otlpro.com/"),
            ("mail", "Email", "otesla.vn@gmail.com"))


def logo_mark(size: int) -> Image.Image:
    """The square logo's mark, without the OTL ROASTER words under it."""
    art = Image.open(LOGO).convert("RGB")
    top = art.crop((0, 0, art.width, round(art.height * 0.62)))
    grey = top.convert("L").point(lambda v: 255 if v < 235 else 0)
    mark = top.crop(grey.getbbox())
    mark.thumbnail((size, size), Image.LANCZOS)
    return mark


def about_face() -> Image.Image:
    w, h = 916, 468
    s = 4
    big = Image.new("RGBA", (w * s, h * s), rgb(PAGE) + (255,))
    d = ImageDraw.Draw(big)
    px, py, pw, ph = PRODUCT
    rounded(d, PRODUCT)
    d.line(((pw - 150) * s, (py + 20) * s, (pw - 150) * s, (py + ph - 20) * s), fill=CARD_LINE, width=s)
    d.line((0, (214 - DY) * s, w * s, (214 - DY) * s), fill=CARD_LINE, width=s)
    cw = (w - 24) // 3
    for i in range(3):
        rounded(d, (i * (cw + 12), 322 - DY, cw, 80))
    d.line((0, (430 - DY) * s, w * s, (430 - DY) * s), fill=CARD_LINE, width=s)
    image = big.resize((w, h), Image.LANCZOS)
    t = ImageDraw.Draw(image)

    mark = logo_mark(64)
    image.paste(mark, (30, py + (ph - mark.height) // 2))
    t.text((116, py + 40), "OTL Roaster", font=font("arialbd.ttf", 28), fill=INK, anchor="lm")
    t.text((116, py + 70), "SILO 6", font=font("arialbd.ttf", 17), fill=MUTED, anchor="lm")
    t.text((pw - 130, py + 34), "Version", font=font("arial.ttf", 14), fill=MUTED, anchor="lm")
    t.text((pw - 130, py + 64), "1.0.0", font=font("arial.ttf", 28), fill=INK, anchor="lm")

    t.text((4, 196 - DY), "OTESLA INDUSTRIAL COMPANY LIMITED", font=font("arialbd.ttf", 19), fill=INK, anchor="lm")
    t.text((4, 240 - DY), "Tax Code", font=font("arial.ttf", 15), fill=MUTED, anchor="lm")
    t.text((120, 240 - DY), "0314844413", font=font("arial.ttf", 16), fill=INK, anchor="lm")
    t.text((4, 272 - DY), "Office", font=font("arial.ttf", 15), fill=MUTED, anchor="lm")
    for i, line in enumerate(("No. 44, N5 Street, Tan Phuoc Quarter, Tan Dong Hiep Ward,", "Ho Chi Minh City, Vietnam.")):
        t.text((120, 272 - DY + 24 * i), line, font=font("arial.ttf", 16), fill=INK, anchor="lm")
    for i, (name, label, value) in enumerate(CONTACTS):
        x = i * (cw + 12)
        image.alpha_composite(icon(name, 24, NAV_INK, px=1.75, cut=WHITE), (x + 18, 350 - DY))
        t.text((x + 56, 348 - DY), label, font=font("arial.ttf", 13), fill=MUTED, anchor="lm")
        t.text((x + 56, 374 - DY), value, font=font("arial.ttf", 16), fill=BLUE if label == "Website" else INK, anchor="lm")
    t.text((0, 456 - DY), "Copyright ©2025 O TESLA Industrial Co., Ltd. All Rights Reserved.", font=font("arial.ttf", 14),
           fill=MUTED, anchor="lm")
    return image


def render(folder: Path) -> dict[str, Path]:
    faces = {"ab_page": about_face(), "pr_page": parameter_face()}
    folder.mkdir(parents=True, exist_ok=True)
    paths = {}
    for key, image in faces.items():
        path = folder / f"{key}.png"
        image.save(path)
        paths[key] = path
    return paths


def main(path: str, asset_dir: str) -> None:
    project = Project(path)
    about, params = project.screen("Set_About"), project.screen("Set_Parameter")
    for page, prefix in ((about, "ab_"), (params, "pr_")):
        for element in [e for e in page.elements if e.name.startswith(prefix)][::-1]:
            edit.delete_element(project, page, element.index)
    frame.prune_bank(project)

    donor = Project(fill.DONOR)
    tpl_rect = donor.element("scr_MainScreen", 1)
    tpl_entry = donor.element("scr_Discharge", 52)

    assets = render(Path(asset_dir))
    bank = frame.Bank(project)
    for key, file in assets.items():
        bank.add(key, file)
    bank.commit()

    def picture(page, key, x, y, name):
        _, _, w, h = bank.where[key]
        item = edit.clone_element(project, tpl_rect, page, 0, 0, 10, 10, name)
        clear_links(item)
        frame.face(item, bank, key)
        frame.flat(item, PAGE)
        for state in item.states:
            state.set("TransColor", bgr(PAGE))
        frame.picture_rect(item, x, y, w, h)

    picture(about, "ab_page", 100, CONTENT_TOP, "ab_page")
    picture(params, "pr_page", 100, CARD_Y, "pr_page")
    for c, (_, _, rows) in enumerate(CARDS):
        for r, (_, low, high, _) in enumerate(rows):
            name = f"pr_{c + 1}_{r + 1}"
            x = card_x(c) + CARD_W - 14 - BOX_W + 6
            y = CARD_Y + ROW_TOP + ROW_H * r + (ROW_H - BOX_H) // 2 + 2
            item = edit.clone_element(project, tpl_entry, params, x, y, BOX_W - 14, BOX_H - 4, name)
            clear_links(item)
            for key in ("ReadVar", "WriteVar"):
                item.section.set(key, ADDRESSES[name])
            item.section.set("MemFmt", 2)   # one signed word, value x10
            item.section.set("MemLen", 1)
            item.section.set("IntNum", len(str(high)))
            item.section.set("DotNum", 1)
            item.section.set("MinValue", f"{low:.1f}")
            item.section.set("MaxValue", f"{high:.1f}")
            item.section.set("Style", 3)
            text_style(item, 18, VALUE, True, RIGHT)

    print(project.save(path))
    print(f"Set_About: {len(about.elements)} elements, Set_Parameter: {len(params.elements)} elements")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
