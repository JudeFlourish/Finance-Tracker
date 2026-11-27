from sqlalchemy import Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..models import Entry, entry_checks, not_blank


class Expense(Entry):
    __tablename__ = "expenses"
    __table_args__ = (
        *entry_checks(),
        not_blank("description"),
        # filtering and sorting by date is the most common query
        Index("idx_expenses_date", "date"),
        # AUTOINCREMENT: an id is never used again, even after a delete
        {"sqlite_autoincrement": True},
    )

    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(Text)
