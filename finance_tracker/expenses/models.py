from dataclasses import dataclass

from ..models import Entry


@dataclass(kw_only=True)
class Expense(Entry):
    description: str
    category: str
