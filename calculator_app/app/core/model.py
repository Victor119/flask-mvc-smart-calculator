"""
app/core/model.py
-----------------
MVC Model: holds application state and persists it via the DatabaseManager.
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from app.cache.expression_cache import ExpressionCache
from app.db.manager import DatabaseManager
from app.widgets.ui import MyDisplayBox

logger = logging.getLogger(__name__)


class Model:
    """Stores per-session state and acts as the single source of truth."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        session_id: str = None,
        cache: ExpressionCache = None,
    ) -> None:
        self.db_manager = db_manager
        self.session_id = session_id or str(uuid.uuid4())
        self.cache = cache if cache is not None else ExpressionCache()

        # Load or initialise session state
        session_data = self.db_manager.get_session(self.session_id)
        if session_data:
            self.lastChoice: int = session_data["last_choice"]
            self.lastInput: str  = session_data["last_input"]
        else:
            self.lastChoice = 0
            self.lastInput  = ""

        # Output view references (set by the web layer)
        self.calculatorOutputView: Optional[MyDisplayBox] = None
        self.fibonacciOutputView:  Optional[MyDisplayBox] = None
        self.factorialOutputView:  Optional[MyDisplayBox] = None

    # ------------------------------------------------------------------
    # Setters / getters
    # ------------------------------------------------------------------

    def setLastChoice(self, ch: int) -> None:
        self.lastChoice = ch
        self.db_manager.update_session(self.session_id, last_choice=ch)
        self._notify()

    def getLastChoice(self) -> int:
        return self.lastChoice

    def setLastInput(self, txt: str) -> None:
        self.lastInput = txt
        self.db_manager.update_session(self.session_id, last_input=txt)

    def setCalculatorView(self, db: MyDisplayBox) -> None:
        self.calculatorOutputView = db

    def setFibonacciView(self, db: MyDisplayBox) -> None:
        self.fibonacciOutputView = db

    def setFactorialView(self, db: MyDisplayBox) -> None:
        self.factorialOutputView = db

    def get_session_id(self) -> str:
        return self.session_id

    # ------------------------------------------------------------------
    # Cache helpers (proxy to ExpressionCache)
    # ------------------------------------------------------------------

    def get_cache_stats(self) -> dict:
        return self.cache.get_stats()

    def clear_cache(self, operation_type: str = None) -> None:
        self.cache.clear(operation_type)

    # ------------------------------------------------------------------
    # Observer notification
    # ------------------------------------------------------------------

    def _notify(self) -> None:
        if self.calculatorOutputView:
            self.calculatorOutputView.setText(f"Last choice is {self.lastChoice}")
        if self.fibonacciOutputView:
            self.fibonacciOutputView.setText(f"Last input is `{self.lastInput}`")