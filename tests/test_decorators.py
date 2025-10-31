"""Tests for capability decorators."""

from beast_agent.decorators import capability


def test_capability_decorator():
    """Test capability decorator adds metadata."""

    @capability("test_capability", version="2.0.0")
    async def test_func():
        pass

    assert hasattr(test_func, "_capability_name")
    assert test_func._capability_name == "test_capability"
    assert test_func._capability_version == "2.0.0"


def test_capability_decorator_default_version():
    """Test capability decorator uses default version."""

    @capability("test_capability")
    async def test_func():
        pass

    assert test_func._capability_version == "1.0.0"
