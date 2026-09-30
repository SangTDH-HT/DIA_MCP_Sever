"""Draw the Fill page of the new Silo HMI (Home_Fill) after Sang's Fill silo form.

Run:  python build_fill_page.py <project.dpa> <asset folder>

Left: a STATUS bar over the process - hopper, its bottom valve, the material
line (green) into the silo top, the SFV on the silo and the vacuum line (cyan)
to the pump - with FILLING RATE, CAPACITY WEIGHT, VACCUM and FILL MODE /
COUNTDOWN cards leading into it. Right: CURRENT WEIGHT, then SELECT SILO with
the round START and the MANUAL / AUTO mode.

Static artwork is rendered into pictures (Sang's hopper.png and Silo_5.png,
pipes, card frames, labels, units). Everything that moves with the PLC is a
Delta element laid over it. No PLC addresses exist yet, so every element
points at internal memory; ADDRESSES is the list to rebind.

Re-runnable: every element it made (prefix "fl_") is removed first and the
picture bank is pruned to what the project still uses.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

import build_silo_frame as frame
from build_silo_frame import INK, MUTED, NAV_INK, PAGE, WHITE, bgr, font, icon, rgb
import copy

from dpa import edit, macro, picbank
from dpa.model import Project

DONOR = r"C:\OTL\OTL_SILO\OTL_Silo6\Code_Silo_AThanh\HMI_AThanh.dpa"
DONOR_TEXT = r"C:\OTL\Document_Soft\Delta\ConnectDintoolProtoco.dpa"   # Character Display
DONOR_SET = r"C:\OTL\OTL_SILO\OTL_Silo6\HMI\SiloOld_AThanh.dpa"        # Set Constant
ICONS = Path(__file__).resolve().parent / "assets" / "drawings"  # Sang's source drawings (kept local, not pushed)

CARD_LINE = "#E1E6EC"
TILE = "#EEF1F4"         # grey tile behind card icons and the status code
MATERIAL = "#2E9E48"     # material line, hopper to silo
VACUUM = "#35C2C8"       # vacuum line, SFV to pump
LEADER = "#8C95A0"       # dashed leaders from cards to the process
# START / DUNG face after Sang's sample: two soft rings round a pale disc.
FACE_TOP, FACE_BOTTOM, FACE_EDGE = "#FFFFFF", "#E4E8ED", "#D9DEE4"
FACE_INK = "#4A5563"
GO = ("#DDF5EC", "#C3EEDB", "#2BB57A")      # outer ring, inner ring, power icon
STOP = ("#FDE4E8", "#FBCDD5", "#F0405A")    # outer ring, inner ring, stop square

ADDRESSES = {
    "fl_status": "$206",        # status code
    "fl_status_silo": "$207",   # silo being filled
    "fl_status_time": "$208",   # elapsed, s
    "fl_sfv_no": "$209",        # SFV number
    "fl_rate": "$201",          # Filling rate, kg/min x10
    "fl_capacity": "$202",      # Capacity weight, kg x10
    "fl_pressure": "$204",      # Pressure, kPa x10
    "fl_dec_time": "$203",      # Dec. time, s
    "fl_countdown": "$211",     # Countdown, s
    "fl_fill_mode": "$210.6",   # 0 PULSED, 1 CONTINUOUS
    "fl_weight": "$200",        # Current weight, kg x10
    "fl_silo": "$205",          # Selected silo, 0..5 = silo 1..6
    "fl_silo_open": "$212.0",   # spare bit the list opener writes; nothing reads it
    "fl_silo_name": "$300",     # name of the selected silo, 20 ASCII chars (PLC copies it)
    **{f"fl_name_{i + 1}": f"${310 + 10 * i}" for i in range(6)},  # silo names, 20 chars each
    "fl_mode": "$210.1",        # 0 MANUAL, 1 AUTO
    "fl_sfv": "$210.2",         # SFV open
    "fl_start": "$210.5",       # START / DUNG, momentary; the PLC toggles the run
    "fl_running": "$210.7",     # filling running: the button shows DUNG
}

# Panel layout (1024x600). The content area is x 100..1016, y 66..592.
STATUS = (100, 66, 674, 46)
PROCESS = (100, 120, 674, 472)       # the drawing under the status bar
WEIGHT = (784, 66, 232, 144)
SILO = (784, 222, 232, 370)
MODE_RULE = 470                      # hairline between the silo pick and the mode
MODE_BTN = (800, 520, 200, 50)
START = (835, 329, 130, 130)
COMBO = (800, 276, 200, 42)          # same 16 px inset as the mode switch
POPUP = "pop_Silo"                   # the list the silo field opens, over the card
ROW_H, ROWS = 40, 6
NAME_CHARS = 20
FIELD_LINE = "#C9D0D8"

# Inside the process drawing, in panel coordinates.
RATE_CARD = (150, 216, 130, 88)
CAP_CARD = (463, 320, 128, 105)
VAC_CARD = (617, 320, 154, 115)
MODE_CARD = (100, 513, 220, 78)      # wide enough for CONTINUOUS in bold 16
SFV_TAG = (292, 190, 70, 22)
SFV_AT = (398, 188)                  # valve picture, 26x26
SILO_AT, SILO_H = (366, 214), 330
HOPPER_AT, HOPPER_W = (109, 342), 138
HOP_OUT = 109 + round(108 * 138 / 188)
PUMP = (700, 494)


# --- drawing helpers -----------------------------------------------------------

def rounded(draw: ImageDraw.ImageDraw, box, fill=WHITE, outline=CARD_LINE, radius=6, width=1, s=4) -> None:
    x, y, w, h = box
    draw.rounded_rectangle((x * s, y * s, (x + w) * s - 1, (y + h) * s - 1), radius=radius * s, fill=fill,
                           outline=outline, width=width * s)


def polyline(draw: ImageDraw.ImageDraw, points, colour: str, width: int = 3, s: int = 4) -> None:
    pts = [(x * s, y * s) for x, y in points]
    draw.line(pts, fill=colour, width=width * s, joint="curve")
    for x, y in pts:
        r = width * s / 2
        draw.ellipse((x - r, y - r, x + r, y + r), fill=colour)


def arrowhead(draw: ImageDraw.ImageDraw, x: int, y: int, direction: str, colour: str, s: int = 4) -> None:
    dx, dy = {"right": (1, 0), "down": (0, 1), "up": (0, -1), "left": (-1, 0)}[direction]
    px, py = -dy, dx
    tip = (x * s, y * s)
    back = ((x - dx * 9 + px * 5) * s, (y - dy * 9 + py * 5) * s)
    back2 = ((x - dx * 9 - px * 5) * s, (y - dy * 9 - py * 5) * s)
    draw.polygon([tip, back, back2], fill=colour)


def dashed(draw: ImageDraw.ImageDraw, points, colour: str = LEADER, s: int = 4) -> None:
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        length = max(abs(x1 - x0), abs(y1 - y0))
        for t in range(0, length, 6):
            a, b = t / length, min(t + 3, length) / length
            draw.line(((x0 + (x1 - x0) * a) * s, (y0 + (y1 - y0) * a) * s,
                       (x0 + (x1 - x0) * b) * s, (y0 + (y1 - y0) * b) * s), fill=colour, width=int(1.2 * s))


def line_art(name: str, width: int | None = None, height: int | None = None, back: str = PAGE) -> Image.Image:
    """One of Sang's drawings, scaled, with thin lines kept dark."""
    source = Image.open(ICONS / name).convert("RGBA")
    if width is None:
        width = round(source.width * height / source.height)
    if height is None:
        height = round(source.height * width / source.width)
    art = source.resize((width, height), Image.LANCZOS)
    art.putalpha(art.getchannel("A").point(lambda a: min(255, int(a * 1.9))))
    flat = Image.new("RGBA", art.size, rgb(back) + (255,))
    flat.alpha_composite(art)
    return flat


