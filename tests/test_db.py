import sqlite3

import pytest
from flask import g
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from finance_tracker import create_app
from finance_tracker.budgets.models import Budget
from finance_tracker.database import create_tables, db
from finance_tracker.db import get_db
from finance_tracker.expenses.models import Expense
from finance_tracker.income.models import Income


def insert(conn, description="Lunch", amount=12.5, date="2026-11-05", category="Food"):
    conn.execute(
        "INSERT INTO expenses (description, amount, date, category) VALUES (?, ?, ?, ?)",
        (description, amount, date, category),
    )


# tables made by the SQLAlchemy models

def test_tables_and_indexes_are_created(app):
    with app.app_context():
        inspector = inspect(db.engine)
        assert set(inspector.get_table_names()) >= {"expenses", "income", "budgets"}
        assert [i["name"] for i in inspector.get_indexes("expenses")] == ["idx_expenses_date"]
        assert [i["name"] for i in inspector.get_indexes("income")] == ["idx_income_date"]


def test_columns_match_the_old_schema(app):
    # same column names as schema.sql had, so databases made before SQLAlchemy still work
    with app.app_context():
        inspector = inspect(db.engine)
        columns = {t: [c["name"] for c in inspector.get_columns(t)] for t in ("expenses", "income", "budgets")}
    assert columns == {
        "expenses": ["id", "description", "category", "amount", "date"],
        "income": ["id", "source", "amount", "date"],
        "budgets": ["id", "category", "monthly_limit"],
    }


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


def test_create_tables_twice_keeps_data(app, conn):
    insert(conn)
    conn.commit()
    with app.app_context():
        create_tables()
        create_tables()
    assert conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0] == 1


def test_init_db_command(app):
    result = app.test_cli_runner().invoke(args=["init-db"])
    assert "Database is ready." in result.output


def test_database_url_comes_from_database_path(app, tmp_path):
    assert app.config["SQLALCHEMY_DATABASE_URI"] == f"sqlite:///{tmp_path / 'test.db'}"


def test_database_made_before_sqlalchemy_still_works(tmp_path):
    # an expenses table exactly as schema.sql made it, with data in it
    path = tmp_path / "old.db"
    old = sqlite3.connect(path)
    old.execute(
        "CREATE TABLE expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "description TEXT NOT NULL CHECK (length(trim(description)) > 0), "
        "amount REAL NOT NULL CHECK (amount > 0), date TEXT NOT NULL, category TEXT NOT NULL)"
    )
    old.execute("INSERT INTO expenses (description, amount, date, category) VALUES ('Lunch', 12.5, '2026-11-01', 'Food')")
    old.commit()
    old.close()

    app = create_app({"TESTING": True, "DATABASE": str(path)})
    with app.app_context():
        [expense] = db.session.scalars(db.select(Expense)).all()
        assert expense.to_dict() == {
            "id": 1, "description": "Lunch", "amount": 12.5, "date": "2026-11-01", "category": "Food",
        }
        # the missing tables were added next to it
        assert {"income", "budgets"} <= set(inspect(db.engine).get_table_names())


# the models through the SQLAlchemy session

def test_session_saves_and_reads_each_model(app):
    with app.app_context():
        db.session.add_all([
            Expense(description="Lunch", amount=12.5, date="2026-11-05", category="Food"),
            Income(source="Salary", amount=1500, date="2026-11-01"),
            Budget(category="Food", monthly_limit=300),
        ])
        db.session.commit()
        assert db.session.get(Expense, 1).description == "Lunch"
        assert db.session.get(Income, 1).source == "Salary"
        assert db.session.get(Budget, 1).monthly_limit == 300


@pytest.mark.parametrize("model", [
    Expense(description="Lunch", amount=0, date="2026-11-05", category="Food"),
    Expense(description=" ", amount=1, date="2026-11-05", category="Food"),
    Expense(description="Lunch", amount=1, date="5 Nov", category="Food"),
    Income(source="Salary", amount=-5, date="2026-11-01"),
    Income(source="", amount=5, date="2026-11-01"),
    Budget(category="Food", monthly_limit=0),
], ids=repr)
def test_model_rules_are_enforced_by_the_database(app, model):
    with app.app_context():
        db.session.add(model)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
        assert db.session.scalars(db.select(type(model))).all() == []


def test_one_budget_per_category(app):
    with app.app_context():
        db.session.add(Budget(category="Food", monthly_limit=300))
        db.session.commit()
        db.session.add(Budget(category="Food", monthly_limit=100))
        with pytest.raises(IntegrityError):
            db.session.commit()


def test_repr_shows_the_values():
    assert repr(Budget(category="Food", monthly_limit=300)) == "Budget(id=None, category='Food', monthly_limit=300)"


# the plain sqlite3 connection (used by the repositories for now)

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
