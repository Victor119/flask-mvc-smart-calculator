"""
app/auth/manager.py
-------------------
Console-based and container-based authentication for the Calculator Application.
"""

from __future__ import annotations

import getpass
import hashlib
import json
import logging
import os
import sys
from datetime import datetime
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class AuthenticationManager:
    """Handles user authentication for both interactive and container modes."""

    # Predefined users.  In production replace with a proper user-store.
    _USERS: dict = {
        "admin": {"password_hash": None, "role": "admin"},
        "user":  {"password_hash": None, "role": "user"},
    }
    _DEFAULT_PASSWORDS: dict = {"admin": "admin123", "user": "user123"}

    def __init__(self, auth_state_path: Optional[str] = None):
        if auth_state_path is None:
            # __file__ = app/auth/manager.py
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            self.auth_state_path = os.path.join(data_dir, ".auth_state.json")
        else:
            self.auth_state_path = auth_state_path

        self.current_user: Optional[str] = None
        self.current_role: Optional[str] = None

        # Build hashed user table at runtime
        self.users = {
            username: {
                "password_hash": self._hash_password(self._DEFAULT_PASSWORDS[username]),
                "role": info["role"],
            }
            for username, info in self._USERS.items()
        }

        # Citim starea de logare de pe disc la initializare
        self._load_auth_state()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def _load_auth_state(self) -> None:
        if not os.path.exists(self.auth_state_path):
            return
        try:
            with open(self.auth_state_path, "r") as fh:
                state = json.load(fh)
            self.current_user = state.get("user")
            self.current_role = state.get("role")
            if self.current_user:
                logger.info(
                    "Loaded persisted auth for %s (%s)",
                    self.current_user,
                    self.current_role,
                )
        except Exception as exc:
            logger.warning("Failed to load auth state: %s", exc)

    def _persist_auth_state(self) -> None:
        try:
            with open(self.auth_state_path, "w") as fh:
                json.dump({"user": self.current_user, "role": self.current_role}, fh)
        except Exception as exc:
            logger.warning("Failed to persist auth state: %s", exc)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def verify_credentials(self, username: str, password: str) -> bool:
        """Return True when *username* / *password* match a known user."""
        if username not in self.users:
            return False
        return self.users[username]["password_hash"] == self._hash_password(password)

    def authenticate_console(self) -> Tuple[bool, Optional[str]]:
        """Interactive terminal authentication (up to 3 attempts)."""
        if self.current_user:
            print(f"Already authenticated as {self.current_user} ({self.current_role})")
            return True, self.current_role

        print("\n=== Calculator Authentication ===")
        max_attempts = 3

        for attempt in range(max_attempts):
            try:
                username = input("Username: ").strip()
                password = getpass.getpass("Password: ")

                if self.verify_credentials(username, password):
                    self.current_user = username
                    self.current_role = self.users[username]["role"]
                    self._persist_auth_state()
                    print(f"Authentication successful! Logged in as {username} ({self.current_role})")
                    logger.info("User %s authenticated (role=%s)", username, self.current_role)
                    return True, self.current_role

                remaining = max_attempts - attempt - 1
                if remaining:
                    print(f"Invalid credentials. {remaining} attempt(s) remaining.")
                else:
                    print("Authentication failed. Maximum attempts exceeded.")
                    logger.warning("Authentication failed for user: %s", username)

            except (KeyboardInterrupt, EOFError):
                print("\nAuthentication cancelled. Exiting...")
                self.logout()
                sys.exit(0)
            except Exception as exc:
                logger.error("Authentication error: %s", exc)
                print(f"Authentication error: {exc}")

        self.logout()
        return False, None

    def authenticate_container_mode(self) -> Tuple[bool, Optional[str]]:
        """Container-friendly authentication via environment variables."""
        if self.current_user:
            logger.info("Already authenticated as %s (%s)", self.current_user, self.current_role)
            return True, self.current_role

        from config import Config  # local import to avoid circular deps at module load

        username = Config.CONTAINER_USERNAME
        password = Config.CONTAINER_PASSWORD

        if username and password:
            if self.verify_credentials(username, password):
                self._set_user(username)
                logger.info("Container auth successful for %s (%s)", username, self.current_role)
                print(f"Container authentication successful! Logged in as {username} ({self.current_role})")
                return True, self.current_role

            logger.warning("Container authentication failed for user: %s", username)
            print(f"Container authentication failed for user: {username}")
            return False, None

        # Fallback: use default admin (development convenience)
        if self.verify_credentials("admin", "admin123"):
            self._set_user("admin")
            logger.info("Default admin authentication used")
            print(f"Using default authentication: admin ({self.current_role})")
            return True, self.current_role

        return False, None

    def _set_user(self, username: str) -> None:
        self.current_user = username
        self.current_role = self.users[username]["role"]
        self._persist_auth_state()

    def logout(self) -> None:
        """Clear authentication state and remove persisted file."""
        if self.current_user:
            logger.info(
                "Logout: %s (%s) at %s",
                self.current_user,
                self.current_role,
                datetime.utcnow().isoformat(),
            )
            print(f"User {self.current_user} logged out.")

        self.current_user = None
        self.current_role = None

        if os.path.exists(self.auth_state_path):
            try:
                os.remove(self.auth_state_path)
                logger.info("Persisted auth state removed.")
            except Exception as exc:
                logger.warning("Failed to remove auth state file: %s", exc)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def is_authenticated(self) -> bool:
        return self.current_user is not None

    def is_admin(self) -> bool:
        return self.current_role == "admin"

    def get_current_user(self) -> Optional[str]:
        return self.current_user

    def get_current_role(self) -> Optional[str]:
        return self.current_role