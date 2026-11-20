"""Spending categories, shared by expenses, budgets and the dashboard."""

CATEGORIES = ["Food", "Transport", "Rent", "Utilities", "Health",
              "Entertainment", "Education", "Business", "Other"]

# used when a form sends a category we don't know
DEFAULT_CATEGORY = "Other"

# colors for the pie chart, picked by hand
COLORS = {
    "Food": "#36a2eb",
    "Transport": "#ff6384",
    "Rent": "#9966ff",
    "Utilities": "#ff9f40",
    "Health": "#4bc0c0",
    "Entertainment": "#ffcd56",
    "Education": "#a3e635",
    "Business": "#f472b6",
    "Other": "#94a3b8",
}
