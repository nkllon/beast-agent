"""Tests for agent discovery functionality.

Tests that agents can discover other agents on the cluster.
"""

import asyncio
import json
import pytest
from beast_agent import BaseAgent


class DiscoveryTestAgent(BaseAgent):
    """Test agent for discovery tests."""

    def __init__(self, agent_id: str, capabilities: list, mailbox_url=None):
        """Initialize test agent."""
        super().__init__(
            agent_id=agent_id, capabilities=capabilities, mailbox_url=mailbox_url
        )

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
async def test_discover_agents(mailbox_config, redis_available):
    """Test that agents can discover other agents on the cluster."""
    if not redis_available:
        pytest.skip("Redis not available")

    agent1 = DiscoveryTestAgent("discovery-agent-1", ["test"], mailbox_config)
    agent2 = DiscoveryTestAgent("discovery-agent-2", ["test"], mailbox_config)
    agent3 = DiscoveryTestAgent("discovery-agent-3", ["other"], mailbox_config)

    # Start all agents
    await agent1.startup()
    await agent2.startup()
    await agent3.startup()

    await asyncio.sleep(0.1)

    # Agent1 should discover all other agents
    agent_ids = await agent1.discover_agents()

    assert "discovery-agent-1" in agent_ids
    assert "discovery-agent-2" in agent_ids
    assert "discovery-agent-3" in agent_ids
    assert len(agent_ids) >= 3

    # Cleanup
    await agent1.shutdown()
    await agent2.shutdown()
    await agent3.shutdown()


@pytest.mark.asyncio
@pytest.mark.skipif(
    not pytest.importorskip("beast_mailbox_core"),
    reason="beast-mailbox-core not available",
)
async def test_get_agent_info(mailbox_config, redis_available):
    """Test that agents can get metadata for other agents."""
    if not redis_available:
        pytest.skip("Redis not available")

    agent1 = DiscoveryTestAgent(
        "info-agent-1", ["capability1", "capability2"], mailbox_config
    )
    agent2 = DiscoveryTestAgent("info-agent-2", ["other"], mailbox_config)

    await agent1.startup()
    await agent2.startup()

    await asyncio.sleep(0.1)

    # Agent2 should be able to get info about agent1
    agent_info = await agent2.get_agent_info("info-agent-1")

    assert agent_info is not None
    assert agent_info["agent_id"] == "info-agent-1"
    assert "capability1" in agent_info["capabilities"]
    assert "capability2" in agent_info["capabilities"]
    assert "registered_at" in agent_info
    assert "state" in agent_info

    # Cleanup
    await agent1.shutdown()
    await agent2.shutdown()


@pytest.mark.asyncio
@pytest.mark.skipif(
    not pytest.importorskip("beast_mailbox_core"),
    reason="beast-mailbox-core not available",
)
async def test_find_agents_by_capability(mailbox_config, redis_available):
    """Test that agents can find other agents by capability."""
    if not redis_available:
        pytest.skip("Redis not available")

    agent1 = DiscoveryTestAgent("cap-agent-1", ["search", "index"], mailbox_config)
    agent2 = DiscoveryTestAgent("cap-agent-2", ["search"], mailbox_config)
    agent3 = DiscoveryTestAgent("cap-agent-3", ["other"], mailbox_config)

    await agent1.startup()
    await agent2.startup()
    await agent3.startup()

    await asyncio.sleep(0.1)

    # Find all agents with "search" capability
    matching = await agent1.find_agents_by_capability("search")

    assert len(matching) >= 2
    agent_ids = [a["agent_id"] for a in matching]
    assert "cap-agent-1" in agent_ids
    assert "cap-agent-2" in agent_ids
    assert "cap-agent-3" not in agent_ids

    # Find agents with "other" capability
    matching = await agent1.find_agents_by_capability("other")
    assert len(matching) >= 1
    assert matching[0]["agent_id"] == "cap-agent-3"

    # Cleanup
    await agent1.shutdown()
    await agent2.shutdown()
    await agent3.shutdown()


@pytest.mark.asyncio
async def test_discover_agents_no_mailbox():
    """Test that discover_agents raises error when mailbox not initialized."""
    agent = DiscoveryTestAgent("no-mailbox-agent", ["test"])

    # Should raise RuntimeError before startup
    with pytest.raises(RuntimeError, match="Mailbox not initialized"):
        await agent.discover_agents()


@pytest.mark.asyncio
@pytest.mark.skipif(
    not pytest.importorskip("beast_mailbox_core"),
    reason="beast-mailbox-core not available",
)
async def test_discover_agents_empty_cluster(mailbox_config, redis_available):
    """Test discover_agents when no other agents are online."""
    if not redis_available:
        pytest.skip("Redis not available")

    agent = DiscoveryTestAgent("lonely-agent", ["test"], mailbox_config)
    await agent.startup()

    await asyncio.sleep(0.1)

    # Should at least find itself
    agent_ids = await agent.discover_agents()
    assert "lonely-agent" in agent_ids

    await agent.shutdown()
