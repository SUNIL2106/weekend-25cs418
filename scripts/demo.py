from app.memory import get_db
from app.worker import enqueue, claim, finish, record_step
from app.agents import Supervisor

def main():
    # Initialises both databases.
    get_db().close()

    supervisor = Supervisor()
    questions = [
        "What printer slots are available?",
        "What is the material limit?",
        "Book the 11:00 slot for me."
    ]

    print("=== Campus PrintDesk Agent Demo ===")

    for q in questions:
        run_id = enqueue(q)
        job = claim("demo-worker")
        assert job is not None

        result = supervisor.run(q, student_id=1)
        record_step(
            run_id, 1, result["delegated_to"],
            "scripted_request", result["result"]
        )
        finish(run_id, result)

        print(f"\nStudent: {q}")
        print("Agent:", result)

    con = get_db()
    print("\nRuns:", [
        dict(r) for r in con.execute(
            "SELECT id,status,attempts FROM runs ORDER BY id"
        ).fetchall()
    ])
    con.close()
    print("\nDEMO PASS")

if __name__ == "__main__":
    main()
