"""Build the navigation frame of the new Silo HMI (C:\\OTL\\SILO_Ban_Moi).

Run:  python build_silo_frame.py <project.dpa> <donor.dpa> <asset folder>

The project already holds six empty screens: Home_Fill, Home_Discharge,
Home_Blend, Setting, Data, and Khung_Chung, which the other five name as their
base screen. This draws only the frame around the content area:

  Khung_Chung    logo, user block, divider lines, time and date
  every page     Home / Setting / Data on the left, the page's own entry lit
  Home_* pages   Fill / Discharge / Blend tabs, the page's own tab lit

The lit entry lives on each page, not on the base screen, because a base screen
cannot know which page sits above it without a PLC or internal bit.

A Delta button takes its face from a bitmap, so every nav entry is one Goto
Screen whose picture is rendered here - Lucide icon, label and fill in one image.
That keeps each entry a single object instead of rectangle + label + overlay.
"""

from __future__ import annotations

import io
import struct
import sys
from pathlib import Path

import pymupdf
from PIL import Image, ImageChops, ImageDraw, ImageFont

from dpa import edit, picbank
from dpa.document import Raw
from dpa.model import Project

LUCIDE = Path(__file__).resolve().parent / "assets" / "lucide"  # lucide-static SVGs, ISC licence
LOGO = Path(r"C:\OTL\LOGO_OTESLA\OTL\print_transparent_black-01.png")
FONTS = Path(r"C:\Windows\Fonts")

PAGE = "#F3F5F8"      # screen background, header and sidebar share it
RULE = "#E6EAEF"      # divider under the header and right of the sidebar
INK = "#1E2630"       # lit tab label
MUTED = "#5B6571"     # unlit tab label
NAV_INK = "#2F3A45"   # unlit sidebar icon and label
NAV_ON = "#4A84B6"    # lit sidebar entry
NAV_LABEL = "#6B7785" # unlit sidebar label, quieter than its icon
TAB_ON = "#D6E6F5"    # lit tab fill
TAB_LINE = "#1F6FB2"  # lit tab underline
WHITE = "#FFFFFF"

# Measured off Sang's mockup (1633x963) and scaled to the 1024x600 panel.
HEADER_H = 58
SIDEBAR_W = 92
FOOTER_Y = 537        # top of the Operation mode / START bar
NAV_X, NAV_W, NAV_H = 9, 73, 76
NAV_Y = (82, 176, 268)
TAB_X, TAB_Y, TAB_W, TAB_H = (231, 419, 607), 3, 180, 52  # wide enough for DISCHARGE bold 26 (156 px)
TAB_SIZE_ON, TAB_SIZE_OFF = 20, 16  # Sang: lit tab larger, unlit two steps smaller
LOGO_XY, LOGO_H = (12, 6), 46
USER_XY, USER_W, USER_H = (1024 - 14 - 176, 11), 176, 36


def rgb(hex_rgb: str) -> tuple[int, int, int]:
    value = int(hex_rgb.lstrip("#"), 16)
    return (value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF


def bgr(hex_rgb: str) -> int:
    """DOPSoft stores colours as BGR integers, the Windows way."""
    r, g, b = rgb(hex_rgb)
    return (b << 16) | (g << 8) | r


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / name), size)


def icon(name: str, size: int, colour: str, px: float = 2.0, solid: bool = False, cut: str = PAGE) -> Image.Image:
    """A Lucide icon whose lines come out `px` pixels wide at `size`.

    Rendered at 4x and scaled down; a whole-pixel stroke stays sharp where a
    fractional one (2 units at 30 px = 2.5 px) smears across two pixel rows.
    `solid` fills the shapes, as the mockup draws Home and the user; the house
    door is then punched out in `cut`, the colour behind the icon.
    """
    stroke = px * 24 / size
    svg = (LUCIDE / f"{name}.svg").read_text(encoding="utf-8")
    svg = svg.replace('stroke-width="2"', f'stroke-width="{stroke:.3f}"')
    if solid:
        svg = svg.replace('fill="none"', 'fill="currentColor"', 1)
        # The door comes first in Lucide's file; move it last so the filled
        # body does not paint over it.
        start = svg.find('<path d="M15 21v-8')
        if start >= 0:
            end = svg.index("/>", start) + 2
            door = svg[start:end].replace("<path ", f'<path fill="{cut}" stroke="{cut}" ', 1)
            door = door.replace("M15 21v-8", "M15 23v-10").replace("1 1v8", "1 1v10")  # open the door through the floor
            svg = svg[:start] + svg[end:]
            svg = svg.replace("</svg>", door + "</svg>")
    svg = svg.replace("currentColor", colour)
    doc = pymupdf.open(stream=svg.encode("utf-8"), filetype="svg")
    big = size * 4
    page = doc[0]
    pix = page.get_pixmap(matrix=pymupdf.Matrix(big / page.rect.width, big / page.rect.height), alpha=True)
    image = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGBA")
    return image.resize((size, size), Image.LANCZOS)


