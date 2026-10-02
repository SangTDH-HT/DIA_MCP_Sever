"""Point the Silo HMI at the PLC: every placeholder `$` address becomes its DB address.

Run:  python bind_plc.py <project.dpa> <hmi_map.json>

The page scripts (build_fill_page.py, build_home_pages.py, ...) draw the pages
on internal memory `$2xx..$7xx`. The PLC (PLC_SILO_6_Sa) keeps one exchange DB
"HMI" for the panel; gen_hmi_db.py lays it out and writes hmi_map.json, the
member -> address table. BIND below says which `$` address is which member.

Run it again after any page script: a page that was redrawn is back on `$`
addresses, and this puts it on the PLC again. Addresses already on the PLC are
left alone. The list openers ($212.0, $232.0, $252.0, $521.0) and "acknowledge
all" ($910.0) stay inside the panel - the PLC has no use for them.

The alarm list is rewritten to the bits of DB "Loi_He_Thong" (FC "Gom_Loi").
"""

from __future__ import annotations

import json
import sys

import build_data_page as data
import silo_i18n as i18n
from dpa.model import Project

KEYS = ("ReadVar", "WriteVar")
LINK = "{EtherLink1}2@"

BIND = {
    # Home_Fill
    "$200": "Fl.Weight", "$201": "Fl.Rate", "$202": "Fl.Capacity", "$203": "Fl.DecTime", "$204": "Fl.Pressure",
    "$205": "Fl.Pick", "$206": "Fl.Status", "$207": "Fl.StatusSilo", "$208": "Fl.StatusTime", "$209": "Fl.SfvNo",
    "$211": "Fl.Countdown", "$210.1": "Fl.Auto", "$210.2": "Fl.Sfv", "$210.5": "Fl.Start",
    "$210.6": "Fl.Continuous", "$210.7": "Fl.Running", "$300": "Fl.SiloName",
    # silo names, shared by the three silo lists
    **{f"${310 + 10 * i}": f"SiloName[{i + 1}]" for i in range(6)},
    # Home_Discharge
    "$220": "Dc.Status", "$221": "Dc.StatusSilo", "$222": "Dc.StatusTime", "$223": "Dc.Hopper", "$224": "Dc.Rate",
    "$225": "Dc.Current", "$226": "Dc.Pressure", "$227": "Dc.DecTime", "$228": "Dc.Target", "$229": "Dc.Pick",
    "$231": "Dc.SdvNo", "$230.0": "Dc.Auto", "$230.1": "Dc.ValveMan", "$230.2": "Dc.ValveRun", "$230.3": "Dc.Ghfv",
    "$230.4": "Dc.Sdv", "$230.5": "Dc.Start", "$230.6": "Dc.Running", "$230.7": "Dc.Done", "$370": "Dc.SiloName",
    # Home_Blend
    "$240": "Bl.Status", "$241": "Bl.StatusSilo", "$242": "Bl.StatusTime", "$243": "Bl.Hopper", "$244": "Bl.Rate",
    "$245": "Bl.Current", "$246": "Bl.Pressure", "$247": "Bl.DecTime", "$248": "Bl.Target",
    "$251": "Bl.SdvNo", "$250.0": "Bl.Auto", "$250.1": "Bl.ValveMan", "$250.2": "Bl.ValveRun", "$250.3": "Bl.Ghfv",
    "$250.4": "Bl.Sdv", "$250.5": "Bl.Start", "$250.6": "Bl.Running", "$250.7": "Bl.Done",
    # Set_Calibration
    "$500": "Cal.Pick", "$502": "Cal.SiloName", "$512": "Cal.Points", "$513": "Cal.Point", "$514": "Cal.Weight",
    "$515": "Cal.Latched", "$516": "Cal.Frames",
    "$520.0": "Cal.BtnTare", "$520.1": "Cal.BtnTareUndo", "$520.2": "Cal.BtnZero", "$520.3": "Cal.BtnZeroUndo",
    "$520.4": "Cal.BtnApply", "$520.5": "Cal.BtnCancel", "$520.6": "Cal.BtnRead", "$520.7": "Cal.BtnWrite",
    **{f"${530 + c}": f"Cal.Zero[{c + 1}]" for c in range(4)},
    **{f"${534 + c}": f"Cal.Net[{c + 1}]" for c in range(4)},
    **{f"${538 + c}": f"Cal.Tare[{c + 1}]" for c in range(4)},
    "$542": "Cal.FuncPick", "$544": "Cal.FuncName",
    **{f"${560 + 10 * i}": f"FuncName[{i + 1}]" for i in range(6)},
    "$620": "Cal.FuncHint", "$640": "Cal.FuncNow", "$641": "Cal.FuncNew", "$650": "Cal.Message",
    # Set_Parameter: 3 cards x 6 rows
    **{f"${700 + k}": f"Par[{k + 1}]" for k in range(18)},
}
# The recipe pick and names ($249, $380, $390..$440) are the panel's own recipe registers: build_recipe_page.py
# puts them on ENRCPNO / ENRCPn after this script.
PANEL_ONLY = {"$212.0", "$232.0", "$252.0", "$521.0", "$910.0", "$249", "$380", *(f"${390 + 10 * i}" for i in range(6))}

