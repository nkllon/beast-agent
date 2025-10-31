# Bug Report: Critical Issues Found in Live-Fire Testing

**From**: beast-agent maintainer (live-fire testing)  
**To**: beast-agent maintainer  
**Date**: 2025-10-30  
**Status**: Critical - Blocks production cluster operation

---

## Summary

Live-fire testing on production cluster (`vonnegut`) revealed **3 critical bugs** that prevent agents from functioning properly:

1. ❌ **CRITICAL**: Message consumption - agents don't process inbox messages
2. ❌ **HIGH**: Discovery authentication - `discover_agents()` fails on authenticated clusters
3. ❌ **HIGH**: Agent registration authentication - registration fails on authenticated clusters

---

## Bug #1: Message Consumption Failure (CRITICAL)

### Description
Agents successfully send messages but **do not receive or process incoming messages** from their inbox.

### Symptoms
- ✅ Message sending works (`send_message()` succeeds)
- ✅ Handler registration works (`register_handler()` succeeds)
- ✅ Mailbox service starts successfully (`start()` returns True)
- ❌ **Inbox messages are never processed/handled**
- ❌ Agents are "deaf" - cannot receive messages from other agents

### Impact
**CRITICAL** - Agents cannot receive messages, making multi-agent communication impossible.

### Reproduction
1. Start agent with authenticated Redis cluster
2. Register message handler
3. Send message from another agent
4. Message appears in Redis stream but agent never processes it

### Root Cause Analysis
**Investigation needed**: 
- Is `RedisMailboxService.start()` properly polling the inbox stream with authentication?
- Is the message handler being called but failing silently?
- Is there an authentication issue preventing message consumption?

### Status
🔴 **PENDING** - Needs investigation and fix

---

## Bug #2: Discovery Authentication Failure (HIGH)

### Description
`discover_agents()` fails on authenticated Redis clusters because the Redis client is created without a password.

### Symptoms
- ✅ `discover_agents()` works on unauthenticated Redis
- ❌ `discover_agents()` fails on authenticated Redis clusters
- Error: Authentication required or connection refused

### Impact
**HIGH** - Agents cannot discover each other on production clusters with authentication.

### Root Cause
```python
# BEFORE (buggy):
redis_client = redis.Redis(
    host=host, port=port, db=db, decode_responses=True
)
# Missing password parameter!
```

### Fix Applied
✅ **FIXED** in commit (pending) - Added `password` parameter to Redis client:

```python
# AFTER (fixed):
password = (
    self._mailbox_config.password
    if hasattr(self._mailbox_config, "password")
    else None
)
redis_client = redis.Redis(
    host=host, port=port, db=db, password=password, decode_responses=True
)
```

### Status
✅ **FIXED** - Password now included in `discover_agents()`, `get_agent_info()`, `find_agents_by_capability()`

---

## Bug #3: Agent Registration Authentication Failure (HIGH)

### Description
`_register_agent_name()` and `_unregister_agent_name()` fail on authenticated Redis clusters because Redis clients are created without a password.

### Symptoms
- ✅ Agent registration works on unauthenticated Redis
- ❌ Agent registration fails on authenticated Redis clusters
- Warning: `Failed to register agent name on cluster: auth required`

### Impact
**HIGH** - Agents cannot register themselves on production clusters with authentication, making them invisible to other agents.

### Root Cause
Same as Bug #2 - Redis clients created without `password` parameter in:
- `_register_agent_name()`
- `_unregister_agent_name()`

### Fix Applied
✅ **FIXED** in commit (pending) - Added `password` parameter to all Redis client connections.

### Status
✅ **FIXED** - Password now included in agent registration/unregistration methods

---

## Test Results

### Environment
- **Cluster**: `vonnegut` (production)
- **Redis**: Authenticated cluster
- **beast-agent**: v0.1.4
- **beast-mailbox-core**: v0.4.3
- **Configuration**: Environment variables from `~/.env`

### What Works
✅ Agent installation  
✅ Auto-configuration from `~/.env` (`REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`)  
✅ Cluster connection (agent connects to `vonnegut`)  
✅ Handler registration  
✅ Message sending (can send to broadcast and other agents)

### What's Broken
❌ Message consumption (CRITICAL)  
❌ Discovery with auth (now fixed)  
❌ Agent registration with auth (now fixed)

---

## Fixes Applied

### Commits
1. ✅ **Authentication fixes** (pending commit):
   - Added `password` parameter to Redis clients in:
     - `_register_agent_name()`
     - `_unregister_agent_name()`
     - `discover_agents()`
     - `get_agent_info()`
     - `find_agents_by_capability()`

### Files Modified
- `src/beast_agent/base_agent.py`

---

## Remaining Work

### Critical: Message Consumption
🔴 **NEEDS INVESTIGATION**:
1. Verify `RedisMailboxService.start()` polls inbox with authentication
2. Check if message handler is being called
3. Verify message payload format matches expected structure
4. Check for silent failures in message processing

### Testing
- [ ] Test message consumption on authenticated cluster
- [ ] Verify agents can discover each other (Bug #2 fix)
- [ ] Verify agents register successfully (Bug #3 fix)

---

## Next Steps

1. **Immediate**: Fix message consumption bug (Bug #1)
2. **Test**: Verify all fixes on production cluster
3. **Release**: Create v0.1.5 with authentication fixes

---

## Impact Assessment

**Before Fixes**:
- Agents could send but not receive messages
- Agents could not discover each other on authenticated clusters
- Agents could not register on authenticated clusters
- **Result**: Multi-agent communication completely broken

**After Fixes** (pending message consumption fix):
- ✅ Agents can discover each other
- ✅ Agents can register on cluster
- ❌ **Still broken**: Message consumption (critical blocker)

---

**Status**: 2 of 3 bugs fixed. Message consumption bug (critical) needs investigation and fix before production deployment.

