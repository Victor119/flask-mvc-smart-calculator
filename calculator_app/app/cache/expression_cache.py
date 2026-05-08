"""
app/cache/expression_cache.py
------------------------------
In-memory cache for calculator, fibonacci, and factorial results.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)
calc_logger = logging.getLogger("calculations")

_OPERATION_TYPES = ("calculator", "fibonacci", "factorial")


class ExpressionCache:
    """Thread-local in-memory result cache with hit/miss telemetry."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {op: {} for op in _OPERATION_TYPES}
        self.hit_count = 0
        self.miss_count = 0

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def get(self, operation_type: str, input_value: str) -> Optional[Any]:
        """Return cached value or *None* on miss."""
        key = str(input_value).strip()
        t0 = time.time()

        if key in self._store[operation_type]:
            self.hit_count += 1
            elapsed = (time.time() - t0) * 1000
            result = self._store[operation_type][key]
            calc_logger.info(
                "CACHE_HIT | op=%s | input='%s' | result=%s | %.2fms",
                operation_type, input_value, result, elapsed,
            )
            logger.debug("Cache HIT %s[%s] -> %s", operation_type, input_value, result)
            return result

        self.miss_count += 1
        elapsed = (time.time() - t0) * 1000
        calc_logger.info(
            "CACHE_MISS | op=%s | input='%s' | %.2fms",
            operation_type, input_value, elapsed,
        )
        logger.debug("Cache MISS %s[%s]", operation_type, input_value)
        return None

    def set(self, operation_type: str, input_value: str, result: Any) -> None:
        """Store a result in the cache."""
        key = str(input_value).strip()
        t0 = time.time()
        self._store[operation_type][key] = result
        elapsed = (time.time() - t0) * 1000
        calc_logger.info(
            "CACHE_STORE | op=%s | input='%s' | result=%s | %.2fms",
            operation_type, input_value, result, elapsed,
        )
        logger.debug("Cache STORED %s[%s] = %s", operation_type, input_value, result)

    def clear(self, operation_type: str = None) -> None:
        """Clear cache for *operation_type* or all caches if *None*."""
        if operation_type and operation_type in self._store:
            count = len(self._store[operation_type])
            self._store[operation_type].clear()
            calc_logger.info("CACHE_CLEAR | op=%s | cleared=%d", operation_type, count)
            logger.info("Cache cleared for %s (%d items)", operation_type, count)
        else:
            total = sum(len(v) for v in self._store.values())
            for op in self._store:
                self._store[op].clear()
            self.hit_count = 0
            self.miss_count = 0
            calc_logger.info("CACHE_CLEAR_ALL | cleared=%d", total)
            logger.info("All caches cleared (%d items)", total)

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> dict:
        total = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total * 100) if total else 0.0
        stats = {
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": round(hit_rate, 2),
            "cache_sizes": {op: len(self._store[op]) for op in _OPERATION_TYPES},
        }
        logger.info("Cache stats: %s", stats)
        return stats