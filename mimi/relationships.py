"""Relationships tracker."""
from .database import fetch_all, fetch_one, execute
from .ui import GREEN, RED, c, header, menu, ask, ask_date, ask_int, pause, print_rows

def add():
    header("RELATIONSHIPS")
    name = ask("Person name")
    if not name:
        print(c("  X Name required.", RED)); return
    rtype = ask("Type", "")
    d = ask_date("Interaction date", allow_blank=True)
    commit = ask("Commitment", "")
    notes = ask("Notes", "")
    execute("""INSERT INTO relationships
               (person_name, relationship_type, interaction_date,
                commitment, notes) VALUES (?, ?, ?, ?, ?)""",
            (name, rtype, d, commit, notes))
    print(c("  OK Saved.", GREEN))

def list_records():
    header("RELATIONSHIPS")
    rows = fetch_all("""SELECT * FROM relationships
                        ORDER BY interaction_date DESC, id DESC LIMIT 100""")
    print_rows(rows, [("id","ID"),("person_name","Person"),("relationship_type","Type"),
                      ("interaction_date","Interaction"),("commitment","Commitment")])

def update():
    rid = ask_int("ID", minimum=1)
    row = fetch_one("SELECT * FROM relationships WHERE id=?", (rid,))
    if not row:
        print(c("  X Not found.", RED)); return
    execute("""UPDATE relationships SET person_name=?, relationship_type=?,
               interaction_date=?, commitment=?, notes=? WHERE id=?""",
            (ask("Name", row["person_name"]),
             ask("Type", row["relationship_type"] or ""),
             ask_date("Date", row["interaction_date"], allow_blank=True),
             ask("Commitment", row["commitment"] or ""),
             ask("Notes", row["notes"] or ""), rid))
    print(c("  OK Updated.", GREEN))

def main():
    while True:
        ch = menu([("1","Add"),("2","List"),("3","Update"),("0","Exit")], "RELATIONSHIPS")
        if ch == "1": add()
        elif ch == "2": list_records()
        elif ch == "3": update()
        elif ch == "0": break
        else: print(c("  X Invalid.", RED))
        if ch != "0": pause()

run = main
