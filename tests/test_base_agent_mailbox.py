"""Integration tests for BaseAgent mailbox integration.

Tests BaseAgent integration with beast-mailbox-core using real Redis.
These tests will be skipped if dependencies are not available.
"""

import asyncio
import pytest

from beast_agent import BaseAgent


class MailboxTestAgent(BaseAgent):
    """Test agent for mailbox integration tests."""

    def __init__(self, agent_id: str, mailbox_config=None):
        """Initialize test agent with optional mailbox config."""
        if mailbox_config:
            super().__init__(
                agent_id=agent_id, capabilities=["test"], mailbox_url=mailbox_config
            )
        else:
            super().__init__(agent_id=agent_id, capabilities=["test"])

    async def on_startup(self) -> None:
        """Test startup hook."""
        pass

    async def on_shutdown(self) -> None:
        """Test shutdown hook."""
        pass


@pytest.mark.asyncio
@pytest.mark.skipif(
    not pytest.importorskip("beast_mailbox_core"),
    reason="beast-mailbox-core not available",
)
async def test_base_agent_mailbox_startup(mailbox_config, redis_available):
    """Test BaseAgent startup with mailbox integration."""
    if not redis_available:
        pytest.skip("Redis not available")

    agent = MailboxTestAgent("test-mailbox-agent", mailbox_config)

    # Startup should initialize mailbox
    await agent.startup()

    # Verify mailbox is initialized
    assert agent._mailbox is not None
    assert agent._state.value == "ready"

    # Cleanup
    await agent.shutdown()


@pytest.mark.asyncio
@pytest.mark.skipif(
    not pytest.importorskip("beast_mailbox_core"),
    reason="beast-mailbox-core not available",
)
async def test_base_agent_mailbox_shutdown(mailbox_config, redis_available):
    """Test BaseAgent shutdown with mailbox integration."""
    if not redis_available:
        pytest.skip("Redis not available")

    agent = MailboxTestAgent("test-shutdown-agent", mailbox_config)

    await agent.startup()
    assert agent._mailbox is not None

    # Shutdown should stop mailbox
    await agent.shutdown()

    # Verify agent is stopped
    assert agent._state.value == "stopped"


@pytest.mark.asyncio
@pytest.mark.skipif(
    not pytest.importorskip("beast_mailbox_core"),
    reason="beast-mailbox-core not available",
)
async def test_base_agent_send_message(mailbox_config, redis_available):
    """Test BaseAgent send_message via mailbox."""
    if not redis_available:
        pytest.skip("Redis not available")

    sender = MailboxTestAgent("test-sender", mailbox_config)
    receiver = MailboxTestAgent("test-receiver", mailbox_config)

    received_messages = []

    async def handler(content: dict) -> None:
        received_messages.append(content)

    # Setup receiver with handler
    receiver.register_handler("TEST_MESSAGE", handler)
    await receiver.startup()

    # Setup sender
    await sender.startup()

    # Send message
    message_id = await sender.send_message(
        target="test-receiver",
        message_type="TEST_MESSAGE",
        content={"test": "data", "value": 42},
    )

    assert message_id is not None

    # Wait for message processing
    await asyncio.sleep(0.5)

    # Verify message was received
    assert len(received_messages) == 1
    assert received_messages[0]["test"] == "data"
    assert received_messages[0]["value"] == 42

    # Cleanup
    await sender.shutdown()
    await receiver.shutdown()


@pytest.mark.asyncio
@pytest.mark.skipif(
    not pytest.importorskip("beast_mailbox_core"),
    reason="beast-mailbox-core not available",
)
async def test_base_agent_mailbox_message_handler(mailbox_config, redis_available):
    """Test BaseAgent mailbox message handler routing."""
    if not redis_available:
        pytest.skip("Redis not available")

    agent = MailboxTestAgent("test-handler-agent", mailbox_config)

    call_count = []

    async def test_handler(content: dict) -> None:
        call_count.append(content)

    agent.register_handler("TEST_HANDLER", test_handler)
    await agent.startup()

    # Send message via mailbox (simulating external message)
    from beast_mailbox_core import RedisMailboxService

    sender = RedisMailboxService("external-sender", mailbox_config)
    await sender.start()

    await sender.send_message(
        recipient="test-handler-agent",
        payload={"type": "TEST_HANDLER", "content": {"data": "value"}},
        message_type="direct_message",
    )

    # Wait for processing
    await asyncio.sleep(0.5)

    # Verify handler was called
    assert len(call_count) == 1
    assert call_count[0]["data"] == "value"

    # Cleanup
    await sender.stop()
    await agent.shutdown()


@pytest.mark.asyncio
@pytest.mark.skipif(
    not pytest.importorskip("beast_mailbox_core"),
    reason="beast-mailbox-core not available",
)
async def test_base_agent_mailbox_health_check(mailbox_config, redis_available):
    """Test BaseAgent health check includes mailbox status."""
    if not redis_available:
        pytest.skip("Redis not available")

    agent = MailboxTestAgent("test-health-agent", mailbox_config)

    await agent.startup()

    # Check health
    health = agent.health_check()

    assert health.healthy is True
    assert health.metadata["mailbox_connected"] is True
    assert "agent_id" in health.metadata
    assert "capabilities" in health.metadata

    # Cleanup
    await agent.shutdown()
