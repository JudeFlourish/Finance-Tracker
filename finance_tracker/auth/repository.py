from sqlalchemy import select

from ..repository import Repository
from .models import User
from .passwords import hash_password


class UserRepository(Repository):
    """All database access for user accounts."""

    def add(self, email, password):
        """Create an account and return it. The password is hashed here, so a
        plain password can never reach the database by mistake."""
        user = User(email=email, password_hash=hash_password(password))
        self.session.add(user)
        self._commit()
        return user

    def get(self, user_id):
        return self.session.get(User, user_id)

    def get_by_email(self, email):
        # the email column is NOCASE, so any mix of upper and lower case matches
        return self.session.scalars(select(User).where(User.email == email)).first()
