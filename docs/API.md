# API Reference

Complete API reference for `beast-agent`.

---

## 📚 Table of Contents

- [BaseAgent](#baseagent)
- [AgentConfig](#agentconfig)
- [Types](#types)
- [Decorators](#decorators)

---

## BaseAgent

### Class: `BaseAgent`

Abstract base class for all Beast Mode agents.

**Module**: `beast_agent.base_agent`

#### Constructor

Initializes a new agent instance.

```python
BaseAgent(
    agent_id: str,
    capabilities: List[str],
    mailbox_url: Optional[Union[str, MailboxConfig]] = None,
    config: Optional[AgentConfig] = None
)
```

**Parameters**:
- `agent_id` (str, required): Unique identifier for this agent instance
- `capabilities` (List[str], required): List of capability names this agent provides
- `mailbox_url` (Optional[Union[str, MailboxConfig]]): Redis connection configuration
  - `str`: Redis URL string (e.g., `"redis://localhost:6379"`) for unauthenticated connections
  - `MailboxConfig`: Advanced configuration object with authentication support (recommended for production)
  - `None`: Uses `REDIS_URL` environment variable
- `config` (AgentConfig, optional): Agent configuration (defaults to env vars)

**Raises**:
- `pydantic.ValidationError`: If config validation fails

**Example**:
```python
from beast_agent import BaseAgent, AgentConfig

# Example 1: Unauthenticated connection (string URL)
config = AgentConfig(log_level="DEBUG")
agent = MyAgent(
    agent_id="my-agent",
    capabilities=["cap1", "cap2"],
    mailbox_url="redis://localhost:6379",
    config=config
)

# Example 2: Authenticated connection (MailboxConfig) - Recommended for production
from beast_mailbox_core import MailboxConfig
import os

mailbox_config = MailboxConfig(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    password=os.getenv("REDIS_PASSWORD"),
    db=0
)

agent = MyAgent(
    agent_id="my-agent",
    capabilities=["cap1", "cap2"],
    mailbox_url=mailbox_config,  # Pass MailboxConfig object for authenticated clusters
    config=config
)
```

#### Attributes

- `agent_id` (str): Unique identifier for this agent instance
- `capabilities` (List[str]): List of capability names this agent provides
- `state` (AgentState): Current agent lifecycle state (read-only)
- `config` (AgentConfig): Agent configuration (read-only)

#### Methods

##### `async startup() -> None`

Initialize agent and register with mailbox.

**Lifecycle**:
1. Transitions to `INITIALIZING` state
2. Connects to mailbox (v0.2.0)
3. Calls `on_startup()` hook
4. Transitions to `READY` state

**Example**:
```python
await agent.startup()
assert agent.state == AgentState.READY
```

##### `async shutdown() -> None`

Gracefully shutdown the agent.

**Lifecycle**:
1. Transitions to `STOPPING` state
2. Calls `on_shutdown()` hook
3. Disconnects from mailbox (v0.2.0)
4. Transitions to `STOPPED` state

**Example**:
```python
await agent.shutdown()
assert agent.state == AgentState.STOPPED
```

##### `abstract async on_startup() -> None`

Subclass hook for custom startup logic.

**Override** to add agent-specific initialization:
```python
async def on_startup(self) -> None:
    """Initialize database connection."""
    self.db = await connect_to_database()
```

##### `abstract async on_shutdown() -> None`

Subclass hook for custom shutdown logic.

**Override** to add agent-specific cleanup:
```python
async def on_shutdown(self) -> None:
    """Close database connection."""
    await self.db.close()
```

##### `health_check() -> HealthStatus`

Return agent health status.

**Returns**: `HealthStatus` object with current agent state

**Example**:
```python
health = agent.health_check()
print(f"Healthy: {health.healthy}, State: {health.state}")
```

##### `ready() -> bool`

Return True if agent is ready to handle messages.

**Returns**: `True` if agent state is `READY` or `RUNNING`

**Example**:
```python
if agent.ready():
    await agent.process_message(message)
```

##### `register_handler(message_type: str, handler: Callable) -> None`

Register handler for message type.

**Parameters**:
- `message_type` (str): Message type to handle (e.g., "TASK_REQUEST")
- `handler` (Callable): Async callable to handle messages of this type

**Example**:
```python
async def handle_task_request(message: dict) -> None:
    """Handle task request messages."""
    pass

agent.register_handler("TASK_REQUEST", handle_task_request)
```

##### `async send_message(target: str, message_type: str, content: Dict[str, Any]) -> str`

Send message to target agent via mailbox.

**Parameters**:
- `target` (str): Target agent ID
- `message_type` (str): Message type (e.g., "HELP_REQUEST")
- `content` (Dict[str, Any]): Message content dictionary

**Returns**: Message ID from mailbox service

**Raises**: `RuntimeError` if mailbox is not initialized

**Note**: Requires mailbox integration (v0.2.0+). Message sending works with `beast-mailbox-core`.

**Example**:
```python
await agent.startup()
message_id = await agent.send_message(
    target="other-agent",
    message_type="HELP_REQUEST",
    content={"request": "I need help"}
)
```

##### `async discover_agents() -> List[str]`

Discover all active agents on the cluster.

**Returns**: List of active agent IDs

**Raises**: `RuntimeError` if mailbox is not initialized

**Example**:
```python
await agent.startup()
all_agents = await agent.discover_agents()
print(f"Found {len(all_agents)} agents: {all_agents}")
```

##### `async get_agent_info(agent_id: str) -> Optional[Dict[str, Any]]`

Get metadata for a specific agent.

**Parameters**:
- `agent_id` (str): Agent ID to query

**Returns**: Agent metadata dictionary (agent_id, capabilities, state, registered_at) or None if not found

**Raises**: `RuntimeError` if mailbox is not initialized

**Example**:
```python
agent_info = await agent.get_agent_info("other-agent-id")
if agent_info:
    print(f"Capabilities: {agent_info['capabilities']}")
    print(f"State: {agent_info['state']}")
```

##### `async find_agents_by_capability(capability: str) -> List[Dict[str, Any]]`

Find all agents that provide a specific capability.

**Parameters**:
- `capability` (str): Capability name to search for

**Returns**: List of agent metadata dictionaries for agents with the capability

**Raises**: `RuntimeError` if mailbox is not initialized

**Example**:
```python
search_agents = await agent.find_agents_by_capability("search")
for agent_info in search_agents:
    print(f"Found search agent: {agent_info['agent_id']}")
```

##### `async handle_message(message: Dict[str, Any]) -> None`

Route message to registered handler.

**Parameters**:
- `message` (Dict[str, Any]): Message dictionary with 'type' and 'content' keys

**Message Format**:
```python
{
    "type": "MESSAGE_TYPE",
    "content": {...}
}
```

**Example**:
```python
message = {
    "type": "TASK_REQUEST",
    "content": {"task_id": "123", "data": {...}}
}
await agent.handle_message(message)
```

---

## AgentConfig

### Class: `AgentConfig`

Pydantic model for agent configuration validation.

**Module**: `beast_agent.models`

#### Constructor

```python
AgentConfig(
    log_level: str = "INFO",
    heartbeat_interval: int = 30
)
```

**Parameters**:
- `log_level` (str, default="INFO"): Python logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `heartbeat_interval` (int, default=30): Heartbeat interval in seconds (minimum: 1)

**Raises**:
- `pydantic.ValidationError`: If validation fails

**Example**:
```python
from beast_agent import AgentConfig

config = AgentConfig(log_level="DEBUG", heartbeat_interval=60)
```

#### Class Methods

##### `from_env() -> AgentConfig`

Load configuration from environment variables.

**Environment Variables**:
- `AGENT_LOG_LEVEL`: Logging level (default: INFO)
- `AGENT_HEARTBEAT_INTERVAL`: Heartbeat interval in seconds (default: 30)

**Returns**: `AgentConfig` instance loaded from environment

**Example**:
```python
import os
os.environ["AGENT_LOG_LEVEL"] = "DEBUG"
config = AgentConfig.from_env()
assert config.log_level == "DEBUG"
```

##### `from_dict(data: Dict[str, Any]) -> AgentConfig`

Create AgentConfig from dictionary.

**Parameters**:
- `data` (Dict[str, Any]): Dictionary with config values

**Returns**: `AgentConfig` instance

**Raises**:
- `pydantic.ValidationError`: If data is invalid

**Example**:
```python
data = {"log_level": "WARNING", "heartbeat_interval": 60}
config = AgentConfig.from_dict(data)
```

#### Instance Methods

##### `to_dict() -> Dict[str, Any]`

Convert AgentConfig to dictionary.

**Returns**: Dictionary representation of configuration

**Example**:
```python
config = AgentConfig(log_level="DEBUG")
data = config.to_dict()
assert data["log_level"] == "DEBUG"
```

##### `get_log_level_int() -> int`

Get log level as Python logging constant.

**Returns**: Integer log level constant (e.g., `logging.INFO`)

**Example**:
```python
config = AgentConfig(log_level="DEBUG")
assert config.get_log_level_int() == logging.DEBUG
```

---

## Types

### Enum: `AgentState`

Agent lifecycle states.

**Module**: `beast_agent.types`

**Values**:
- `INITIALIZING`: Agent is initializing
- `READY`: Agent is ready to handle messages
- `RUNNING`: Agent is processing messages
- `STOPPING`: Agent is shutting down
- `STOPPED`: Agent is stopped
- `ERROR`: Agent is in error state

**Example**:
```python
from beast_agent import AgentState

if agent.state == AgentState.READY:
    await agent.process_message(message)
```

### Class: `HealthStatus`

Agent health status dataclass.

**Module**: `beast_agent.types`

#### Attributes

- `healthy` (bool): True if agent is healthy
- `state` (AgentState): Current agent state
- `last_heartbeat` (datetime): Last heartbeat timestamp
- `message_queue_size` (int): Current message queue size
- `error_count` (int): Total error count
- `metadata` (Dict[str, Any]): Additional metadata

**Example**:
```python
from beast_agent import HealthStatus

health = agent.health_check()
print(f"Healthy: {health.healthy}")
print(f"State: {health.state.value}")
print(f"Errors: {health.error_count}")
print(f"Metadata: {health.metadata}")
```

---

## Decorators

### Function: `capability(name: str, version: str = "1.0.0") -> Callable`

Decorator to mark methods as agent capabilities.

**Module**: `beast_agent.decorators`

**Parameters**:
- `name` (str, required): Capability name
- `version` (str, default="1.0.0"): Capability version

**Returns**: Decorated function with capability metadata

**Example**:
```python
from beast_agent.decorators import capability

class MyAgent(BaseAgent):
    @capability("process_document", version="1.0.0")
    async def process_document(self, document: str) -> dict:
        """Process a document."""
        return {"status": "processed"}
```

**Metadata**:
- `func._capability_name`: Capability name
- `func._capability_version`: Capability version

---

## Exceptions

### `pydantic.ValidationError`

Raised when configuration validation fails.

**Module**: `pydantic`

**Example**:
```python
from pydantic import ValidationError
from beast_agent import AgentConfig

try:
    config = AgentConfig(log_level="INVALID")
except ValidationError as e:
    print(f"Validation error: {e}")
```

---

## See Also

- [Agent Development Guide](AGENT_DEVELOPMENT.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Requirements](../.kiro/specs/requirements.md)

