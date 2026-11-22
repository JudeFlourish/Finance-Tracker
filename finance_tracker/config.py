"""Settings read from environment variables, so no secret is ever committed.

For local development put them in a .env file (see .env.example).
"""
import os
import secrets


def from_environment(instance_path):
    return {
        # without SECRET_KEY a random one is made at startup, fine for development
        "SECRET_KEY": os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        # the SQLite file lives in instance/, which is not committed
        "DATABASE": os.environ.get("DATABASE") or os.path.join(instance_path, "finance.db"),
    }
