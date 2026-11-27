"""create the expenses, income and budgets tables

Revision ID: 0001
Revises:
Create Date: 2026-11-27

The first migration: the three tables as the models define them.

A database made before migrations existed (by schema.sql or create_all) already
has these tables, but without constraint names. Those tables are rebuilt into
exactly the same shape as a new database, keeping every row, so later
migrations work the same on every teammate's database.
"""
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

DATE_FORMAT = "date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'"


# each function creates its table under any name, so a rebuild can make a copy first.
# Constraint names always use the real table name, so they are right after the rename;
# op.f() marks a name as final, so the naming convention doesn't add the copy's name to it.

def create_expenses(name="expenses"):
    op.create_table(
        name,
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("date", sa.Text(), nullable=False),
        sa.CheckConstraint(DATE_FORMAT, name=op.f("ck_expenses_date_format")),
        sa.CheckConstraint("amount > 0", name=op.f("ck_expenses_amount_positive")),
        sa.CheckConstraint("length(trim(description)) > 0", name=op.f("ck_expenses_description_not_blank")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_expenses")),
        sqlite_autoincrement=True,
    )


def create_income(name="income"):
    op.create_table(
        name,
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("date", sa.Text(), nullable=False),
        sa.CheckConstraint(DATE_FORMAT, name=op.f("ck_income_date_format")),
        sa.CheckConstraint("amount > 0", name=op.f("ck_income_amount_positive")),
        sa.CheckConstraint("length(trim(source)) > 0", name=op.f("ck_income_source_not_blank")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_income")),
        sqlite_autoincrement=True,
    )


def create_budgets(name="budgets"):
    op.create_table(
        name,
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("monthly_limit", sa.Float(), nullable=False),
        sa.CheckConstraint("monthly_limit > 0", name=op.f("ck_budgets_limit_positive")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_budgets")),
        sa.UniqueConstraint("category", name=op.f("uq_budgets_category")),
        sqlite_autoincrement=True,
    )


# table name, how to create it, its columns, its date index (if any)
TABLES = [
    ("expenses", create_expenses, ["id", "description", "category", "amount", "date"], "idx_expenses_date"),
    ("income", create_income, ["id", "source", "amount", "date"], "idx_income_date"),
    ("budgets", create_budgets, ["id", "category", "monthly_limit"], None),
]

# what a row must pass to fit the new table (the same rules as above, in SQL)
RULES = {
    "expenses": f"amount > 0 AND length(trim(description)) > 0 AND {DATE_FORMAT} AND category IS NOT NULL",
    "income": f"amount > 0 AND length(trim(source)) > 0 AND {DATE_FORMAT}",
    "budgets": "monthly_limit > 0 AND category IS NOT NULL AND category NOT IN "
               "(SELECT category FROM budgets GROUP BY category HAVING count(*) > 1)",
}


def check_old_rows(name):
    """Stop before anything is changed if an old row would not fit the new table.

    The check runs before any table is touched: SQLite can't always undo a
    half-done change to its tables, so the upgrade must not fail halfway.
    """
    # COALESCE: a missing (NULL) value makes the rule NULL, which counts as broken
    bad = op.get_bind().execute(
        sa.text(f"SELECT id FROM {name} WHERE NOT COALESCE({RULES[name]}, 0) ORDER BY id")
    ).scalars().all()
    if bad:
        ids = ", ".join(str(i) for i in bad)
        raise RuntimeError(
            f"Can't upgrade the {name} table: rows with id {ids} break its rules "
            "(an amount or limit of 0 or less, an empty text, a wrong date, or a second budget "
            "for the same category). Fix or delete them, then run the upgrade again."
        )


def rebuild(name, create, columns):
    """Replace an old table with the new definition, keeping its rows and ids."""
    bind = op.get_bind()
    new = f"_new_{name}"
    # AUTOINCREMENT remembers the highest id ever used, even if that row was
    # deleted; keep it, so an old id is never given out again
    last_id = bind.execute(
        sa.text("SELECT seq FROM sqlite_sequence WHERE name = :name"), {"name": name}
    ).scalar()

    create(new)
    names = ", ".join(columns)
    op.execute(f"INSERT INTO {new} ({names}) SELECT {names} FROM {name}")
    op.drop_table(name)  # also drops its old index
    op.rename_table(new, name)

    if last_id is not None:
        bind.execute(sa.text("DELETE FROM sqlite_sequence WHERE name = :name"), {"name": name})
        bind.execute(
            sa.text("INSERT INTO sqlite_sequence (name, seq) VALUES (:name, :seq)"),
            {"name": name, "seq": last_id},
        )


def upgrade():
    existing = set(sa.inspect(op.get_bind()).get_table_names())
    # check every old table first, so either all of them are upgraded or none is
    for name, *_ in TABLES:
        if name in existing:
            check_old_rows(name)

    for name, create, columns, index in TABLES:
        if name in existing:
            rebuild(name, create, columns)
        else:
            create()
        if index:
            op.create_index(index, name, ["date"])


def downgrade():
    # back to an empty database: this deletes all the data
    op.drop_index("idx_income_date", table_name="income")
    op.drop_index("idx_expenses_date", table_name="expenses")
    op.drop_table("budgets")
    op.drop_table("income")
    op.drop_table("expenses")
