"""Base class for the feature repositories (expenses, income, budgets)."""


class Repository:
    """Gets its SQLAlchemy session from outside (db.session), so tests can
    use a temporary database. Only the repositories talk to the database."""

    def __init__(self, session):
        self.session = session

    def _commit(self):
        """One transaction: everything since the last commit is saved, or nothing is."""
        try:
            self.session.commit()
        except Exception:
            # after a failed commit the session can't be used until it is rolled back
            self.session.rollback()
            raise
