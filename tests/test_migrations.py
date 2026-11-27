import logging
import sqlite3

import pytest
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from flask_migrate import downgrade, upgrade

from finance_tracker import create_app
from finance_tracker.database import MIGRATIONS_DIR, db, is_up_to_date


def latest_revision():
    config = Config()
    config.set_main_option("script_location", MIGRATIONS_DIR)
    return ScriptDirectory.from_config(config).get_current_head()


# the newest file in migrations/versions/, so the tests don't change with every migration
LATEST = latest_revision()

# exactly what finance_tracker/schema.sql created before migrations existed
OLD_SCHEMA = """
CREATE TABLE IF NOT EXISTS expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT    NOT NULL CHECK (length(trim(description)) > 0),
    amount      REAL    NOT NULL CHECK (amount > 0),
    date        TEXT    NOT NULL CHECK (date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    category    TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses (date);
CREATE TABLE IF NOT EXISTS budgets (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    category      TEXT    NOT NULL UNIQUE,
    monthly_limit REAL    NOT NULL CHECK (monthly_limit > 0)
);
CREATE TABLE IF NOT EXISTS income (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT    NOT NULL CHECK (length(trim(source)) > 0),
    amount REAL    NOT NULL CHECK (amount > 0),
    date   TEXT    NOT NULL CHECK (date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]')
);
CREATE INDEX IF NOT EXISTS idx_income_date ON income (date);
"""


def make_app(path, testing=True):
    """An app on that database file, without running any migration."""
    return create_app({"TESTING": testing, "DATABASE": str(path)})


def run_sql(path, sql):
    conn = sqlite3.connect(path)
    conn.executescript(sql)
    conn.commit()
    conn.close()


def query(path, sql):
    conn = sqlite3.connect(path)
    rows = conn.execute(sql).fetchall()
    conn.close()
    return rows


def schema(path):
    """Every table and index with its SQL, to compare two databases."""
    rows = query(path, "SELECT type, name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY name")
    # SQLite keeps the quotes a table was renamed with, they don't change anything
    return [(kind, name, (sql or "").replace('"', "")) for kind, name, sql in rows]


def upgrade_db(path):
    app = make_app(path)
    with app.app_context():
        upgrade()
    return app


@pytest.fixture
def new_db(tmp_path):
    """A brand-new database after `flask db upgrade`."""
    path = tmp_path / "new.db"
    upgrade_db(path)
    return path


@pytest.fixture
def old_db(tmp_path):
    """A database made by schema.sql, with data, and with the highest expense deleted."""
    path = tmp_path / "old.db"
    run_sql(path, OLD_SCHEMA + """
        INSERT INTO expenses (description, amount, date, category) VALUES ('Lunch', 12.5, '2026-11-01', 'Food');
        INSERT INTO expenses (description, amount, date, category) VALUES ('Bus', 3, '2026-11-05', 'Transport');
        INSERT INTO expenses (description, amount, date, category) VALUES ('Deleted', 9, '2026-11-06', 'Other');
        DELETE FROM expenses WHERE description = 'Deleted';
        INSERT INTO income (source, amount, date) VALUES ('Salary', 1500, '2026-11-01');
        INSERT INTO budgets (category, monthly_limit) VALUES ('Food', 300);
    """)
    return path


# a new database

