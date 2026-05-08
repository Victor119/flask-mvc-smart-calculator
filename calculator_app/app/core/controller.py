"""
app/core/controller.py
----------------------
MVC Controller: orchestrates calculations, enforces permissions, and
logs every operation via the calc_logger.
"""

from __future__ import annotations


import logging
import time
from typing import Any, Dict, Optional, Tuple

from app.auth.manager import AuthenticationManager
from app.core.model import Model
from app.db.manager import DatabaseManager
from app.widgets.ui import MyDisplayBox, Point

logger      = logging.getLogger(__name__)
calc_logger = logging.getLogger("calculations")


class Controller:
    """Mediates between the web layer and the Model; executes calculations."""

    _OPERATION_MAP: Dict[str, int] = {
        "calculator": 1,
        "fibonacci":  2,
        "factorial":  3,
    }

    # Restrictions for non-admin users
    _ADMIN_ONLY: Dict[str, Any] = {
        "calculator": ["eval", "exec", "import", "__"],
        "fibonacci":  29,   # max n for regular users
        "factorial":  200,  # max n for regular users
    }

    def __init__(
        self,
        db_manager: DatabaseManager,
        auth_manager: AuthenticationManager = None,
    ) -> None:
        self.model: Optional[Model] = None
        self.db_manager = db_manager
        self.auth_manager = auth_manager or AuthenticationManager()

    def setModel(self, model: Model) -> None:
        self.model = model

    # ------------------------------------------------------------------
    # Permission check
    # ------------------------------------------------------------------

    def check_permission(self, operation_type: str, input_value: str) -> Tuple[bool, str]:
        if not self.auth_manager.is_authenticated():
            return False, "Authentication required"

        if self.auth_manager.is_admin():
            return True, "Admin access granted"

        if operation_type == "calculator":
            for kw in self._ADMIN_ONLY["calculator"]:
                if kw in input_value.lower():
                    return False, f"Restricted keyword '{kw}'. Admin access required."

        elif operation_type == "fibonacci":
            try:
                if int(input_value.strip()) > self._ADMIN_ONLY["fibonacci"]:
                    return False, f"Fibonacci above {self._ADMIN_ONLY['fibonacci']} requires admin."
            except ValueError:
                return False, "Invalid input for fibonacci"

        elif operation_type == "factorial":
            try:
                if int(input_value.strip()) > self._ADMIN_ONLY["factorial"]:
                    return False, f"Factorial above {self._ADMIN_ONLY['factorial']} requires admin."
            except ValueError:
                return False, "Invalid input for factorial"

        return True, "User access granted"

    # ------------------------------------------------------------------
    # GUI-style control methods
    # ------------------------------------------------------------------

    def chControl(self, aString: str) -> None:
        """Set the active choice from a string token (e.g. '1', '2', '3')."""
        t0 = time.time()
        try:
            ch = int(aString.strip().split()[-1])
            self.model.setLastChoice(ch)
            calc_logger.info(
                "CHOICE_CHANGE | user=%s | choice=%d | %.2fms",
                self.auth_manager.get_current_user(), ch, (time.time() - t0) * 1000,
            )
        except Exception as exc:
            calc_logger.error(
                "CHOICE_ERROR | user=%s | input='%s' | error=%s | %.2fms",
                self.auth_manager.get_current_user(), aString, exc, (time.time() - t0) * 1000,
            )
            logger.error("Invalid input to chControl: %s — %s", aString, exc)

    def inpControl(self, aString: str) -> Any:
        """Route the input string to the appropriate handler."""
        t0 = time.time()
        choice = self.model.getLastChoice()
        op = {1: "calculator", 2: "fibonacci", 3: "factorial"}.get(choice)

        calc_logger.info("CALCULATION_START | op=%s | input='%s' | choice=%d", op, aString, choice)
        self.model.setLastInput(aString)

        try:
            if choice == 1:
                return self._handle_calculator(aString, t0)
            elif choice == 2:
                return self._handle_fibonacci(aString, t0)
            elif choice == 3:
                return self._handle_factorial(aString, t0)
            else:
                calc_logger.warning("NO_OPERATION | choice=%d | input='%s'", choice, aString)
                return "No operation selected"
        except Exception as exc:
            calc_logger.error(
                "UNEXPECTED_ERROR | op=%s | input='%s' | error=%s | %.2fms",
                op, aString, exc, (time.time() - t0) * 1000,
            )
            logger.error("Unexpected error in inpControl: %s", exc)
            return f"Error: {exc}"

    # ------------------------------------------------------------------
    # Individual operation handlers
    # ------------------------------------------------------------------

    def _handle_calculator(self, aString: str, t0: float) -> Any:
        from python_calculator.calculator import process_expression  # deferred import

        n = aString.strip()
        cached = self.model.cache.get("calculator", n)
        if cached is not None:
            self.model.calculatorOutputView.setText(f"{cached} (cached)")
            calc_logger.info("CALC_CACHED | op=calculator | input='%s' | result=%s | %.2fms",
                             n, cached, (time.time() - t0) * 1000)
            return cached

        try:
            result = process_expression(n)
            self.model.cache.set("calculator", n, result)
            self.model.calculatorOutputView.setText(str(result))
            calc_logger.info("CALC_OK | op=calculator | input='%s' | result=%s | %.2fms",
                             n, result, (time.time() - t0) * 1000)
            return result
        except Exception as exc:
            self.model.calculatorOutputView.setText("Invalid expression")
            calc_logger.error("CALC_ERR | op=calculator | input='%s' | error=%s | %.2fms",
                              aString, exc, (time.time() - t0) * 1000)
            logger.error("Calculator error '%s': %s", aString, exc)
            return "Invalid expression"

    def _handle_fibonacci(self, aString: str, t0: float) -> Any:
        try:
            n = int(aString.strip())
        except ValueError as exc:
            self.model.fibonacciOutputView.setText("Invalid input")
            calc_logger.error("CALC_ERR | op=fibonacci | input='%s' | error=%s", aString, exc)
            return "Invalid input"

        cached = self.model.cache.get("fibonacci", str(n))
        if cached is not None:
            self.model.fibonacciOutputView.setText(f"{cached} (cached)")
            calc_logger.info("CALC_CACHED | op=fibonacci | n=%d | result=%s | %.2fms",
                             n, cached, (time.time() - t0) * 1000)
            return cached

        result = self._fibonacci(n)
        self.model.cache.set("fibonacci", str(n), result)
        self.model.fibonacciOutputView.setText(str(result))
        calc_logger.info("CALC_OK | op=fibonacci | n=%d | result=%s | %.2fms",
                         n, result, (time.time() - t0) * 1000)
        return result

    def _handle_factorial(self, aString: str, t0: float) -> Any:
        try:
            n = int(aString.strip())
        except ValueError as exc:
            self.model.factorialOutputView.setText("Invalid input")
            calc_logger.error("CALC_ERR | op=factorial | input='%s' | error=%s", aString, exc)
            return "Invalid input"

        cached = self.model.cache.get("factorial", str(n))
        if cached is not None:
            self.model.factorialOutputView.setText(f"{cached} (cached)")
            calc_logger.info("CALC_CACHED | op=factorial | n=%d | result=%s | %.2fms",
                             n, cached, (time.time() - t0) * 1000)
            return cached

        result = self._factorial(n)
        self.model.cache.set("factorial", str(n), result)
        self.model.factorialOutputView.setText(str(result))
        calc_logger.info("CALC_OK | op=factorial | n=%d | result=%s | %.2fms",
                         n, result, (time.time() - t0) * 1000)
        return result

    # ------------------------------------------------------------------
    # Pure math helpers
    # ------------------------------------------------------------------

    def _fibonacci(self, n: int) -> int:
        if n <= 1:
            return n
        return self._fibonacci(n - 1) + self._fibonacci(n - 2)

    def _factorial(self, n: int) -> Any:
        if n < 0:
            logger.warning("Negative factorial requested: %d", n)
            return "Error: negative number"
        result = 1
        for i in range(2, n + 1):
            result *= i
        return result

    # ------------------------------------------------------------------
    # High-level API entry point (used by Flask routes)
    # ------------------------------------------------------------------

    def calculate(
        self,
        operation_type: str,
        input_value: str,
        ip_address: str = None,
        user_agent: str = None,
    ) -> dict:
        t0 = time.time()
        calc_logger.info(
            "API_START | op=%s | input='%s' | ip=%s", operation_type, input_value, ip_address
        )

        if operation_type not in self._OPERATION_MAP:
            raise ValueError(f"Invalid operation type: {operation_type}")

        # Ensure views are available
        for setter, attr in (
            (self.model.setCalculatorView, "calculatorOutputView"),
            (self.model.setFibonacciView,  "fibonacciOutputView"),
            (self.model.setFactorialView,  "factorialOutputView"),
        ):
            if getattr(self.model, attr) is None:
                setter(MyDisplayBox(Point(0, 0), 0, 0))

        # Cache hit?
        cached = self.model.cache.get(operation_type, input_value)
        if cached is not None:
            elapsed = (time.time() - t0) * 1000
            req_id = self.db_manager.log_request(
                operation_type, input_value,
                result=f"{cached} (cached)", status="success_cached",
                ip_address=ip_address, user_agent=user_agent,
            )
            calc_logger.info("API_CACHED | op=%s | result=%s | %.2fms | req=%s",
                             operation_type, cached, elapsed, req_id)
            return self._success_payload(req_id, operation_type, input_value, cached,
                                         cached=True, api_ms=elapsed)

        try:
            self.chControl(str(self._OPERATION_MAP[operation_type]))
            result = self.inpControl(input_value)

            if result is None:
                view_map = {
                    "calculator": self.model.calculatorOutputView,
                    "fibonacci":  self.model.fibonacciOutputView,
                    "factorial":  self.model.factorialOutputView,
                }
                result = view_map[operation_type].getText()

            elapsed = (time.time() - t0) * 1000
            req_id = self.db_manager.log_request(
                operation_type, input_value,
                result=str(result), status="success",
                ip_address=ip_address, user_agent=user_agent,
            )
            calc_logger.info("API_OK | op=%s | result=%s | %.2fms | req=%s",
                             operation_type, result, elapsed, req_id)
            return self._success_payload(req_id, operation_type, input_value, result,
                                         cached=False, api_ms=elapsed)

        except Exception as exc:
            elapsed = (time.time() - t0) * 1000
            req_id = self.db_manager.log_request(
                operation_type, input_value,
                status="error", error_message=str(exc),
                ip_address=ip_address, user_agent=user_agent,
            )
            calc_logger.error("API_ERR | op=%s | error=%s | %.2fms | req=%s",
                              operation_type, exc, elapsed, req_id)
            return {
                "request_id": req_id,
                "operation_type": operation_type,
                "input_value": input_value,
                "error": str(exc),
                "cached": False,
                "status": "error",
                "session_id": self.model.get_session_id(),
                "execution_time_ms": elapsed,
            }

    @staticmethod
    def _success_payload(req_id, op, inp, result, cached, api_ms) -> dict:
        return {
            "request_id": req_id,
            "operation_type": op,
            "input_value": inp,
            "result": result,
            "cached": cached,
            "status": "success",
            "execution_time_ms": api_ms,
        }