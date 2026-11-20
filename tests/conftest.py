import pytest

from finance_tracker import create_app


@pytest.fixture
def app(tmp_path):
    # every test gets its own data file, so the real expenses.json is never touched
    return create_app({
        "TESTING": True,
        "DATA_FILE": str(tmp_path / "expenses.json"),
    })


@pytest.fixture
def client(app):
    return app.test_client()
