from finance_tracker import create_app


def test_default_config():
    app = create_app()
    assert not app.testing
    assert app.config["SECRET_KEY"]
    assert app.config["DATA_FILE"].endswith("expenses.json")


def test_test_config_overrides_defaults(app, tmp_path):
    assert app.testing
    assert app.config["DATA_FILE"] == str(tmp_path / "expenses.json")


def test_home_page_with_no_data(client):
    response = client.get("/")
    assert response.status_code == 200
