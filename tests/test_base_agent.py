"""Tests for BaseAgent class."""

import pytest
from beast_agent import BaseAgent, AgentState


class TestAgent(BaseAgent):
    """Test agent implementation."""

    async def on_startup(self) -> None:
        """Test startup hook."""
        self.started = True

    async def on_shutdown(self) -> None:
        """Test shutdown hook."""
        self.stopped = True


@pytest.mark.asyncio
async def test_agent_initialization():
    """Test agent initializes correctly."""
    agent = TestAgent(agent_id="test-agent", capabilities=["test"])

    assert agent.agent_id == "test-agent"
    assert agent.capabilities == ["test"]
    assert agent._state == AgentState.INITIALIZING


@pytest.mark.asyncio
async def test_agent_startup():
    """Test agent startup lifecycle."""
    agent = TestAgent(agent_id="test-agent", capabilities=["test"])

    await agent.startup()

    assert agent._state == AgentState.READY
    assert agent.started is True
    assert agent.ready() is True


@pytest.mark.asyncio
async def test_agent_shutdown():
    """Test agent shutdown lifecycle."""
    agent = TestAgent(agent_id="test-agent", capabilities=["test"])

    await agent.startup()
    await agent.shutdown()

    assert agent._state == AgentState.STOPPED
    assert agent.stopped is True
    assert agent.ready() is False


@pytest.mark.asyncio
async def test_health_check():
    """Test health check returns correct status."""
    agent = TestAgent(agent_id="test-agent", capabilities=["test"])

    await agent.startup()
    health = agent.health_check()

    assert health.healthy is True
    assert health.state == AgentState.READY
    assert health.metadata["agent_id"] == "test-agent"


@pytest.mark.asyncio
async def test_register_handler():
    """Test message handler registration."""
    agent = TestAgent(agent_id="test-agent", capabilities=["test"])

    async def test_handler(message):
        pass

    agent.register_handler("TEST_MESSAGE", test_handler)

    assert "TEST_MESSAGE" in agent._handlers
    assert agent._handlers["TEST_MESSAGE"] == test_handler

