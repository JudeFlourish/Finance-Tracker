"""create the users table

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-27

User accounts (US-10). Nothing is linked to a user yet; user_id on expenses,
income and budgets comes with US-12.
"""
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        # NOCASE: "Ann@Mail.com" and "ann@mail.com" count as the same email
        sa.Column("email", sa.Text(collation="NOCASE"), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
        sqlite_autoincrement=True,
    )


def downgrade():
    op.drop_table("users")
