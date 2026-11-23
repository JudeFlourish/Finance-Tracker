from ..validation import parse_amount, parse_category
from .models import Budget


def validate_budget(form):
    """Turn raw form values into a Budget, or raise ValidationError."""
    return Budget(
        # a budget for a category that doesn't exist makes no sense, so strict
        category=parse_category(form.get("category"), strict=True),
        monthly_limit=parse_amount(form.get("monthly_limit"), field="Budget"),
    )
