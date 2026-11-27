"""Import the old expenses.json into SQLite: `flask --app financeapp import-json expenses.json`."""
import json

import click
from flask.cli import with_appcontext

from .database import db
from .expenses.repository import ExpenseRepository
from .expenses.validation import validate_expense
from .validation import ValidationError


class ImportFailed(Exception):
    pass


def read_expenses(path):
    """Read and check every expense first, so a bad file imports nothing."""
    try:
        with open(path, encoding="utf-8") as f:
            records = json.load(f)
    except FileNotFoundError:
        raise ImportFailed(f"File not found: {path}")
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ImportFailed(f"Not valid JSON: {error}")
    if not isinstance(records, list):
        raise ImportFailed("Expected a list of expenses")

    expenses = []
    for number, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise ImportFailed(f"Expense {number} is not an object")
        try:
            # same rules as the add form; old ids are dropped, the database makes new ones
            expenses.append(validate_expense(record))
        except ValidationError as error:
            raise ImportFailed(f"Expense {number}: {error}")
    return expenses


@click.command("import-json")
@click.argument("path", type=click.Path(dir_okay=False))
@with_appcontext
def import_json_command(path):
    """Import expenses from an old expenses.json file."""
    try:
        expenses = read_expenses(path)
    except ImportFailed as error:
        raise click.ClickException(f"{error}. Nothing was imported.")
    # one transaction: every expense is saved, or none
    count = ExpenseRepository(db.session).add_many(expenses)
    click.echo(f"Imported {count} expenses.")


def init_app(app):
    app.cli.add_command(import_json_command)
