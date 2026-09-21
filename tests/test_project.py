import time
from pathlib import Path
import pytest

from app.print_db import get_db
from app.tools.print_tools import (
    list_printers, list_available_slots, get_policy,
    get_student_requests, book_print_slot, cancel_print, notify_student
)
from app.memory import get_db as agent_db
from app.worker import enqueue, claim, finish

@pytest.fixture(autouse=True)
def clean():
    p = Path("runtime")
    if p.exists():
        for f in p.glob("*.db"):
            f.unlink()
    get_db().close()
    agent_db().close()

def test_printers():
    assert len(list_printers()) == 2

def test_available_slots_excludes_booked():
    ids = [x["id"] for x in list_available_slots()]
    assert 1 not in ids

def test_policy_is_data():
    assert get_policy()["max_material_grams"] == "80"

def test_student_requests():
    assert get_student_requests(2)[0]["status"] == "booked"

def test_book_success():
    r = book_print_slot(1,2,50,"k1")
    assert r["status"] == "booked"

def test_material_rule():
    with pytest.raises(ValueError, match="exceeds"):
        book_print_slot(1,2,81,"k2")

def test_zero_material_rule():
    with pytest.raises(ValueError):
        book_print_slot(1,2,0,"k3")

def test_slot_clash():
    with pytest.raises(ValueError):
        book_print_slot(1,1,20,"k4")

def test_idempotent_booking():
    a = book_print_slot(1,2,50,"same-key")
    b = book_print_slot(1,2,50,"same-key")
    assert a == b

def test_active_limit():
    book_print_slot(1,2,10,"a")
    book_print_slot(1,3,10,"b")
    with pytest.raises(ValueError, match="active"):
        book_print_slot(1,4,10,"c")

def test_cancel_releases_slot():
    book_print_slot(1,2,10,"cancel-book")
    cancel_print(1,2,"cancel-key")
    assert 2 in [x["id"] for x in list_available_slots()]

def test_cancel_is_idempotent():
    book_print_slot(1,2,10,"cancel-book")
    a = cancel_print(1,2,"cancel-key")
    b = cancel_print(1,2,"cancel-key")
    assert a == b

def test_notification_idempotency():
    a = notify_student(1,"hello","note1")
    b = notify_student(1,"hello","note1")
    assert a == b

def test_queue_claim_and_finish():
    run = enqueue("hello")
    job = claim("worker")
    assert job["id"] == run
    finish(run, {"ok":True})
    con = agent_db()
    assert con.execute(
        "SELECT status FROM runs WHERE id=?", (run,)
    ).fetchone()["status"] == "done"
    con.close()

def test_crash_and_replay():
    run = enqueue("crash me")
    first = claim("dead-worker",lease_seconds=1)
    assert first["id"] == run

    time.sleep(1.1)

    second = claim("replay-worker",lease_seconds=1)
    assert second["id"] == run
