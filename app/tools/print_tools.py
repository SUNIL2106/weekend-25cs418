from ..print_db import get_db
from ..idempotency import run_effect

def list_printers():
    con = get_db()
    try:
        rows = con.execute(
            "SELECT id,name,location,status FROM printers ORDER BY id"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()

def list_available_slots():
    con = get_db()
    try:
        rows = con.execute("""
            SELECT s.id, p.name AS printer, p.location, s.slot_time
            FROM slots s JOIN printers p ON p.id=s.printer_id
            WHERE p.status='available'
              AND NOT EXISTS (
                  SELECT 1 FROM print_requests r
                  WHERE r.slot_id=s.id AND r.status='booked'
              )
            ORDER BY s.slot_time, s.id
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()

def get_policy():
    con = get_db()
    try:
        return {
            r["key"]: r["value"]
            for r in con.execute("SELECT key,value FROM policies").fetchall()
        }
    finally:
        con.close()

def get_student_requests(student_id):
    con = get_db()
    try:
        rows = con.execute("""
            SELECT r.id,r.slot_id,r.material_grams,r.status,
                   s.slot_time,p.name printer
            FROM print_requests r
            JOIN slots s ON s.id=r.slot_id
            JOIN printers p ON p.id=s.printer_id
            WHERE r.student_id=?
            ORDER BY r.id
        """,(student_id,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()

def book_print_slot(student_id, slot_id, material_grams, idempotency_key):
    con = get_db()
    try:
        policy = get_policy()
        max_material = int(policy["max_material_grams"])
        max_active = int(policy["max_active_requests"])

        if material_grams <= 0:
            raise ValueError("Material must be positive.")
        if material_grams > max_material:
            raise ValueError(
                f"Material exceeds policy limit of {max_material}g."
            )

        active = con.execute(
            "SELECT COUNT(*) c FROM print_requests "
            "WHERE student_id=? AND status='booked'",
            (student_id,)
        ).fetchone()["c"]
        if active >= max_active:
            raise ValueError(
                f"Student already has {active} active requests; "
                f"limit is {max_active}."
            )

        slot = con.execute("""
            SELECT s.id,p.name,s.slot_time,p.status
            FROM slots s JOIN printers p ON p.id=s.printer_id
            WHERE s.id=?
        """,(slot_id,)).fetchone()
        if not slot:
            raise ValueError("Slot does not exist.")
        if slot["status"] != "available":
            raise ValueError("Printer is not available.")

        def effect():
            try:
                con.execute("BEGIN IMMEDIATE")
                occupied = con.execute(
                    "SELECT id FROM print_requests "
                    "WHERE slot_id=? AND status='booked'",
                    (slot_id,)
                ).fetchone()
                if occupied:
                    con.rollback()
                    raise ValueError("Slot was just booked by another request.")
                cur = con.execute("""
                    INSERT INTO print_requests
                    (student_id,slot_id,material_grams,status)
                    VALUES(?,?,?,'booked')
                """,(student_id,slot_id,material_grams))
                con.commit()
                return {
                    "request_id":cur.lastrowid,
                    "slot_id":slot_id,
                    "status":"booked"
                }
            except:
                try:
                    con.rollback()
                except:
                    pass
                raise

        result = run_effect(con,idempotency_key,"book_slot",effect)
        con.commit()
        return result
    finally:
        con.close()

def cancel_print(student_id, request_id, idempotency_key):
    con = get_db()
    try:
        def effect():
            row = con.execute(
                "SELECT id,status FROM print_requests "
                "WHERE id=? AND student_id=?",
                (request_id,student_id)
            ).fetchone()
            if not row:
                raise ValueError("Request not found.")
            if row["status"] == "cancelled":
                return {
                    "request_id":request_id,
                    "status":"cancelled",
                    "already_cancelled":True
                }
            con.execute(
                "UPDATE print_requests SET status='cancelled' WHERE id=?",
                (request_id,)
            )
            con.commit()
            return {"request_id":request_id,"status":"cancelled"}

        result = run_effect(con,idempotency_key,"cancel_print",effect)
        con.commit()
        return result
    finally:
        con.close()

def notify_student(student_id, message, idempotency_key):
    con = get_db()
    try:
        def effect():
            con.execute(
                "INSERT INTO notifications"
                "(student_id,message,idempotency_key) VALUES(?,?,?)",
                (student_id,message,idempotency_key)
            )
            con.commit()
            return {
                "sent":True,
                "student_id":student_id,
                "message":message
            }
        result = run_effect(con,idempotency_key,"notification",effect)
        con.commit()
        return result
    finally:
        con.close()

TOOL_REGISTRY = {
    "list_printers": {
        "fn": list_printers,
        "description": (
            "Read-only. Use when the student asks which printers exist. "
            "Do not use to book or change anything. Changes: none."
        )
    },
    "list_available_slots": {
        "fn": list_available_slots,
        "description": (
            "Read-only. Use before discussing or choosing free slots. "
            "Do not use as a substitute for booking. Changes: none."
        )
    },
    "get_policy": {
        "fn": get_policy,
        "description": (
            "Read-only. Use when explaining limits. "
            "Do not use to perform a booking. Changes: none."
        )
    },
    "get_student_requests": {
        "fn": get_student_requests,
        "description": (
            "Read-only. Use to show a student's requests. "
            "Do not cancel or create requests. Changes: none."
        )
    },
    "book_print_slot": {
        "fn": book_print_slot,
        "description": (
            "Side effect. Use only when the student clearly asks to book "
            "a slot. Do not call for availability questions. "
            "Changes: creates a booked request and enforces data-backed limits."
        )
    },
    "cancel_print": {
        "fn": cancel_print,
        "description": (
            "Side effect. Use only when the student clearly asks to cancel "
            "one of their requests. Changes: marks the request cancelled."
        )
    },
    "notify_student": {
        "fn": notify_student,
        "description": (
            "Side effect. Use after a meaningful booking/cancellation result. "
            "Do not spam or duplicate notifications. Changes: appends a "
            "notification record."
        )
    }
}
