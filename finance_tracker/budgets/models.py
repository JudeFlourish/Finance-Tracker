from sqlalchemy import CheckConstraint, Float, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import db


# not an Entry: a budget is a limit per month, it has no date of its own.
# No link to expenses either: removing a budget never touches any expense.
class Budget(db.Model):
    __tablename__ = "budgets"
    __table_args__ = (
        CheckConstraint("monthly_limit > 0", name="limit_positive"),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # unique: one monthly spending limit per category (US-05)
    category: Mapped[str] = mapped_column(Text, unique=True)
    monthly_limit: Mapped[float] = mapped_column(Float)
