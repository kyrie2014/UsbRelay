# -*- coding: utf-8 -*-
"""
Performance Optimizations Utility Module

Provides optimized implementations for common operations including:
- Connection pooling
- Caching with TTL
- Serialization (msgpack instead of pickle)
- Adaptive waits
"""

import time
import logging
import msgpack
import threading
from functools import wraps
from typing import Any, Callable, Dict, Optional, List, Tuple
from contextlib import contextmanager

logger = logging.getLogger(__name__)


# =============================================================================
# SERIALIZATION (Issue #6: Pickle vs MessagePack)
# =============================================================================

class Serializer:
    """Optimized message serialization using MessagePack."""
    
    @staticmethod
    def serialize(obj: Any) -> bytes:
        """
        Serialize object to bytes using MessagePack.
        
        Args:
            obj: Object to serialize
        
        Returns:
            Binary data
        """
        try:
            return msgpack.packb(obj, use_bin_type=True)
        except Exception as e:
            logger.error(f'Serialization failed: {e}')
            return b''
    
    @staticmethod
    def deserialize(data: bytes) -> Any:
        """
        Deserialize bytes using MessagePack.
        
        Args:
            data: Binary data
        
        Returns:
            Deserialized object
        """
        try:
            return msgpack.unpackb(data, raw=False)
        except Exception as e:
            logger.error(f'Deserialization failed: {e}')
            return None


# =============================================================================
# CACHING (Issue #8: Device Binding Cache)
# =============================================================================

def cached(ttl: int = 300):
    """
    Cache decorator with time-to-live (TTL).
    
    Args:
        ttl: Cache lifetime in seconds (default: 5 minutes)
    
    Returns:
        Decorated function with caching
    
    Example:
        @cached(ttl=600)
        def get_device_binding(serial: str):
            # Expensive operation, cached for 10 minutes
            pass
    """
    def decorator(func: Callable) -> Callable:
        cache: Dict[tuple, Any] = {}
        cache_time: Dict[tuple, float] = {}
        lock = threading.Lock()
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = (args, tuple(sorted(kwargs.items())))
            current_time = time.time()
            
            with lock:
                # Check if cached and not expired
                if key in cache and current_time - cache_time[key] < ttl:
                    hit_rate = getattr(wrapper, '_hits', 0) / max(1, getattr(wrapper, '_calls', 1))
                    logger.debug(f'{func.__name__} cache hit (rate: {hit_rate:.1%})')
                    return cache[key]
                
                # Call function and cache result
                result = func(*args, **kwargs)
                cache[key] = result
                cache_time[key] = current_time
                
                # Track statistics
                wrapper._calls = getattr(wrapper, '_calls', 0) + 1
                wrapper._misses = getattr(wrapper, '_misses', 0) + 1
                
                return result
        
        wrapper._cache_clear = lambda: cache.clear()
        return wrapper
    
    return decorator


