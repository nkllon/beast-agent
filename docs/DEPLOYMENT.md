# Deployment Guide

This guide explains how to deploy `beast-agent` instances.

---

## 📚 Table of Contents

- [Overview](#overview)
- [Deployment Patterns](#deployment-patterns)
- [Configuration](#configuration)
- [Environment Variables](#environment-variables)
- [Best Practices](#best-practices)

---

## Overview

`beast-agent` instances can be deployed in various patterns depending on your needs:

1. **Per-Repository Agent**: One agent per repository
2. **Per-Branch Agent**: One agent per branch
3. **Shared Agent**: Single agent for multiple repositories/branches
4. **Distributed Agents**: Multiple agents coordinating across services

---

## Deployment Patterns

### Pattern 1: Per-Repository Agent

**Use Case**: Monitor and automate a single repository

**Design**:
```python
class RepoAgent(BaseAgent):
    def __init__(self, repo_name: str):
        super().__init__(
            agent_id=f"repo-agent-{repo_name}",
            capabilities=["monitor_repo", "automate_tasks"]
        )
        self.repo_name = repo_name
```

**Deployment**:
- One agent instance per repository
- Agent ID: `repo-agent-{repo_name}`
- Repository-specific configuration

**Example**:
```bash
# Repository: python-monorepo
export REPO_NAME="python-monorepo"
python -m my_app.agents.repo_agent

# Repository: frontend-app
export REPO_NAME="frontend-app"
python -m my_app.agents.repo_agent
```

### Pattern 2: Per-Branch Agent

**Use Case**: Monitor and automate specific branches

**Design**:
```python
class BranchAgent(BaseAgent):
    def __init__(self, repo_name: str, branch_name: str):
        super().__init__(
            agent_id=f"branch-agent-{repo_name}-{branch_name}",
            capabilities=["monitor_branch", "run_tests"]
        )
        self.repo_name = repo_name
        self.branch_name = branch_name
```

**Deployment**:
- One agent instance per branch
- Agent ID: `branch-agent-{repo_name}-{branch_name}`
- Branch-specific configuration

**Example**:
```bash
# Main branch
export REPO_NAME="python-monorepo"
export BRANCH_NAME="main"
python -m my_app.agents.branch_agent

# Feature branch
export REPO_NAME="python-monorepo"
export BRANCH_NAME="feature/new-api"
python -m my_app.agents.branch_agent
```

### Pattern 3: Shared Agent

**Use Case**: Single agent managing multiple repositories/branches

**Design**:
```python
class SharedAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="shared-agent",
            capabilities=["monitor_all", "orchestrate"]
        )
        self.managed_repos = []
```

**Deployment**:
- Single agent instance for multiple repositories
- Agent ID: `shared-agent`
- Centralized configuration

**Example**:
```bash
python -m my_app.agents.shared_agent
```

### Pattern 4: Distributed Agents

**Use Case**: Multiple agents coordinating across services

**Design**:
```python
class DistributedAgent(BaseAgent):
    def __init__(self, service_name: str):
        super().__init__(
            agent_id=f"service-agent-{service_name}",
            capabilities=["service_monitor", "cross_service_coord"]
        )
        self.service_name = service_name
```

**Deployment**:
- Multiple agent instances across services
- Agent ID: `service-agent-{service_name}`
- Service-specific configuration

**Example**:
```bash
# API service
export SERVICE_NAME="api"
python -m my_app.agents.service_agent

# Worker service
export SERVICE_NAME="worker"
python -m my_app.agents.service_agent
```

---

## Configuration

### Environment Variables

Configure agents via environment variables:

```bash
# Required
export REDIS_URL="redis://localhost:6379"

# Optional
export AGENT_LOG_LEVEL="INFO"
export AGENT_HEARTBEAT_INTERVAL="30"
```

### Configuration Priority

Configuration is loaded in this order (highest to lowest priority):

1. **Constructor arguments** (highest priority)
2. **Environment variables**
3. **Default values** (fallback)

**Example**:
```python
# Priority 1: Constructor args
agent = MyAgent(
    agent_id="my-agent",
    capabilities=["cap1"],
    config=AgentConfig(log_level="DEBUG")
)

# Priority 2: Environment variables
export AGENT_LOG_LEVEL="INFO"
agent = MyAgent(agent_id="my-agent", capabilities=["cap1"])

# Priority 3: Defaults
agent = MyAgent(agent_id="my-agent", capabilities=["cap1"])
# Uses: log_level="INFO", heartbeat_interval=30
```

---

## Environment Variables

### Required Variables

#### `REDIS_URL`

Redis mailbox connection URL.

**Format**: `redis://[host]:[port]` or `redis://[password]@[host]:[port]`

**Default**: `redis://localhost:6379`

**Example**:
```bash
export REDIS_URL="redis://localhost:6379"
export REDIS_URL="redis://password@redis.example.com:6379"
```

### Optional Variables

#### `AGENT_LOG_LEVEL`

Python logging level.

**Values**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

**Default**: `INFO`

**Example**:
```bash
export AGENT_LOG_LEVEL="DEBUG"
```

#### `AGENT_HEARTBEAT_INTERVAL`

Heartbeat interval in seconds.

**Range**: >= 1

**Default**: `30`

**Example**:
```bash
export AGENT_HEARTBEAT_INTERVAL="60"
```

---

## Best Practices

### 1. Agent ID Naming

Use descriptive, unique agent IDs:

```python
# Good
agent_id="repo-agent-python-monorepo"
agent_id="branch-agent-frontend-main"
agent_id="service-agent-api-production"

# Bad
agent_id="agent1"
agent_id="test"
agent_id="agent"
```

### 2. Configuration Management

Use environment-specific configuration:

```bash
# Development
export AGENT_LOG_LEVEL="DEBUG"
export REDIS_URL="redis://localhost:6379"

# Production
export AGENT_LOG_LEVEL="INFO"
export REDIS_URL="redis://prod-redis:6379"
```

### 3. Health Monitoring

Monitor agent health regularly:

```python
import asyncio

async def monitor_health(agent: BaseAgent):
    while True:
        health = agent.health_check()
        if not health.healthy:
            # Alert or restart
            print(f"Agent unhealthy: {health.state}")
        await asyncio.sleep(60)

# Start monitoring
asyncio.create_task(monitor_health(agent))
```

### 4. Graceful Shutdown

Handle shutdown signals gracefully:

```python
import signal
import asyncio

async def main():
    agent = MyAgent()
    await agent.startup()
    
    # Handle shutdown signals
    def signal_handler(sig, frame):
        print("Shutting down...")
        asyncio.create_task(agent.shutdown())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Keep running
    while agent.state != AgentState.STOPPED:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
```

### 5. Error Recovery

Implement error recovery strategies:

```python
async def on_startup(self) -> None:
    """Initialize with retry logic."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            self.db = await connect_to_database()
            break
        except ConnectionError as e:
            if attempt == max_retries - 1:
                raise
            self._logger.warning(f"Connection failed, retrying: {e}")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### 6. Resource Cleanup

Always cleanup resources in `on_shutdown()`:

```python
async def on_shutdown(self) -> None:
    """Cleanup all resources."""
    if hasattr(self, "db") and self.db:
        await self.db.close()
    
    if hasattr(self, "cache") and self.cache:
        await self.cache.flush()
    
    if hasattr(self, "connections"):
        for conn in self.connections:
            await conn.close()
```

### 7. Logging Configuration

Configure logging appropriately for your environment:

```python
# Development: Verbose logging
export AGENT_LOG_LEVEL="DEBUG"

# Production: Minimal logging
export AGENT_LOG_LEVEL="INFO"
```

### 8. Deployment Checklist

Before deploying, ensure:

- [ ] Agent ID is unique and descriptive
- [ ] Environment variables are set correctly
- [ ] Redis mailbox is accessible
- [ ] Health monitoring is configured
- [ ] Shutdown handlers are registered
- [ ] Error recovery is implemented
- [ ] Resource cleanup is in place
- [ ] Logging is configured appropriately

---

## Container Deployment

### Dockerfile Example

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy application code
COPY . .

# Set environment variables
ENV REDIS_URL="redis://redis:6379"
ENV AGENT_LOG_LEVEL="INFO"

# Run agent
CMD ["python", "-m", "my_app.agents.my_agent"]
```

### Docker Compose Example

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  agent:
    build: .
    environment:
      - REDIS_URL=redis://redis:6379
      - AGENT_LOG_LEVEL=INFO
    depends_on:
      - redis
```

---

## Kubernetes Deployment

### Deployment Example

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: beast-agent
spec:
  replicas: 1
  selector:
    matchLabels:
      app: beast-agent
  template:
    metadata:
      labels:
        app: beast-agent
    spec:
      containers:
      - name: agent
        image: my-registry/beast-agent:latest
        env:
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: agent-config
              key: redis-url
        - name: AGENT_LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: agent-config
              key: log-level
```

---

## See Also

- [Agent Development Guide](AGENT_DEVELOPMENT.md)
- [API Reference](API.md)
- [Requirements](../.kiro/specs/requirements.md)

