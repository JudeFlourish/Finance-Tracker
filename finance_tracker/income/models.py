from dataclasses import dataclass

from ..models import Entry


@dataclass(kw_only=True)
class Income(Entry):
    source: str  # where the money came from, e.g. "Salary"
