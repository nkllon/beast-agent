# Beast Agent

> **Base agent class for ALL Beast Mode agents**

[![PyPI version](https://img.shields.io/pypi/v/beast-agent?label=PyPI&color=blue)](https://pypi.org/project/beast-agent/)
[![Python Versions](https://img.shields.io/pypi/pyversions/beast-agent.svg)](https://pypi.org/project/beast-agent/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## 🎯 Purpose

**The foundational base class (`BaseAgent`) that EVERY Beast Mode agent inherits from.**

This package provides:
- ✅ Standardized agent lifecycle (startup, shutdown, health checks)
- ✅ Message handling via beast-mailbox-core integration
- ✅ Agent registration and discovery
- ✅ Capability declaration and management
- ✅ Optional logging/telemetry hooks
- ✅ Configuration management

**Architectural Clarity:**
- `beast-agent` = **Low-level base class** (every agent IS-A beast-agent)
- `beast-agentic-framework` = **High-level orchestration** (multi-agent coordination)

---

## 🚀 Quick Start

### Installation

```bash
pip install beast-agent
```

### Configuration

Configure Redis connection via environment variable (for unauthenticated connections):

```bash
export REDIS_URL="redis://localhost:6379"
```

Or pass directly to constructor:
- **String URL**: `mailbox_url="redis://localhost:6379"` (unauthenticated only)
- **MailboxConfig object**: For authenticated/production clusters (see Authentication section)
- **None**: Uses `REDIS_URL` environment variable

### Create Your First Agent

```python
from beast_agent import BaseAgent
from beast_agent.decorators import capability

class MyAgent(BaseAgent):
    """Simple agent with a single capability"""
    
    def __init__(self):
        super().__init__(
            agent_id="my-agent",
            capabilities=["process_data"]
        )
    
    @capability("process_data")
    async def process_data(self, data: dict) -> dict:
        """Process data and return results"""
        # Your agent logic here
        return {"status": "processed", "result": data}

# Run the agent
async def main():
    agent = MyAgent()
    await agent.startup()
    # Agent is now ready to handle messages
    
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## 🔐 Connecting with Authentication

If your Redis cluster requires authentication, use `MailboxConfig` instead of a URL string:

```python
from beast_agent import BaseAgent
from beast_mailbox_core import MailboxConfig
import os

class AuthenticatedAgent(BaseAgent):
    """Agent that connects to authenticated Redis cluster."""
    
    def __init__(self):
        # Create MailboxConfig with password
        mailbox_config = MailboxConfig(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD"),  # Required for authenticated clusters
            db=0
        )
        
        super().__init__(
            agent_id="authenticated-agent",
            capabilities=["example"],
            mailbox_url=mailbox_config  # Pass MailboxConfig object, not URL string
        )
    
    async def on_startup(self) -> None:
        self._logger.info("Connected to authenticated cluster!")
    
    async def on_shutdown(self) -> None:
        self._logger.info("Disconnecting...")
```

**Note**: The `mailbox_url` parameter accepts:
- **String URL**: `"redis://localhost:6379"` (for unauthenticated connections)
- **MailboxConfig object**: For authenticated or advanced configurations (recommended for production)
- **None**: Uses `REDIS_URL` environment variable

**For production clusters with authentication, always use `MailboxConfig`** - URL parsing doesn't support passwords in the URL format.

See `examples/authenticated_agent.py` for a complete example.

---

## 🔍 Cluster Discovery

After your agent starts, it automatically registers on the cluster. Other agents can discover you, and you can discover them:

### Discover All Agents

```python
# After startup, discover all active agents on the cluster
await agent.startup()

# List all agent IDs
all_agents = await agent.discover_agents()
print(f"Found {len(all_agents)} agents: {all_agents}")
```

### Get Agent Metadata

```python
# Get metadata for a specific agent
agent_info = await agent.get_agent_info("other-agent-id")
if agent_info:
    print(f"Agent ID: {agent_info['agent_id']}")
    print(f"Capabilities: {agent_info['capabilities']}")
    print(f"State: {agent_info['state']}")
    print(f"Registered: {agent_info['registered_at']}")
```

### Find Agents by Capability

```python
# Find all agents that provide a specific capability
search_agents = await agent.find_agents_by_capability("search")
for agent_info in search_agents:
    print(f"Found search agent: {agent_info['agent_id']}")
    
    # Send message to discovered agent
    await agent.send_message(
        target=agent_info["agent_id"],
        message_type="HELP_REQUEST",
        content={"request": "I need help with search"}
    )
```

### Redis Keys Used

The cluster uses these Redis keys for discovery:
- `beast:agents:all` - Set containing all active agent IDs
- `beast:agents:{agent_id}` - Hash with agent metadata (expires after 60 seconds)

### Complete Discovery Example

```python
import asyncio
from beast_agent import BaseAgent
from beast_mailbox_core import MailboxConfig

class DiscoveryAgent(BaseAgent):
    def __init__(self):
        mailbox_config = MailboxConfig(
            host="your-redis-host",
            port=6379,
            password="your-password",
            db=0
        )
        super().__init__(
            agent_id="discovery-agent",
            capabilities=["discover", "communicate"],
            mailbox_url=mailbox_config
        )
    
    async def on_startup(self) -> None:
        self.register_handler("HELP_REQUEST", self.handle_help)
        
        # Discover all agents on cluster
        all_agents = await self.discover_agents()
        self._logger.info(f"Found {len(all_agents)} agents: {all_agents}")
        
        # Find agents with specific capability
        helpers = await self.find_agents_by_capability("help")
        for helper in helpers:
            self._logger.info(f"Found helper: {helper['agent_id']}")
    
    async def handle_help(self, content: dict) -> None:
        sender = content.get("sender")
        self._logger.info(f"Received help request from {sender}")

async def main():
    agent = DiscoveryAgent()
    await agent.startup()
    
    # Keep running
    await asyncio.sleep(3600)
    
    await agent.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📋 Agent Patterns

### Per-Repo Agent Pattern

```python
class RepoAgent(BaseAgent):
    """Agent that monitors a single repository"""
    
    def __init__(self, repo_name: str):
        super().__init__(
            agent_id=f"repo-agent-{repo_name}",
            capabilities=["code_review", "pr_validation", "security_scan"]
        )
        self.repo_name = repo_name
    
    @capability("code_review")
    async def review_code(self, pr_number: int) -> dict:
        """Review code in PR"""
        # Review logic
        return {"status": "reviewed", "pr": pr_number}
```

### Per-Branch Agent Pattern

```python
class BranchAgent(BaseAgent):
    """Agent specific to a branch"""
    
    def __init__(self, repo_name: str, branch_name: str):
        super().__init__(
            agent_id=f"branch-agent-{repo_name}-{branch_name}",
            capabilities=["deployment", "testing", "monitoring"]
        )
        self.repo = repo_name
        self.branch = branch_name
    
    @capability("deployment")
    async def deploy(self, environment: str) -> dict:
        """Deploy branch to environment"""
        # Deployment logic
        return {"status": "deployed", "environment": environment}
```

---

## 🔧 Features

### Agent Lifecycle

```python
agent = MyAgent()
await agent.startup()  # Initialize and register
# ... agent is running ...
await agent.shutdown()  # Graceful cleanup
```

### Message Handling

```python
# Register handler for message type
agent.register_handler("TASK_REQUEST", handle_task_request)

# Send message to another agent
await agent.send_message(
    target="other-agent-id",
    message_type="HELP_REQUEST",
    content={"task": "analyze_code"}
)
```

### Health Checks

```python
health = agent.health_check()
print(f"Healthy: {health.healthy}")
print(f"State: {health.state}")
```

---

## 📚 Documentation

- **[Agent Development Guide](docs/AGENT_DEVELOPMENT.md)** - How to create custom agents
- **[Deployment Patterns](docs/DEPLOYMENT.md)** - Per-repo, per-branch, orchestration
- **[API Reference](docs/API.md)** - Complete API documentation
- **[Examples](examples/)** - Example agent implementations

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/beast_agent --cov-report=html

# Run specific test
pytest tests/test_base_agent.py

# Run integration tests (requires Redis and beast-mailbox-core)
# Note: Integration tests are automatically skipped if dependencies unavailable
pytest tests/test_mailbox_integration.py

# Run all tests including integration (if Redis available)
pytest tests/
```

### Integration Testing

Integration tests require:
- **Redis**: Running locally (via Docker) or in CI (via service containers)
- **beast-mailbox-core**: Installed as dependency

**Local Testing:**
- Redis Docker container is automatically managed via `conftest.py` fixtures
- Tests gracefully skip if Redis/Docker unavailable
- Uses separate test database (db=15) to avoid conflicts

**CI Testing:**
- Redis service container automatically provided in GitHub Actions
- Integration tests run against real Redis in CI

---

## 🤝 Integration

### Required Dependencies
- `beast-mailbox-core` >= 0.3.0 - Messaging and discovery

### Optional Dependencies
- `beast-observability` - Enhanced telemetry
- Any cloud platform (works with AWS, GCP, Azure, on-prem)

---

## 📦 Package Status

**Tier:** 1 (Foundation)  
**Phase:** Development  
**Coverage:** Target 90%+  
**Quality:** Target zero defects

---

## 🔗 Related Packages

- `beast-mailbox-core` - Redis-backed mailbox utilities
- `beast-agentic-framework` - Multi-agent orchestration
- `beast-observability` - Unified telemetry
- `beast-redaction-client` - Data classification

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

Part of the **[Beast Mode](https://github.com/nkllon)** multi-agent framework ecosystem.

---

**Built with ❤️ by the Beast Mode team**

