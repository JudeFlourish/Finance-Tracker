from sqlalchemy import Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..models import Entry, entry_checks, not_blank


# money coming in (US-04), kept apart from expenses
class Income(Entry):
    __tablename__ = "income"
    __table_args__ = (
        *entry_checks(),
        not_blank("source"),
        Index("idx_income_date", "date"),
        {"sqlite_autoincrement": True},
    )

    source: Mapped[str] = mapped_column(Text)  # where the money came from, e.g. "Salary"
