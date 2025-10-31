"""Tests for BaseAgent class.

All tests use real Redis in Docker containers (no mocks).
Redis is a requirement for beast-agent to function with mailbox integration.
"""

import pytest

from beast_agent import BaseAgent, AgentState


class MinimalAgent(BaseAgent):
    """Minimal test agent implementation."""

    async def on_startup(self) -> None:
        """Test startup hook."""
        self.started = True

    async def on_shutdown(self) -> None:
        """Test shutdown hook."""
        self.stopped = True


@pytest.mark.asyncio
async def test_agent_initialization(redis_docker):
    """Test agent initializes correctly."""
    agent = MinimalAgent(agent_id="test-agent", capabilities=["test"])

    assert agent.agent_id == "test-agent"
    assert agent.capabilities == ["test"]
    assert agent._state == AgentState.INITIALIZING


@pytest.mark.asyncio
@pytest.mark.skipif(not pytest.importorskip("beast_mailbox_core"), reason="beast-mailbox-core not available")
async def test_agent_startup(mailbox_config, redis_available):
    """Test agent startup lifecycle with real Redis."""
    if not redis_available:
        pytest.skip("Redis not available")
    
    agent = MinimalAgent(
        agent_id="test-agent",
        capabilities=["test"],
        mailbox_url=mailbox_config
    )

    await agent.startup()

    assert agent._state == AgentState.READY
    assert agent.started is True
    assert agent.ready() is True
    
    await agent.shutdown()


@pytest.mark.asyncio
@pytest.mark.skipif(not pytest.importorskip("beast_mailbox_core"), reason="beast-mailbox-core not available")
async def test_agent_shutdown(mailbox_config, redis_available):
    """Test agent shutdown lifecycle with real Redis."""
    if not redis_available:
        pytest.skip("Redis not available")
    
    agent = MinimalAgent(
        agent_id="test-agent",
        capabilities=["test"],
        mailbox_url=mailbox_config
    )

    await agent.startup()
    await agent.shutdown()

    assert agent._state == AgentState.STOPPED
    assert agent.stopped is True
    assert agent.ready() is False


@pytest.mark.asyncio
@pytest.mark.skipif(not pytest.importorskip("beast_mailbox_core"), reason="beast-mailbox-core not available")
async def test_health_check(mailbox_config, redis_available):
    """Test health check returns correct status with real Redis."""
    if not redis_available:
        pytest.skip("Redis not available")
    
    agent = MinimalAgent(
        agent_id="test-agent",
        capabilities=["test"],
        mailbox_url=mailbox_config
    )

    await agent.startup()
    health = agent.health_check()

    assert health.healthy is True
    assert health.state == AgentState.READY
    assert health.metadata["agent_id"] == "test-agent"
    
    await agent.shutdown()


@pytest.mark.asyncio
async def test_register_handler():
    """Test message handler registration (doesn't require Redis)."""
    agent = MinimalAgent(agent_id="test-agent", capabilities=["test"])

    async def test_handler(message):
        pass

    agent.register_handler("TEST_MESSAGE", test_handler)

    assert "TEST_MESSAGE" in agent._handlers
    assert agent._handlers["TEST_MESSAGE"] == test_handler

