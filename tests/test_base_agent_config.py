"""Tests for BaseAgent configuration handling."""

import os
import pytest
from pydantic import ValidationError

from beast_agent import BaseAgent, AgentConfig
from beast_agent.types import AgentState


class ConfigTestAgent(BaseAgent):
    """Test agent for configuration tests."""

    async def on_startup(self) -> None:
        pass

    async def on_shutdown(self) -> None:
        pass


@pytest.mark.asyncio
async def test_agent_config_from_env():
    """Test agent loads config from environment variables."""
    os.environ["AGENT_LOG_LEVEL"] = "DEBUG"
    os.environ["AGENT_HEARTBEAT_INTERVAL"] = "45"

    try:
        agent = ConfigTestAgent(agent_id="test", capabilities=["test"])
        assert agent.config.log_level == "DEBUG"
        assert agent.config.heartbeat_interval == 45
    finally:
        os.environ.pop("AGENT_LOG_LEVEL", None)
        os.environ.pop("AGENT_HEARTBEAT_INTERVAL", None)


@pytest.mark.asyncio
async def test_agent_config_from_constructor():
    """Test agent accepts AgentConfig instance from constructor."""
    config = AgentConfig(log_level="WARNING", heartbeat_interval=60)
    agent = ConfigTestAgent(agent_id="test", capabilities=["test"], config=config)

    assert agent.config.log_level == "WARNING"
    assert agent.config.heartbeat_interval == 60


@pytest.mark.asyncio
async def test_agent_config_validation_error():
    """Test agent raises ValidationError for invalid config."""
    with pytest.raises(ValidationError):
        # Invalid log level
        ConfigTestAgent(
            agent_id="test",
            capabilities=["test"],
            config=AgentConfig(log_level="INVALID"),
        )


@pytest.mark.asyncio
async def test_agent_config_uses_log_level():
    """Test agent logger uses config log level."""
    config = AgentConfig(log_level="DEBUG")
    agent = ConfigTestAgent(agent_id="test-debug", capabilities=["test"], config=config)

    assert agent._logger.level == 10  # logging.DEBUG


@pytest.mark.asyncio
async def test_agent_send_message():
    """Test send_message method requires mailbox to be initialized."""
    agent = ConfigTestAgent(agent_id="test", capabilities=["test"])

    # Should raise RuntimeError if mailbox not initialized
    with pytest.raises(RuntimeError, match="Mailbox not initialized"):
        await agent.send_message("target", "TEST_MESSAGE", {"data": "value"})


@pytest.mark.asyncio
async def test_agent_handle_message_with_handler():
    """Test handle_message routes to registered handler."""
    agent = ConfigTestAgent(agent_id="test", capabilities=["test"])

    handled_messages = []

    async def test_handler(message):
        handled_messages.append(message)

    agent.register_handler("TEST_MESSAGE", test_handler)

    await agent.handle_message({"type": "TEST_MESSAGE", "content": {"data": "value"}})

    assert len(handled_messages) == 1
    assert handled_messages[0]["type"] == "TEST_MESSAGE"


@pytest.mark.asyncio
async def test_agent_handle_message_no_handler():
    """Test handle_message logs warning when no handler registered."""
    agent = ConfigTestAgent(agent_id="test", capabilities=["test"])

    # Should not raise error, just log warning
    await agent.handle_message({"type": "UNKNOWN_MESSAGE", "content": {}})


@pytest.mark.asyncio
async def test_agent_handle_message_handler_error():
    """Test handle_message handles handler exceptions gracefully."""
    agent = ConfigTestAgent(agent_id="test", capabilities=["test"])

    async def error_handler(message):
        raise ValueError("Handler error")

    agent.register_handler("ERROR_MESSAGE", error_handler)

    initial_error_count = agent._error_count

    # Should catch error and increment error count
    await agent.handle_message({"type": "ERROR_MESSAGE", "content": {}})

    assert agent._error_count == initial_error_count + 1
