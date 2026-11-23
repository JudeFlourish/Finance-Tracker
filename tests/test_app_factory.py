import os

import pytest

from finance_tracker import config, create_app, web
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


def test_home_page_is_the_dashboard(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Quick add" in response.get_data(as_text=True)


def test_old_expense_urls_are_gone(client):
    assert client.get("/export").status_code == 404
    assert client.post("/add").status_code == 404


def test_nav_links_every_page(client):
    page = client.get("/expenses/").get_data(as_text=True)
    for url in ["/", "/expenses/", "/income/", "/budgets/"]:
        assert f'href="{url}"' in page


@pytest.mark.parametrize("url, label", [
    ("/", "Home"),
    ("/expenses/", "Expenses"),
    ("/income/", "Income"),
    ("/budgets/", "Budgets"),
])
def test_nav_highlights_current_page(client, url, label):
    page = client.get(url).get_data(as_text=True)
    assert f'class="nav-link active">{label}</a>' in page
    assert page.count("nav-link active") == 1


def test_nav_hides_link_until_page_exists(app, monkeypatch):
    # a planned page with no route yet gets no link, so there are never dead links
    monkeypatch.setattr(web, "NAV_LINKS", web.NAV_LINKS + [("Reports", "reports.index")])
    with app.app_context():
        assert ("Reports", "reports.index") not in nav_links()
        app.view_functions["reports.index"] = lambda: "reports"
        assert ("Reports", "reports.index") in nav_links()


def test_every_feature_is_registered(app):
    assert {"expenses", "income", "budgets", "dashboard"} <= set(app.blueprints)
