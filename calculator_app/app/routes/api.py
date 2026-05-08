"""
app/routes/api.py
-----------------
REST API endpoints (JSON).
All routes are registered on the `api_bp` Blueprint.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime

from flask import Blueprint, jsonify, request

from app import extensions
from app.core.controller import Controller
from app.core.model import Model

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__, url_prefix="/api")


# ------------------------------------------------------------------
# Error handlers
# ------------------------------------------------------------------

@api_bp.app_errorhandler(404)
def not_found(_):
    return jsonify({"error": "Endpoint not found"}), 404


@api_bp.app_errorhandler(500)
def internal_error(err):
    logger.error("Internal server error: %s", err)
    return jsonify({"error": "Internal server error"}), 500


# ------------------------------------------------------------------
# Health
# ------------------------------------------------------------------

@api_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat(), "version": "1.0.0"}), 200


# ------------------------------------------------------------------
# Core calculation
# ------------------------------------------------------------------

@api_bp.route("/calculate", methods=["POST"])
def api_calculate():
    t0 = time.time()
    client_ip = request.remote_addr

    data = request.get_json()
    logger.info("API request from %s: %s", client_ip, data)

    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    operation_type = data.get("operation_type")
    input_value    = data.get("input_value")
    session_id     = data.get("session_id")

    if not operation_type or input_value is None:
        return jsonify({"error": "operation_type and input_value are required"}), 400

    model      = Model(extensions.db_manager, session_id, extensions.global_cache)
    controller = Controller(extensions.db_manager)
    controller.setModel(model)

    result = controller.calculate(
        operation_type=operation_type,
        input_value=str(input_value),
        ip_address=client_ip,
        user_agent=request.headers.get("User-Agent"),
    )

    elapsed = (time.time() - t0) * 1000
    status_code = 200 if result["status"] == "success" else 400
    logger.info("Request completed in %.2fms for %s", elapsed, client_ip)
    return jsonify(result), status_code


# ------------------------------------------------------------------
# Convenience wrappers
# ------------------------------------------------------------------

def _delegate(operation_type: str, key: str):
    """Helper: re-shape request and call api_calculate()."""
    data = request.get_json()
    if not data or key not in data:
        return jsonify({"error": f"{key} is required"}), 400

    # Mutate data so api_calculate() can process it
    data["operation_type"] = operation_type
    data["input_value"]    = data.pop(key)

    # Push modified data back via the global request context trick
    request._cached_json = (data, data)          # works for Flask ≥ 2
    try:
        return api_calculate()
    except Exception:
        request._cached_json = ({}, {})
        raise


@api_bp.route("/calculator", methods=["POST"])
def api_calculator():
    try:
        return _delegate("calculator", "expression")
    except Exception as exc:
        logger.error("Calculator API error: %s", exc)
        return jsonify({"error": "Internal server error"}), 500


@api_bp.route("/fibonacci", methods=["POST"])
def api_fibonacci():
    try:
        return _delegate("fibonacci", "n")
    except Exception as exc:
        logger.error("Fibonacci API error: %s", exc)
        return jsonify({"error": "Internal server error"}), 500


@api_bp.route("/factorial", methods=["POST"])
def api_factorial():
    try:
        return _delegate("factorial", "n")
    except Exception as exc:
        logger.error("Factorial API error: %s", exc)
        return jsonify({"error": "Internal server error"}), 500


# ------------------------------------------------------------------
# History & analytics
# ------------------------------------------------------------------

@api_bp.route("/history", methods=["GET"])
def api_history():
    try:
        limit  = min(int(request.args.get("limit", 50)), 1000)
        offset = int(request.args.get("offset", 0))
        history = extensions.db_manager.get_request_history(limit=limit, offset=offset)
        return jsonify({"history": history, "limit": limit, "offset": offset, "count": len(history)}), 200
    except Exception as exc:
        logger.error("History API error: %s", exc)
        return jsonify({"error": "Internal server error"}), 500


@api_bp.route("/analytics", methods=["GET"])
def api_analytics():
    try:
        return jsonify(extensions.db_manager.get_analytics()), 200
    except Exception as exc:
        logger.error("Analytics API error: %s", exc)
        return jsonify({"error": "Internal server error"}), 500


# ------------------------------------------------------------------
# Cache
# ------------------------------------------------------------------

@api_bp.route("/cache/stats", methods=["GET"])
def api_cache_stats():
    try:
        return jsonify({
            "cache_stats": extensions.global_cache.get_stats(),
            "timestamp":   datetime.utcnow().isoformat(),
        }), 200
    except Exception as exc:
        logger.error("Cache stats error: %s", exc)
        return jsonify({"error": "Internal server error"}), 500


@api_bp.route("/cache/clear", methods=["POST"])
def api_cache_clear():
    t0 = time.time()
    client_ip = request.remote_addr
    try:
        data = request.get_json(silent=True) or {}
        op   = data.get("operation_type")
        extensions.global_cache.clear(op)
        msg = f"Cache cleared for {op}" if op else "All caches cleared"
        return jsonify({
            "message":          msg,
            "timestamp":        datetime.utcnow().isoformat(),
            "execution_time_ms": (time.time() - t0) * 1000,
        }), 200
    except Exception as exc:
        logger.error("Cache clear error for %s: %s", client_ip, exc)
        return jsonify({"error": "Internal server error"}), 500


# ------------------------------------------------------------------
# Authentication
# ------------------------------------------------------------------

@api_bp.route("/login", methods=["POST"])
def api_login():
    try:
        data = request.get_json()
        if not data or "username" not in data or "password" not in data:
            return jsonify({"error": "Username and password are required"}), 400

        username = data["username"]
        password = data["password"]

        if extensions.auth_manager.verify_credentials(username, password):
            extensions.auth_manager.current_user = username
            extensions.auth_manager.current_role = extensions.auth_manager.users[username]["role"]
            logger.info("API auth successful for user: %s", username)
            return jsonify({
                "status":    "success",
                "message":   "Authentication successful",
                "user":      username,
                "role":      extensions.auth_manager.current_role,
                "timestamp": datetime.utcnow().isoformat(),
            }), 200

        logger.warning("API auth failed for user: %s", username)
        return jsonify({"error": "Invalid credentials"}), 401

    except Exception as exc:
        logger.error("Login API error: %s", exc)
        return jsonify({"error": "Internal server error"}), 500


@api_bp.route("/logout", methods=["POST"])
def api_logout():
    try:
        user = extensions.auth_manager.get_current_user()
        extensions.auth_manager.logout()
        return jsonify({
            "status":    "success",
            "message":   f"User {user} logged out successfully",
            "timestamp": datetime.utcnow().isoformat(),
        }), 200
    except Exception as exc:
        logger.error("Logout API error: %s", exc)
        return jsonify({"error": "Internal server error"}), 500


@api_bp.route("/auth/status", methods=["GET"])
def api_auth_status():
    try:
        am = extensions.auth_manager
        return jsonify({
            "authenticated": am.is_authenticated(),
            "user":          am.get_current_user(),
            "role":          am.get_current_role(),
            "is_admin":      am.is_admin(),
            "timestamp":     datetime.utcnow().isoformat(),
        }), 200
    except Exception as exc:
        logger.error("Auth status error: %s", exc)
        return jsonify({"error": "Internal server error"}), 500