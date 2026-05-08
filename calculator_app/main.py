"""
main.py  –  Entry point for the Calculator Application.

Run from DavaX_python-main/:
    python -m calculator_app.main

Or directly:
    cd calculator_app && python main.py
"""

from __future__ import annotations

import os
import sys

# ── Put calculator_app/ on sys.path FIRST so that sub-packages
#    (app, config, logging_config) are importable as top-level names.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

# ── Logging before everything else ───────────────────────────────────────────
from logging_config import setup_enhanced_logging
logger, _ = setup_enhanced_logging()

# ── Application imports (all absolute, no relative imports) ──────────────────
import atexit
import signal

import app.extensions as extensions
from calculator_app.factory import create_app
from app.auth.manager import AuthenticationManager
from app.cache.expression_cache import ExpressionCache
from app.db.manager import DatabaseManager
from config import Config


# ─────────────────────────────────────────────────────────────────────────────
# Signal / shutdown helpers
# ─────────────────────────────────────────────────────────────────────────────

def setup_signal_handlers() -> None:
    """Handle graceful shutdown without requiring arguments (uses global singleton)."""
    def _handler(sig, _frame):
        names = {signal.SIGINT: "SIGINT (Ctrl+C)", signal.SIGTERM: "SIGTERM"}
        print(f"\n\n=== {names.get(sig, sig)} received ===")
        if extensions.auth_manager.get_current_user():
            print(f"Logging out: {extensions.auth_manager.get_current_user()}")
            extensions.auth_manager.logout()
        print("Goodbye!")
        sys.exit(0)

    def _atexit_cleanup():
        if extensions.auth_manager.get_current_user():
            extensions.auth_manager.logout()

    signal.signal(signal.SIGINT,  _handler)
    signal.signal(signal.SIGTERM, _handler)
    atexit.register(_atexit_cleanup)
    logger.info("Signal handlers registered.")


# ─────────────────────────────────────────────────────────────────────────────
# Authentication setup
# ─────────────────────────────────────────────────────────────────────────────

def setup_authentication():
    auth = extensions.auth_manager

    if Config.CONTAINER_MODE:
        print("=== Container Mode ===")
        success, role = auth.authenticate_container_mode()
    else:
        print("=== Interactive Mode ===")
        print("  Admin : username='admin'  password='admin123'")
        print("  User  : username='user'   password='user123'\n")

        if os.path.exists(auth.auth_state_path):
            try:
                os.remove(auth.auth_state_path)
            except OSError:
                pass

        success, role = auth.authenticate_console()

    if not success:
        print("Authentication failed. Exiting...")
        sys.exit(1)

    return auth, role


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs(os.path.join(_THIS_DIR, "data"), exist_ok=True)

    print("=== Calculator Application ===")

    extensions.db_manager   = DatabaseManager(db_path=Config.DB_PATH)
    extensions.global_cache = ExpressionCache()
    extensions.auth_manager, user_role = setup_authentication()

    # Initialize authentication (which writes the login state to the global singleton)
    user_role = setup_authentication()

    setup_signal_handlers()

    flask_app = create_app()

    if Config.CONTAINER_MODE:
        host, port, debug = "0.0.0.0", Config.PORT, Config.FLASK_DEBUG
        print(f"Server → http://0.0.0.0:{port}  (Container, role={user_role})")
    else:
        host, port, debug = "127.0.0.1", 5000, True
        print(f"Server → http://127.0.0.1:5000  (role={user_role})")
        print("Ctrl+C to stop.")

    try:
        flask_app.run(host=host, port=port, debug=debug, use_reloader=False)
    except KeyboardInterrupt:
        extensions.auth_manager.logout()
        print("Goodbye!")
    except Exception as exc:
        logger.error("Server error: %s", exc)
        extensions.auth_manager.logout()
        sys.exit(1)