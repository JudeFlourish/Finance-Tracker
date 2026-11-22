import os

from finance_tracker import config, create_app


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


def test_home_page_with_no_data(client):
    response = client.get("/")
    assert response.status_code == 200
