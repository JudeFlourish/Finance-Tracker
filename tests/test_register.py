import pytest
from sqlalchemy import select

from finance_tracker.auth.models import User
from finance_tracker.auth.passwords import check_password


def register(client, **fields):
    form = {"email": "ann@example.com", "password": "correct horse", "confirm": "correct horse"}
    form.update(fields)
    return client.post("/register", data=form)


def users(session):
    return list(session.scalars(select(User)))


def messages(client):
    # what the next page will show as flash messages
    with client.session_transaction() as session:
        return [message for _, message in session.get("_flashes", [])]


def logged_in_id(client):
    # Flask-Login keeps the logged-in user's id in the session as "_user_id"
    with client.session_transaction() as session:
        return session.get("_user_id")


# the page

def test_register_page_has_the_form(client):
    response = client.get("/register")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "<h1>Create an account</h1>" in page
    assert 'type="email" id="email" name="email"' in page
    assert 'type="password" id="password" name="password"' in page
    assert 'type="password" id="confirm" name="confirm"' in page
    assert 'autocomplete="new-password"' in page


def test_nav_shows_register_when_logged_out(client):
    page = client.get("/").get_data(as_text=True)
    assert 'href="/register"' in page


# registering

def test_register_creates_account_and_logs_in(client, session):
    response = register(client, email="  Ann@Example.COM ")
    assert response.status_code == 302
    assert response.location == "/"
    [user] = users(session)
    assert user.email == "ann@example.com"
    assert logged_in_id(client) == str(user.id)
    assert messages(client) == ["Welcome! Your account is ready."]


def test_only_a_hash_of_the_password_is_saved(client, session):
    register(client)
    [user] = users(session)
    assert user.password_hash != "correct horse"
    assert check_password(user.password_hash, "correct horse")


def test_after_registering_the_nav_shows_the_email(client):
    register(client)
    page = client.get("/").get_data(as_text=True)
    assert '<span class="nav-user">ann@example.com</span>' in page
    assert 'href="/register"' not in page


def test_logged_in_user_is_sent_away_from_register(client):
    register(client)
    response = client.get("/register")
    assert response.status_code == 302
    assert response.location == "/"


@pytest.mark.parametrize("fields, message", [
    ({"email": ""}, "Please enter your email"),
    ({"email": "not-an-email"}, "Please enter a valid email address"),
    ({"password": "short", "confirm": "short"}, "Your password needs at least 8 characters"),
    ({"confirm": "something else"}, "The two passwords don&#39;t match"),
])
def test_bad_form_saves_nothing_and_says_why(client, session, fields, message):
    response = register(client, **fields)
    assert response.status_code == 400
    page = response.get_data(as_text=True)
    assert message in page
    assert users(session) == []
    assert logged_in_id(client) is None


def test_after_an_error_the_email_is_kept_but_never_the_password(client):
    page = register(client, email="ann@example.com", confirm="something else").get_data(as_text=True)
    assert 'value="ann@example.com"' in page
    assert "correct horse" not in page
    assert "something else" not in page


def test_typed_email_is_escaped(client):
    page = register(client, email='"><script>alert(1)</script>').get_data(as_text=True)
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;" in page


@pytest.mark.parametrize("email", ["ann@example.com", "ANN@example.com"])
def test_duplicate_email_is_refused(client, session, email):
    register(client)
    client.get("/")  # show the welcome message, so only the new ones are left
    other = client.application.test_client()  # someone else, not logged in
    response = register(other, email=email, password="another one", confirm="another one")
    assert response.status_code == 400
    assert "An account with this email already exists." in response.get_data(as_text=True)
    assert len(users(session)) == 1
    assert logged_in_id(other) is None


def test_two_people_get_two_accounts(app, session):
    register(app.test_client(), email="ann@example.com")
    register(app.test_client(), email="bob@example.com")
    assert [u.email for u in users(session)] == ["ann@example.com", "bob@example.com"]


# finding the user again on the next request (Flask-Login)

def test_a_deleted_account_is_logged_out(client, session):
    register(client)
    session.delete(users(session)[0])
    session.commit()
    page = client.get("/").get_data(as_text=True)
    assert 'href="/register"' in page


def test_a_broken_user_id_in_the_session_is_logged_out(client):
    with client.session_transaction() as s:
        s["_user_id"] = "not-a-number"
    page = client.get("/").get_data(as_text=True)
    assert 'href="/register"' in page
