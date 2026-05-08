"""
app/factory.py
--------------
Flask application factory — kept in a dedicated file to avoid the
  `from app import create_app`
name-resolution ambiguity that appears when the package is loaded via
`python -m calculator_app.main`.
"""

from __future__ import annotations

import os


def create_app():
    from flask import Flask
    from flask_cors import CORS
    from app.routes.api import api_bp
    from app.routes.web import web_bp

    application = Flask(__name__, template_folder="templates")
    application.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    CORS(application)

    application.register_blueprint(api_bp)
    application.register_blueprint(web_bp)

    return application