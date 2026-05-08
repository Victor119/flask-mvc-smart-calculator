"""
app/extensions.py
-----------------
Module-level singletons that are initialized exactly once when this module 
is first imported. These are then shared across routes, controllers, and main.py.

This pattern avoids circular imports, prevents 'NoneType' errors, and guarantees
that the entire app shares the same authentication state, database connection, 
and cache memory.
"""

from __future__ import annotations

# Importăm clasele din modulele lor respective
from app.auth.manager import AuthenticationManager
from app.db.manager import DatabaseManager
from app.cache.expression_cache import ExpressionCache

# =====================================================================
# GLOBAL SINGLETONS
# =====================================================================

# 1. Database - Manages history and connection to SQLite
db_manager = DatabaseManager()

#2. Cache - Stores the results of mathematical expressions in memory
global_cache = ExpressionCache()

# 3. Authentication Manager - Remembers who is logged in (also reads from data/.auth_state.json)
auth_manager = AuthenticationManager()