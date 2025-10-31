"""Tests for agent name registration on cluster.

Tests agent name registration and unregistration in Redis
for discovery functionality.
"""

import asyncio
import json
import pytest

from beast_agent import BaseAgent


class NameRegistrationTestAgent(BaseAgent):
    """Test agent for name registration tests."""

    def __init__(self, agent_id: str, mailbox_config=None):
        """Initialize test agent with optional mailbox config."""
        if mailbox_config:
            super().__init__(
                agent_id=agent_id, capabilities=["test"], mailbox_url=mailbox_config
            )
        else:
            super().__init__(agent_id=agent_id, capabilities=["test"])

    async def on_startup(self) -> None:
        """Test agent startup hook."""
        pass

    async def on_shutdown(self) -> None:
        """Test agent shutdown hook."""
        pass


@pytest.mark.asyncio
@pytest.mark.skipif(
    not pytest.importorskip("beast_mailbox_core"),
    reason="beast-mailbox-core not available",
)
async def test_agent_name_registration(mailbox_config, redis_available):
    """Test that agent name is registered in Redis on startup."""
    if not redis_available:
        pytest.skip("Redis not available")

    import redis.asyncio as redis

    agent = NameRegistrationTestAgent("test-name-reg", mailbox_config)

    # Verify agent not registered before startup
    redis_client = redis.Redis(
        host=mailbox_config.host,
        port=mailbox_config.port,
        db=mailbox_config.db if hasattr(mailbox_config, "db") else 0,
        decode_responses=True,
    )

    key = "beast:agents:test-name-reg"
    agent_info = await redis_client.get(key)
    assert agent_info is None, "Agent should not be registered before startup"

    # Check agent not in set
    is_member = await redis_client.sismember("beast:agents:all", "test-name-reg")
    assert not is_member, "Agent should not be in agents set before startup"

    # Start agent (should register name)
    await agent.startup()

    # Wait a moment for registration
    await asyncio.sleep(0.1)

    # Verify agent is registered
    agent_info_str = await redis_client.get(key)
    assert agent_info_str is not None, "Agent should be registered in Redis"

    # Verify agent info structure
    agent_info = json.loads(agent_info_str)
    assert agent_info["agent_id"] == "test-name-reg"
    assert agent_info["capabilities"] == ["test"]
    assert "registered_at" in agent_info
    assert "state" in agent_info

    # Verify agent in set
    is_member = await redis_client.sismember("beast:agents:all", "test-name-reg")
    assert is_member, "Agent should be in agents set after startup"

    # Verify key has expiration (TTL should be set)
    ttl = await redis_client.ttl(key)
    assert ttl > 0, "Agent registration key should have expiration"
    assert ttl <= 60, "Agent registration should expire within 60 seconds"

    await redis_client.aclose()

    # Cleanup
    await agent.shutdown()


@pytest.mark.asyncio
@pytest.mark.skipif(
    not pytest.importorskip("beast_mailbox_core"),
    reason="beast-mailbox-core not available",
)
async def test_agent_name_unregistration(mailbox_config, redis_available):
    """Test that agent name is unregistered from Redis on shutdown."""
    if not redis_available:
        pytest.skip("Redis not available")

    import redis.asyncio as redis

    agent = NameRegistrationTestAgent("test-name-unreg", mailbox_config)

    redis_client = redis.Redis(
        host=mailbox_config.host,
        port=mailbox_config.port,
        db=mailbox_config.db if hasattr(mailbox_config, "db") else 0,
        decode_responses=True,
    )

    # Start agent
    await agent.startup()
    await asyncio.sleep(0.1)

    # Verify agent is registered
    key = "beast:agents:test-name-unreg"
    agent_info = await redis_client.get(key)
    assert agent_info is not None, "Agent should be registered"

    is_member = await redis_client.sismember("beast:agents:all", "test-name-unreg")
    assert is_member, "Agent should be in agents set"

    # Shutdown agent (should unregister)
    await agent.shutdown()

    # Wait a moment for unregistration
    await asyncio.sleep(0.1)

    # Verify agent is unregistered
    agent_info = await redis_client.get(key)
    assert agent_info is None, "Agent should be unregistered from Redis"

    # Verify agent not in set
    is_member = await redis_client.sismember("beast:agents:all", "test-name-unreg")
    assert not is_member, "Agent should not be in agents set after shutdown"

    await redis_client.aclose()