def test_upgrade_creates_every_table(new_db):
    tables = {name for (name,) in query(new_db, "SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert {"expenses", "income", "budgets", "alembic_version"} <= tables
    assert query(new_db, "SELECT version_num FROM alembic_version") == [(LATEST,)]


def test_migrations_match_the_models(new_db):
    # same check as `flask db check`: a model changed without a migration fails here
    app = make_app(new_db)
    with app.app_context(), db.engine.connect() as connection:
        differences = compare_metadata(MigrationContext.configure(connection), db.metadata)
    assert differences == []


def test_upgrade_twice_changes_nothing(new_db):
    before = schema(new_db)
    upgrade_db(new_db)
    assert schema(new_db) == before


def test_downgrade_to_the_start_and_up_again(new_db):
    app = make_app(new_db)
    with app.app_context():
        downgrade(revision="base")
        tables = {name for (name,) in query(new_db, "SELECT name FROM sqlite_master WHERE type = 'table'")}
        assert not {"expenses", "income", "budgets"} & tables
        upgrade()
    assert query(new_db, "SELECT version_num FROM alembic_version") == [(LATEST,)]


def test_is_up_to_date(tmp_path):
    path = tmp_path / "empty.db"
    app = make_app(path)
    with app.app_context():
        assert is_up_to_date() is False
        upgrade()
        assert is_up_to_date() is True


# a database made before migrations existed

def test_old_database_keeps_every_row_and_id(old_db):
    upgrade_db(old_db)
    assert query(old_db, "SELECT id, description, amount, date, category FROM expenses ORDER BY id") == [
        (1, "Lunch", 12.5, "2026-11-01", "Food"),
        (2, "Bus", 3.0, "2026-11-05", "Transport"),
    ]
    assert query(old_db, "SELECT id, source, amount, date FROM income") == [(1, "Salary", 1500.0, "2026-11-01")]
    assert query(old_db, "SELECT id, category, monthly_limit FROM budgets") == [(1, "Food", 300.0)]


def test_old_database_gets_the_same_tables_as_a_new_one(old_db, new_db):
    upgrade_db(old_db)
    assert schema(old_db) == schema(new_db)


def test_old_database_never_reuses_a_deleted_id(old_db):
    # expense 3 was deleted before the upgrade, so the next expense must get 4
    upgrade_db(old_db)
    run_sql(old_db, "INSERT INTO expenses (description, amount, date, category) VALUES ('Tea', 2, '2026-11-07', 'Food')")
    assert query(old_db, "SELECT max(id) FROM expenses") == [(4,)]


def test_old_database_still_enforces_the_rules(old_db):
    upgrade_db(old_db)
    with pytest.raises(sqlite3.IntegrityError):
        run_sql(old_db, "INSERT INTO budgets (category, monthly_limit) VALUES ('Food', 50)")
    with pytest.raises(sqlite3.IntegrityError):
        run_sql(old_db, "INSERT INTO income (source, amount, date) VALUES ('Gift', 0, '2026-11-02')")


def test_database_from_before_income_and_budgets(tmp_path):
    # the very first SQLite version: only an expenses table
    path = tmp_path / "first.db"
    run_sql(path, """
        CREATE TABLE expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, description TEXT NOT NULL,
                               amount REAL NOT NULL, date TEXT NOT NULL, category TEXT NOT NULL);
        INSERT INTO expenses (description, amount, date, category) VALUES ('Lunch', 12.5, '2026-11-01', 'Food');
    """)
    upgrade_db(path)
    assert query(path, "SELECT description FROM expenses") == [("Lunch",)]
    assert query(path, "SELECT count(*) FROM income") == [(0,)]
    assert query(path, "SELECT count(*) FROM budgets") == [(0,)]


def upgrade_error(path, caplog):
    """Run the upgrade, expecting it to stop; returns the error it logged.
    Like the `flask db upgrade` command, Flask-Migrate logs the error and exits with 1."""
    with pytest.raises(SystemExit):
        upgrade_db(path)
    return " ".join(r.getMessage() for r in caplog.records if r.levelno >= logging.ERROR)


def test_bad_old_rows_stop_the_upgrade_and_change_nothing(tmp_path, caplog):
    # rows that break a rule can't be copied; the database must be left exactly as it was
    path = tmp_path / "bad.db"
    run_sql(path, """
        CREATE TABLE expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, description TEXT,
                               amount REAL, date TEXT, category TEXT);
        INSERT INTO expenses (description, amount, date, category) VALUES ('Lunch', 12.5, '2026-11-01', 'Food');
        INSERT INTO expenses (description, amount, date, category) VALUES ('Free lunch', 0, '2026-11-01', 'Food');
        INSERT INTO expenses (description, amount, date, category) VALUES (NULL, 5, '2026-11-01', 'Food');
    """)
    before = schema(path)
    assert "Can't upgrade the expenses table: rows with id 2, 3 break its rules" in upgrade_error(path, caplog)
    # Alembic makes its own (empty) version table first; no version in it means
    # the next `db upgrade` runs this migration again once the rows are fixed
    assert [t for t in schema(path) if t[1] != "alembic_version"] == before
    assert query(path, "SELECT * FROM alembic_version") == []
    assert query(path, "SELECT count(*) FROM expenses") == [(3,)]

    # after fixing the rows, the same upgrade goes through
    run_sql(path, "DELETE FROM expenses WHERE id IN (2, 3)")
    upgrade_db(path)
    assert query(path, "SELECT id, description FROM expenses") == [(1, "Lunch")]
    assert query(path, "SELECT version_num FROM alembic_version") == [(LATEST,)]


def test_duplicate_old_budgets_stop_the_upgrade(tmp_path, caplog):
    path = tmp_path / "dup.db"
    run_sql(path, """
        CREATE TABLE budgets (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, monthly_limit REAL);
        INSERT INTO budgets (category, monthly_limit) VALUES ('Food', 100);
        INSERT INTO budgets (category, monthly_limit) VALUES ('Food', 200);
    """)
    assert "budgets table: rows with id 1, 2" in upgrade_error(path, caplog)
    assert query(path, "SELECT count(*) FROM budgets") == [(2,)]


# reminder when someone forgot to run the migrations

def test_warns_once_when_the_database_is_not_up_to_date(tmp_path, caplog):
    client = make_app(tmp_path / "empty.db", testing=False).test_client()
    with caplog.at_level(logging.WARNING):
        client.get("/does-not-exist")
        client.get("/does-not-exist")
    warnings = [r.getMessage() for r in caplog.records if "not up to date" in r.getMessage()]
    assert warnings == ["The database is not up to date. Run: uv run flask --app financeapp db upgrade"]


def test_no_warning_when_up_to_date(new_db, caplog):
    client = make_app(new_db, testing=False).test_client()
    with caplog.at_level(logging.WARNING):
        client.get("/does-not-exist")
    assert not [r for r in caplog.records if "not up to date" in r.getMessage()]
