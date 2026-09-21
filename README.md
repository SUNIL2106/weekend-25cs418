# Campus PrintDesk Agent

A complete weekend project based on the supplied brief. The chosen domain is **college 3D-print booking**: students request printer slots and material, while a limited set of printer slots creates a real clash/resource constraint.

## Why this is a good fit

- Limited printer slots can clash.
- Print material has a data-backed limit.
- Booking, cancellation, and notification are side effects.
- The project has two SQLite databases.
- It has a durable queue and lease-based worker.
- Side effects use idempotency keys.
- A supervisor delegates to an information specialist and a print specialist.
- The information specialist has no write tools.
- `python -m scripts.demo` and `python -m scripts.crash_demo` require no API key.
- 15 pytest tests are included.

## Architecture

```text
Student
   |
   v
Supervisor Agent
   |----------------------> Info Specialist
   |                         read-only tools only
   |
   `----------------------> Print Specialist
                             booking/cancel tools
                                      |
                         +------------+------------+
                         |                         |
                    printdesk.db                agent.db
                    domain data                  memory
                    policies                     queue
                    printers                     runs
                    slots                        tool calls
                    requests                     effects
                         |
                         v
                       Worker
                 lease -> execute
                 crash -> replay

                 notification side effect
```

## Data-backed rules

The `policies` table stores:
- `max_material_grams`
- `max_active_requests`
- `booking_window_days`

The booking tool enforces those rules itself. This is important because the model cannot bypass the business rule simply by skipping a read-only policy check.

## Run

```bash
python -m scripts.demo
python -m scripts.crash_demo
pytest -q
```

Install the only dependency with:

```bash
pip install -r requirements.txt
```


