"""
config.py
---------
Centralised configuration for the Calculator Application.
Values are read from environment variables with sensible defaults.
"""

import os


class Config:
    # Flask
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    FLASK_DEBUG: bool = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

    # Server
    HOST: str = os.environ.get("HOST", "127.0.0.1")
    PORT: int = int(os.environ.get("PORT", 5000))

    # Database
    DB_PATH: str = os.environ.get(
        "DB_PATH",
        os.path.join(os.path.dirname(__file__), "data", "calculator_api.db"),
    )

    # Container / deployment mode
    CONTAINER_MODE: bool = os.environ.get("CONTAINER_MODE", "false").lower() == "true"
    CONTAINER_USERNAME: str = os.environ.get("CONTAINER_USERNAME", "")
    CONTAINER_PASSWORD: str = os.environ.get("CONTAINER_PASSWORD", "")

    # Auth state persistence path
    AUTH_STATE_PATH: str = os.path.join(os.path.dirname(__file__), ".auth_state.json")