# Finance Tracker

A web-based expense tracker built with **Python and Flask**. Users can log expenses, filter them by date range and category, see spending in charts, and export the filtered data to CSV.

The goal of this project was to learn server-side web development: routing, handling forms, rendering templates, saving data, and validating input.

## Features

- **Add and delete expenses** with a description, amount, date and category
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
| Storage  | JSON file                           |
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

`expenses.json` is created automatically the first time you add an expense.

The SQLite database (`instance/finance.db`) and its tables are also created on startup.
To create them without starting the server:

```bash
uv run flask --app financeapp init-db
```

### Configuration

Settings are read from environment variables, or from a `.env` file in the project folder.
`.env` is git-ignored; `.env.example` shows every setting with placeholder values. All are optional.

| Variable     | Default                           | Purpose                     |
|--------------|-----------------------------------|-----------------------------|
| `SECRET_KEY` | random key made at startup        | Flask secret key            |
| `DATABASE`   | `instance/finance.db`             | SQLite database file        |
| `DATA_FILE`  | `expenses.json` in project folder | Where expenses are saved    |

### Tests

```bash
uv run pytest
```

Each test uses its own temporary database and data file, so your real data is never touched.

## Project Structure

```
python-finance-tracker/
├── financeapp.py            # entry point: create_app() and run
├── finance_tracker/
│   ├── __init__.py          # create_app(): config, database and routes
│   ├── config.py            # settings from environment variables
│   ├── db.py                # SQLite connection per request, init-db command
│   ├── schema.sql           # tables, CHECK constraints, indexes
│   ├── categories.py        # category list and chart colours
│   ├── models.py            # Entry base class (shared by expenses and income)
│   ├── validation.py        # ValidationError + shared field parsers
│   ├── web.py               # redirect_back(): safe return to the previous page
│   ├── routes.py            # routes, persistence, chart data
│   ├── expenses/
│   │   ├── models.py        # Expense
│   │   ├── filters.py       # ExpenseFilter (date range and category from the url)
│   │   ├── validation.py    # validate_expense()
│   │   └── repository.py    # ExpenseRepository (SQL only)
│   ├── templates/
│   │   └── index.html       # Dashboard (Jinja2 template)
│   └── static/
│       ├── style.css        # Layout and dark theme
│       └── script.js        # Chart rendering and delete confirmation
├── tests/
│   ├── conftest.py          # app, client and conn fixtures (temporary database)
│   ├── test_app_factory.py
│   ├── test_db.py           # schema, constraints, connection handling
│   ├── test_expense_repository.py  # repository, filters, validate_expense
│   ├── test_expenses.py
│   └── test_validation.py   # shared parsers and redirect_back
├── pyproject.toml           # dependencies
└── uv.lock                  # pinned versions
```

## Routes

| Method | Route          | Description                                                      |
|--------|----------------|------------------------------------------------------------------|
| GET    | `/`            | Dashboard. Optional query params: `start`, `end`, `category`     |
| POST   | `/add`         | Validates the form and creates an expense                        |
| POST   | `/delete/<id>` | Deletes an expense by id                                         |
| GET    | `/export`      | Downloads filtered expenses as CSV (same query params as `/`)    |

## Data Model

Each expense is stored as one object in `expenses.json`:

```json
{
    "id": 1,
    "description": "Lunch",
    "amount": 12.5,
    "date": "2025-09-25",
    "category": "Food"
}
```

Categories: Food, Transport, Rent, Utilities, Health, Entertainment, Education, Business, Other.

## Design Decisions

- **Post/Redirect/Get.** Every POST request ends with a redirect. Refreshing the page after adding or deleting never resubmits the form.
- **Filters live in the URL.** Filtering uses GET query parameters, so any filtered view can be bookmarked or shared. The CSV export reuses the same parameters, so it always matches what is on screen.
- **ISO dates.** Dates are stored as `YYYY-MM-DD` strings, so date-range filtering is a simple string comparison with no parsing.
- **Validation on the server.** The HTML form checks input in the browser, but the backend validates everything again, because requests can be sent without using the form.
- **Safe ids.** A new id is the current highest id plus one, not `len(list) + 1`, so ids stay unique after deletions.
- **Safe output.** Jinja2 escapes user input when rendering, and chart data is passed to JavaScript with `tojson`.
- **Charts are prepared in Python.** Totals per category and per day are calculated on the backend; JavaScript only draws them.

## Known Limitations

This is a learning project, and these trade-offs were made on purpose:

- **JSON file storage** is not safe when several requests write at the same time. A real deployment would use a database.
- **No login.** All data is shared by anyone who opens the app.
- **No CSRF protection** on the forms.
- **Debug mode is on** in `financeapp.py`. It must be turned off for production.
- **Charts need internet**, because Chart.js is loaded from a CDN.

## Roadmap

- [ ] Move storage to SQLite
- [ ] Add unit tests with pytest
- [ ] Edit existing expenses
- [ ] Track income as well as expenses
- [ ] User accounts and CSRF protection (Flask-Login, Flask-WTF)
# Finance-Tracker
