# Request to beast-mailbox-core: Environment Variable Support

**From**: beast-agent maintainer  
**To**: beast-mailbox-core maintainer  
**Date**: 2025-10-30  
**Priority**: High - Required for production cluster connections

---

## Summary

`beast-agent` needs `beast-mailbox-core` to read environment variables when `RedisMailboxService` is created with `config=None`. Currently, it defaults to `localhost:6379`, which prevents connecting to production clusters without explicitly creating a `MailboxConfig`.

---

## Current Behavior

When `RedisMailboxService` is created with `config=None`:

```python
from beast_mailbox_core import RedisMailboxService

service = RedisMailboxService(agent_id="test", config=None)
# Creates default MailboxConfig(host='localhost', port=6379, password=None)
# Does NOT read from environment variables
```

**Problem**: This defaults to localhost, making it impossible to connect to production Redis clusters without explicitly creating a `MailboxConfig` object.

---

## Requested Behavior

When `RedisMailboxService` is created with `config=None`, `beast-mailbox-core` should:

1. **Read from environment variables** in this order:
   - Check `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`, `REDIS_DB`
   - If `REDIS_HOST` is set, create `MailboxConfig` from these variables
   - Fallback to `REDIS_URL` if `REDIS_HOST` is not set
   - Only default to `localhost:6379` if no environment variables are set

2. **Create `MailboxConfig` from environment variables**:
   ```python
   MailboxConfig(
       host=os.getenv("REDIS_HOST", "localhost"),
       port=int(os.getenv("REDIS_PORT", "6379")),
       password=os.getenv("REDIS_PASSWORD"),
       db=int(os.getenv("REDIS_DB", "0")),
       stream_prefix="beast:mailbox",
       enable_recovery=True
   )
   ```

---

## Use Case

`beast-agent`'s `BaseAgent` should be able to work with production clusters by simply setting environment variables:

```python
# User sets environment variables
export REDIS_HOST="production-redis-cluster.example.com"
export REDIS_PORT="6379"
export REDIS_PASSWORD="cluster-password"

# beast-agent can just pass None and let beast-mailbox-core handle it
from beast_agent import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="my-agent",
            capabilities=["example"],
            mailbox_url=None  # Should work with env vars from beast-mailbox-core
        )
```

**Current workaround**: Users must explicitly create `MailboxConfig`:
```python
from beast_mailbox_core import MailboxConfig
mailbox_config = MailboxConfig(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    password=os.getenv("REDIS_PASSWORD")
)
```

This exposes Redis-specific configuration details in `beast-agent`, which violates the contract that `beast-mailbox-core` should handle all Redis-specific logic.

---

## Contract Rationale

**Separation of Concerns**:
- `beast-agent` (`BaseAgent`): Generic agent framework, shouldn't know about Redis
- `beast-mailbox-core`: Handles all Redis-specific configuration, connection logic, and operations

**Current Contract Breakdown**:
- `beast-agent` currently has to create `MailboxConfig` from environment variables to connect to production clusters
- This means `beast-agent` knows about Redis-specific environment variables (`REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`)
- This violates the contract - `beast-mailbox-core` should own all Redis configuration

---

## Proposed Solution

Update `RedisMailboxService.__init__()` to:

1. If `config=None`, check environment variables
2. If `REDIS_HOST` is set, create `MailboxConfig` from env vars
3. If `REDIS_URL` is set, parse it and create `MailboxConfig`
4. Only default to `localhost:6379` if no env vars are set

This way, `beast-agent` can simply pass `None` and `beast-mailbox-core` handles everything.

---

## Impact

**Benefits**:
- Simplifies usage - just set environment variables, no need to create `MailboxConfig`
- Maintains contract - `beast-mailbox-core` owns all Redis configuration
- Enables production cluster connections out of the box
- Consistent with how many Redis clients handle configuration

**Breaking Changes**: 
- None (current behavior with explicit `MailboxConfig` remains unchanged)
- Only affects `config=None` case

---

## Success Criteria

✅ `RedisMailboxService(agent_id="test", config=None)` reads from `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD` environment variables  
✅ Falls back to `REDIS_URL` if `REDIS_HOST` not set  
✅ Only defaults to `localhost:6379` if no environment variables are set  
✅ Backward compatible - explicit `MailboxConfig` still works  
✅ `beast-agent` can connect to production clusters with just environment variables

---

## Reference

- Current `beast-agent` implementation: `src/beast_agent/base_agent.py` - `_create_mailbox_config()`
- `beast-agent` issue: Cannot connect to production clusters without explicit `MailboxConfig` creation
- Contract violation: `beast-agent` currently handles Redis-specific environment variables (should be in `beast-mailbox-core`)

---

**Thank you for considering this request!**

