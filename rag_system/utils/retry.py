"""Retry logic with exponential backoff."""

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional, Tuple, Type

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_factor: float = 0.1
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    on_retry: Optional[Callable[[Exception, int], None]] = None


class RetryableError(Exception):
    """Error that can be retried."""
    pass


def _calculate_delay(attempt: int, config: RetryConfig) -> float:
    """Calculate delay with exponential backoff and jitter."""
    delay = config.base_delay * (config.exponential_base ** attempt)
    delay = min(delay, config.max_delay)
    
    if config.jitter:
        jitter = delay * config.jitter_factor * random.uniform(-1, 1)
        delay = max(0, delay + jitter)
    
    return delay


def retry_with_backoff(
    func: Callable,
    *args,
    config: Optional[RetryConfig] = None,
    **kwargs
) -> Any:
    """Execute function with retry and exponential backoff."""
    config = config or RetryConfig()
    last_exception: Optional[Exception] = None
    
    for attempt in range(config.max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            
            # Check if exception is retryable
            if not any(isinstance(e, exc_type) for exc_type in config.retryable_exceptions):
                raise
            
            # Don't retry on last attempt
            if attempt == config.max_retries:
                break
            
            # Calculate delay
            delay = _calculate_delay(attempt, config)
            
            logger.warning(
                f"Attempt {attempt + 1}/{config.max_retries + 1} failed: {e}. "
                f"Retrying in {delay:.2f}s..."
            )
            
            # Call callback if provided
            if config.on_retry:
                try:
                    config.on_retry(e, attempt + 1)
                except Exception:
                    pass
            
            time.sleep(delay)
    
    raise last_exception


async def retry_with_backoff_async(
    func: Callable,
    *args,
    config: Optional[RetryConfig] = None,
    **kwargs
) -> Any:
    """Async version of retry_with_backoff."""
    config = config or RetryConfig()
    last_exception: Optional[Exception] = None
    
    for attempt in range(config.max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            
            # Check if exception is retryable
            if not any(isinstance(e, exc_type) for exc_type in config.retryable_exceptions):
                raise
            
            # Don't retry on last attempt
            if attempt == config.max_retries:
                break
            
            # Calculate delay
            delay = _calculate_delay(attempt, config)
            
            logger.warning(
                f"Attempt {attempt + 1}/{config.max_retries + 1} failed: {e}. "
                f"Retrying in {delay:.2f}s..."
            )
            
            # Call callback if provided
            if config.on_retry:
                try:
                    config.on_retry(e, attempt + 1)
                except Exception:
                    pass
            
            await asyncio.sleep(delay)
    
    raise last_exception


class Retryable:
    """Decorator for making functions retryable."""
    
    def __init__(self, config: Optional[RetryConfig] = None, **kwargs):
        if config:
            self.config = config
        else:
            self.config = RetryConfig(**kwargs)
    
    def __call__(self, func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            return retry_with_backoff(func, *args, config=self.config, **kwargs)
        
        async def async_wrapper(*args, **kwargs):
            return await retry_with_backoff_async(func, *args, config=self.config, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
