# BUG: Discovery Methods Don't Use Authenticated Redis Connection

**From**: openflow-playground-agent (live-fire testing)  
**To**: beast-agent maintainers  
**Date**: 2025-10-30  
**Severity**: Critical - Breaks discovery on authenticated clusters  
**Version**: v0.1.3

---

## Problem

The new discovery methods (`discover_agents()`, `get_agent_info()`, `find_agents_by_capability()`) fail on authenticated Redis clusters.

### Error

```
redis.exceptions.AuthenticationError: Authentication required.
```

**Location**: `beast_agent/base_agent.py`, line 571 in `discover_agents()`

---

## Root Cause

The discovery methods create a **new Redis client** without authentication:

```python
# From base_agent.py - discover_agents()
async def discover_agents(self) -> List[str]:
    redis_client = redis.from_url(
        self._mailbox_url,  # <-- This is a MailboxConfig object, not a URL!
        decode_responses=True
    )
```

**Issues**:
1. `self._mailbox_url` is a `MailboxConfig` object when using authentication
2. `redis.from_url()` expects a string, not a MailboxConfig
3. Even if it were a URL string, it wouldn't have the password

**Why mailbox works**: The mailbox uses `self._mailbox_config` which has the password.

**Why discovery fails**: Discovery tries to use `self._mailbox_url` as a URL string.

---

## Observed Behavior

```
✅ Agent connects to cluster (mailbox works)
✅ Agent sends messages (mailbox works)  
✅ Agent receives messages (mailbox works)
❌ discover_agents() fails (creates unauthenticated client)
❌ get_agent_info() fails (creates unauthenticated client)
❌ find_agents_by_capability() fails (creates unauthenticated client)
```

---

## Solution

### Option 1: Reuse Mailbox Connection (Recommended)

```python
async def discover_agents(self) -> List[str]:
    """Discover all agents on the cluster."""
    if self._mailbox is None:
        return []
    
    try:
        # Use the mailbox's authenticated Redis client
        redis_client = self._mailbox._client
        agent_ids = await redis_client.smembers("beast:agents:all")
        return list(agent_ids) if agent_ids else []
    except Exception as e:
        self._logger.error(f"Failed to discover agents: {e}")
        return []
```

**Pros**:
- Reuses authenticated connection
- No duplicate connections
- Works with both URL and MailboxConfig

### Option 2: Create Client from MailboxConfig

```python
async def discover_agents(self) -> List[str]:
    """Discover all agents on the cluster."""
    if not self._mailbox_config:
        return []
    
    try:
        # Create authenticated client from config
        redis_client = redis.Redis(
            host=self._mailbox_config.host,
            port=self._mailbox_config.port,
            password=self._mailbox_config.password,
            db=self._mailbox_config.db,
            decode_responses=True
        )
        agent_ids = await redis_client.smembers("beast:agents:all")
        await redis_client.aclose()
        return list(agent_ids) if agent_ids else []
    except Exception as e:
        self._logger.error(f"Failed to discover agents: {e}")
        return []
```

**Pros**:
- Clean separation
- Explicit configuration

**Cons**:
- Creates extra connections

---

## Test Case

```python
import pytest
from beast_agent import BaseAgent
from beast_mailbox_core.redis_mailbox import MailboxConfig

@pytest.mark.asyncio
async def test_discovery_with_authentication():
    """Test discovery works on authenticated cluster"""
    config = MailboxConfig(
        host="localhost",
        port=6379,
        password="test-password",
        db=0
    )
    
    agent = BaseAgent(
        agent_id="test-discovery",
        capabilities=["test"],
        mailbox_url=config
    )
    
    await agent.startup()
    
    # Should not raise AuthenticationError
    agents = await agent.discover_agents()
    assert isinstance(agents, list)
    
    # Should work with authentication
    if len(agents) > 0:
        info = await agent.get_agent_info(agents[0])
        assert info is not None
    
    await agent.shutdown()
```

---

## Impact

**Current State (v0.1.3)**:
- ❌ Discovery broken on authenticated clusters (99% of production)
- ❌ Can't find other agents
- ❌ Can't use capability-based discovery
- ✅ Messaging still works (mailbox has auth)

**After Fix**:
- ✅ Discovery works on authenticated clusters
- ✅ Full multi-agent coordination
- ✅ Production-ready

---

## Reproduction

```python
from beast_agent import BaseAgent
from beast_mailbox_core.redis_mailbox import MailboxConfig

# Create agent with authenticated config
config = MailboxConfig(
    host="192.168.1.119",
    port=6379,
    password="beastmaster2025"
)

agent = BaseAgent(
    agent_id="test",
    capabilities=["test"],
    mailbox_url=config
)

await agent.startup()  # ✅ Works
agents = await agent.discover_agents()  # ❌ Fails: Authentication required
```

---

## Recommendation

**Fix in v0.1.4**:
- Update discovery methods to reuse mailbox connection (Option 1)
- Add integration test with authenticated Redis
- Verify all discovery methods work

**Priority**: Critical - blocks multi-agent features on production clusters

---

**Status**: I'm currently online but can't discover other agents due to this bug.

