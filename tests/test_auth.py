import sqlite3
from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from finance_tracker.auth.models import User
from finance_tracker.auth.passwords import check_password, hash_password
from finance_tracker.auth.repository import UserRepository
from finance_tracker.auth.validation import parse_email, validate_registration
from finance_tracker.validation import ValidationError


def form(**fields):
    values = {"email": "ann@example.com", "password": "correct horse", "confirm": "correct horse"}
    values.update(fields)
    return values


@pytest.fixture
def repo(session):
    return UserRepository(session)


# passwords

def test_hash_is_not_the_password():
    hashed = hash_password("correct horse")
    assert "correct horse" not in hashed
    assert hashed.startswith("scrypt:")


def test_same_password_gets_a_different_hash_each_time():
    # a random salt, so two users with the same password don't have the same hash
    assert hash_password("correct horse") != hash_password("correct horse")


def test_check_password():
    hashed = hash_password("correct horse")
    assert check_password(hashed, "correct horse") is True
    assert check_password(hashed, "Correct horse") is False
    assert check_password(hashed, "") is False


# validate_registration

def test_validate_registration():
    registration = validate_registration(form(email="  Ann.Lee@Example.COM "))
    assert registration.email == "ann.lee@example.com"
    assert registration.password == "correct horse"


def test_password_spaces_are_kept():
    # spaces count as characters, a password is never trimmed
    assert validate_registration(form(password=" 12345678 ", confirm=" 12345678 ")).password == " 12345678 "


@pytest.mark.parametrize("fields, message", [
    ({"email": ""}, "Please enter your email"),
    ({"email": "   "}, "Please enter your email"),
    ({"email": None}, "Please enter your email"),
    ({"email": "ann"}, "Please enter a valid email address"),
    ({"email": "ann@"}, "Please enter a valid email address"),
    ({"email": "@example.com"}, "Please enter a valid email address"),
    ({"email": "ann@@example.com"}, "Please enter a valid email address"),
    ({"email": "ann example@mail.com"}, "Please enter a valid email address"),
    ({"password": "short", "confirm": "short"}, "Your password needs at least 8 characters"),
    ({"password": "1234567", "confirm": "1234567"}, "Your password needs at least 8 characters"),
    ({"password": None}, "Your password needs at least 8 characters"),
    ({"password": "x" * 129, "confirm": "x" * 129}, "Your password can have at most 128 characters"),
    ({"confirm": "correct horsE"}, "The two passwords don't match"),
    ({"confirm": ""}, "The two passwords don't match"),
])
def test_validate_registration_rejects_bad_forms(fields, message):
    with pytest.raises(ValidationError, match=message):
        validate_registration(form(**fields))


def test_exactly_8_and_128_characters_are_allowed():
    for password in ("x" * 8, "x" * 128):
        assert validate_registration(form(password=password, confirm=password)).password == password


def test_parse_email_does_not_look_the_domain_up():
    # only the format is checked, so it works offline and for any domain
    assert parse_email("someone@no-such-domain-for-sure.example") == "someone@no-such-domain-for-sure.example"


# UserRepository

def test_add_saves_a_hash_and_returns_the_user(repo):
    user = repo.add("ann@example.com", "correct horse")
    assert user.id == 1
    assert user.email == "ann@example.com"
    assert user.password_hash != "correct horse"
    assert check_password(user.password_hash, "correct horse")
    assert isinstance(user.created_at, datetime)


def test_password_is_not_stored_anywhere_in_the_row(repo, app):
    repo.add("ann@example.com", "correct horse")
    conn = sqlite3.connect(app.config["DATABASE"])
    row = conn.execute("SELECT * FROM users").fetchone()
    conn.close()
    assert not any("correct horse" in str(value) for value in row)


def test_get_and_get_by_email(repo):
    user = repo.add("ann@example.com", "correct horse")
    assert repo.get(user.id) is user
    assert repo.get_by_email("ann@example.com") is user
    assert repo.get(99) is None
    assert repo.get_by_email("bob@example.com") is None


def test_get_by_email_ignores_case(repo):
    user = repo.add("ann@example.com", "correct horse")
    assert repo.get_by_email("ANN@Example.com") is user


def test_one_account_per_email_even_in_another_case(repo):
    # the database stops it, even if the route forgot to check
    repo.add("ann@example.com", "correct horse")
    with pytest.raises(IntegrityError):
        repo.add("Ann@Example.com", "another password")
    assert [u.email for u in repo.session.scalars(select(User))] == ["ann@example.com"]
    # and the session still works afterwards
    repo.add("bob@example.com", "correct horse")
    assert [u.email for u in repo.session.scalars(select(User))] == ["ann@example.com", "bob@example.com"]


# User model

def test_user_works_with_flask_login(repo):
    user = repo.add("ann@example.com", "correct horse")
    assert user.is_authenticated is True
    assert user.is_active is True
    assert user.get_id() == str(user.id)


def test_repr_never_shows_the_hash(repo):
    user = repo.add("ann@example.com", "correct horse")
    assert repr(user) == "User(id=1, email='ann@example.com')"
    assert user.password_hash not in repr(user)
