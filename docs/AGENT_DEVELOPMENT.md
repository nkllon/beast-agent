# Agent Development Guide

This guide explains how to create custom agents using `beast-agent`.

---

## 📚 Table of Contents

- [Quick Start](#quick-start)
- [Creating a Custom Agent](#creating-a-custom-agent)
- [Lifecycle Methods](#lifecycle-methods)
- [Capabilities](#capabilities)
- [Message Handling](#message-handling)
- [Configuration](#configuration)
- [Best Practices](#best-practices)

---

## Quick Start

Here's a minimal example of a custom agent:

```python
import asyncio
from beast_agent import BaseAgent
from beast_agent.decorators import capability


class SimpleAgent(BaseAgent):
    """A simple agent with basic capabilities."""

    def __init__(self):
        super().__init__(
            agent_id="simple-agent",
            capabilities=["process_data", "echo"]
        )

    async def on_startup(self) -> None:
        """Initialize agent-specific resources."""
        print(f"SimpleAgent {self.agent_id} starting up...")

    async def on_shutdown(self) -> None:
        """Cleanup agent-specific resources."""
        print(f"SimpleAgent {self.agent_id} shutting down...")

    @capability("process_data", version="1.0.0")
    async def process_data(self, data: dict) -> dict:
        """Process incoming data."""
        return {"status": "processed", "result": data}

    @capability("echo", version="1.0.0")
    async def echo(self, message: str) -> str:
        """Echo back a message."""
        return f"Echo: {message}"


async def main():
    """Run the agent."""
    agent = SimpleAgent()
    
    await agent.startup()
    health = agent.health_check()
    print(f"Agent healthy: {health.healthy}")
    
    await agent.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Creating a Custom Agent

### Step 1: Inherit from BaseAgent

All custom agents must inherit from `BaseAgent`:

```python
from beast_agent import BaseAgent

class MyAgent(BaseAgent):
    pass
```

### Step 2: Implement Required Methods

You must implement two abstract methods:

```python
class MyAgent(BaseAgent):
    async def on_startup(self) -> None:
        """Initialize agent-specific resources."""
        pass
    
    async def on_shutdown(self) -> None:
        """Cleanup agent-specific resources."""
        pass
```

### Step 3: Initialize with Agent ID and Capabilities

Override `__init__` and call `super().__init__()`:

```python
class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="my-agent",
            capabilities=["capability1", "capability2"]
        )
```

**Parameters**:
- `agent_id` (str, required): Unique identifier for this agent instance
- `capabilities` (List[str], required): List of capability names this agent provides
- `mailbox_url` (str, optional): Redis mailbox URL (defaults to `REDIS_URL` env var)
- `config` (AgentConfig, optional): Agent configuration (defaults to env vars)

---

## Lifecycle Methods

### on_startup()

Called during `startup()` lifecycle, after mailbox connection but before READY state.

**Use Cases**:
- Initialize agent-specific resources
- Connect to external services
- Load configuration files
- Register message handlers

**Example**:
```python
async def on_startup(self) -> None:
    """Initialize database connection."""
    self.db = await connect_to_database()
    self._logger.info("Database connected")
```

### on_shutdown()

Called during `shutdown()` lifecycle, before mailbox disconnection.

**Use Cases**:
- Close connections
- Save state
- Cleanup resources

**Example**:
```python
async def on_shutdown(self) -> None:
    """Cleanup database connection."""
    if self.db:
        await self.db.close()
    self._logger.info("Database disconnected")
```

### Lifecycle Flow

```
INITIALIZING
    ↓ startup()
READY → on_startup() called here
    ↓ (optional)
RUNNING
    ↓ shutdown()
STOPPING → on_shutdown() called here
    ↓
STOPPED
```

---

## Capabilities

Capabilities are agent features that can be discovered and invoked by other agents.

### Declaring Capabilities

Use the `@capability` decorator:

```python
from beast_agent.decorators import capability

class MyAgent(BaseAgent):
    @capability("process_data", version="1.0.0")
    async def process_data(self, data: dict) -> dict:
        """Process incoming data."""
        return {"status": "processed"}
```

**Decorator Parameters**:
- `name` (str, required): Capability name (must match method name or be specified)
- `version` (str, optional): Capability version (defaults to "1.0.0")

### Capability Best Practices

1. **Async Methods**: All capabilities should be `async` methods
2. **Type Hints**: Use type hints for parameters and return values
3. **Documentation**: Add docstrings explaining what the capability does
4. **Error Handling**: Handle errors gracefully within capabilities
5. **Idempotency**: Design capabilities to be idempotent when possible

---

## Message Handling

Agents can send and receive messages via the mailbox (v0.2.0 integration).

### Registering Message Handlers

Register handlers for specific message types:

```python
async def on_startup(self) -> None:
    """Register message handlers."""
    self.register_handler("HELP_REQUEST", self.handle_help_request)
    self.register_handler("DATA_UPDATE", self.handle_data_update)

async def handle_help_request(self, content: dict) -> None:
    """Handle help request messages."""
    sender = content.get("sender")
    self._logger.info(f"Received help request from {sender}")

async def handle_data_update(self, content: dict) -> None:
    """Handle data update messages."""
    data = content.get("data")
    # Process data update...
```

### Sending Messages

Send messages to other agents:

```python
async def request_help(self, target_agent: str) -> None:
    """Send help request to another agent."""
    await self.send_message(
        target=target_agent,
        message_type="HELP_REQUEST",
        content={"request": "I need help", "sender": self.agent_id}
    )
```

**Note**: Message sending requires mailbox integration (v0.2.0). In v0.1.0, `send_message()` logs but doesn't actually send.

---

## Configuration

### Environment Variables

Configure agents via environment variables:

```bash
export AGENT_LOG_LEVEL="DEBUG"
export AGENT_HEARTBEAT_INTERVAL="60"
export REDIS_URL="redis://localhost:6379"
```

**Variables**:
- `AGENT_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `AGENT_HEARTBEAT_INTERVAL`: Heartbeat interval in seconds (minimum: 1)
- `REDIS_URL`: Redis mailbox connection URL

### Programmatic Configuration

Pass configuration via constructor:

```python
from beast_agent import BaseAgent, AgentConfig

config = AgentConfig(log_level="DEBUG", heartbeat_interval=60)

agent = MyAgent(
    agent_id="my-agent",
    capabilities=["cap1"],
    config=config
)
```

### Configuration Validation

Configuration is validated using pydantic. Invalid values raise `pydantic.ValidationError`:

```python
try:
    agent = MyAgent(agent_id="my-agent", capabilities=["cap1"])
except ValidationError as e:
    print(f"Configuration error: {e}")
```

---

## Best Practices

### 1. Agent ID Naming

Use descriptive, unique agent IDs:

```python
# Good
agent_id="repo-agent-python-monorepo"
agent_id="deployment-agent-production"

# Bad
agent_id="agent1"
agent_id="test"
```

### 2. Error Handling

Handle errors gracefully:

```python
async def on_startup(self) -> None:
    try:
        self.db = await connect_to_database()
    except ConnectionError as e:
        self._logger.error(f"Database connection failed: {e}")
        raise  # Re-raise if critical
```

### 3. Logging

Use the agent's logger (not Python's root logger):

```python
# Good
self._logger.info("Processing data")
self._logger.error("Processing failed", exc_info=True)

# Bad
import logging
logging.info("Processing data")  # Don't use root logger
```

### 4. State Management

Track agent state appropriately:

```python
async def process_data(self, data: dict) -> dict:
    if self.state != AgentState.READY:
        raise RuntimeError("Agent not ready")
    
    # Process data...
```

### 5. Resource Cleanup

Always cleanup resources in `on_shutdown()`:

```python
async def on_shutdown(self) -> None:
    """Cleanup all resources."""
    if hasattr(self, "db") and self.db:
        await self.db.close()
    
    if hasattr(self, "cache") and self.cache:
        await self.cache.flush()
```

### 6. Capability Versioning

Version your capabilities appropriately:

```python
@capability("process_data", version="1.0.0")
async def process_data(self, data: dict) -> dict:
    # v1.0.0 implementation
    pass

@capability("process_data_v2", version="2.0.0")
async def process_data_v2(self, data: dict) -> dict:
    # v2.0.0 implementation with breaking changes
    pass
```

---

## Examples

See `examples/simple_agent.py` for a complete working example.

---

## Next Steps

- Read [API Reference](API.md) for complete API documentation
- Read [Deployment Guide](DEPLOYMENT.md) for deployment patterns
- Review [Requirements](../.kiro/specs/requirements.md) for functional requirements

