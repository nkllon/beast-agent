# Integration with beast-mailbox-core

This guide shows how to use `beast-agent` with `beast-mailbox-core` for production multi-agent clusters.

---

## Overview

`beast-agent` integrates with `beast-mailbox-core` to provide:
- Redis-backed message passing between agents
- Agent registration and discovery on the cluster
- Authenticated connections to production Redis clusters

---

## Installation

Both packages are required:

```bash
pip install beast-agent beast-mailbox-core
```

---

## Authentication: Using MailboxConfig

**For production clusters with authentication, you MUST use `MailboxConfig`:**

```python
from beast_agent import BaseAgent
from beast_mailbox_core import MailboxConfig
import os

class MyAgent(BaseAgent):
    def __init__(self):
        # Create MailboxConfig with password for authenticated Redis
        mailbox_config = MailboxConfig(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD"),  # Required for authenticated clusters
            db=int(os.getenv("REDIS_DB", "0")),
            stream_prefix="mailbox",
            enable_recovery=True,
        )
        
        super().__init__(
            agent_id="my-agent",
            capabilities=["my-capability"],
            mailbox_url=mailbox_config  # Pass MailboxConfig object, not URL string
        )
    
    async def on_startup(self) -> None:
        self._logger.info("Connected to authenticated cluster!")
    
    async def on_shutdown(self) -> None:
        self._logger.info("Disconnecting...")
```

**Important**: The `mailbox_url` parameter in `BaseAgent.__init__()` accepts:
- **String URL**: `"redis://localhost:6379"` (unauthenticated connections only)
- **MailboxConfig object**: For authenticated/production clusters (recommended)
- **None**: Uses `REDIS_URL` environment variable

**URL string parsing does NOT support passwords** - use `MailboxConfig` for authenticated clusters.

---

## Agent Discovery

After your agent starts, it automatically registers on the cluster. Use discovery methods to find other agents:

### Discover All Agents

```python
async def on_startup(self) -> None:
    # Discover all active agents on the cluster
    all_agents = await self.discover_agents()
    self._logger.info(f"Found {len(all_agents)} agents: {all_agents}")
    # Output: Found 3 agents: ['agent-1', 'agent-2', 'agent-3']
```

### Get Agent Metadata

```python
# Get metadata for a specific agent
agent_info = await self.get_agent_info("other-agent-id")
if agent_info:
    self._logger.info(f"Agent: {agent_info['agent_id']}")
    self._logger.info(f"Capabilities: {agent_info['capabilities']}")
    self._logger.info(f"State: {agent_info['state']}")
    self._logger.info(f"Registered: {agent_info['registered_at']}")
```

### Find Agents by Capability

```python
# Find all agents that provide a specific capability
search_agents = await self.find_agents_by_capability("search")
for agent_info in search_agents:
    self._logger.info(f"Found search agent: {agent_info['agent_id']}")
    
    # Send message to discovered agent
    await self.send_message(
        target=agent_info["agent_id"],
        message_type="HELP_REQUEST",
        content={"request": "I need help with search"}
    )
```

---

## Redis Keys Used by Cluster

The cluster uses these Redis keys for discovery:

- **`beast:agents:all`** - Redis SET containing all active agent IDs
  - Add: Automatically when agent starts (`_register_agent_name()`)
  - Remove: Automatically when agent shuts down (`_unregister_agent_name()`)
  - Query: Use `discover_agents()` method

- **`beast:agents:{agent_id}`** - Redis STRING with JSON metadata
  - Contains: `agent_id`, `capabilities`, `state`, `registered_at` timestamp
  - Expires: 60 seconds (should be refreshed by heartbeat mechanism)
  - Query: Use `get_agent_info(agent_id)` method

---

## Complete Integration Example

