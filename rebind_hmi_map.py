"""Re-point the Silo HMI after DB "HMI" was laid out again: every old address becomes its member's new one.

Run:  python rebind_hmi_map.py <project.dpa> <old hmi_map.json> <new hmi_map.json>

gen_hmi_db.py writes the member -> address table of DB "HMI". When members are
removed or inserted in the middle, everything behind them moves; this script
looks each address the project uses up in the old table and writes the same
member's address from the new one. It touches every plain key of every element,
state and screen that holds such an address (read, write, interlock, visible...),
the recipe's PLC address in [EnhanceRcp], and the statements of every macro.

It stops without saving if the project still uses a member the new table no
longer has - that element has to be dealt with first.
"""

from __future__ import annotations

import json
import re
import sys

from dpa import macro
from dpa.document import Entry
from dpa.model import Project

ADDRESS = re.compile(rb"\{EtherLink1\}2@DB(\d+)\.DB[XBWDS][0-9.]+")


def main(path: str, old_file: str, new_file: str) -> None:
    old = json.load(open(old_file, encoding="utf-8"))
    new = json.load(open(new_file, encoding="utf-8"))
    db = str(old["db"]).encode()
    member = {v["address"].encode(): k for k, v in old["members"].items()}
    # the recipe's PLC address is the first byte of "Rc" written as a double word
    for k, v in old["members"].items():
        member.setdefault(v["address"].replace("DBB", "DBD").encode(), k + "|DBD")

    def target(address: bytes) -> bytes | None:
        name = member.get(address)
        if name is None:
            return address                      # not in the table (another DB, or not ours): leave it
        plain, _, form = name.partition("|")
        if plain not in new["members"]:
            return None
        out = new["members"][plain]["address"]
        return (out.replace("DBB", "DBD") if form else out).encode()

    project = Project(path)
    moved, gone = 0, []
    for section in project.doc.sections:
        for item in section.items:
            if not isinstance(item, Entry):
                continue
            if item.blob is None:
                found = ADDRESS.fullmatch(item.value or b"")
                if found and found.group(1) == db:
                    to = target(item.value)
                    if to is None:
                        gone.append(f"[{section.name}] {item.key.decode()} = {item.value.decode()} ({member[item.value]})")
                    elif to != item.value:
                        item.value = to
                        moved += 1
            elif item.key.endswith(b"MacroLen") and b"DB" + db + b"." in item.blob:
                lines = macro.statements(item.blob)
                gone.append(f"[{section.name}] {item.key.decode()}: macro uses DB{db.decode()} ({lines[0]} ...) - rebuild it with its page script")
    cycle_only = [g for g in gone if "CycleMacroLen" not in g]
    if cycle_only:
        raise SystemExit("not saved - the project uses members the new table does not have:\n  " + "\n  ".join(cycle_only))
    print(project.save(path))
    print(f"{moved} addresses moved")
    for line in gone:
        print("left as it is:", line)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
