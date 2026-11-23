import os

from finance_tracker import config, create_app
from finance_tracker.web import nav_links


def clear_env(monkeypatch):
    for name in ("SECRET_KEY", "DATABASE"):
        monkeypatch.delenv(name, raising=False)


def test_default_config(monkeypatch, tmp_path):
    # checks the settings only, so no real database is created
    clear_env(monkeypatch)
    settings = config.from_environment(str(tmp_path))
    assert settings["SECRET_KEY"]
    assert settings["DATABASE"] == os.path.join(str(tmp_path), "finance.db")


def test_config_from_environment(monkeypatch, tmp_path):
    clear_env(monkeypatch)
    monkeypatch.setenv("SECRET_KEY", "test-key")
    monkeypatch.setenv("DATABASE", str(tmp_path / "test.db"))
    app = create_app()
    assert not app.testing
    assert app.config["SECRET_KEY"] == "test-key"
    assert app.config["DATABASE"] == str(tmp_path / "test.db")


def test_test_config_overrides_defaults(app, tmp_path):
    assert app.testing
    assert app.config["DATABASE"] == str(tmp_path / "test.db")


def test_home_page_goes_to_expenses(client):
    # until the dashboard is built, "/" shows the expenses page
    response = client.get("/")
    assert response.status_code == 302
    assert response.location == "/expenses/"
    assert client.get("/", follow_redirects=True).status_code == 200


def test_old_expense_urls_are_gone(client):
    assert client.get("/export").status_code == 404
    assert client.post("/add").status_code == 404


def test_nav_shows_only_pages_that_exist(client):
    page = client.get("/expenses/").get_data(as_text=True)
    assert 'href="/expenses/"' in page
    # income and budgets have no page yet, so no dead links
    assert 'href="/income' not in page
    assert 'href="/budgets' not in page


def test_nav_highlights_current_page(client):
    page = client.get("/expenses/").get_data(as_text=True)
    assert 'class="nav-link active">Expenses</a>' in page


def test_nav_link_appears_when_page_is_added(app):
    # adding a route with the endpoint name from NAV_LINKS is enough
    with app.app_context():
        assert ("Income", "income.list_income") not in nav_links()
        app.view_functions["income.list_income"] = lambda: "income"
        assert ("Income", "income.list_income") in nav_links()


def test_every_feature_is_registered(app):
    assert {"expenses", "income", "budgets", "dashboard"} <= set(app.blueprints)
