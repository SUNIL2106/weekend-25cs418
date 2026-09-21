from pathlib import Path
from .db import init_db, DB_DIR

BASE = Path(__file__).resolve().parent.parent
PRINT_DB = DB_DIR / "printdesk.db"
SCHEMA = BASE / "schema" / "printdesk.sql"

def get_db():
    return init_db(PRINT_DB, SCHEMA)
