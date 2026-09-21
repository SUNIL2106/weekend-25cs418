import time
from .memory import get_db

def enqueue(question):
    con = get_db()
    try:
        cur = con.execute(
            "INSERT INTO runs(question,status) VALUES(?, 'queued')",
            (question,)
        )
        con.commit()
        return cur.lastrowid
    finally:
        con.close()

def claim(worker_id, lease_seconds=2):
    con = get_db()
    try:
        now = time.time()
        con.execute("BEGIN IMMEDIATE")
        row = con.execute("""
            SELECT * FROM runs
            WHERE status='queued'
               OR (status='running' AND lease_until < ?)
            ORDER BY id LIMIT 1
        """,(now,)).fetchone()

        if not row:
            con.commit()
            return None

        con.execute("""
            UPDATE runs
            SET status='running',worker_id=?,lease_until=?,attempts=attempts+1
            WHERE id=?
        """,(worker_id,now+lease_seconds,row["id"]))
        con.commit()
        return dict(row)
    finally:
        con.close()

def finish(run_id, result):
    con = get_db()
    try:
        con.execute(
            "UPDATE runs SET status='done',lease_until=NULL WHERE id=?",
            (run_id,)
        )
        con.commit()
    finally:
        con.close()

def record_step(run_id, step_no, agent, action, result):
    con = get_db()
    try:
        cur = con.execute("""
            INSERT INTO run_steps(run_id,step_no,agent,action,result)
            VALUES(?,?,?,?,?)
        """,(run_id,step_no,agent,action,str(result)))
        con.execute("""
            INSERT INTO tool_calls
            (run_step_id,tool_name,arguments,result)
            VALUES(?,?,?,?)
        """,(cur.lastrowid,action,"{}",str(result)))
        con.commit()
    finally:
        con.close()
