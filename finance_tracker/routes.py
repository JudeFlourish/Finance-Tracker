# Expense routes
# simple finance tracker, I made it to learn backend with Python (Flask)

import csv
import io
import json
from datetime import date

from flask import Blueprint, current_app, render_template, request, redirect, url_for, Response

from .categories import CATEGORIES, COLORS
from .validation import ValidationError, parse_amount, parse_category, parse_date, parse_text

bp = Blueprint("expenses", __name__)


def data_file():
    # all expenses are saved in this file, no database for now
    # the path comes from the config so tests can use their own file
    return current_app.config["DATA_FILE"]


def load_expenses():
    # if the file is not created yet we just start with empty list
    try:
        with open(data_file(), "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_expenses(expenses):
    with open(data_file(), "w") as f:
        json.dump(expenses, f, indent=4)


def filter_expenses(expenses, start, end, category):
    result = []
    for e in expenses:
        # dates are saved like "2025-09-25" so I can compare them as strings
        if start and e["date"] < start:
            continue
        if end and e["date"] > end:
            continue
        if category != "All" and e["category"] != category:
            continue
        result.append(e)
    return result


def get_total(expenses):
    total = 0
    for e in expenses:
        total += e["amount"]
    return total


def get_filters():
    # filters come from the url, for example /?start=2025-09-01&category=Food
    start = request.args.get("start", "")
    end = request.args.get("end", "")
    category = request.args.get("category", "All")
    return start, end, category


def build_dashboard_context(expenses, start="", end="", category="All"):
    filtered = filter_expenses(expenses, start, end, category)
    filtered.sort(key=lambda e: e["date"], reverse=True)  # newest first

    total = get_total(filtered)

    # data for the charts, the drawing itself is done in script.js
    # pie chart: total per category (same order as categories list)
    pie_labels = []
    pie_values = []
    pie_colors = []
    for c in CATEGORIES:
        amount = 0
        for e in filtered:
            if e["category"] == c:
                amount += e["amount"]
        if amount > 0:
            pie_labels.append(c)
            pie_values.append(amount)
            pie_colors.append(COLORS[c])

    # bar chart: total per day
    by_date = {}
    for e in filtered:
        if e["date"] in by_date:
            by_date[e["date"]] += e["amount"]
        else:
            by_date[e["date"]] = e["amount"]
    bar_labels = sorted(by_date)
    bar_values = []
    for day in bar_labels:
        bar_values.append(by_date[day])

    chart_data = {
        "pie_labels": pie_labels,
        "pie_values": pie_values,
        "pie_colors": pie_colors,
        "bar_labels": bar_labels,
        "bar_values": bar_values,
    }

    return {
        "expenses": filtered,
        "total": total,
        "categories": CATEGORIES,
        "chart_data": chart_data,
        "start": start,
        "end": end,
        "category": category,
        "today": str(date.today()),
    }


@bp.route("/")
def index():
    start, end, category = get_filters()
    error = request.args.get("error", "")

    context = build_dashboard_context(load_expenses(), start, end, category)
    context["error"] = error

    return render_template("index.html", **context)


@bp.route("/edit/<int:expense_id>")
def edit_expense(expense_id):
    expenses = load_expenses()
    expense = next((e for e in expenses if e["id"] == expense_id), None)
    if expense is None:
        return redirect(url_for("expenses.index"))

    start, end, category = get_filters()
    context = build_dashboard_context(expenses, start, end, category)
    context["edit_expense"] = expense
    context["error"] = ""

    return render_template("index.html", **context)


def read_expense_form():
    # checking inputs again on the server
    # (the browser checks too but someone can skip that)
    # raises ValidationError with a message for the user
    return {
        "description": parse_text(request.form.get("description"), "Please write a description"),
        "amount": parse_amount(request.form.get("amount")),
        "date": parse_date(request.form.get("date")),
        "category": parse_category(request.form.get("category")),
    }


@bp.route("/update/<int:expense_id>", methods=["POST"])
def update_expense(expense_id):
    try:
        fields = read_expense_form()
    except ValidationError as e:
        return redirect(url_for("expenses.index", error=str(e)))

    expenses = load_expenses()
    for e in expenses:
        if e["id"] == expense_id:
            e.update(fields)
            break
    save_expenses(expenses)

    return redirect(url_for("expenses.index"))


@bp.route("/add", methods=["POST"])
def add_expense():
    try:
        fields = read_expense_form()
    except ValidationError as e:
        return redirect(url_for("expenses.index", error=str(e)))

    expenses = load_expenses()

    # at first I used len(expenses) + 1 for id but after deleting
    # two expenses could get the same id, so now I take biggest id + 1
    new_id = 1
    for e in expenses:
        if e["id"] >= new_id:
            new_id = e["id"] + 1

    expense = {"id": new_id, **fields}
    expenses.append(expense)
    save_expenses(expenses)

    return redirect(url_for("expenses.index"))


@bp.route("/delete/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    expenses = load_expenses()
    new_list = []
    for e in expenses:
        if e["id"] != expense_id:
            new_list.append(e)
    save_expenses(new_list)
    return redirect(url_for("expenses.index"))


@bp.route("/export")
def export_csv():
    # exports only what you see with the current filter
    start, end, category = get_filters()
    filtered = filter_expenses(load_expenses(), start, end, category)
    filtered.sort(key=lambda e: e["date"])

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Description", "Category", "Amount"])
    for e in filtered:
        writer.writerow([e["date"], e["description"], e["category"], f"{e['amount']:.2f}"])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=expenses.csv"},
    )

