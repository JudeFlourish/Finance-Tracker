import os

from finance_tracker import create_app


def clear_env(monkeypatch):
    for name in ("SECRET_KEY", "DATABASE", "DATA_FILE"):
        monkeypatch.delenv(name, raising=False)


def test_default_config(monkeypatch):
    clear_env(monkeypatch)
    app = create_app()
    assert not app.testing
    assert app.config["SECRET_KEY"]
    assert app.config["DATABASE"] == os.path.join(app.instance_path, "finance.db")
    assert app.config["DATA_FILE"].endswith("expenses.json")


def test_config_from_environment(monkeypatch, tmp_path):
    clear_env(monkeypatch)
    monkeypatch.setenv("SECRET_KEY", "test-key")
    monkeypatch.setenv("DATABASE", str(tmp_path / "test.db"))
    app = create_app()
    assert app.config["SECRET_KEY"] == "test-key"
    assert app.config["DATABASE"] == str(tmp_path / "test.db")


def test_test_config_overrides_defaults(app, tmp_path):
    assert app.testing
    assert app.config["DATA_FILE"] == str(tmp_path / "expenses.json")


def test_home_page_with_no_data(client):
    response = client.get("/")
    assert response.status_code == 200
