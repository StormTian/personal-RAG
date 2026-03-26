"""Dependency injection container for RAG system."""

import inspect
from abc import ABC
from typing import Any, Callable, Dict, Optional, Type, TypeVar, get_type_hints

T = TypeVar('T')


class DependencyProvider:
    """Base class for dependency providers."""
    
    def __init__(self, provider: Callable[..., T]):
        self.provider = provider
    
    def get(self) -> T:
        """Get the dependency instance."""
        raise NotImplementedError


class Singleton(DependencyProvider):
    """Singleton provider that creates instance once."""
    
    def __init__(self, provider: Callable[..., T]):
        super().__init__(provider)
        self._instance: Optional[T] = None
    
    def get(self) -> T:
        if self._instance is None:
            self._instance = self.provider()
        return self._instance


class Factory(DependencyProvider):
    """Factory provider that creates new instance each time."""
    
    def get(self) -> T:
        return self.provider()


class Container:
    """Dependency injection container."""
    
    def __init__(self):
        self._registrations: Dict[Type, DependencyProvider] = {}
        self._instances: Dict[Type, Any] = {}
    
    def register_singleton(self, interface: Type[T], implementation: Callable[..., T]) -> None:
        """Register a singleton dependency."""
        self._registrations[interface] = Singleton(implementation)
    
    def register_factory(self, interface: Type[T], implementation: Callable[..., T]) -> None:
        """Register a factory dependency."""
        self._registrations[interface] = Factory(implementation)
    
    def register_instance(self, interface: Type[T], instance: T) -> None:
        """Register an existing instance."""
        self._instances[interface] = instance
    
    def resolve(self, interface: Type[T]) -> T:
        """Resolve a dependency by interface type."""
        # Check for registered instance first
        if interface in self._instances:
            return self._instances[interface]
        
        # Check for registered provider
        if interface in self._registrations:
            return self._registrations[interface].get()
        
        # Try to auto-create if it's a concrete class
        if not isinstance(interface, type) or issubclass(interface, ABC):
            raise KeyError(f"No registration found for {interface}")
        
        try:
            return self._create_instance(interface)
        except Exception as e:
            raise KeyError(f"Failed to create instance of {interface}: {e}")
    
    def _create_instance(self, cls: Type[T]) -> T:
        """Create instance with auto-injected dependencies."""
        # Get constructor signature
        sig = inspect.signature(cls.__init__)
        type_hints = get_type_hints(cls.__init__)
        
        # Build kwargs from dependencies
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            # Get parameter type hint
            param_type = type_hints.get(param_name, param.annotation)
            if param_type is inspect.Parameter.empty:
                # Use default value if no type hint
                if param.default is not inspect.Parameter.empty:
                    kwargs[param_name] = param.default
                continue
            
            # Try to resolve dependency
            try:
                kwargs[param_name] = self.resolve(param_type)
            except KeyError:
                # Use default if available
                if param.default is not inspect.Parameter.empty:
                    kwargs[param_name] = param.default
                else:
                    raise
        
        return cls(**kwargs)
    
    def build_provider(self, func: Callable) -> Callable:
        """Build a provider function with auto-injected dependencies."""
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)
        
        def wrapper(*args, **kwargs):
            # Get all parameters
            bound = sig.bind_partial(*args, **kwargs)
            bound.apply_defaults()
            
            # Inject missing dependencies
            for param_name, param in sig.parameters.items():
                if param_name in bound.arguments:
                    continue
                
                param_type = type_hints.get(param_name, param.annotation)
                if param_type is inspect.Parameter.empty:
                    continue
                
                try:
                    bound.arguments[param_name] = self.resolve(param_type)
                except KeyError:
                    pass  # Will fail at call time if required
            
            return func(*bound.args, **bound.kwargs)
        
        return wrapper


def inject(func: Callable) -> Callable:
    """Decorator to mark a function for dependency injection."""
    func._inject = True
    return func


# Global container instance
_container: Optional[Container] = None


def get_container() -> Container:
    """Get or create global DI container."""
    global _container
    if _container is None:
        _container = Container()
    return _container


def register_singleton(interface: Type[T], implementation: Callable[..., T]) -> None:
    """Register a singleton in global container."""
    get_container().register_singleton(interface, implementation)


def register_factory(interface: Type[T], implementation: Callable[..., T]) -> None:
    """Register a factory in global container."""
    get_container().register_factory(interface, implementation)


def resolve(interface: Type[T]) -> T:
    """Resolve a dependency from global container."""
    return get_container().resolve(interface)
