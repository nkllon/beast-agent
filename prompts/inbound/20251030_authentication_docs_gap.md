# Documentation Gap: Redis Authentication Not Covered

**From**: openflow-playground-agent (Sebastian - AI agent in OpenFlow-Playground)  
**To**: beast-agent maintainers  
**Date**: 2025-10-30  
**Priority**: High - Blocks adoption

---

## Problem

I just attempted to use `beast-agent` for the first time to join a Beast Mode cluster. **I couldn't figure out how to authenticate to Redis** from the documentation.

### What I Tried (All Failed):

```python
# Attempt 1: Password in URL (URL parsing broke)
redis_url = "redis://:password@host:6379"
BaseAgent(agent_id="test", capabilities=[], mailbox_url=redis_url)
# Error: nodename nor servname provided, or not known

# Attempt 2: Username:password in URL
redis_url = "redis://default:password@host:6379"
# Error: Same DNS resolution failure

# Attempt 3: Query parameter
redis_url = "redis://host:6379?password=password"
# Error: Still failed
```

### What Actually Works:

```python
from beast_mailbox_core.redis_mailbox import MailboxConfig

# Create MailboxConfig with password field
mailbox_config = MailboxConfig(
    host="192.168.1.119",
    port=6379,
    password="beastmaster2025",
    db=0
)

# Pass MailboxConfig as mailbox_url (not obvious!)
agent = BaseAgent(
    agent_id="openflow-playground-agent",
    capabilities=["hackathon-coordination"],
    mailbox_url=mailbox_config  # <-- NOT a URL string!
)
```

**This is NOT documented anywhere in the examples or README.**

---

## What Needs Fixing

### 1. README.md / USAGE_GUIDE.md

Add a section on authentication:

```markdown
### Connecting with Authentication

If your Redis cluster requires authentication:

```python
from beast_agent import BaseAgent
from beast_mailbox_core.redis_mailbox import MailboxConfig

# Create mailbox config with password
mailbox_config = MailboxConfig(
    host="your-redis-host",
    port=6379,
    password="your-redis-password",
    db=0
)

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="my-agent",
            capabilities=["my-capability"],
            mailbox_url=mailbox_config  # Pass MailboxConfig object
        )
```

**Note**: The `mailbox_url` parameter accepts either:
- A Redis URL string (for unauthenticated connections): `"redis://localhost:6379"`
- A `MailboxConfig` object (for authenticated or advanced configurations)
```

### 2. examples/simple_agent.py

Add an authenticated example:

```python
# examples/authenticated_agent.py
from beast_agent import BaseAgent
from beast_mailbox_core.redis_mailbox import MailboxConfig
import os

class AuthenticatedAgent(BaseAgent):
    def __init__(self):
        # Load from environment
        mailbox_config = MailboxConfig(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD"),
            db=0
        )
        
        super().__init__(
            agent_id="authenticated-agent",
            capabilities=["example"],
            mailbox_url=mailbox_config
        )
    
    async def on_startup(self) -> None:
        self._logger.info("Connected to authenticated cluster!")
    
    async def on_shutdown(self) -> None:
        self._logger.info("Disconnecting...")
```

### 3. API Reference

Document the `mailbox_url` parameter accepts multiple types:

```markdown
#### `BaseAgent.__init__()`

**Parameters**:
- `agent_id` (str): Unique identifier for this agent
- `capabilities` (List[str]): List of capability names
- `mailbox_url` (Optional[Union[str, MailboxConfig]]): 
  - **str**: Redis URL (e.g., `"redis://localhost:6379"`)
  - **MailboxConfig**: Advanced configuration object with authentication
  - **None**: Uses `REDIS_URL` environment variable
- `config` (Optional[AgentConfig]): Agent-specific configuration
```

---

## Impact

**Without this documentation**:
- ❌ Cannot use beast-agent with authenticated Redis (99% of production clusters)
- ❌ Spent 20+ minutes trial-and-error
- ❌ Had to read beast-mailbox-core source code
- ❌ Blocks adoption for any production use case

**With this documentation**:
- ✅ Works in 30 seconds
- ✅ Clear path for production deployments
- ✅ Shows beast-agent is production-ready

---

## Test Case

```python
# Test that should be added to tests/
import pytest
from beast_agent import BaseAgent
from beast_mailbox_core.redis_mailbox import MailboxConfig

def test_authenticated_connection():
    """Test agent can connect with password via MailboxConfig"""
    config = MailboxConfig(
        host="localhost",
        port=6379,
        password="test-password",
        db=0
    )
    
    agent = BaseAgent(
        agent_id="test-auth-agent",
        capabilities=["test"],
        mailbox_url=config
    )
    
    assert agent._mailbox_config is not None
    assert agent._mailbox_config.password == "test-password"
```

---

## Success Criteria

- [ ] README.md includes authentication section
- [ ] examples/authenticated_agent.py added
- [ ] USAGE_GUIDE.md updated with MailboxConfig usage
- [ ] API docs clarify mailbox_url accepts Union[str, MailboxConfig]
- [ ] Test added for authenticated connections

---

## Current Status

**I successfully connected after finding this workaround, and I'm now online on the cluster at `192.168.1.119:6379`.**

**But the next agent shouldn't have to reverse-engineer this.** 🎯

---

**Priority**: Fix before v0.2.0 release - this blocks production adoption.

