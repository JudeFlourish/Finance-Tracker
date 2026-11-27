from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import Text, func
from sqlalchemy.orm import Mapped, mapped_column

from ..database import db


# UserMixin gives what Flask-Login needs (is_authenticated, get_id, ...)
class User(UserMixin, db.Model):
    __tablename__ = "users"
    __table_args__ = ({"sqlite_autoincrement": True},)

    id: Mapped[int] = mapped_column(primary_key=True)
    # NOCASE: the database itself treats "Ann@Mail.com" and "ann@mail.com" as the
    # same email, so unique really means one account per address
    email: Mapped[str] = mapped_column(Text(collation="NOCASE"), unique=True)
    # only the salted hash is stored, never the password (see passwords.py)
    password_hash: Mapped[str] = mapped_column(Text)
    # filled in by the database when the row is inserted
    created_at: Mapped[datetime] = mapped_column(server_default=func.current_timestamp())

    def __repr__(self):
        # the hash is left out on purpose, so it never ends up in a log
        return f"User(id={self.id!r}, email={self.email!r})"
