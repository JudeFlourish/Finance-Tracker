"""Data for the charts. The drawing itself is done in script.js.

Plain function, no Flask or database, so it can be tested on its own.
"""
from ..categories import CATEGORIES, COLORS


def chart_data(expenses):
    # pie chart: total per category, same order as the categories list,
    # categories with nothing spent are left out
    by_category = {}
    for e in expenses:
        by_category[e.category] = by_category.get(e.category, 0) + e.amount
    pie_labels = [c for c in CATEGORIES if by_category.get(c, 0) > 0]

    # bar chart: total per day, oldest day first
    by_date = {}
    for e in expenses:
        by_date[e.date] = by_date.get(e.date, 0) + e.amount
    bar_labels = sorted(by_date)

    return {
        "pie_labels": pie_labels,
        "pie_values": [by_category[c] for c in pie_labels],
        "pie_colors": [COLORS[c] for c in pie_labels],
        "bar_labels": bar_labels,
        "bar_values": [by_date[d] for d in bar_labels],
    }
