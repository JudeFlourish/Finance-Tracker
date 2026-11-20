"""Settings read from environment variables, so no secret is ever committed."""
import os
import secrets

# expenses.json stays in the project folder, same place as before
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def from_environment():
    return {
        # without SECRET_KEY a random one is made at startup, fine for development
        "SECRET_KEY": os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        "DATA_FILE": os.environ.get("DATA_FILE") or os.path.join(PROJECT_DIR, "expenses.json"),
    }
