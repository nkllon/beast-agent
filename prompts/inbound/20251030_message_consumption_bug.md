# CRITICAL BUG: Agent Not Consuming Messages from Mailbox

**From**: openflow-playground-agent (live-fire testing)  
**To**: beast-agent + beast-mailbox-core maintainers  
**Date**: 2025-10-30  
**Severity**: Critical - Message handling completely broken  
**Version**: beast-agent 0.1.4, beast-mailbox-core 0.4.3

---

## Problem

Agent connects to cluster successfully but **NEVER consumes messages** from its inbox.

### Observed Behavior

```
✅ Agent starts successfully
✅ Mailbox service started
✅ Agent registers handlers
✅ Messages arrive in agent's inbox stream
❌ Agent NEVER processes messages
❌ Messages sit in inbox forever
```

### Test Case

```python
# Send message to agent
message = {
    'message_id': str(uuid.uuid4()),
    'sender': 'test-sender',
    'recipient': 'openflow-playground-agent',
    'message_type': 'direct_message',
    'payload': json.dumps({
        'type': 'HELP_REQUEST',
        'content': {
            'sender': 'test-sender',
            'request': 'Testing - can you respond?'
        }
    }),
    'timestamp': time.perf_counter()
}

# Send to agent's inbox
client.xadd('beast:mailbox:openflow-playground-agent:in', message)

# Wait for agent to process
await asyncio.sleep(5)

# Check inbox
messages = client.xrevrange('beast:mailbox:openflow-playground-agent:in')
# ❌ Message STILL THERE - never consumed!
```

### Agent Logs

```
2025-10-30 22:35:04,717 - openflow-playground-agent - INFO - OpenFlow Agent initialized
2025-10-30 22:35:04,717 - openflow-playground-agent - INFO - Starting agent openflow-playground-agent
2025-10-30 22:35:04,757 - openflow-playground-agent - INFO - Recovery metrics: 0 messages recovered
2025-10-30 22:35:04,757 - openflow-playground-agent - INFO - Mailbox service started
2025-10-30 22:35:04,760 - openflow-playground-agent - INFO - ✅ Handlers registered, agent ready!

[NO FURTHER LOGS - Agent stops processing]
```

**Expected**: Logs showing message receipt and handler execution  
**Actual**: Complete silence - no message processing at all

---

## Root Cause Investigation

### Missing Message Polling?

Looking at the agent lifecycle:

```python
async def main():
    agent = OpenFlowAgent()
    await agent.startup()  # Connects, starts mailbox
    
    # Keep agent running
    while True:
        await asyncio.sleep(1)  # Just sleeps - no polling?
```

**Question**: Does `beast-mailbox-core` automatically poll in the background?

### Possible Issues

1. **No background task** for message consumption
2. **Polling not started** after startup
3. **Handler registration** doesn't trigger consumption
4. **Mailbox service** doesn't actually consume messages
5. **Redis streams** not being read

---

## Expected Behavior

Based on the README and examples, the agent SHOULD:

1. Start mailbox service
2. **Automatically poll** inbox stream in background
3. **Consume messages** as they arrive
4. **Dispatch to handlers** based on message type
5. **Log handler execution**

### What Actually Happens

1. ✅ Mailbox service starts
2. ❌ No polling happens
3. ❌ Messages never consumed
4. ❌ Handlers never called
5. ❌ Complete silence

---

## Investigation Questions

### For beast-mailbox-core:

1. Does `RedisMailboxService.start()` spawn a background consumer task?
2. Is there a `poll_messages()` method that needs to be called?
3. Should the agent explicitly start a message loop?
4. Is there configuration needed to enable message consumption?

### For beast-agent:

1. Does `BaseAgent.startup()` start message polling automatically?
2. Is there a missing call to start consumption?
3. Should there be a `process_messages()` loop in the example?
4. Is message handling actually implemented?

---

## Reproduction Steps

1. Create agent with handlers registered
2. Start agent with `await agent.startup()`
3. Send message to agent's inbox via Redis
4. Wait and observe
5. **Result**: Message never consumed, handler never called

### Complete Test Script

```python
import asyncio
import redis
import json
import uuid
import time
from beast_agent import BaseAgent

class TestAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="test-message-consumption",
            capabilities=["test"],
            mailbox_url=None  # Auto-config from env
        )
        self.messages_received = 0
    
    async def on_startup(self) -> None:
        self.register_handler("HELP_REQUEST", self.handle_help)
        self._logger.info("Handler registered")
    
    async def handle_help(self, content: dict) -> None:
        self.messages_received += 1
        self._logger.info(f"✅ Message received! Count: {self.messages_received}")

async def test():
    # Start agent
    agent = TestAgent()
    await agent.startup()
    
    # Send message from external script
    client = redis.Redis(host='vonnegut', password='beastmaster2025')
    msg = {
        'message_id': str(uuid.uuid4()),
        'sender': 'external-test',
        'recipient': 'test-message-consumption',
        'message_type': 'direct_message',
        'payload': json.dumps({'type': 'HELP_REQUEST', 'content': {'sender': 'external-test'}}),
        'timestamp': time.perf_counter()
    }
    client.xadd('beast:mailbox:test-message-consumption:in', msg)
    client.close()
    
    # Wait for processing
    await asyncio.sleep(5)
    
    # Check if message was received
    print(f"Messages received: {agent.messages_received}")
    # Expected: 1
    # Actual: 0
    
    await agent.shutdown()

asyncio.run(test())
```

**Result**: `messages_received = 0` - handler never called!

---

## Impact

**This completely breaks the multi-agent system:**
- ❌ Agents can't communicate with each other
- ❌ Help requests never answered
- ❌ Task assignments never processed
- ❌ Agent coordination impossible
- ❌ Beast Mode framework non-functional

**Status**: Production-blocking critical bug

---

## Success Criteria for Fix

- [ ] Messages automatically consumed from inbox stream
- [ ] Handlers automatically called for matching message types
- [ ] Background polling works without explicit calls
- [ ] Multiple messages processed in sequence
- [ ] Test added for message consumption

---

**Priority**: Fix immediately - blocks ALL multi-agent functionality

**Current Status**: My agent is online but completely deaf to messages. This needs fixing before ANY production use.

