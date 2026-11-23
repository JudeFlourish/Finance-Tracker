# Finance Tracker

A web-based finance tracker built with **Python and Flask**. Users can log expenses and income and set a monthly budget per category. Expenses can be filtered by date range and category, shown in charts, and exported to CSV.

The goal of this project was to learn server-side web development: routing, handling forms, rendering templates, saving data, and validating input.

## Features

- **Add, edit and delete expenses** with a description, amount, date and category
- **Home dashboard:** pick a month and see its income, spending and balance (income − spending), quick-add an expense or income, recent activity and charts
- **Income:** record money coming in (source, amount, date), see the total, delete entries; kept apart from expenses
- **Monthly budgets:** set, change or remove a spending limit for any category
- **Filter** by start date, end date and category
- **Running total** for the current filter
- **Charts:** spending by category (pie) and spending over time (bar)
- **CSV export** of exactly what the current filter shows
- **Server-side validation** of every form field (required, numeric, positive, known category)
- **Responsive dark UI** that stacks into a single column on small screens

## Tech Stack

| Layer    | Technology                          |
|----------|-------------------------------------|
| Backend  | Python 3, Flask                     |
| Frontend | HTML (Jinja2 templates), CSS, JavaScript |
| Charts   | Chart.js                            |
| Storage  | SQLite                              |
| Tooling  | uv (dependencies), pytest (tests)   |

## Getting Started

### Prerequisites

