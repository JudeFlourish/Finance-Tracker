"""HTTP layer for accounts (US-10). No SQL and no validation rules in here."""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user
from sqlalchemy.exc import IntegrityError

from ..database import db
from ..validation import ValidationError
from .repository import UserRepository
from .validation import MIN_PASSWORD_LENGTH, validate_registration

bp = Blueprint("auth", __name__)

EMAIL_TAKEN = "An account with this email already exists."


def _form_page(email="", status=200):
    # only the email is shown again after an error, never the password
    return render_template(
        "auth/register.html", email=email, min_length=MIN_PASSWORD_LENGTH,
    ), status


@bp.route("/register", methods=["GET", "POST"])
def register():
    # someone already logged in doesn't need a new account
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))
    if request.method == "GET":
        return _form_page()

    typed_email = request.form.get("email", "")
    try:
        registration = validate_registration(request.form)
    except ValidationError as error:
        flash(str(error), "error")
        return _form_page(typed_email, 400)

    repo = UserRepository(db.session)
    if repo.get_by_email(registration.email) is not None:
        flash(EMAIL_TAKEN, "error")
        return _form_page(typed_email, 400)
    try:
        user = repo.add(registration.email, registration.password)
    except IntegrityError:
        # two sign-ups with the same email at the same moment: the UNIQUE rule catches the second
        flash(EMAIL_TAKEN, "error")
        return _form_page(typed_email, 400)

    login_user(user)
    flash("Welcome! Your account is ready.", "success")
    return redirect(url_for("dashboard.home"))
