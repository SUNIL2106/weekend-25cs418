PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS printers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    location TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('available','maintenance'))
);

CREATE TABLE IF NOT EXISTS slots (
    id INTEGER PRIMARY KEY,
    printer_id INTEGER NOT NULL REFERENCES printers(id),
    slot_time TEXT NOT NULL,
    UNIQUE(printer_id, slot_time)
);

CREATE TABLE IF NOT EXISTS policies (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS print_requests (
    id INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    slot_id INTEGER NOT NULL REFERENCES slots(id),
    material_grams INTEGER NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('booked','cancelled','completed')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(slot_id)
);

CREATE TABLE IF NOT EXISTS effects (
    id INTEGER PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    effect_type TEXT NOT NULL,
    result TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    message TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DELETE FROM notifications;
DELETE FROM effects;
DELETE FROM print_requests;
DELETE FROM slots;
DELETE FROM printers;
DELETE FROM policies;
DELETE FROM students;

INSERT INTO printers VALUES
(1,'MakerBot A','Innovation Lab','available'),
(2,'Prusa B','Innovation Lab','available');

INSERT INTO slots VALUES
(1,1,'2026-09-22 10:00'),
(2,1,'2026-09-22 11:00'),
(3,1,'2026-09-22 12:00'),
(4,2,'2026-09-22 10:00'),
(5,2,'2026-09-22 11:00');

INSERT INTO policies VALUES
('max_material_grams','80'),
('max_active_requests','2'),
('booking_window_days','7');

INSERT INTO students VALUES
(1,'Anu','anu@example.edu',1),
(2,'Rahul','rahul@example.edu',1);

INSERT INTO print_requests(id,student_id,slot_id,material_grams,status)
VALUES (1,2,1,40,'booked');
