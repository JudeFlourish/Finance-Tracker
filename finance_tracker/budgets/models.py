from dataclasses import dataclass


# not an Entry: a budget is a limit per month, it has no date of its own
@dataclass(kw_only=True)
class Budget:
    category: str
    monthly_limit: float
    id: int | None = None
