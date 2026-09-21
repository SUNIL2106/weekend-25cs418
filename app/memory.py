from pathlib import Path
from .db import init_db, DB_DIR

BASE = Path(__file__).resolve().parent.parent
AGENT_DB = DB_DIR / "agent.db"
SCHEMA = BASE / "schema" / "agent.sql"

def get_db():
    return init_db(AGENT_DB, SCHEMA)

def remember(con, conversation_id, role, content):
    con.execute(
        "INSERT INTO messages(conversation_id,role,content) VALUES(?,?,?)",
        (conversation_id, role, content)
    )
    con.commit()

def history(con, conversation_id, limit=20):
    rows = con.execute(
        "SELECT role,content FROM messages WHERE conversation_id=? "
        "ORDER BY id DESC LIMIT ?", (conversation_id, limit)
    ).fetchall()
    return list(reversed([dict(r) for r in rows]))
