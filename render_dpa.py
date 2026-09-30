"""Render a .dpa design to PNG without DIAScreen - for reviews and the README.

Run:  python render_dpa.py <project.dpa> <out folder> [screen ...]

Each screen is drawn as the panel would draw it at rest: its base screen first,
then every element in drawing order. Elements with a picture show it from the
project's own picture bank (found by PictureOffset, as DIAScreen does); numeric
and character displays show a sample value in the element's own font, colour
and alignment. Live values come from the PLC, so SAMPLE fills in believable ones.
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from dpa import picbank
from dpa.model import Project

FONTS = Path(r"C:\Windows\Fonts")

SAMPLE = {  # element name -> text shown instead of zeros
    "fl_weight": "486.5", "fl_rate": "42.5", "fl_capacity": "3000.0", "fl_pressure": "-45.2", "fl_dec_time": "12",
    "fl_status": "12", "fl_status_silo": "3", "fl_status_time": "184", "fl_sfv_no": "3", "fl_countdown": "45",
    "fl_silo_name": "Silo 3", "fl_fill_mode": "PULSED",
    "dc_target": "250.0", "dc_hopper": "86.4", "dc_rate": "18.5", "dc_current": "1180.0", "dc_name": "Cà phê Robusta",
    "dc_pressure": "-38.0", "dc_dec_time": "30", "dc_status": "21", "dc_status_silo": "2", "dc_status_time": "96",
    "bl_target": "120.0", "bl_hopper": "40.2", "bl_rate": "15.0", "bl_current": "960.0", "bl_name": "Espresso Blend",
    "bl_pressure": "-40.5", "bl_dec_time": "30", "bl_status": "31", "bl_status_silo": "1", "bl_status_time": "54",
    "cal_silo_shown": "BỒN 1", "cal_points_shown": "3", "cal_point_shown": "1", "cal_func_shown": "Mức lọc", "cal_weight": "500.0", "cal_latched": "1",
    "cal_frames": "20060", "cal_func_name": "Mức lọc", "cal_func_now": "4", "cal_func_new": "5",
    "cal_message": "Đã chốt điểm 1 - đặt quả chuẩn 500 kg cho điểm 2",
    "cal_func_hint": "0-8 · càng lớn càng mượt, càng chậm",
    **{f"cal_net_ch{c}": "500.0" for c in range(1, 5)},
    "fr_time": "09:27:22", "fr_date": "09/30/2026",
}


def colour(bgr: str | None, default=(30, 38, 48)) -> tuple[int, int, int]:
    if bgr is None:
        return default
    v = int(bgr)
    return v & 0xFF, (v >> 8) & 0xFF, (v >> 16) & 0xFF


def bank_by_offset(project: Project) -> dict[int, Image.Image]:
    entry = project.doc.first("Picture").entries("Size")[0]
    out, offset = {}, len(picbank.MAGIC)
    for picture in picbank.read(entry.blob or b""):
        _, width, height = struct.unpack_from("<Iii", picture.record, 4)
        pixels = picture.record[4 + 40:]
        image = Image.frombytes("RGBA", (width, abs(height)), pixels[: width * abs(height) * 4], "raw", "BGRA")
        if height > 0:  # bottom-up DIB
            image = image.transpose(Image.FLIP_TOP_BOTTOM)
        out[offset] = image.convert("RGB")
        offset += len(picture.record)
    return out


def sample_text(element) -> str | None:
    name, kind = element.name, element.type_code
    if name in SAMPLE:
        return SAMPLE[name]
    if name.startswith(("fl_name_", "dc_name_", "cal_silo_name_")):
        return f"Silo {name.rsplit('_', 1)[1]}"
    if kind in ("5.1", "6.1"):
        decimals = element.section.get_int("DotNum", 0)
        return "0" if not decimals else "0." + "0" * decimals
    if kind == "5.2":
        return ""
    if kind in ("5.3", "12.1"):
        return "09/30/2026"
    if kind == "5.4":
        return "09:27:22"
    return None


def draw_text(canvas: Image.Image, element, text: str) -> None:
    state = element.states[0]
    size = state.get_int("FontSize0", 16)
    bold = state.get("FontBold") == "1"
    face = ImageFont.truetype(str(FONTS / ("arialbd.ttf" if bold else "arial.ttf")), size)
    x, y, w, h = element.rect
    align = state.get_int("FontAlign", 34)
    anchor_x = "l" if align & 1 else "r" if align & 4 else "m"
    tx = x + 4 if anchor_x == "l" else x + w - 4 if anchor_x == "r" else x + w / 2
    ImageDraw.Draw(canvas).text((tx, y + h / 2), text, font=face, fill=colour(state.get("FontColor")), anchor=anchor_x + "m")


def draw_elements(canvas: Image.Image, screen, bank: dict[int, Image.Image]) -> None:
    for element in screen.elements:
        state = element.states[0] if element.states else None
        if state is not None and state.get("Picture Name") and state.get_int("PictureOffset") in bank:
            art = bank[state.get_int("PictureOffset")]
            x, y = state.get_int("PictureCoordX", 0), state.get_int("PictureCoordY", 0)
            w, h = state.get_int("PictureWidth", art.width), state.get_int("PictureHeight", art.height)
            canvas.paste(art.resize((w, h), Image.LANCZOS) if (w, h) != art.size else art, (x, y))
        text = sample_text(element)
        if text:
            draw_text(canvas, element, text)


def render(project: Project, name: str) -> Image.Image:
    screen = project.screen(name)
    width, height = (int(v) for v in project.info()["resolution"].split("x")) if "resolution" in project.info() else (1024, 600)
    canvas = Image.new("RGB", (width, height), colour(screen.section.get("BgColor"), (243, 245, 248)))
    bank = bank_by_offset(project)
    base_id = screen.section.get_int("BaseScreenID", 0)
    base = next((s for s in project.screens if s.id == base_id and base_id), None)
    if base is not None:
        draw_elements(canvas, base, bank)
    draw_elements(canvas, screen, bank)
    return canvas


def main(path: str, out_dir: str, *names: str) -> None:
    project = Project(path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name in names or [s.name for s in project.screens if s.section.get("ScreenType") == "0"]:
        target = out / f"{name}.png"
        render(project, name).save(target)
        print(target)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
