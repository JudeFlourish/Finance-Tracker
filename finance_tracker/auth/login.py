"""Flask-Login set-up: how a logged-in user is found again on every request.

After login_user(user), Flask-Login keeps only the user's id in the signed
session cookie. On the next request it calls load_user(id) to get the User back
as current_user. /login, /logout and protecting pages come with US-11.
"""
from flask_login import LoginManager

from ..database import db
from .repository import UserRepository

login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    # the id comes from the session cookie as text; a deleted account gives None,
    # which Flask-Login treats as "not logged in"
    try:
        return UserRepository(db.session).get(int(user_id))
    except ValueError:
        return None


def init_app(app):
    login_manager.init_app(app)