# DB "Loi_He_Thong" (standard access): four words in a row, one alarm a bit.
ERROR_DB = 10
WORDS = {"Loi_Silo": 0, "Loi_Truyen_Thong": 2, "Canh_Bao_Silo": 4, "Canh_Bao_Me": 6}
ALARMS = (  # word, bit, (English, Vietnamese, French)
    ("Loi_Silo", 0, ("Suction motor overload", "Quá tải động cơ hút chân không", "Surcharge du moteur d'aspiration")),
    ("Loi_Silo", 1, ("Suction motor overload (manual mode) – press Reset", "Quá tải động cơ hút (chế độ tay) – bấm Reset",
                     "Surcharge du moteur (mode manuel) – appuyer sur Reset")),
    ("Loi_Silo", 2, ("Suction line blocked while filling", "Nghẹt đường hút khi nạp liệu", "Ligne d'aspiration bouchée au remplissage")),
    ("Loi_Silo", 3, ("Suction line blocked while discharging", "Nghẹt đường hút khi xả liệu", "Ligne d'aspiration bouchée à la vidange")),
    ("Loi_Silo", 4, ("Suction line blocked while blending", "Nghẹt đường hút khi phối trộn", "Ligne d'aspiration bouchée au mélange")),
    ("Loi_Silo", 5, ("Pressure over limit (manual mode) – press Reset", "Áp suất vượt ngưỡng (chế độ tay) – bấm Reset",
                     "Pression hors limite (mode manuel) – appuyer sur Reset")),
    ("Loi_Truyen_Thong", 0, ("Scale of silos 1–4 not responding (RW-ST04D)", "Mất kết nối đầu cân bồn 1–4 (RW-ST04D)",
                             "Balance des silos 1–4 sans réponse (RW-ST04D)")),
    ("Loi_Truyen_Thong", 1, ("Scale of silos 5–6 not responding (RW-ST02D)", "Mất kết nối đầu cân bồn 5–6 (RW-ST02D)",
                             "Balance des silos 5–6 sans réponse (RW-ST02D)")),
    ("Loi_Truyen_Thong", 2, ("Suction motor drive not responding", "Mất kết nối biến tần động cơ hút", "Variateur du moteur d'aspiration sans réponse")),
    *(("Canh_Bao_Silo", i, (f"Silo {i + 1} is full – cannot be picked for filling", f"Bồn {i + 1} đã đầy – không chọn nạp được",
                            f"Silo {i + 1} plein – remplissage impossible")) for i in range(6)),
    *(("Canh_Bao_Silo", 6 + i, (f"Silo {i + 1} is empty – cannot be picked for discharge", f"Bồn {i + 1} đã cạn – không chọn xả được",
                                f"Silo {i + 1} vide – vidange impossible")) for i in range(6)),
    ("Canh_Bao_Silo", 12, ("Recipe is over 120 kg", "Công thức vượt 120 kg", "Recette supérieure à 120 kg")),
    ("Canh_Bao_Silo", 13, ("Not enough material in a silo for the recipe", "Bồn không đủ liệu cho công thức", "Silo insuffisant pour la recette")),
    ("Canh_Bao_Me", 0, ("Fill batch ended with an error", "Mẻ nạp kết thúc lỗi", "Lot de remplissage terminé en erreur")),
    ("Canh_Bao_Me", 1, ("Discharge batch ended with an error", "Mẻ xả kết thúc lỗi", "Lot de vidange terminé en erreur")),
    ("Canh_Bao_Me", 2, ("Blend batch ended with an error", "Mẻ phối trộn kết thúc lỗi", "Lot de mélange terminé en erreur")),
    ("Canh_Bao_Me", 3, ("Scale calibration failed", "Hiệu chỉnh cân thất bại", "Échec de l'étalonnage")),
)


def word_bit(db: int, offset: int, bit: int) -> str:
    """Bit of a WORD in an S7 DB: the high byte comes first, so bits 0..7 sit in the second byte."""
    return f"{LINK}DB{db}.DBX{offset + 1 if bit < 8 else offset}.{bit % 8}"


def main(path: str, map_file: str) -> None:
    members = json.load(open(map_file, encoding="utf-8"))["members"]
    missing = sorted(set(BIND.values()) - set(members))
    if missing:
        raise SystemExit(f"hmi_map.json has no member {missing}")

    project = Project(path)
    bound, left = 0, set()
    for screen in project.screens:
        for element in screen.elements:
            for key in KEYS:
                value = element.section.get(key)
                if not value or not value.startswith("$"):
                    continue
                if value in BIND:
                    element.section.set(key, members[BIND[value]]["address"])
                    bound += 1
                elif value not in PANEL_ONLY:
                    left.add(f"{screen.name}/{element.name} {key}={value}")

    data.ALARMS = tuple((words[0], word_bit(ERROR_DB, WORDS[word], bit), f"{word}.%X{bit}") for word, bit, words in ALARMS)
    data.write_alarms(project)
    # the message in every language of the project: wMessageLenNNN-000 English, -001 Vietnamese, -002 French
    i18n.ensure_languages(project)
    section = project.doc.first("Alarm")
    for n, (_, _, words) in enumerate(ALARMS, 1):
        for slot, text in zip(i18n.SLOTS, words):
            for entry in section.entries(f"wMessageLen{n:03d}-00{slot}"):
                entry.set_text(text)

    print(project.save(path))
    print(f"{bound} addresses on the PLC, {len(data.ALARMS)} alarms on DB{ERROR_DB}")
    for line in sorted(left):
        print("still on internal memory:", line)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
