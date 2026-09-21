import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DB_DIR = BASE / "runtime"
DB_DIR.mkdir(exist_ok=True)

def connect(path):
    con = sqlite3.connect(path, timeout=5)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con

def init_db(db_path, schema_path):
    # Seed/schema scripts run only when the SQLite file is first created.
    # Opening a connection must never reseed an existing database.
    first_create = not Path(db_path).exists()
    con = connect(db_path)
    if first_create:
        con.executescript(Path(schema_path).read_text())
        con.commit()
    return con
