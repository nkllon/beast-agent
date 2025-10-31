# Using beast-agent for Multi-Agent Communication

You are working on a component that needs to participate in the Beast Mode agent cluster. The `beast-agent` package provides the base class and infrastructure you need.

## Installation

If you're working on the production cluster, you can install `beast-agent` directly:

```bash
pip install beast-agent
```

Or pin a specific version:

```bash
pip install beast-agent==0.1.2
```

## Quick Start

### 1. Create Your Agent

Extend `BaseAgent` to create your agent:

```python
from beast_agent import BaseAgent
from beast_agent.decorators import capability

class MyAgent(BaseAgent):
    """Your agent implementation."""
    
    def __init__(self):
        super().__init__(
            agent_id="my-agent-id",  # Unique identifier - make it descriptive
            capabilities=["my_capability"],  # List of capabilities this agent provides
            mailbox_url=None  # Uses REDIS_URL env var, or pass redis://host:port
        )
    
    async def on_startup(self) -> None:
        """Called after mailbox connection is established."""
        # Your initialization code here
        self._logger.info("My agent is ready!")
    
    async def on_shutdown(self) -> None:
        """Called before mailbox disconnection."""
        # Your cleanup code here
        self._logger.info("My agent is shutting down")
```

### 2. Register Message Handlers

Handle incoming messages from other agents:

```python
async def on_startup(self) -> None:
    # Register handlers for message types
    self.register_handler("HELP_REQUEST", self.handle_help_request)
    self.register_handler("TASK_ASSIGNMENT", self.handle_task)
    
    self._logger.info("Handlers registered")

async def handle_help_request(self, content: dict) -> None:
    """Handle help request from another agent."""
    sender = content.get("sender")
    request = content.get("request")
    
    self._logger.info(f"Received help request from {sender}: {request}")
    
    # Send response back
    await self.send_message(
        target=sender,
        message_type="HELP_RESPONSE",
        content={"response": "I can help!", "agent_id": self.agent_id}
    )

async def handle_task(self, content: dict) -> None:
    """Handle task assignment."""
    task = content.get("task")
    # Process task...
    self._logger.info(f"Processing task: {task}")
```

### 3. Start Your Agent

Run your agent:

```python
import asyncio

async def main():
    agent = MyAgent()
    
    # Start agent (connects to mailbox and registers agent name on cluster)
    await agent.startup()
    
    # Agent is now registered on the cluster and can send/receive messages
    # Other agents can discover you via: beast:agents:all set in Redis
    # Your agent info is at: beast:agents:{your_agent_id}
    
    # Keep agent running
    try:
        await asyncio.sleep(3600)  # Run for 1 hour, or use your own loop
    except KeyboardInterrupt:
        pass
    finally:
        await agent.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

## Key Features

### Agent Name Registration (v0.1.2+)

When your agent starts, it automatically:
- ✅ Registers its name on the Redis cluster (`beast:agents:{agent_id}`)
- ✅ Adds itself to the active agents set (`beast:agents:all`)
- ✅ Publishes metadata: agent_id, capabilities, state, timestamp
- ✅ Uses the same Redis connection as mailbox (production cluster)

Other agents can discover you by:
- Querying `beast:agents:all` set to get all active agent IDs
- Reading `beast:agents:{agent_id}` to get your metadata

### Configuration

Configure via environment variables (for unauthenticated connections):

```bash
export REDIS_URL="redis://your-redis-host:6379"
export AGENT_LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
export AGENT_HEARTBEAT_INTERVAL="30"  # seconds
```

Or pass directly to constructor:

```python
# For unauthenticated connections - simple URL string
agent = MyAgent(
    agent_id="my-agent",
    capabilities=["my_cap"],
    mailbox_url="redis://redis-host:6379"
)
```

### Connecting with Authentication (Production Clusters)

**If your Redis cluster requires authentication, use `MailboxConfig`:**

```python
from beast_agent import BaseAgent
from beast_mailbox_core import MailboxConfig
import os

class MyAgent(BaseAgent):
    def __init__(self):
        # Create MailboxConfig with password for authenticated clusters
        mailbox_config = MailboxConfig(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD"),  # Required for authenticated clusters
            db=0
        )
        
        super().__init__(
            agent_id="my-agent",
            capabilities=["my_cap"],
            mailbox_url=mailbox_config  # Pass MailboxConfig object, not URL string
        )
```

**Important**: The `mailbox_url` parameter accepts:
- **String URL**: `"redis://host:port"` (for unauthenticated connections only)
- **MailboxConfig object**: For authenticated clusters or advanced configurations (recommended for production)
- **None**: Uses `REDIS_URL` environment variable

**For production clusters, always use `MailboxConfig`** - URL string parsing doesn't support passwords.

### Agent ID Best Practices

Use descriptive, unique agent IDs:

```python
# Good - descriptive and unique
agent_id="repo-agent-python-monorepo"
agent_id="deployment-agent-production"
agent_id="service-agent-api-main"

# Bad - not descriptive
agent_id="agent1"
agent_id="test"
```

## Example: Two Agents Chatting

Here's a complete example of two agents communicating:

```python
import asyncio
from beast_agent import BaseAgent

class ChatAgent(BaseAgent):
    def __init__(self, agent_id: str, partner_id: str):
        super().__init__(
            agent_id=agent_id,
            capabilities=["chat"]
        )
        self.partner_id = partner_id
    
    async def on_startup(self) -> None:
        self.register_handler("CHAT_MESSAGE", self.handle_chat)
        self._logger.info(f"{self.agent_id} ready to chat!")
    
    async def handle_chat(self, content: dict) -> None:
        message = content.get("message", "")
        sender = content.get("sender", "unknown")
        self._logger.info(f"{self.agent_id} received from {sender}: {message}")
    
    async def send_chat(self, message: str) -> None:
        await self.send_message(
            target=self.partner_id,
            message_type="CHAT_MESSAGE",
            content={"message": message, "sender": self.agent_id}
        )

async def main():
    # Create two agents
    agent1 = ChatAgent("agent-alice", "agent-bob")
    agent2 = ChatAgent("agent-bob", "agent-alice")
    
    # Start both
    await agent1.startup()
    await agent2.startup()
    
    # Let them chat
    await asyncio.sleep(1)
    await agent1.send_chat("Hello from Alice!")
    
    await asyncio.sleep(1)
    await agent2.send_chat("Hi Alice! Bob here.")
    
    # Keep running
    await asyncio.sleep(10)
    
    # Shutdown
    await agent1.shutdown()
    await agent2.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

## Requirements

- Python 3.9+
- Redis cluster accessible (configure via `REDIS_URL`)
- `beast-mailbox-core` (installed automatically with beast-agent)

## Resources

- **Package**: https://pypi.org/project/beast-agent/
- **Repository**: https://github.com/nkllon/beast-agent
- **Documentation**: See README.md and AGENT.md in the repository

## Next Steps

1. Install: `pip install beast-agent`
2. Create your agent class extending `BaseAgent`
3. Implement `on_startup()` and `on_shutdown()`
4. Register message handlers
5. Start your agent - it will automatically register on the cluster!
6. Other agents can discover you and send messages

Your agent name will be registered on the cluster automatically when you call `startup()`, making you discoverable by other agents on the same Redis cluster.

