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
# Run tests
pytest

# Run with coverage
pytest --cov=src/beast_agent --cov-report=html

# Run specific test
pytest tests/test_base_agent.py
```

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