- [uv](https://docs.astral.sh/uv/). It installs the right Python version (3.10+) for you if needed.

| OS | Install uv |
|---|---|
| Windows (PowerShell) | `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` |
| macOS / Linux / WSL | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

### Installation

```bash
git clone https://github.com/firdavz/python-finance-tracker.git
cd python-finance-tracker

uv sync            # creates .venv and installs the exact versions from uv.lock
cp .env.example .env   # then put your own SECRET_KEY in .env
```

### Run

```bash
uv run python financeapp.py
# or: uv run flask --app financeapp run --debug
```

Then open **http://127.0.0.1:5000** in your browser.

Expenses are saved in a SQLite database (`instance/finance.db`), which is created
with its tables on startup. To create it without starting the server:

```bash
uv run flask --app financeapp init-db
```

### Import old data

Earlier versions saved expenses in `expenses.json`. To move them into the database:

```bash
uv run flask --app financeapp import-json expenses.json
```

Every expense is checked first with the same rules as the add form. If any one is
invalid, or the file is missing or not valid JSON, nothing is imported. Old ids are
not kept; the database gives each expense a new one. Run it only once, because
running it again adds the same expenses a second time.

### Configuration

Settings are read from environment variables, or from a `.env` file in the project folder.
`.env` is git-ignored; `.env.example` shows every setting with placeholder values. All are optional.

| Variable     | Default                           | Purpose                     |
|--------------|-----------------------------------|-----------------------------|
| `SECRET_KEY` | random key made at startup        | Flask secret key            |
| `DATABASE`   | `instance/finance.db`             | SQLite database file        |

### Tests

```bash
uv run pytest
```

Each test uses its own temporary database, so your real data is never touched.

## Contributing

- **One branch per card**, named `feature/<card-id>-short-name` (for example `feature/US-03-edit-expense`), created from an up-to-date `main`.
- **Tests must pass before merge.** Run `uv run pytest` before opening a pull request. No pull request is merged into `main` while a test is failing.
- **Add tests with every change**, one test file per feature (`tests/test_<feature>.py`).
- **Every pull request is reviewed** and approved by another team member before it is merged.
- **Follow the structure:** code is grouped by feature (`expenses/`, `income/`, `budgets/`, `dashboard/`); routes handle HTTP only, rules go in `validation.py` and SQL in `repository.py`; features don't import each other, except the dashboard reading repositories.

## Project Structure

```
python-finance-tracker/
├── financeapp.py            # entry point: create_app() and run
├── finance_tracker/
│   ├── __init__.py          # create_app(): config, database, one blueprint per feature
│   ├── config.py            # settings from environment variables
│   ├── db.py                # SQLite connection per request, init-db command
│   ├── schema.sql           # tables, CHECK constraints, indexes
│   ├── categories.py        # category list and chart colours
│   ├── models.py            # Entry base class (shared by expenses and income)
│   ├── validation.py        # ValidationError + shared field parsers
│   ├── web.py               # redirect_back(), nav bar links, 404 page
│   ├── charts.py            # chart data (totals per category and per day), expenses only
│   ├── importer.py          # flask import-json command (old expenses.json)
│   ├── expenses/
│   │   ├── models.py        # Expense
│   │   ├── filters.py       # ExpenseFilter (date range and category from the url)
│   │   ├── validation.py    # validate_expense()
│   │   ├── repository.py    # ExpenseRepository (SQL only)
│   │   └── routes.py        # list, add, edit, delete, export
│   ├── income/
│   │   ├── models.py        # Income (an Entry, like Expense)
│   │   ├── validation.py    # validate_income()
│   │   ├── repository.py    # IncomeRepository (SQL only)
│   │   └── routes.py        # income page: list, total, add, delete
│   ├── budgets/
│   │   ├── models.py        # Budget
│   │   ├── validation.py    # validate_budget()
│   │   ├── repository.py    # BudgetRepository (SQL only, one budget per category)
│   │   └── routes.py        # budgets page: set, change, remove
│   ├── dashboard/
│   │   ├── stats.py         # Month, parse_month(), recent_transactions() (plain functions)
│   │   └── routes.py        # home page; only reads the other features' repositories
│   ├── templates/
│   │   ├── base.html        # shared layout: nav bar, flash messages
│   │   ├── 404.html         # page not found, in the app's layout
│   │   ├── _forms.html      # expense and income form fields, shared by every form
│   │   ├── dashboard/
│   │   │   └── home.html    # month totals, balance, quick add, recent activity, charts
│   │   ├── expenses/
│   │   │   ├── list.html    # expenses page (filters, add form, list, charts)
│   │   │   └── edit.html    # edit one expense
│   │   ├── income/
│   │   │   └── list.html    # add form, income list and total
│   │   └── budgets/
│   │       └── list.html    # one row per category: set, change or remove its budget
│   └── static/
│       ├── style.css        # Layout and dark theme
│       ├── script.js        # chart rendering (expenses page and dashboard)
│       └── confirm.js       # asks before delete / remove (every page)
├── tests/
│   ├── conftest.py          # app, client and conn fixtures (temporary database)
│   ├── test_app_factory.py
│   ├── test_budgets.py      # budgets page, repository, rules and validation
│   ├── test_dashboard.py    # months, balance, recent activity, quick add
│   ├── test_db.py           # schema, constraints, connection handling
│   ├── test_expense_repository.py  # repository, filters, validate_expense
│   ├── test_expenses.py     # routes, filters, export, charts
│   ├── test_importer.py     # import-json: good, bad and partly bad files
│   ├── test_income.py       # income page, repository, rules and validation
│   ├── test_performance.py  # expenses page and dashboard under 2 s with 1,000 expenses
│   └── test_validation.py   # shared parsers and redirect_back
├── pyproject.toml           # dependencies
└── uv.lock                  # pinned versions
```

## Routes

| Method | Route                   | Description                                                        |
|--------|-------------------------|--------------------------------------------------------------------|
| GET    | `/`                     | Home dashboard for a month. Optional query param: `month=YYYY-MM`  |
| GET    | `/expenses/`            | Expenses page. Optional query params: `start`, `end`, `category`   |
| POST   | `/expenses/add`         | Validates the form and creates an expense                          |
| GET    | `/expenses/<id>/edit`   | Edit page, filled in with the expense's current values             |
| POST   | `/expenses/<id>/edit`   | Validates and saves; on an error shows the form again as typed     |
| POST   | `/expenses/delete/<id>` | Deletes an expense by id                                           |
| GET    | `/expenses/export`      | Downloads filtered expenses as CSV (same query params as the page) |
| GET    | `/income/`              | Income page: add form, income list (newest first) and total        |
| POST   | `/income/`              | Validates the form and adds income                                 |
| POST   | `/income/<id>/delete`   | Deletes an income entry                                            |
| GET    | `/budgets/`             | Budgets page: every category with its monthly limit                |
| POST   | `/budgets/`             | Sets a category's budget, or changes it if it already has one      |
| POST   | `/budgets/<id>/delete`  | Removes a budget (its category's expenses are kept)                |

## Data Model

Each expense is one row in the `expenses` table (see `finance_tracker/schema.sql`):

| Column        | Type    | Rule                                   |
|---------------|---------|----------------------------------------|
| `id`          | INTEGER | primary key, never reused              |
| `description` | TEXT    | not blank                              |
| `amount`      | REAL    | greater than 0                         |
| `date`        | TEXT    | `YYYY-MM-DD`                           |
| `category`    | TEXT    | one of the categories below            |

Each monthly budget is one row in the `budgets` table:

| Column          | Type    | Rule                                   |
|-----------------|---------|----------------------------------------|
| `id`            | INTEGER | primary key, never reused              |
| `category`      | TEXT    | one of the categories below, unique (one budget per category) |
| `monthly_limit` | REAL    | greater than 0                         |

Budgets are not linked to expenses, so removing a budget never deletes any expense.

Each income entry is one row in the `income` table, kept apart from expenses:

| Column   | Type    | Rule                                   |
|----------|---------|----------------------------------------|
| `id`     | INTEGER | primary key, never reused              |
| `source` | TEXT    | not blank (e.g. "Salary")              |
| `amount` | REAL    | greater than 0                         |
| `date`   | TEXT    | `YYYY-MM-DD`                           |

New tables are created on startup, so an existing database gets them without losing data.

Categories: Food, Transport, Rent, Utilities, Health, Entertainment, Education, Business, Other.

## Design Decisions

- **Post/Redirect/Get.** Every POST request ends with a redirect and a one-time flash message. Refreshing the page after adding, editing or deleting never resubmits the form.
- **Back to the same view.** Forms send the current filtered page in a hidden `next` field, and only paths on this site are accepted.
- **Filters live in the URL.** Filtering uses GET query parameters, so any filtered view can be bookmarked or shared. The CSV export reuses the same parameters, so it always matches what is on screen.
- **ISO dates.** Dates are stored as `YYYY-MM-DD` strings, so date-range filtering is a simple string comparison with no parsing.
- **Validation on the server.** The HTML form checks input in the browser, but the backend validates everything again, because requests can be sent without using the form.
- **Safe ids.** SQLite `AUTOINCREMENT` ids are never reused, even after deletions. Unknown ids return 404.
- **Layers.** Routes only handle HTTP; validation and SQL live in their own modules (`validation.py`, `repository.py`).
- **Safe output and queries.** Jinja2 escapes user input when rendering, chart data is passed to JavaScript with `tojson`, and SQL always uses `?` parameters.
- **Charts are prepared in Python.** Totals per category and per day are calculated on the backend; JavaScript only draws them.
- **Fast with real amounts of data.** With 1,000 expenses the dashboard and the expenses page are each served in well under 0.1 seconds (the target is under 2 seconds). Filtering by date uses an index; `tests/test_performance.py` checks the target on every test run.

## Known Limitations

This is a learning project, and these trade-offs were made on purpose:

- **No login.** All data is shared by anyone who opens the app.
- **No CSRF protection** on the forms.
- **Debug mode is on** in `financeapp.py`. It must be turned off for production.
- **Charts need internet**, because Chart.js is loaded from a CDN.

## Roadmap

- [x] Move storage to SQLite
- [x] Add unit tests with pytest
- [x] Edit existing expenses
- [ ] Track income as well as expenses
- [ ] User accounts and CSRF protection (Flask-Login, Flask-WTF)
# Finance-Tracker
