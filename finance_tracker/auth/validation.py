from dataclasses import dataclass

from email_validator import EmailNotValidError, validate_email

from ..validation import ValidationError

MIN_PASSWORD_LENGTH = 8
# a limit, so nobody can make the server hash a huge text
MAX_PASSWORD_LENGTH = 128


@dataclass(frozen=True)
class Registration:
    email: str
    password: str


def parse_email(value):
    """A valid email address, in lower case, so the same address always matches."""
    if not isinstance(value, str) or value.strip() == "":
        raise ValidationError("Please enter your email")
    try:
        # check_deliverability=False: only the format is checked, no internet lookup
        # (that would be slow and fail without a connection)
        email = validate_email(value.strip(), check_deliverability=False).normalized
    except EmailNotValidError:
        raise ValidationError("Please enter a valid email address")
    return email.lower()


def parse_new_password(password, confirm):
    """The rules for a new password; used by register (and change password, US-15)."""
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f"Your password needs at least {MIN_PASSWORD_LENGTH} characters")
    if len(password) > MAX_PASSWORD_LENGTH:
        raise ValidationError(f"Your password can have at most {MAX_PASSWORD_LENGTH} characters")
    if password != confirm:
        raise ValidationError("The two passwords don't match")
    # not stripped: spaces are allowed in a password and count as characters
    return password


def validate_registration(form):
    """Turn the register form into a Registration, or raise ValidationError.

    Whether the email is already taken needs the database, so the route checks
    that with UserRepository.get_by_email.
    """
    return Registration(
        email=parse_email(form.get("email")),
        password=parse_new_password(form.get("password"), form.get("confirm")),
    )
