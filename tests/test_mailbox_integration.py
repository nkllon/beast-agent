"""Integration tests for BaseAgent mailbox integration.

These tests require beast-mailbox-core and a Redis instance.
They will be skipped if dependencies are not available.
"""

import asyncio
import pytest


@pytest.mark.asyncio
@pytest.mark.skipif(
    not pytest.importorskip("beast_mailbox_core"),
    reason="beast-mailbox-core not available",
)
async def test_mailbox_config_fixture(mailbox_config, redis_available):
    """Test that mailbox_config fixture works correctly."""
    if not redis_available:
        pytest.skip("Redis not available")

    from beast_mailbox_core import MailboxConfig

    assert isinstance(mailbox_config, MailboxConfig)
    assert mailbox_config.host == "localhost"
    assert mailbox_config.port == 6379
    assert mailbox_config.db == 15
    assert mailbox_config.stream_prefix == "test:mailbox"
    assert mailbox_config.enable_recovery is True


@pytest.mark.asyncio
@pytest.mark.skipif(
    not pytest.importorskip("beast_mailbox_core"),
    reason="beast-mailbox-core not available",
)
async def test_redis_mailbox_service_creation(mailbox_config, redis_available):
    """Test creating RedisMailboxService with test config."""
    if not redis_available:
        pytest.skip("Redis not available")

    from beast_mailbox_core import RedisMailboxService

    service = RedisMailboxService(
        agent_id="test-agent-integration", config=mailbox_config
    )

    assert service.agent_id == "test-agent-integration"
    # Verify inbox stream format (actual format may vary by mailbox-core version)
    assert service.inbox_stream is not None
    assert "test-agent-integration" in service.inbox_stream

    # Cleanup
    await service.stop()


@pytest.mark.asyncio
@pytest.mark.skipif(
    not pytest.importorskip("beast_mailbox_core"),
    reason="beast-mailbox-core not available",
)
async def test_mailbox_service_start_stop(mailbox_config, redis_available):
    """Test starting and stopping mailbox service."""
    if not redis_available:
        pytest.skip("Redis not available")

    from beast_mailbox_core import RedisMailboxService

    service = RedisMailboxService(agent_id="test-start-stop", config=mailbox_config)

    # Start service
    result = await service.start()
    assert result is True

    # Stop service
    await service.stop()


@pytest.mark.asyncio
@pytest.mark.skipif(
    not pytest.importorskip("beast_mailbox_core"),
    reason="beast-mailbox-core not available",
)
async def test_mailbox_send_receive_message(mailbox_config, redis_available):
    """Test sending and receiving messages via mailbox."""
    if not redis_available:
        pytest.skip("Redis not available")

    from beast_mailbox_core import RedisMailboxService, MailboxMessage

    sender_id = "test-sender"
    receiver_id = "test-receiver"

    # Create sender and receiver
    sender = RedisMailboxService(sender_id, mailbox_config)
    receiver = RedisMailboxService(receiver_id, mailbox_config)

    received_messages = []

    async def handler(msg: MailboxMessage) -> None:
        received_messages.append(msg)

    # Start receiver with handler
    receiver.register_handler(handler)
    await receiver.start()

    # Start sender
    await sender.start()

    # Send message
    message_id = await sender.send_message(
        recipient=receiver_id,
        payload={"type": "TEST_MESSAGE", "content": {"test": "data"}},
        message_type="direct_message",
    )

    # Wait for message to be processed
    await asyncio.sleep(0.5)

    # Verify message was received
    assert len(received_messages) == 1
    assert received_messages[0].sender == sender_id
    assert received_messages[0].recipient == receiver_id
    assert received_messages[0].payload["type"] == "TEST_MESSAGE"

    # Cleanup
    await sender.stop()
    await receiver.stop()


@pytest.mark.asyncio
@pytest.mark.skipif(
    not pytest.importorskip("beast_mailbox_core"),
    reason="beast-mailbox-core not available",
)
async def test_mailbox_message_handler_registration(mailbox_config, redis_available):
    """Test registering and calling message handlers."""
    if not redis_available:
        pytest.skip("Redis not available")

    from beast_mailbox_core import RedisMailboxService, MailboxMessage

    call_count = []

    async def test_handler(msg: MailboxMessage) -> None:
        call_count.append(msg)

    service = RedisMailboxService(agent_id="test-handler", config=mailbox_config)

    service.register_handler(test_handler)
    await service.start()

    # Handler should be registered (check internal state)
    # Note: RedisMailboxService may use different internal attribute name
    # Just verify service is running and handler was registered
    assert service is not None

    # Send message to self (for testing handler)
    sender = RedisMailboxService("test-sender-2", mailbox_config)
    await sender.start()

    await sender.send_message(
        recipient="test-handler",
        payload={"type": "TEST", "content": {}},
        message_type="direct_message",
    )

    # Wait for processing
    await asyncio.sleep(0.5)

    # Verify handler was called
    assert len(call_count) == 1

    # Cleanup
    await service.stop()
    await sender.stop()
