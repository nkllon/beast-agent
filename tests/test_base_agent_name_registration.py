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

    def __init__(
        self,
        agent_id: str,
        mailbox_config=None,
        capability_graph_ttl: str | None = None,
    ):
        """Initialize test agent with optional mailbox config and Turtle capability graph."""
        kwargs = {}
        if capability_graph_ttl is not None:
            kwargs["capability_graph_ttl"] = capability_graph_ttl
        if mailbox_config:
            super().__init__(
                agent_id=agent_id,
                capabilities=["test"],
                mailbox_url=mailbox_config,
                **kwargs,
            )
        else:
            super().__init__(agent_id=agent_id, capabilities=["test"], **kwargs)

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


SAMPLE_CAPABILITY_TTL = """\
@prefix bh: <https://nkllon.com/ontology/beast-harness#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<urn:beast:endpoint:test-ttl-reg> a bh:AgentEndpoint ;
    rdfs:label "test-ttl-reg" ;
    bh:endpointId "test-ttl-reg" ;
    bh:driverId "beast-peer" ;
    bh:trustTier bh:RuntimeSelfAnnounced ;
    bh:defaultPosture bh:ObserveOnly ;
    bh:hasCapability bh:RepoFreePrompt .
"""


def test_capability_graph_ttl_health_metadata_without_mailbox():
    """BaseAgent accepts optional capability_graph_ttl and surfaces it in health metadata."""
    agent = NameRegistrationTestAgent(
        "test-ttl-local",
        capability_graph_ttl=SAMPLE_CAPABILITY_TTL,
    )
    assert agent.capability_graph_ttl == SAMPLE_CAPABILITY_TTL
    status = agent.health_check()
    assert status.metadata["has_capability_graph_ttl"] is True
    assert status.metadata["capability_graph_ttl"] == SAMPLE_CAPABILITY_TTL


@pytest.mark.asyncio
@pytest.mark.skipif(
    not pytest.importorskip("beast_mailbox_core"),
    reason="beast-mailbox-core not available",
)
async def test_agent_registration_publishes_capability_graph_ttl_and_announcement(
    mailbox_config, redis_available
):
    """Startup registers capability_graph_ttl in Redis and publishes to announcements stream."""
    if not redis_available:
        pytest.skip("Redis not available")

    import redis.asyncio as redis

    redis_client = redis.Redis(
        host=mailbox_config.host,
        port=mailbox_config.port,
        db=mailbox_config.db if hasattr(mailbox_config, "db") else 0,
        decode_responses=True,
    )
    stream_key = "beast:stream:global:announcements"
    before_len = await redis_client.xlen(stream_key)

    agent = NameRegistrationTestAgent(
        "test-ttl-reg",
        mailbox_config=mailbox_config,
        capability_graph_ttl=SAMPLE_CAPABILITY_TTL,
    )
    await agent.startup()
    await asyncio.sleep(0.1)

    try:
        raw_info = await redis_client.get("beast:agents:test-ttl-reg")
        assert raw_info is not None
        info = json.loads(raw_info)
        assert info["agent_id"] == "test-ttl-reg"
        assert info["capabilities"] == ["test"]
        assert info["capability_graph_ttl"] == SAMPLE_CAPABILITY_TTL

        # Legacy flat capability lookup must remain backwards-compatible
        matches = await agent.find_agents_by_capability("test")
        assert any(m["agent_id"] == "test-ttl-reg" for m in matches)

        # Global announcement stream must contain the CAPABILITY_ANNOUNCEMENT envelope
        after_entries = await redis_client.xrevrange(stream_key, count=10)
        assert (
            len(after_entries) > 0 and await redis_client.xlen(stream_key) > before_len
        )
        matching_envelopes = []
        for _entry_id, fields in after_entries:
            envelope_raw = fields.get("envelope")
            if envelope_raw:
                env = json.loads(envelope_raw)
                if env.get("header", {}).get("sender") == "test-ttl-reg":
                    matching_envelopes.append(env)
        assert (
            matching_envelopes
        ), "Expected CAPABILITY_ANNOUNCEMENT on announcements stream"
        latest = matching_envelopes[0]
        assert latest["payload"]["type"] == "CAPABILITY_ANNOUNCEMENT"
        assert latest["payload"]["capability_graph_ttl"] == SAMPLE_CAPABILITY_TTL
        assert latest["payload"]["capabilities"] == ["test"]
    finally:
        await agent.shutdown()
        await redis_client.aclose()
