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

-- one monthly spending limit per category (US-05)
-- no link to expenses: removing a budget never touches any expense
CREATE TABLE IF NOT EXISTS budgets (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    category      TEXT    NOT NULL UNIQUE,
    monthly_limit REAL    NOT NULL CHECK (monthly_limit > 0)
);

-- money coming in (US-04), kept apart from expenses
CREATE TABLE IF NOT EXISTS income (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT    NOT NULL CHECK (length(trim(source)) > 0),
    amount REAL    NOT NULL CHECK (amount > 0),
    date   TEXT    NOT NULL CHECK (date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]')
);
CREATE INDEX IF NOT EXISTS idx_income_date ON income (date);