@pytest.mark.asyncio
@pytest.mark.skipif(
    not pytest.importorskip("beast_mailbox_core"),
    reason="beast-mailbox-core not available",
)
async def test_multiple_agents_registration(mailbox_config, redis_available):
    """Test that multiple agents can be registered simultaneously."""
    if not redis_available:
        pytest.skip("Redis not available")

    import redis.asyncio as redis

    agent1 = NameRegistrationTestAgent("test-agent-1", mailbox_config)
    agent2 = NameRegistrationTestAgent("test-agent-2", mailbox_config)
    agent3 = NameRegistrationTestAgent("test-agent-3", mailbox_config)

    redis_client = redis.Redis(
        host=mailbox_config.host,
        port=mailbox_config.port,
        db=mailbox_config.db if hasattr(mailbox_config, "db") else 0,
        decode_responses=True,
    )

    # Start all agents
    await agent1.startup()
    await agent2.startup()
    await agent3.startup()

    await asyncio.sleep(0.1)

    # Verify all agents registered
    for agent_id in ["test-agent-1", "test-agent-2", "test-agent-3"]:
        key = f"beast:agents:{agent_id}"
        agent_info = await redis_client.get(key)
        assert agent_info is not None, f"Agent {agent_id} should be registered"

        is_member = await redis_client.sismember("beast:agents:all", agent_id)
        assert is_member, f"Agent {agent_id} should be in agents set"

    # Verify all agents in set
    all_agents = await redis_client.smembers("beast:agents:all")
    assert "test-agent-1" in all_agents
    assert "test-agent-2" in all_agents
    assert "test-agent-3" in all_agents

    # Cleanup
    await agent1.shutdown()
    await agent2.shutdown()
    await agent3.shutdown()

    await asyncio.sleep(0.1)

    # Verify all unregistered
    all_agents = await redis_client.smembers("beast:agents:all")
    assert "test-agent-1" not in all_agents
    assert "test-agent-2" not in all_agents
    assert "test-agent-3" not in all_agents

    await redis_client.aclose()


@pytest.mark.asyncio
@pytest.mark.skipif(
    not pytest.importorskip("beast_mailbox_core"),
    reason="beast-mailbox-core not available",
)
async def test_agent_name_registration_no_mailbox():
    """Test that agent name registration is skipped when mailbox is not configured."""
    agent = NameRegistrationTestAgent("test-no-mailbox")

    # Should not fail even without mailbox
    await agent.startup()

    # Agent should still start successfully
    assert agent.ready()

    await agent.shutdown()


@pytest.mark.asyncio
@pytest.mark.skipif(
    not pytest.importorskip("beast_mailbox_core"),
    reason="beast-mailbox-core not available",
)
async def test_agent_registration_uses_mailbox_connection(
    mailbox_config, redis_available
):
    """Test that agent registration uses the same Redis connection as mailbox."""
    if not redis_available:
        pytest.skip("Redis not available")

    import redis.asyncio as redis

    agent = NameRegistrationTestAgent("test-connection", mailbox_config)

    # Start agent
    await agent.startup()
    await asyncio.sleep(0.1)

    # Verify agent registered in same Redis DB as mailbox config
    redis_client = redis.Redis(
        host=mailbox_config.host,
        port=mailbox_config.port,
        db=mailbox_config.db if hasattr(mailbox_config, "db") else 0,
        decode_responses=True,
    )

    key = "beast:agents:test-connection"
    agent_info = await redis_client.get(key)
    assert agent_info is not None, "Agent should be registered using mailbox connection"

    # Verify host and port match
    # (Connection success confirms we're using the same Redis instance)

    await redis_client.aclose()
    await agent.shutdown()
