import time
from app.worker import enqueue, claim

def main():
    run_id = enqueue("What slots are available?")

    first = claim("worker-A", lease_seconds=1)
    assert first and first["id"] == run_id
    print(f"Worker A claimed run {run_id} and crashed before finishing.")

    time.sleep(1.2)

    second = claim("worker-B", lease_seconds=2)
    assert second and second["id"] == run_id
    print(f"Worker B reclaimed expired lease for run {run_id}.")
    print("PASS: dead worker run was recovered by another worker.")

if __name__ == "__main__":
    main()