def card_title(t: ImageDraw.ImageDraw, cx: float, y: int, words: str, size: int = 12) -> None:
    """Small uppercase title with the form's thin underline and dot."""
    face = font("arial.ttf", size)
    t.text((cx, y), words, font=face, fill=INK, anchor="mm")
    half = t.textlength(words, font=face) / 2
    t.line((cx - half, y + 10, cx - 4, y + 10), fill=CARD_LINE)
    t.line((cx + 4, y + 10, cx + half, y + 10), fill=CARD_LINE)
    t.ellipse((cx - 1.5, y + 8.5, cx + 1.5, y + 11.5), fill=CARD_LINE)


def local(box, origin):
    x, y, w, h = box
    return (x - origin[0], y - origin[1], w, h)


def process_drawing() -> Image.Image:
    ox, oy, w, h = PROCESS
    s = 4
    big = Image.new("RGBA", (w * s, h * s), rgb(PAGE) + (255,))
    d = ImageDraw.Draw(big)
    L = lambda p: (p[0] - ox, p[1] - oy)

    # cards, drawn first so the lines meet their edges
    for box in (RATE_CARD, CAP_CARD, VAC_CARD, MODE_CARD):
        rounded(d, local(box, (ox, oy)))
    rounded(d, local(SFV_TAG, (ox, oy)), outline="#C9D0D8", radius=5)
    vx, vy, vw, vh = local(VAC_CARD, (ox, oy))
    d.line(((vx + 8) * s, (vy + 48) * s, (vx + vw - 8) * s, (vy + 48) * s), fill=CARD_LINE, width=s)
    d.line(((vx + vw // 2) * s, (vy + 54) * s, (vx + vw // 2) * s, (vy + vh - 6) * s), fill=CARD_LINE, width=s)
    rounded(d, (vx + 8, vy + 8, 32, 32), fill=TILE, outline=TILE, radius=5)
    mx, my, mw, mh = local(MODE_CARD, (ox, oy))
    d.line(((mx + mw // 2) * s, (my + 8) * s, (mx + mw // 2) * s, (my + mh - 8) * s), fill=CARD_LINE, width=s)

    # material line: hopper outlet -> bottom valve -> floor -> up -> silo top
    polyline(d, [L((HOP_OUT, 414)), L((HOP_OUT, 494)), L((290, 494)), L((290, 222)), L((386, 222))], MATERIAL)
    arrowhead(d, *L((394, 222)), "right", MATERIAL)
    # vacuum line: SFV top -> pump inlet
    polyline(d, [L((SFV_AT[0] + 13, SFV_AT[1])), L((SFV_AT[0] + 13, 129)), L((605, 129)), L((605, 509)), L((664, 509))], VACUUM)
    arrowhead(d, *L((672, 509)), "right", VACUUM)

    # bottom valve of the hopper: two triangles tip to tip
    bx, by = L((HOP_OUT, 432))
    for sign in (-1, 1):
        d.polygon([((bx - 9) * s, (by + sign * 11) * s), ((bx + 9) * s, (by + sign * 11) * s), (bx * s, by * s)],
                  fill=WHITE, outline=NAV_INK, width=6)

    # leaders from the cards into the process
    dashed(d, [L((RATE_CARD[0] + RATE_CARD[2], 262)), L((290, 262))])
    dashed(d, [L((HOP_OUT - 10, 432)), L((150, 432)), L((150, 513))])
    dashed(d, [L((463, 372)), L((458, 372))])
    dashed(d, [L((694, 435)), L((694, 470))])
    dashed(d, [L((SFV_TAG[0] + SFV_TAG[2], 201)), L((SFV_AT[0], 201))])

    # vacuum pump: volute, outlet and foot
    cx, cy = L(PUMP)
    r = 24
    d.ellipse(((cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s), fill=TILE, outline=NAV_INK, width=2 * s)
    d.rectangle(((cx + 4) * s, (cy - r - 1) * s, (cx + r + 10) * s, (cy - r + 9) * s), fill=TILE, outline=NAV_INK, width=2 * s)
    d.line(((cx - 20) * s, (cy + r + 5) * s, (cx + 20) * s, (cy + r + 5) * s), fill=NAV_INK, width=2 * s)
    for sx in (-1, 1):
        d.line(((cx + sx * 11) * s, (cy + r) * s, (cx + sx * 15) * s, (cy + r + 5) * s), fill=NAV_INK, width=2 * s)

    image = big.resize((w, h), Image.LANCZOS)

    # drawings, icons and words at 1x so they stay sharp
    silo = line_art("Silo_5.png", height=SILO_H)
    image.paste(silo, L((SILO_AT[0] + (91 - silo.width) // 2, SILO_AT[1])))
    image.paste(line_art("hopper.png", width=HOPPER_W), L(HOPPER_AT))
    image.alpha_composite(icon("fan", 30, NAV_INK, px=1.75), (cx - 15, cy - 15))
    image.alpha_composite(icon("fan", 22, NAV_INK, px=1.5, cut=TILE), (vx + 13, vy + 13))
    t = ImageDraw.Draw(image)
    t.text(L((HOPPER_AT[0], 322)), "Hopper", font=font("arial.ttf", 15), fill=INK)
    sx, sy, sw, sh = local(SFV_TAG, (ox, oy))
    t.text((sx + 8, sy + sh / 2), "SFV :", font=font("arial.ttf", 14), fill=INK, anchor="lm")

    rx, ry, rw, rh = local(RATE_CARD, (ox, oy))
    card_title(t, rx + rw / 2, ry + 16, "FILLING RATE")
    t.text((rx + rw - 14, ry + 60), "kg/m", font=font("arial.ttf", 14), fill=INK, anchor="rm")
    cx2, cy2, cw, ch = local(CAP_CARD, (ox, oy))
    card_title(t, cx2 + cw / 2, cy2 + 18, "CAPACITY WEIGHT")
    t.text((cx2 + cw - 12, cy2 + 70), "kg", font=font("arial.ttf", 15), fill=INK, anchor="rm")
    t.text((vx + 48, vy + 17), "VACCUM", font=font("arialbd.ttf", 13), fill=INK, anchor="lm")
    t.text((vx + 48, vy + 33), "M-008", font=font("arial.ttf", 12), fill=MUTED, anchor="lm")
    t.text((vx + vw / 4, vy + 64), "Pressure [kPa]", font=font("arial.ttf", 11), fill=INK, anchor="mm")
    t.text((vx + vw * 3 / 4, vy + 64), "Dec.Time [s]", font=font("arial.ttf", 11), fill=INK, anchor="mm")
    card_title(t, mx + mw / 4, my + 14, "FILL MODE", 11)
    card_title(t, mx + mw * 3 / 4, my + 14, "COUNTDOWN", 11)
    return image


def status_bar() -> Image.Image:
    x, y, w, h = STATUS
    s = 4
    big = Image.new("RGBA", (w * s, h * s), rgb(PAGE) + (255,))
    d = ImageDraw.Draw(big)
    rounded(d, (0, 0, w, h))
    d.rectangle((0, 0, 4 * s, h * s - 1), fill=LEADER)
    rounded(d, (12, 8, 46, 30), fill=TILE, outline=TILE, radius=5)
    for dx in (480, 580):
        d.line((dx * s, 8 * s, dx * s, (h - 8) * s), fill=CARD_LINE, width=s)
    image = big.resize((w, h), Image.LANCZOS)
    t = ImageDraw.Draw(image)
    t.text((70, h / 2), "STATUS", font=font("arial.ttf", 13), fill=MUTED, anchor="lm")
    t.text((492, h / 2), "SILO", font=font("arial.ttf", 14), fill=MUTED, anchor="lm")
    image.alpha_composite(icon("clock", 20, NAV_INK, px=1.5, cut=WHITE), (592, (h - 20) // 2))
    t.text((664, h / 2), "s", font=font("arial.ttf", 14), fill=MUTED, anchor="lm")
    return image


def card_base(box):
    x, y, w, h = box
    s = 4
    big = Image.new("RGBA", (w * s, h * s), rgb(PAGE) + (255,))
    d = ImageDraw.Draw(big)
    rounded(d, (0, 0, w, h))
    rounded(d, (10, 10, 34, 34), fill=TILE, outline=TILE, radius=5)
    return big, d


def weight_card() -> Image.Image:
    x, y, w, h = WEIGHT
    big, d = card_base(WEIGHT)
    image = big.resize((w, h), Image.LANCZOS)
    image.alpha_composite(icon("weight", 22, NAV_INK, px=1.5, cut=TILE), (16, 16))
    t = ImageDraw.Draw(image)
    t.text((56, 27), "CURRENT WEIGHT", font=font("arialbd.ttf", 15), fill=INK, anchor="lm")
    t.text((w - 22, 92), "kg", font=font("arial.ttf", 18), fill=INK, anchor="rm")
    mid = w // 2 - 14
    for dx, colour in ((-44, CARD_LINE), (0, NAV_INK), (44, CARD_LINE)):
        t.line((mid + dx - 16, 124, mid + dx + 16, 124), fill=colour, width=2 if colour == NAV_INK else 1)
    return image


def silo_card() -> Image.Image:
    x, y, w, h = SILO
    big, d = card_base(SILO)
    s = 4
    ry = MODE_RULE - y
    d.line((16 * s, ry * s, (w - 16) * s, ry * s), fill=CARD_LINE, width=s)
    rounded(d, (10, ry + 10, 34, 34), fill=TILE, outline=TILE, radius=5)
    image = big.resize((w, h), Image.LANCZOS)
    image.alpha_composite(icon("cylinder", 22, NAV_INK, px=1.5, cut=TILE), (16, 16))
    image.alpha_composite(icon("sliders-horizontal", 22, NAV_INK, px=1.5, cut=TILE), (16, ry + 16))
    t = ImageDraw.Draw(image)
    t.text((56, 27), "SELECT SILO", font=font("arialbd.ttf", 15), fill=INK, anchor="lm")
    t.text((56, ry + 27), "MODE", font=font("arialbd.ttf", 15), fill=INK, anchor="lm")
    return image


def start_face(running: bool, go: str = "START", stop: str = "DỪNG", size: int = 16) -> Image.Image:
    """START when idle (green), DUNG while filling runs (red)."""
    _, _, w, h = START
    s = 4
    outer, inner, mark = STOP if running else GO
    big = Image.new("RGBA", (w * s, h * s), rgb(WHITE) + (255,))
    d = ImageDraw.Draw(big)
    c = w * s / 2
    ring = lambda r, fill: d.ellipse((c - r * s, c - r * s, c + r * s - 1, c + r * s - 1), fill=fill)
    ring(w / 2, outer)
    ring(w / 2 * 0.82, inner)
    r = w / 2 * 0.62
    ring(r + 1, FACE_EDGE)
    # pale disc, white at the top fading to grey at the bottom
    top, bottom = rgb(FACE_TOP), rgb(FACE_BOTTOM)
    shade = Image.new("RGBA", big.size)
    sd = ImageDraw.Draw(shade)
    for row in range(int(c - r * s), int(c + r * s) + 1):
        k = (row - (c - r * s)) / (2 * r * s)
        sd.line((0, row, big.width, row), fill=tuple(round(a + (b - a) * k) for a, b in zip(top, bottom)) + (255,))
    mask = Image.new("L", big.size, 0)
    ImageDraw.Draw(mask).ellipse((c - r * s, c - r * s, c + r * s - 1, c + r * s - 1), fill=255)
    big.paste(shade, (0, 0), mask)
    if running:
        q = 9
        d.rounded_rectangle((c - q * s, (h / 2 - 17 - q) * s, c + q * s, (h / 2 - 17 + q) * s), radius=3 * s, fill=mark)
    image = big.resize((w, h), Image.LANCZOS)
    if not running:
        image.alpha_composite(icon("power", 24, mark, px=2.25), (w // 2 - 12, h // 2 - 29))
    t = ImageDraw.Draw(image)
    t.text((w / 2, h / 2 + 12), stop if running else go, font=font("arialbd.ttf", size), fill=FACE_INK, anchor="mm")
    return image


def mode_face(auto: bool, labels: tuple[str, str] = ("MANUAL", "AUTO"), size: int = 13) -> Image.Image:
    """Segmented switch: a grey track, the active mode a white raised segment."""
    x, y, w, h = MODE_BTN
    s = 4
    big = Image.new("RGBA", (w * s, h * s), rgb(WHITE) + (255,))
    d = ImageDraw.Draw(big)
    rounded(d, (0, 0, w, h), fill=TILE, outline=TILE, radius=8)
    half = w // 2
    seg = (half + 4 if auto else 4, 4, half - 8, h - 8)
    rounded(d, seg, fill=WHITE, outline="#C9D0D8", radius=6)
    image = big.resize((w, h), Image.LANCZOS)
    t = ImageDraw.Draw(image)
    for i, (label, name) in enumerate(zip(labels, ("hand", "cog"))):
        on = (i == 1) == auto
        face = font("arialbd.ttf" if on else "arial.ttf", size)
        colour = INK if on else MUTED
        span = 16 + 6 + t.textlength(label, font=face)
        left = round(i * half + (half - span) / 2)
        image.alpha_composite(icon(name, 16, colour, px=1.5), (left, (h - 16) // 2))
        t.text((left + 22, h / 2), label, font=face, fill=colour, anchor="lm")
    return image


def field_face(open_: bool) -> Image.Image:
    """The silo field: white box, chevron at the right. Open, it is the list's header."""
    _, _, w, h = COMBO
    s = 4
    big = Image.new("RGBA", (w * s, h * s), rgb(WHITE) + (255,))
    d = ImageDraw.Draw(big)
    if open_:  # square bottom: the rows continue below
        d.rounded_rectangle((0, 0, w * s - 1, (h + 8) * s), radius=6 * s, fill=WHITE, outline=FIELD_LINE, width=s)
        d.line((0, (h - 1) * s, w * s, (h - 1) * s), fill=CARD_LINE, width=s)
    else:
        rounded(d, (0, 0, w, h), outline=FIELD_LINE)
    image = big.resize((w, h), Image.LANCZOS)
    image.alpha_composite(icon("chevron-up" if open_ else "chevron-down", 18, MUTED, px=1.75, cut=WHITE),
                          (w - 30, (h - 18) // 2))
    return image


def row_face(i: int, pressed: bool) -> Image.Image:
    """One row of the silo list: its fixed number, the name is a live element over it."""
    w, h = COMBO[2], ROW_H
    s = 4
    last = i == ROWS - 1
    fill = TILE if pressed else WHITE
    big = Image.new("RGBA", (w * s, h * s), rgb(WHITE) + (255,))
    d = ImageDraw.Draw(big)
    top = -8 * s  # the frame runs on above the row, so no top edge shows
    if last:
        d.rounded_rectangle((0, top, w * s - 1, h * s - 1), radius=6 * s, fill=fill, outline=FIELD_LINE, width=s)
    else:
        d.rectangle((0, top, w * s - 1, h * s + 8 * s), fill=fill, outline=FIELD_LINE, width=s)
        d.line((12 * s, (h - 1) * s, (w - 12) * s, (h - 1) * s), fill=CARD_LINE, width=s)
    image = big.resize((w, h), Image.LANCZOS)
    t = ImageDraw.Draw(image)
    t.text((20, h / 2), str(i + 1), font=font("arial.ttf", 14), fill=MUTED, anchor="mm")
    return image


def _flat(path: Path, back: str) -> Image.Image:
    art = Image.open(path).convert("RGBA")
    flat = Image.new("RGBA", art.size, rgb(back) + (255,))
    flat.alpha_composite(art)
    return flat


def render(folder: Path) -> dict[str, Path]:
    faces = {
        "fl_process": process_drawing(),
        "fl_status_bar": status_bar(),
        "fl_weight_card": weight_card(),
        "fl_silo_card": silo_card(),
        "fl_start_0": start_face(False),
        "fl_start_1": start_face(True),
        "fl_mode_0": mode_face(False),
        "fl_mode_1": mode_face(True),
        "fl_valve_0": _flat(ICONS / "Van_Off.png", PAGE),
        "fl_valve_1": _flat(ICONS / "Van_On.png", PAGE),
        "fl_field_0": field_face(False),
        "fl_field_1": field_face(True),
        **{f"fl_row_{i}_0": row_face(i, False) for i in range(ROWS)},
    }
    folder.mkdir(parents=True, exist_ok=True)
    paths = {}
    for key, image in faces.items():
        path = folder / f"{key}.png"
        image.save(path)
        paths[key] = path
    return paths


# --- element helpers -------------------------------------------------------------

def clear_links(element) -> None:
    for key in ("InterLockVar", "VisibleVar"):
        if element.section.get(key) not in (None, "None"):
            element.section.set(key, "None")


def bind(element, address: str) -> None:
    for key in ("ReadVar", "WriteVar"):
        if element.section.get(key) is not None:
            element.section.set(key, address)


def picture_on(element, state_index: int, bank: frame.Bank, key: str, x: int, y: int, w: int, h: int, back: str) -> None:
    name, offset, _, _ = bank.where[key]
    state = element.states[state_index]
    for k, v in (("PIB Name", "PicBank02"), ("Picture Name", name), ("PictureOffset", offset),
                 ("PictureCoordX", x), ("PictureCoordY", y), ("PictureWidth", w), ("PictureHeight", h),
                 ("PictureStretch", 1), ("StretchMode", 2), ("UsePictureCoord", 0), ("TransEffect", 0),
                 ("TransColor", bgr(back))):
        state.set(k, v)


def text_style(element, size: int, colour: str, bold: bool = False, align: int = 33) -> None:
    for state in element.states:
        for slot in (0, 1):
            state.set(f"FontName{slot}", "Arial")
            state.set(f"FontSize{slot}", size)
        state.set("FontColor", bgr(colour))
        state.set("FontBold", 1 if bold else 0)
        state.set("FontAlign", align)


def silo_popup(project: Project, donor: Project, name: str = POPUP):
    """The sub-screen holding the silo list, emptied if a previous run made it.

    Its frame is copied from the donor's OVERVIEW sub-screen, then sized and
    pinned so the header lands exactly on the silo field.
    """
    existing = [sc for sc in project.screens if sc.name == name]
    if existing:
        screen = existing[0]
        for element in screen.elements[::-1]:
            edit.delete_element(project, screen, element.index)
    else:
        source = donor.screen("OVERVIEW")
        doc = donor.doc
        at = doc.sections.index(source.section)
        block = [copy.deepcopy(x) for x in doc.sections[at:at + 2] if x.name in ("Screen", "AuxKeyElement")]
        section = block[0]
        section.set("ID", max(sc.id for sc in project.screens) + 1)
        for key in ("wTextLen", "wScreenDESCTextLen000", "wScreenDESCTextLen001"):
            for entry in section.entries(key):
                entry.set_text(name)
        last = edit._last_section_index(project.doc, project.screens[-1])
        project.doc.sections[last + 1:last + 1] = block
        from dpa.model import Screen
        screen = Screen(section=section, elements=[])
        project.screens.append(screen)
    x, y, w, _ = COMBO
    h = COMBO[3] + ROW_H * ROWS
    for key, value in (("Width", w), ("Height", h), ("DocSizeX", w), ("DocSizeY", h), ("CenterSubScreen", 0),
                       ("SubScreenX", x), ("SubScreenY", y), ("BgColor", bgr(WHITE)), ("IsUseFrame", 0),
                       ("IsUseTitleBar", 0), ("AutoCloseTime", 0), ("EnableCycleMacro", 0)):
        screen.section.set(key, value)
    return screen


# FontAlign is a bit mask: 1 left, 2 centre, 4 right, plus 32 for middle row.
LEFT, CENTRE, RIGHT = 33, 34, 36


def main(path: str, asset_dir: str) -> None:
    project = Project(path)
    donor = Project(DONOR)
    page = project.screen("Home_Fill")

    for element in [e for e in page.elements if e.name.startswith("fl_")][::-1]:
        edit.delete_element(project, page, element.index)
    popup = silo_popup(project, donor)
    frame.prune_bank(project)

    tpl_rect = donor.element("scr_MainScreen", 1)
    tpl_num = donor.element("scr_Calibcation", 19)
    tpl_multi = donor.element("scr_Discharge", 97)
    tpl_indicator = donor.element("scr_MainScreen", 5)
    tpl_combo = donor.element("scr_Calibcation", 13)
    tpl_graphic = donor.element("scr_MainScreen", 2)
    tpl_push = donor.element("scr_Calibcation", 4)

    assets = render(Path(asset_dir))
    bank = frame.Bank(project)
    for key, file in assets.items():
        bank.add(key, file)
    bank.commit()

    def picture(key, x, y, back=PAGE):
        _, _, w, h = bank.where[key]
        item = edit.clone_element(project, tpl_rect, page, 0, 0, 10, 10, key)
        clear_links(item)
        frame.face(item, bank, key)
        frame.flat(item, back)
        for state in item.states:
            state.set("TransColor", bgr(back))  # the anti-aliased edge blends with this
        frame.picture_rect(item, x, y, w, h)
        return item

    def number(name, box, size, digits, decimals, align=CENTRE, bold=True, colour=INK):
        x, y, w, h = box
        item = edit.clone_element(project, tpl_num, page, x, y, w, h, name)
        clear_links(item)
        item.section.set("ReadVar", ADDRESSES[name])
        item.section.set("IntNum", digits)
        item.section.set("DotNum", decimals)
        text_style(item, size, colour, bold, align)
        return item

    # --- static artwork first, so everything else draws over it ------------
    picture("fl_process", PROCESS[0], PROCESS[1])
    picture("fl_status_bar", STATUS[0], STATUS[1])
    picture("fl_weight_card", WEIGHT[0], WEIGHT[1])
    picture("fl_silo_card", SILO[0], SILO[1])

    # --- status bar ---------------------------------------------------------
    sx, sy = STATUS[0], STATUS[1]
    number("fl_status", (sx + 14, sy + 11, 42, 24), 18, 3, 0)
    number("fl_status_silo", (sx + 530, sy + 11, 40, 24), 18, 2, 0)
    number("fl_status_time", (sx + 616, sy + 11, 44, 24), 18, 4, 0, align=RIGHT)

    # --- process ------------------------------------------------------------
    number("fl_sfv_no", (SFV_TAG[0] + 44, SFV_TAG[1] + 1, 24, 20), 16, 1, 0, align=LEFT)
    sfv = edit.clone_element(project, tpl_graphic, page, 0, 0, 10, 10, "fl_sfv")
    clear_links(sfv)
    sfv.section.set("ReadVar", ADDRESSES["fl_sfv"])
    for i, key in enumerate(("fl_valve_0", "fl_valve_1")):
        picture_on(sfv, i, bank, key, SFV_AT[0], SFV_AT[1], 26, 26, PAGE)
    frame.flat(sfv, PAGE)
    frame.picture_rect(sfv, SFV_AT[0], SFV_AT[1], 26, 26)

    rx, ry, rw, rh = RATE_CARD
    number("fl_rate", (rx + 6, ry + 45, 70, 30), 24, 3, 1, align=RIGHT)  # ends 8 px before kg/m
    cx, cy, cw, ch = CAP_CARD
    number("fl_capacity", (cx + 6, cy + 53, 88, 32), 24, 5, 1, align=RIGHT)
    vx, vy, vw, vh = VAC_CARD
    number("fl_pressure", (vx + 4, vy + 77, vw // 2 - 8, 28), 20, 3, 1)
    number("fl_dec_time", (vx + vw // 2 + 4, vy + 77, vw // 2 - 8, 28), 20, 2, 0)
    mx, my, mw, mh = MODE_CARD
    mode_text = edit.clone_element(project, tpl_indicator, page, mx + 6, my + 38, mw // 2 - 12, 28, "fl_fill_mode")
    clear_links(mode_text)
    mode_text.section.set("ReadVar", ADDRESSES["fl_fill_mode"])
    for i, words in enumerate(("PULSED", "CONTINUOUS")):
        edit.set_state_text(mode_text, words, words, state=i)
    text_style(mode_text, 16, INK, True, CENTRE)
    for state in mode_text.states:
        state.set("FgColor", bgr(WHITE))
        state.set("BgColor", bgr(WHITE))
    number("fl_countdown", (mx + mw // 2 + 6, my + 38, mw // 2 - 12, 28), 16, 2, 0)

    # --- right column ---------------------------------------------------------
    wx, wy, ww, wh = WEIGHT
    # size, box and colour as Sang set them by hand on 30/09
    number("fl_weight", (wx + 24, wy + 49, 167, 75), 64, 3, 1, align=CENTRE, colour="#2B3644")

    # --- silo field and the list it opens --------------------------------------
    # A ComboBox takes its items from the project, never from an address, so
    # the names the operator gives the silos are Character Displays instead.
    text_donor = Project(DONOR_TEXT).element("Screen_1", 2)
    set_donor = Project(DONOR_SET).element("Fill", 62)

    def name_text(screen, key, x, y, w, h, size, bold):
        item = edit.clone_element(project, text_donor, screen, x, y, w, h, key)
        clear_links(item)
        item.section.set("ReadVar", ADDRESSES[key])
        item.section.set("StringLen", NAME_CHARS)
        item.section.set("Style", 3)  # Transparent: no box, no border
        text_style(item, size, INK, bold, LEFT)
        for state in item.states:
            state.set("FgColor", bgr(WHITE))
            state.set("BgColor", bgr(WHITE))
        return item

    def pushbutton(screen, key, x, y, w, h, faces, on_macro):
        item = edit.clone_element(project, tpl_push, screen, x, y, w, h, key)
        clear_links(item)
        bind(item, ADDRESSES["fl_silo_open"])
        item.section.set("Style", 3)
        macro.set_macro(item.section, "ButtonOnMacroLen", on_macro)
        macro.set_macro(item.section, "ButtonOffMacroLen", None)
        for i, face_key in enumerate(faces):
            edit.set_state_text(item, "", "", state=i)
            picture_on(item, i, bank, face_key, x, y, w, h, WHITE)
        return item

    fx, fy, fw, fh = COMBO
    pushbutton(page, "fl_silo", fx, fy, fw, fh, ("fl_field_0", "fl_field_0"),
               macro.screen_statement(macro.OPENSCREEN, popup.id))
    name_text(page, "fl_silo_name", fx + 12, fy + 9, fw - 50, 24, 16, True)

    close = macro.screen_statement(macro.CLOSESUBSCREEN, popup.id)
    pushbutton(popup, "fl_silo_close", 0, 0, fw, fh, ("fl_field_1", "fl_field_1"), close)
    name_text(popup, "fl_silo_name", 12, 9, fw - 50, 24, 16, True)
    for i in range(ROWS):
        y = fh + ROW_H * i
        row = edit.clone_element(project, set_donor, popup, 0, y, fw, ROW_H, f"fl_row_{i + 1}")
        clear_links(row)
        row.section.set("WriteVar", ADDRESSES["fl_silo"])
        row.section.set("SetValue", i)
        row.section.set("Style", 3)
        macro.set_macro(row.section, "BeforeExecMacroLen", None)
        macro.set_macro(row.section, "AfterExecMacroLen", close)
        # Set Constant keeps no picture keys; a pushbutton state has the same
        # layout plus them, so the row borrows the pushbutton's state.
        row.states[0].items = copy.deepcopy(tpl_push.states[0].items)
        edit.set_state_text(row, "", "", state=0)
        picture_on(row, 0, bank, f"fl_row_{i}_0", 0, y, fw, ROW_H, WHITE)
        name_text(popup, f"fl_name_{i + 1}", 40, y + 8, fw - 52, 24, 14, False)

    stx, sty, stw, sth = START
    start = edit.clone_element(project, tpl_push, page, stx, sty, stw, sth, "fl_start")
    clear_links(start)
    bind(start, ADDRESSES["fl_start"])
    start.section.set("ReadVar", ADDRESSES["fl_running"])
    for entry in start.section.entries("ButtonOnMacroLen"):
        entry.value, entry.blob, entry.blob_eol = b"0", None, True
    start.section.set("Style", 3)
    for i, key in enumerate(("fl_start_0", "fl_start_1")):
        edit.set_state_text(start, "", "", state=i)
        picture_on(start, i, bank, key, stx, sty, stw, sth, WHITE)

    bx, by, bw, bh = MODE_BTN
    mode = edit.clone_element(project, tpl_multi, page, bx, by, bw, bh, "fl_mode")
    clear_links(mode)
    bind(mode, ADDRESSES["fl_mode"])
    for i, key in enumerate(("fl_mode_0", "fl_mode_1")):
        edit.set_state_text(mode, "", "", state=i)
        picture_on(mode, i, bank, key, bx, by, bw, bh, WHITE)

    print(project.save(path))
    print(f"Home_Fill: {len(page.elements)} elements, bank {len(picbank.read(bank.entry.blob))} pictures")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