def shapes(width: int, height: int, draw_at_4x) -> Image.Image:
    """Fills and rounded corners drawn at 4x and scaled down, so edges are smooth."""
    big = Image.new("RGBA", (width * 4, height * 4), rgb(PAGE) + (255,))
    draw_at_4x(ImageDraw.Draw(big))
    return big.resize((width, height), Image.LANCZOS)


def centred_text(draw: ImageDraw.ImageDraw, box, text: str, face, colour: str) -> None:
    """Centre on the font's own middle, not the glyphs', so labels share a baseline."""
    x0, y0, x1, y1 = box
    draw.text(((x0 + x1) / 2, (y0 + y1) / 2), text, font=face, fill=colour, anchor="mm")


def tracked_text(draw: ImageDraw.ImageDraw, cx: float, cy: float, text: str, face, colour: str, spacing: float) -> None:
    """Centred text with extra space between letters - small capitals need air to read."""
    widths = [draw.textlength(ch, font=face) for ch in text]
    x = cx - (sum(widths) + spacing * (len(text) - 1)) / 2
    for ch, width in zip(text, widths):
        draw.text((x, cy), ch, font=face, fill=colour, anchor="lm")
        x += width + spacing


def nav_face(icon_name: str, label: str, lit: bool) -> Image.Image:
    ink = WHITE if lit else NAV_INK
    back = NAV_ON if lit else PAGE
    image = shapes(NAV_W, NAV_H, lambda d: d.rounded_rectangle((0, 0, NAV_W * 4 - 1, NAV_H * 4 - 1), radius=24, fill=NAV_ON) if lit else None)
    solid = icon_name == "house"
    glyph = icon(icon_name, 34, ink, px=2.0 if solid else 1.75, solid=solid, cut=back)
    image.alpha_composite(glyph, ((NAV_W - 34) // 2, 8))
    tracked_text(ImageDraw.Draw(image), NAV_W / 2, 57, label.upper(), font("arialbd.ttf" if lit else "arial.ttf", 12), WHITE if lit else NAV_LABEL, 1)
    return image


def tab_face(label: str, lit: bool) -> Image.Image:
    def body(d):
        d.rounded_rectangle((0, 0, TAB_W * 4 - 1, (TAB_H + 8) * 4), radius=24, fill=TAB_ON)
        d.rectangle((9 * 4, (TAB_H - 3) * 4, (TAB_W - 9) * 4 - 1, TAB_H * 4 - 1), fill=TAB_LINE)

    image = shapes(TAB_W, TAB_H, body if lit else (lambda d: None))
    draw = ImageDraw.Draw(image)
    label = label.upper()
    if lit:
        centred_text(draw, (0, 0, TAB_W, TAB_H - 3), label, font("arialbd.ttf", TAB_SIZE_ON), INK)
    else:
        centred_text(draw, (0, 0, TAB_W, TAB_H - 3), label, font("arial.ttf", TAB_SIZE_OFF), MUTED)
    return image


def user_face() -> Image.Image:
    image = Image.new("RGBA", (USER_W, USER_H), rgb(PAGE) + (255,))
    draw = ImageDraw.Draw(image)
    image.alpha_composite(icon("user", 24, NAV_INK, solid=True), (2, (USER_H - 24) // 2))
    face = font("arial.ttf", 17)
    draw.text((36, USER_H // 2), "Default user", font=face, fill=NAV_INK, anchor="lm")
    end = 36 + draw.textlength("Default user", font=face)
    image.alpha_composite(icon("chevron-down", 18, NAV_INK, px=1.75), (round(end) + 10, (USER_H - 18) // 2))
    return image


def logo_face() -> Image.Image:
    """The logo file is drawn on white with no alpha, so multiply it onto the page."""
    source = Image.open(LOGO).convert("RGB")
    height = LOGO_H
    width = round(source.width * height / source.height)
    art = source.resize((width, height), Image.LANCZOS)
    return ImageChops.multiply(art, Image.new("RGB", art.size, rgb(PAGE))).convert("RGBA")


def solid(width: int, height: int, colour: str) -> Image.Image:
    return Image.new("RGBA", (width, height), rgb(colour) + (255,))


def render_assets(folder: Path) -> dict[str, Path]:
    folder.mkdir(parents=True, exist_ok=True)
    faces = {
        "logo": logo_face(),
        "user": user_face(),
        "rule_h": solid(1024, 1, RULE),
        "rule_v": solid(1, 600 - HEADER_H, RULE),
    }
    for key, icon_name, label in (("home", "house", "Home"), ("setting", "settings", "Setting"), ("data", "database", "Data")):
        faces[f"nav_{key}_on"] = nav_face(icon_name, label, True)
        faces[f"nav_{key}_off"] = nav_face(icon_name, label, False)
    for key, label in (("fill", "Fill"), ("discharge", "Discharge"), ("blend", "Blend")):
        faces[f"tab_{key}_on"] = tab_face(label, True)
        faces[f"tab_{key}_off"] = tab_face(label, False)
    paths = {}
    for key, image in faces.items():
        path = folder / f"{key}.png"
        image.save(path)
        paths[key] = path
    return paths


class Bank:
    """The project's picture bank, with each new image's name and byte offset."""

    def __init__(self, project: Project):
        self.section = project.doc.first("Picture")
        self.entry = self.section.entries("Size")[0]
        self.prefix = project.doc.first("Application").as_dict().get("Name") or "NewHMI"
        self.pictures = picbank.read(self.entry.blob or b"")
        self.where: dict[str, tuple[str, int, int, int]] = {}

    def add(self, key: str, path: Path) -> None:
        record = picbank.encode(path)
        _, width, height = struct.unpack_from("<Iii", record, 4)
        picture = picbank.Picture(len(self.pictures) + 1, width, abs(height), record)
        offset = len(picbank.MAGIC) + sum(len(p.record) for p in self.pictures)
        self.pictures.append(picture)
        self.where[key] = (f"{self.prefix}{picture.index:05d}", offset, width, abs(height))

    def commit(self) -> None:
        blob = picbank.write(self.pictures)
        self.entry.blob = blob
        self.entry.value = str(len(blob)).encode("ascii")
        self.entry.blob_eol = True
        # An empty bank is written as "Size=0" plus a blank line; a filled one
        # runs straight into the next section header, as DIAScreen writes it.
        self.section.items = [item for item in self.section.items if not isinstance(item, Raw)]


def prune_bank(project: Project) -> None:
    """Drop pictures no element points at, and re-point the rest at their new offsets.

    DIAScreen finds a picture by PictureOffset, so after removing elements the
    bank is rebuilt from what is still referenced, in first-use order.
    """
    section = project.doc.first("Picture")
    entry = section.entries("Size")[0]
    pictures = picbank.read(entry.blob or b"")
    by_offset, pos = {}, len(picbank.MAGIC)
    for picture in pictures:
        by_offset[pos] = picture.record
        pos += len(picture.record)
    prefix = project.doc.first("Application").as_dict().get("Name") or "NewHMI"
    kept, placed, pos = [], {}, len(picbank.MAGIC)
    for screen in project.screens:
        for element in screen.elements:
            for state in element.states:
                offset = state.get("PictureOffset")
                if not offset or int(offset) not in by_offset:
                    continue
                record = by_offset[int(offset)]
                if record not in placed:
                    width = int.from_bytes(record[8:12], "little")
                    height = abs(int.from_bytes(record[12:16], "little", signed=True))
                    kept.append(picbank.Picture(len(kept) + 1, width, height, record))
                    placed[record] = (f"{prefix}{len(kept):05d}", pos)
                    pos += len(record)
                name, new_offset = placed[record]
                state.set("Picture Name", name)
                state.set("PictureOffset", new_offset)
    blob = picbank.write(kept)
    entry.blob = blob
    entry.value = str(len(blob)).encode("ascii")
    entry.blob_eol = True


def face(element, bank: Bank, key: str) -> None:
    """Show one bank picture on an element, stretched to the element."""
    name, offset, width, height = bank.where[key]
    for state in element.states:
        state.set("PIB Name", "PicBank02")
        state.set("Picture Name", name)
        state.set("PictureOffset", offset)
        state.set("PictureWidth", width)
        state.set("PictureHeight", height)
        state.set("PictureStretch", 1)
        state.set("StretchMode", 2)
        state.set("UsePictureCoord", 0)
        state.set("TransEffect", 0)


def flat(element, fill: str = PAGE) -> None:
    """No button body and no border: only the picture shows, edge to edge.

    DIAScreen fits a picture inside the element's body and border - on save it
    shrinks an 84x80 face to 75x72 - and draws that body in grey #B4B4B4 with
    the rectangle's own #FCFCFC fill peeking out. `Style=3` drops the body (the
    donor's invisible touch overlays use it), every body and border colour goes
    to the page colour in case the panel draws one anyway, and the picture is
    pinned to the element's full size.
    """
    section = element.section
    section.set("Style", 3 if element.type_code == "1.10" else 0)
    # BorderColor alone is not the border: the BDR* trio (0 = black in the
    # donor) draws it, and FgFillEndColor is a grey gradient stop.
    for key in ("BorderColor", "BDRStartColor", "BDRMidColor", "BDREndColor"):
        if section.get(key) is not None:
            section.set(key, bgr(fill))
    for key in ("GradFillStartColor", "GradFillEndColor"):
        if section.get(key) is not None:
            section.set(key, bgr(fill))
    if section.get("ShowBorder") is not None:
        section.set("ShowBorder", 0)
    x, y, width, height = (section.get_int(k, 0) for k in ("X", "Y", "Width", "Height"))
    for state in element.states:
        for key in ("FgColor", "BgColor", "FgFillColor", "FgFillEndColor", *(f"FgFillStopColor{i}" for i in range(5))):
            if state.get(key) is not None:
                state.set(key, bgr(fill))
        if state.get("Picture Name"):
            state.set("PictureCoordX", x)
            state.set("PictureCoordY", y)
            state.set("PictureWidth", width)
            state.set("PictureHeight", height)


PICTURE_KEYS = ("Picture Name", "PIB Name", "PictureOffset", "PictureCoordX", "PictureCoordY", "PictureWidth", "PictureHeight")

# DIAScreen fits a rectangle's picture 4 px in from the sides and 1 px in from
# top and bottom (keeping its aspect), and re-renders the bank to that size on
# save. So a rectangle is drawn this much larger than the picture it carries.
RECT_PAD_X, RECT_PAD_Y = 4, 1


def rule(element) -> None:
    """A divider: a rectangle filled with the rule colour and no picture at all.

    Blanking `Picture Name` is not enough - DIAScreen finds a picture by
    `PictureOffset` and would hang whatever sits there on the line - so every
    picture key goes, leaving the state a plain rectangle's.
    """
    flat(element, RULE)
    # No border: the panel draws a rectangle's border black whatever the colour
    # keys say, while its fill does take GradFillStartColor.
    element.section.set("ShowBorder", 0)
    for state in element.states:
        state.items = [i for i in state.items if getattr(i, "key", b"").decode("latin1") not in PICTURE_KEYS]
        state.set("PictureStretch", 0)


# A State Graphic keeps a different margin: 3 px at the sides, none top and bottom.
GRAPHIC_PAD_X, GRAPHIC_PAD_Y = 3, 0


def picture_rect(element, x: int, y: int, width: int, height: int) -> None:
    """Place a picture-carrying element so its picture lands at x, y, width x height."""
    section = element.section
    pad_x, pad_y = (GRAPHIC_PAD_X, GRAPHIC_PAD_Y) if element.type_code == "7.1" else (RECT_PAD_X, RECT_PAD_Y)
    for key, value in zip(("X", "Y", "Width", "Height"),
                          (x - pad_x, y - pad_y, width + 2 * pad_x, height + 2 * pad_y)):
        section.set(key, value)
    for state in element.states:
        for key, value in zip(("PictureCoordX", "PictureCoordY", "PictureWidth", "PictureHeight"), (x, y, width, height)):
            state.set(key, value)


def main(path: str, donor_path: str, asset_dir: str) -> None:
    project = Project(path)
    donor = Project(donor_path)
    if project.info()["panel"] != donor.info()["panel"]:
        raise SystemExit("donor is a different panel")
    if any(s.elements for s in project.screens) or picbank.read(project.doc.first("Picture").entries("Size")[0].blob or b""):
        raise SystemExit("project already has elements or pictures - start from the empty file")

    picture_rect = donor.element("scr_MainScreen", 1)   # rectangle showing the donor logo
    goto = donor.element("pop_Setting", 5)              # picture-faced Goto Screen, no macros
    time_tpl = donor.element("scr_MainScreen", 11)
    date_tpl = donor.element("scr_MainScreen", 12)

    assets = render_assets(Path(asset_dir))
    bank = Bank(project)
    for key, file in assets.items():
        bank.add(key, file)
    bank.commit()

    screens = {s.name: s for s in project.screens}
    base = screens["Khung_Chung"]
    for screen in project.screens:
        screen.section.set("BgColor", bgr(PAGE))

    def picture(screen, key, x, y, name):
        _, _, width, height = bank.where[key]
        item = edit.clone_element(project, picture_rect, screen, x, y, width, height, name)
        face(item, bank, key)
        flat(item)
        return item

    def goto_button(screen, key, destination, x, y, name):
        _, _, width, height = bank.where[key]
        item = edit.clone_element(project, goto, screen, x, y, width, height, name)
        item.section.set("Level", 0)
        item.section.set("GoToScreenID", destination.id)
        for entry in item.section.entries("GoToScreenName"):
            entry.value = destination.name.encode("latin1")
        face(item, bank, key)
        flat(item)
        return item

    # --- base screen: what never changes between pages -------------------
    rule(picture(base, "rule_h", 0, HEADER_H, "fr_rule_header"))
    rule(picture(base, "rule_v", SIDEBAR_W, HEADER_H, "fr_rule_sidebar"))
    picture(base, "logo", 18, 16, "fr_logo")
    picture(base, "user", 1024 - 24 - 150, 16, "fr_user")
    for template, y, name in ((time_tpl, 540, "fr_time"), (date_tpl, 564, "fr_date")):
        item = edit.clone_element(project, template, base, 4, y, 96, 22, name)
        for state in item.states:
            state.set("FontColor", bgr(NAV_INK))
            state.set("FontAlign", 34)
            for slot in (0, 1):
                state.set(f"FontName{slot}", "Arial")
                state.set(f"FontSize{slot}", 14)

    # --- sidebar on every page, its own entry lit -------------------------
    nav = (("home", screens["Home_Fill"]), ("setting", screens["Setting"]), ("data", screens["Data"]))
    lit_nav = {"Home_Fill": "home", "Home_Discharge": "home", "Home_Blend": "home", "Setting": "setting", "Data": "data"}
    for page_name, lit in lit_nav.items():
        page = screens[page_name]
        for (key, destination), y in zip(nav, NAV_Y):
            state = "on" if key == lit else "off"
            goto_button(page, f"nav_{key}_{state}", destination, NAV_X, y, f"nav_{key}")

    # --- tabs on the three Home pages -------------------------------------
    tabs = (("fill", screens["Home_Fill"]), ("discharge", screens["Home_Discharge"]), ("blend", screens["Home_Blend"]))
    for lit, page in tabs:
        for (key, destination), x in zip(tabs, TAB_X):
            state = "on" if key == lit else "off"
            goto_button(page, f"tab_{key}_{state}", destination, x, TAB_Y, f"tab_{key}")

    print(project.save(path))
    for screen in project.screens:
        print(f"  {screen.id} {screen.name}: {len(screen.elements)} elements")
    print(f"  bank: {len(bank.pictures)} pictures")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
