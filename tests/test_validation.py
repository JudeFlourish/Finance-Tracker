from datetime import date

import pytest

from finance_tracker.models import Entry, total
from finance_tracker.validation import (
    ValidationError, parse_amount, parse_category, parse_date, parse_text,
)
from finance_tracker.web import is_safe_path, redirect_back


# parse_text

def test_parse_text_trims_spaces():
    assert parse_text("  Lunch  ", "msg") == "Lunch"


@pytest.mark.parametrize("value", ["", "   ", None, 123, ["Lunch"]])
def test_parse_text_rejects_blank(value):
    with pytest.raises(ValidationError, match="Please write a description"):
        parse_text(value, "Please write a description")


# parse_amount

@pytest.mark.parametrize("value, expected", [("12.5", 12.5), ("3", 3.0), (" 7 ", 7.0), (12.5, 12.5), (3, 3.0)])
def test_parse_amount_accepts_positive_numbers(value, expected):
    assert parse_amount(value) == expected


@pytest.mark.parametrize("value", ["abc", "", None, "12,50", True, False, [1]])
def test_parse_amount_rejects_non_numbers(value):
    with pytest.raises(ValidationError, match="Amount must be a number"):
        parse_amount(value)


@pytest.mark.parametrize("value", ["0", "-5", "nan", "inf", "-inf"])
def test_parse_amount_rejects_zero_negative_and_special(value):
    with pytest.raises(ValidationError, match="Please enter a positive number"):
        parse_amount(value)


# parse_date

def test_parse_date_keeps_valid_date():
    assert parse_date("2026-11-05") == "2026-11-05"


@pytest.mark.parametrize("value", ["", "  ", None])
def test_parse_date_blank_means_today(value):
    assert parse_date(value) == date.today().isoformat()


@pytest.mark.parametrize("value", ["2026-02-30", "2026-13-01", "05/11/2026", "2026-1-5", "yesterday", 20261105, ["2026-11-05"]])
def test_parse_date_rejects_invalid(value):
    with pytest.raises(ValidationError, match="Please enter a valid date"):
        parse_date(value)


# parse_category

def test_parse_category_keeps_known_category():
    assert parse_category("Food") == "Food"


@pytest.mark.parametrize("value", ["Pizza", "", None, "food"])
def test_parse_category_unknown_becomes_other(value):
    assert parse_category(value) == "Other"


def test_parse_category_strict_keeps_known_category():
    assert parse_category("Food", strict=True) == "Food"


@pytest.mark.parametrize("value", ["Pizza", "", None, "food"])
def test_parse_category_strict_refuses_unknown(value):
    with pytest.raises(ValidationError, match="Please choose a category"):
        parse_category(value, strict=True)


def test_parse_amount_uses_field_name():
    with pytest.raises(ValidationError, match="Budget must be a number"):
        parse_amount("abc", field="Budget")


# models

def test_total_adds_up_entries():
    entries = [Entry(amount=10, date="2026-11-01"), Entry(amount=2.5, date="2026-11-02")]
    assert total(entries) == 12.5
    assert total([]) == 0


# web

@pytest.mark.parametrize("target", ["/", "/edit/3", "/?category=Food"])
def test_safe_paths(target):
    assert is_safe_path(target)


@pytest.mark.parametrize("target", ["", "https://evil.com", "//evil.com", "/\\evil.com", "edit/3"])
def test_unsafe_paths(target):
    assert not is_safe_path(target)


def test_redirect_back_uses_next(app):
    with app.test_request_context("/add", method="POST", data={"next": "/?category=Food"}):
        assert redirect_back("expenses.index").location == "/?category=Food"


def test_redirect_back_refuses_other_sites(app):
    with app.test_request_context("/add", method="POST", data={"next": "//evil.com"}):
        assert redirect_back("expenses.index").location == "/expenses/"
