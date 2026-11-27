"""Password hashing. The only place that knows how passwords are stored.

werkzeug (comes with Flask) hashes with scrypt and a random salt, so the same
password gives a different hash every time, and the hash can't be turned back
into the password.
"""
from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password):
    return generate_password_hash(password)


def check_password(password_hash, password):
    """True when password is the one the hash was made from."""
    return check_password_hash(password_hash, password)
