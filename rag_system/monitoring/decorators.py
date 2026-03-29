"""Tracing decorators for RAG system."""

import functools
import asyncio
from typing import Callable, Any, Optional
from .tracing import get_tracer


def trace_span(
    name: Optional[str] = None,
    attributes: Optional[dict] = None,
    record_exception: bool = True
):
    """Decorator to trace function execution.
    
    Args:
        name: Span name (defaults to function name)
        attributes: Additional span attributes
        record_exception: Whether to record exceptions
        
    Usage:
        @trace_span("my_operation", {"component": "index"})
        async def my_function():
            pass
    """
    def decorator(func: Callable) -> Callable:
        tracer = get_tracer()
        span_name = name or func.__name__
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with tracer.start_as_current_span(span_name) as span:
                # Add attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                
                # Add function info
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("success", True)
                    return result
                except Exception as e:
                    span.set_attribute("success", False)
                    if record_exception:
                        span.record_exception(e)
                    raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with tracer.start_as_current_span(span_name) as span:
                # Add attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                
                # Add function info
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("success", True)
                    return result
                except Exception as e:
                    span.set_attribute("success", False)
                    if record_exception:
                        span.record_exception(e)
                    raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def trace_method(
    name: Optional[str] = None,
    attributes: Optional[dict] = None
):
    """Decorator to trace class method execution.
    
    Similar to trace_span but handles self/cls properly.
    """
    def decorator(method: Callable) -> Callable:
        tracer = get_tracer()
        span_name = name or method.__name__
        
        @functools.wraps(method)
        async def async_wrapper(self_or_cls, *args, **kwargs):
            class_name = self_or_cls.__class__.__name__ if hasattr(self_or_cls, '__class__') else self_or_cls.__name__
            full_name = f"{class_name}.{span_name}"
            
            with tracer.start_as_current_span(full_name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                
                span.set_attribute("class.name", class_name)
                span.set_attribute("method.name", method.__name__)
                
                try:
                    result = await method(self_or_cls, *args, **kwargs)
                    span.set_attribute("success", True)
                    return result
                except Exception as e:
                    span.set_attribute("success", False)
                    span.record_exception(e)
                    raise
        
        @functools.wraps(method)
        def sync_wrapper(self_or_cls, *args, **kwargs):
            class_name = self_or_cls.__class__.__name__ if hasattr(self_or_cls, '__class__') else self_or_cls.__name__
            full_name = f"{class_name}.{span_name}"
            
            with tracer.start_as_current_span(full_name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                
                span.set_attribute("class.name", class_name)
                span.set_attribute("method.name", method.__name__)
                
                try:
                    result = method(self_or_cls, *args, **kwargs)
                    span.set_attribute("success", True)
                    return result
                except Exception as e:
                    span.set_attribute("success", False)
                    span.record_exception(e)
                    raise
        
        if asyncio.iscoroutinefunction(method):
            return async_wrapper
        return sync_wrapper
    
    return decorator
