import sqlite3

import pytest
from flask import g

from finance_tracker.db import get_db, init_db


def insert(conn, description="Lunch", amount=12.5, date="2026-11-05", category="Food"):
    conn.execute(
        "INSERT INTO expenses (description, amount, date, category) VALUES (?, ?, ?, ?)",
        (description, amount, date, category),
    )


def test_tables_and_index_are_created(conn):
    names = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master")}
    assert "expenses" in names
    assert "idx_expenses_date" in names


def test_valid_row_is_saved(conn):
    insert(conn)
    conn.commit()
    row = conn.execute("SELECT * FROM expenses").fetchone()
    assert dict(row) == {
        "id": 1, "description": "Lunch", "amount": 12.5, "date": "2026-11-05", "category": "Food",
    }


@pytest.mark.parametrize("fields", [
    {"amount": 0},
    {"amount": -1},
    {"description": "   "},
    {"date": "05/11/2026"},
    {"date": "2026-1-5"},
])
def test_check_constraints_reject_bad_rows(conn, fields):
    with pytest.raises(sqlite3.IntegrityError):
        insert(conn, **fields)


def test_ids_are_not_reused_after_delete(conn):
    insert(conn)
    insert(conn)
    conn.execute("DELETE FROM expenses WHERE id = 2")
    insert(conn)
    ids = [row["id"] for row in conn.execute("SELECT id FROM expenses ORDER BY id")]
    assert ids == [1, 3]


def test_init_db_twice_keeps_data(app, conn):
    insert(conn)
    conn.commit()
    init_db(conn)
    init_db(conn)
    assert conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0] == 1


def test_init_db_command(app):
    result = app.test_cli_runner().invoke(args=["init-db"])
    assert "Database is ready." in result.output


def test_same_connection_within_a_request(app):
    with app.app_context():
        assert get_db() is get_db()


def test_connection_is_closed_after_request(app):
    with app.app_context():
        conn = get_db()
        assert "db" in g
    # using a closed connection raises an error
    with pytest.raises(sqlite3.ProgrammingError):
        conn.execute("SELECT 1")
