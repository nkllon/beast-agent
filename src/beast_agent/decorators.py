"""Decorators for beast-agent capabilities."""

from typing import Callable


def capability(name: str, version: str = "1.0.0") -> Callable:
    """
    Decorator to mark methods as agent capabilities.

    Args:
        name: Capability name
        version: Capability version (default: "1.0.0")

    Returns:
        Decorated function with capability metadata

    Example:
        @capability("process_document", version="1.0.0")
        async def process_document(self, document: str) -> dict:
            return {"status": "processed"}
    """

    def decorator(func: Callable) -> Callable:
        func._capability_name = name  # type: ignore
        func._capability_version = version  # type: ignore
        return func

    return decorator