class DeviceBindingCache:
    """
    Thread-safe device binding cache with periodic persistence.
    
    Bindings: Dict[serial_number] -> (hub_value, relay_port)
    """
    
    _instance: Optional['DeviceBindingCache'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._cache: Dict[str, Tuple[int, int]] = {}
        self._dirty = False
        self._cache_lock = threading.Lock()
        self._cache_file = 'JPORTS.PKL'
        self._flush_interval = 30  # seconds
        self._last_flush = 0
        self._initialized = True
        
        self._load_cache()
    
    def _load_cache(self) -> None:
        """Load cache from file on startup."""
        from pathlib import Path
        import pickle
        
        if not Path(self._cache_file).exists():
            return
        
        try:
            with open(self._cache_file, 'rb') as f:
                self._cache = pickle.load(f)
            logger.info(f'Loaded {len(self._cache)} device bindings from cache')
        except Exception as e:
            logger.warning(f'Failed to load cache: {e}')
            self._cache = {}
    
    def get(self, serial: str) -> Optional[Tuple[int, int]]:
        """
        Get device binding from cache.
        
        Args:
            serial: Device serial number
        
        Returns:
            Tuple of (hub_value, relay_port) or None
        """
        with self._cache_lock:
            return self._cache.get(serial)
    
    def set(self, serial: str, hub_value: int, relay_port: int) -> None:
        """
        Set device binding in cache (in-memory, instant).
        
        Args:
            serial: Device serial number
            hub_value: USB hub ID value
            relay_port: Relay port index
        """
        with self._cache_lock:
            self._cache[serial] = (hub_value, relay_port)
            self._dirty = True
            
            # Flush if needed
            if time.time() - self._last_flush > self._flush_interval:
                self.flush()
    
    def flush(self) -> None:
        """Persist cache to file."""
        import pickle
        
        with self._cache_lock:
            if not self._dirty:
                return
            
            try:
                with open(self._cache_file, 'wb') as f:
                    pickle.dump(self._cache, f)
                self._dirty = False
                self._last_flush = time.time()
                logger.debug(f'Flushed {len(self._cache)} bindings to disk')
            except Exception as e:
                logger.error(f'Failed to flush cache: {e}')
    
    def clear(self) -> None:
        """Clear cache."""
        with self._cache_lock:
            self._cache.clear()
            self._dirty = True
    
    def get_all(self) -> Dict[str, Tuple[int, int]]:
        """Get all bindings (read-only snapshot)."""
        with self._cache_lock:
            return dict(self._cache)


# =============================================================================
# ADAPTIVE WAITS (Issue #3: Replace Fixed Sleeps)
# =============================================================================

class AdaptiveWaiter:
    """Adaptive wait with exponential backoff."""
    
    @staticmethod
    def wait_until(condition_func: Callable[[], bool], 
                   timeout: int = 10,
                   initial_delay: float = 0.1,
                   max_delay: float = 5.0,
                   backoff_factor: float = 1.5) -> bool:
        """
        Wait for condition to be true with exponential backoff.
        
        Args:
            condition_func: Callable that returns True when condition met
            timeout: Maximum wait time in seconds
            initial_delay: Starting delay in seconds (default: 0.1)
            max_delay: Maximum delay cap in seconds (default: 5.0)
            backoff_factor: Exponential backoff multiplier (default: 1.5)
        
        Returns:
            True if condition met, False if timeout
        
        Example:
            >>> if AdaptiveWaiter.wait_until(
            ...     lambda: device.is_connected(),
            ...     timeout=10
            ... ):
            ...     print("Device connected!")
        """
        start_time = time.time()
        delay = initial_delay
        attempt = 0
        
        while time.time() - start_time < timeout:
            try:
                if condition_func():
                    elapsed = time.time() - start_time
                    logger.debug(f'Condition met after {elapsed:.2f}s ({attempt} attempts)')
                    return True
            except Exception as e:
                logger.warning(f'Condition check failed: {e}')
            
            # Calculate remaining time and sleep duration
            remaining = timeout - (time.time() - start_time)
            sleep_time = min(delay, remaining, max_delay)
            
            if sleep_time > 0:
                time.sleep(sleep_time)
            
            delay = min(delay * backoff_factor, max_delay)
            attempt += 1
        
        logger.warning(f'Timeout waiting for condition after {attempt} attempts')
        return False
    
    @staticmethod
    def wait_for_value(getter_func: Callable[[], Any],
                      expected_value: Any,
                      timeout: int = 10,
                      initial_delay: float = 0.1) -> bool:
        """
        Wait for getter function to return expected value.
        
        Args:
            getter_func: Function that returns current value
            expected_value: Expected value to match
            timeout: Maximum wait time in seconds
            initial_delay: Starting delay in seconds
        
        Returns:
            True if value matched, False if timeout
        """
        return AdaptiveWaiter.wait_until(
            lambda: getter_func() == expected_value,
            timeout=timeout,
            initial_delay=initial_delay
        )


# =============================================================================
# REGEX OPTIMIZATION (Issue #9: Module-Level Regex)
# =============================================================================

import re

# Compile regex patterns once at module level
ADB_DEVICE_PATTERN = re.compile(r'\n(\S+)\s+device')
PORT_STATE_PATTERN = re.compile(r'[0-9a-f]{2}', re.IGNORECASE)


def get_adb_devices_from_output(output: str) -> List[str]:
    """
    Extract device serial numbers from adb devices output.
    
    Uses pre-compiled regex for efficiency.
    
    Args:
        output: Output from 'adb devices' command
    
    Returns:
        List of device serial numbers
    """
    return ADB_DEVICE_PATTERN.findall(output)


def parse_port_states(hex_string: str) -> List[int]:
    """
    Parse binary port states from hex string response.
    
    Args:
        hex_string: Space-separated hex values like "7e 07 06 00 01 02"
    
    Returns:
        List of port state bytes
    """
    try:
        return [int(x, 16) for x in hex_string.split()]
    except ValueError as e:
        logger.error(f'Failed to parse port states: {e}')
        return []


# =============================================================================
# CONNECTION POOLING HELPERS
# =============================================================================

@contextmanager
def get_pooled_db_connection():
    """
    Context manager for getting database connection from pool.
    
    Requires: pip install DBUtils
    
    Example:
        >>> with get_pooled_db_connection() as conn:
        ...     cursor = conn.cursor()
        ...     cursor.execute("SELECT * FROM table")
    """
    from relay.utils.db_pool import DatabasePool
    
    pool = DatabasePool()
    conn = pool.get_connection()
    try:
        yield conn
    finally:
        conn.close()


# =============================================================================
# PERFORMANCE MONITORING
# =============================================================================

class PerformanceTimer:
    """Context manager for timing operations."""
    
    def __init__(self, name: str, log_level: int = logging.DEBUG):
        self.name = name
        self.log_level = log_level
        self.start_time = None
        self.elapsed = 0
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.perf_counter() - self.start_time
        
        if exc_type is not None:
            logger.log(
                self.log_level,
                f'{self.name} failed after {self.elapsed:.3f}s: {exc_val}'
            )
        else:
            logger.log(
                self.log_level,
                f'{self.name} completed in {self.elapsed:.3f}s'
            )
        
        return False


class RateLimiter:
    """Rate limiter using token bucket algorithm."""
    
    def __init__(self, rate: float, burst: int = 1):
        """
        Initialize rate limiter.
        
        Args:
            rate: Tokens per second
            burst: Maximum burst size
        """
        self.rate = rate
        self.burst = burst
        self.tokens = burst
        self.last_update = time.time()
        self.lock = threading.Lock()
    
    def acquire(self, tokens: int = 1, blocking: bool = True) -> bool:
        """
        Acquire tokens, blocking if necessary.
        
        Args:
            tokens: Number of tokens to acquire
            blocking: Whether to block waiting for tokens
        
        Returns:
            True if tokens acquired
        """
        with self.lock:
            # Refill tokens
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(
                self.burst,
                self.tokens + elapsed * self.rate
            )
            self.last_update = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            if not blocking:
                return False
            
            # Calculate wait time
            wait_time = (tokens - self.tokens) / self.rate
            time.sleep(wait_time)
            self.tokens = 0
            return True


# =============================================================================
# BATCH OPERATIONS
# =============================================================================

class BatchProcessor:
    """Batch processor for efficient bulk operations."""
    
    def __init__(self, batch_size: int = 100, flush_interval: float = 5.0):
        """
        Initialize batch processor.
        
        Args:
            batch_size: Number of items to accumulate before processing
            flush_interval: Maximum time between flushes (seconds)
        """
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.batch: List[Any] = []
        self.last_flush = time.time()
        self.lock = threading.Lock()
    
    def add(self, item: Any) -> None:
        """Add item to batch."""
        with self.lock:
            self.batch.append(item)
            
            # Auto-flush if batch full
            if len(self.batch) >= self.batch_size:
                self.flush()
    
    def should_flush(self) -> bool:
        """Check if batch should be flushed."""
        with self.lock:
            is_full = len(self.batch) >= self.batch_size
            is_stale = time.time() - self.last_flush > self.flush_interval
            return is_full or (is_stale and len(self.batch) > 0)
    
    def flush(self) -> List[Any]:
        """Flush batch and return items."""
        with self.lock:
            items = self.batch[:]
            self.batch.clear()
            self.last_flush = time.time()
            return items


__all__ = [
    'Serializer',
    'cached',
    'DeviceBindingCache',
    'AdaptiveWaiter',
    'get_adb_devices_from_output',
    'parse_port_states',
    'get_pooled_db_connection',
    'PerformanceTimer',
    'RateLimiter',
    'BatchProcessor',
]