```python
"""Complete example: Authenticated agent with discovery and messaging."""

import asyncio
import os
from beast_agent import BaseAgent
from beast_mailbox_core import MailboxConfig


class IntegratedAgent(BaseAgent):
    """Agent that demonstrates complete integration with beast-mailbox-core."""

    def __init__(self):
        # Create MailboxConfig with authentication
        mailbox_config = MailboxConfig(
            host=os.getenv("REDIS_HOST", "192.168.1.119"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD", "beastmode2025"),
            db=int(os.getenv("REDIS_DB", "0")),
            stream_prefix="mailbox",
            enable_recovery=True,
        )

        super().__init__(
            agent_id="integrated-example-agent",
            capabilities=["discover", "communicate", "help"],
            mailbox_url=mailbox_config,
        )

    async def on_startup(self) -> None:
        """Called after mailbox connection is established."""
        self._logger.info("Connected to authenticated cluster!")

        # Register message handlers
        self.register_handler("HELP_REQUEST", self.handle_help_request)
        self.register_handler("CHAT_MESSAGE", self.handle_chat)

        # Discover all agents on cluster
        all_agents = await self.discover_agents()
        self._logger.info(f"Found {len(all_agents)} agents on cluster: {all_agents}")

        # Get info about each agent
        for agent_id in all_agents:
            if agent_id != self.agent_id:  # Skip ourselves
                agent_info = await self.get_agent_info(agent_id)
                if agent_info:
                    self._logger.info(
                        f"  - {agent_id}: {agent_info.get('capabilities', [])}"
                    )

        # Find agents with specific capabilities
        helpers = await self.find_agents_by_capability("help")
        self._logger.info(f"Found {len(helpers)} agents with 'help' capability")

        # Send greeting to first discovered agent
        if all_agents and len(all_agents) > 1:
            other_agent = next(
                (aid for aid in all_agents if aid != self.agent_id), None
            )
            if other_agent:
                await self.send_message(
                    target=other_agent,
                    message_type="CHAT_MESSAGE",
                    content={
                        "message": "Hello from integrated agent!",
                        "sender": self.agent_id,
                    },
                )

    async def handle_help_request(self, content: dict) -> None:
        """Handle help request from another agent."""
        sender = content.get("sender", "unknown")
        request = content.get("request", "")
        self._logger.info(f"Received help request from {sender}: {request}")

        # Send response back
        await self.send_message(
            target=sender,
            message_type="HELP_RESPONSE",
            content={
                "response": "I can help!",
                "agent_id": self.agent_id,
                "capabilities": self.capabilities,
            },
        )

    async def handle_chat(self, content: dict) -> None:
        """Handle chat message from another agent."""
        sender = content.get("sender", "unknown")
        message = content.get("message", "")
        self._logger.info(f"Received chat from {sender}: {message}")

    async def on_shutdown(self) -> None:
        """Called before mailbox disconnection."""
        self._logger.info("Disconnecting from cluster...")


async def main():
    """Run the integrated agent."""
    agent = IntegratedAgent()

    # Start agent (connects to Redis and registers on cluster)
    await agent.startup()

    # Keep agent running
    try:
        agent._logger.info("Agent running... Press Ctrl+C to stop")
        await asyncio.sleep(3600)  # Run for 1 hour
    except KeyboardInterrupt:
        agent._logger.info("Shutting down...")
    finally:
        await agent.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Environment Variables

Configure via environment variables (recommended for production):

```bash
# Redis connection
export REDIS_HOST="192.168.1.119"
export REDIS_PORT="6379"
export REDIS_PASSWORD="beastmode2025"
export REDIS_DB="0"

# Agent configuration
export AGENT_LOG_LEVEL="INFO"
export AGENT_HEARTBEAT_INTERVAL="30"
```

Or use secrets management (AWS Secrets Manager, HashiCorp Vault, etc.) instead of environment variables for production.

---

## API Reference

### BaseAgent.__init__()

```python
BaseAgent(
    agent_id: str,
    capabilities: List[str],
    mailbox_url: Optional[Union[str, MailboxConfig]] = None,
    config: Optional[AgentConfig] = None
)
```

**Parameters:**
- `agent_id` (str): Unique identifier for this agent instance
- `capabilities` (List[str]): List of capability names this agent provides
- `mailbox_url` (Optional[Union[str, MailboxConfig]]): Redis connection configuration
  - `str`: Redis URL string (e.g., `"redis://localhost:6379"`) for unauthenticated connections
  - `MailboxConfig`: Advanced configuration object with authentication support (recommended for production)
  - `None`: Uses `REDIS_URL` environment variable
- `config` (Optional[AgentConfig]): Agent configuration (uses `AgentConfig.from_env()` if None)

---

## Troubleshooting

### Cannot Connect to Redis

**Problem**: Agent fails to connect to Redis cluster

**Solutions:**
1. Verify Redis host and port are correct
2. Check if password is required and provided via `MailboxConfig`
3. Ensure Redis is accessible from your network
4. Check firewall rules

### Cannot Discover Other Agents

**Problem**: `discover_agents()` returns empty list or doesn't find expected agents

**Solutions:**
1. Ensure all agents are started and have called `startup()`
2. Verify all agents are using the same Redis instance/database
3. Check Redis keys: `KEYS beast:agents:*` to see registered agents
4. Wait a moment after agent startup for registration to complete

### Authentication Errors

**Problem**: Connection fails with authentication error

**Solutions:**
1. Use `MailboxConfig` object instead of URL string
2. Verify password is correct
3. Check Redis ACL configuration if using ACLs

---

## Related Documentation

- **beast-mailbox-core API**: See [beast-mailbox-core documentation](https://github.com/nkllon/beast-mailbox-core)
- **BaseAgent API**: See `docs/API.md` in this repository
- **Examples**: See `examples/authenticated_agent.py` and `examples/discovery_example.py`

---

## Version Compatibility

- `beast-agent` >= 0.1.3 (includes discovery methods)
- `beast-mailbox-core` >= 0.3.0 (required for mailbox integration)

