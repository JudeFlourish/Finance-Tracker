-- Database tables. Dates are ISO "YYYY-MM-DD" text, so they sort as strings.
-- "IF NOT EXISTS" makes this safe to run on every startup, and new tables
-- can simply be added at the end.

CREATE TABLE IF NOT EXISTS expenses (
    -- AUTOINCREMENT: an id is never used again, even after a delete
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT    NOT NULL CHECK (length(trim(description)) > 0),
    amount      REAL    NOT NULL CHECK (amount > 0),
    date        TEXT    NOT NULL CHECK (date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    category    TEXT    NOT NULL
);

-- filtering and sorting by date is the most common query
CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses (date);
