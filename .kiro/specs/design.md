# Beast Agent - Design

**Status**: ✅ Implemented (Retroactive Documentation)  
**Repository**: https://github.com/nkllon/beast-agent  
**Version**: 0.1.0

---

## 🎯 Design Overview

The `beast-agent` package provides a foundational base class (`BaseAgent`) that ALL Beast Mode agents inherit from. This design ensures consistency, testability, and production-readiness across the entire multi-agent ecosystem.

**Core Principle**: "At least one agent per repo, potentially more per branch"

---

## 🏗️ Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────┐
│              Beast Mode Ecosystem                   │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─────────────┐    ┌──────────────┐              │
│  │ NIM Agent   │    │ ADK Agent    │              │
│  │ (Tier 3)    │    │ (Tier 3)     │              │
│  └──────┬──────┘    └──────┬───────┘              │
│         │                   │                       │
│         └──────────┬────────┘                       │
│                    │                                │
│         ┌──────────▼──────────┐                    │
│         │  BaseAgent          │ ◄── YOU ARE HERE   │
│         │  (Tier 1)           │                    │
│         └──────────┬──────────┘                    │
│                    │                                │
│         ┌──────────▼──────────┐                    │
│         │ beast-mailbox-core  │                    │
│         │ (External)          │                    │
│         └─────────────────────┘                    │
└─────────────────────────────────────────────────────┘
```

### Class Hierarchy

```python
ABC (Abstract Base Class)
 └── BaseAgent
      ├── RepoAgent (per-repo pattern)
      ├── BranchAgent (per-branch pattern)
      ├── NIMAgent (NVIDIA NIM integration)
      ├── ADKAgent (Google ADK integration)
      └── CustomAgent (user-defined)
```

---

## 📦 Module Structure

### Core Modules

#### `src/beast_agent/__init__.py`
**Purpose**: Package exports and version definition

**Exports**:
- `BaseAgent` - Main abstract base class
- `AgentState` - Lifecycle state enum
- `HealthStatus` - Health status dataclass
- `capability` - Capability decorator

**Design Decision**: Flat export structure for ease of use (`from beast_agent import BaseAgent`)

---

#### `src/beast_agent/base_agent.py`
**Purpose**: Core `BaseAgent` abstract base class

**Class**: `BaseAgent(ABC)`

**Responsibilities**:
1. **Lifecycle Management**: startup, shutdown, health checks
2. **Message Routing**: register handlers, route incoming messages
3. **Configuration**: load from env vars or defaults
4. **Logging**: structured logging per agent instance
5. **State Tracking**: monitor agent state transitions

**Key Methods**:

```python
class BaseAgent(ABC):
    # Lifecycle
    async def startup() -> None
    async def shutdown() -> None
    
    # Hooks (abstract - must override)
    @abstractmethod
    async def on_startup() -> None
    @abstractmethod
    async def on_shutdown() -> None
    
    # Health
    def health_check() -> HealthStatus
    def ready() -> bool
    
    # Messaging
    def register_handler(message_type: str, handler: Callable) -> None
    async def send_message(target: str, message_type: str, content: dict) -> None
    async def handle_message(message: dict) -> None
```

**Design Decisions**:
- **Abstract on_startup/on_shutdown**: Forces subclasses to implement initialization
- **Async by default**: All I/O operations are async for performance
- **Lazy mailbox connection**: Mailbox initialized in startup(), not __init__
- **Structured logging**: Per-agent logger with agent_id in format

**Future Integration Points** (commented out in v0.1.0):
```python
# TODO: Integrate with beast-mailbox-core
# from beast_mailbox_core import MailboxClient
# self._mailbox = MailboxClient(self._mailbox_url)
# await self._mailbox.connect()
```

---

#### `src/beast_agent/types.py`
**Purpose**: Type definitions and data structures

**Types Defined**:

1. **`AgentState` (Enum)**:
   - `INITIALIZING` - Agent starting up
   - `READY` - Ready to receive messages
   - `RUNNING` - Actively processing
   - `STOPPING` - Shutting down
   - `STOPPED` - Fully stopped
   - `ERROR` - Error state

2. **`HealthStatus` (Dataclass)**:
   ```python
   @dataclass
   class HealthStatus:
       healthy: bool
       state: AgentState
       last_heartbeat: datetime
       message_queue_size: int
       error_count: int
       metadata: Dict[str, any]
   ```

**Design Decision**: Separate types module for clean separation of concerns

---

#### `src/beast_agent/decorators.py`
**Purpose**: Capability marking decorator

**Decorator**: `@capability(name: str, version: str = "1.0.0")`

**Usage**:
```python
class MyAgent(BaseAgent):
    @capability("process_document", version="1.0.0")
    async def process_document(self, doc: str) -> dict:
        return {"status": "processed"}
```

**Design Decision**: Metadata-based capability declaration for introspection

**Metadata Attached**:
- `func._capability_name` - Capability identifier
- `func._capability_version` - Semantic version

**Future Enhancement**: Capability discovery system can introspect these attributes

---

## 🧪 Test Architecture

### Test Structure

```
tests/
├── __init__.py
├── test_base_agent.py      # BaseAgent lifecycle tests
└── test_decorators.py      # Capability decorator tests
```

### Test Coverage Strategy

**Unit Tests (70%+ target)**:
- Agent initialization
- Lifecycle transitions (INITIALIZING → READY → STOPPED)
- Health checks
- Handler registration
- Configuration loading

**Integration Tests (20%+ target)** (Future):
- Integration with beast-mailbox-core
- Multi-agent communication
- Message send/receive flows

**Test Agent Pattern**:
```python
class TestAgent(BaseAgent):
    """Minimal test implementation"""
    async def on_startup(self) -> None:
        self.started = True
    
    async def on_shutdown(self) -> None:
        self.stopped = True
```

**Design Decision**: Use minimal test implementations to isolate BaseAgent behavior

---

## 🔧 Configuration Design

### Configuration Sources (Priority Order)

1. **Constructor arguments** (highest priority)
2. **Environment variables**
3. **Default values** (fallback)

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `REDIS_URL` | Mailbox connection URL | `redis://localhost:6379` |
| `AGENT_LOG_LEVEL` | Logging level | `INFO` |
| `AGENT_HEARTBEAT_INTERVAL` | Heartbeat interval (seconds) | `30` |

### Configuration Example

```python
# Method 1: Constructor args
agent = MyAgent(
    agent_id="custom-agent",
    capabilities=["capability1"],
    mailbox_url="redis://prod-server:6379",
    config={"custom_setting": "value"}
)

# Method 2: Environment variables
export REDIS_URL="redis://prod-server:6379"
export AGENT_LOG_LEVEL="DEBUG"
agent = MyAgent(agent_id="custom-agent", capabilities=["capability1"])
```

**Design Decision**: Explicit > Implicit (constructor args override env vars)

---

## 📊 Lifecycle State Machine

```
┌─────────────┐
│ INITIALIZING│
└──────┬──────┘
       │ startup()
       ▼
┌──────────────┐
│    READY     │◄─────┐
└──────┬───────┘      │
       │              │
       │ (optional)   │
       ▼              │
┌──────────────┐      │
│   RUNNING    │──────┘
└──────┬───────┘
       │ shutdown()
       ▼
┌──────────────┐
│   STOPPING   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   STOPPED    │
└──────────────┘

       ERROR (any state can transition to ERROR)
```

**State Transitions**:
- `INITIALIZING` → `READY`: After successful startup
- `READY` → `RUNNING`: When processing messages (optional)
- `RUNNING` → `READY`: After message processing (optional)
- `READY` → `STOPPING`: On shutdown request
- `STOPPING` → `STOPPED`: After cleanup complete
- Any → `ERROR`: On unhandled exception

---

## 🔌 Integration Points

### Required: beast-mailbox-core

**Current Status**: Placeholder (commented out in v0.1.0)  
**v0.2.0 Status**: Integration design complete, ready for implementation

**Integration API** (based on `beast-mailbox-core` v0.4.1):
```python
from beast_mailbox_core import RedisMailboxService, MailboxMessage, MailboxConfig

class BaseAgent:
    async def startup(self):
        # Initialize mailbox service
        mailbox_config = MailboxConfig.from_url(self._mailbox_url)
        self._mailbox = RedisMailboxService(
            agent_id=self.agent_id,
            config=mailbox_config,
            recovery_callback=self._handle_recovery  # Optional recovery metrics
        )
        
        # Start mailbox service (connects to Redis)
        await self._mailbox.start()
        
        # Register mailbox message handler (routes to BaseAgent handlers)
        await self._mailbox.register_handler(self._mailbox_message_handler)
```

**Message Routing Flow**:
1. `RedisMailboxService` receives message → calls registered handler
2. `BaseAgent._mailbox_message_handler()` receives `MailboxMessage`
3. Extracts `message_type` from `MailboxMessage.payload`
4. Routes to `BaseAgent._handlers[message_type]` if registered
5. Logs warning if no handler registered

**Send Message Flow**:
```python
async def send_message(self, target: str, message_type: str, content: Dict[str, Any]) -> str:
    """Send message via RedisMailboxService."""
    message_id = await self._mailbox.send_message(
        recipient=target,
        payload={"type": message_type, "content": content},
        message_type="direct_message"
    )
    return message_id
```

**Agent Registration/Discovery**:
- Agent registration happens automatically when `RedisMailboxService.start()` is called
- The agent_id is passed to `RedisMailboxService.__init__()` and used for routing
- Discovery queries handled by `beast-mailbox-core` (via Redis streams)
- Capabilities are not automatically registered - need to be published separately (v0.2.0)

**Shutdown Flow**:
```python
async def shutdown(self):
    """Stop mailbox service."""
    if self._mailbox:
        await self._mailbox.stop()
```

**Error Handling**:
- Mailbox connection errors → transition to ERROR state
- Message send failures → increment error_count, log error
- Handler exceptions → catch, increment error_count, continue processing
- Recovery metrics → optional callback for pending message recovery

**Design Decisions**:
1. **Lazy Initialization**: Mailbox created in `startup()`, not `__init__()`
2. **Handler Wrapper**: `_mailbox_message_handler()` wraps `MailboxMessage` → extracts payload → routes to BaseAgent handlers
3. **Message Format**: `payload` contains `{"type": str, "content": dict}` structure
4. **Error Recovery**: Optional recovery_callback for handling pending message recovery metrics

---

#### v0.2.0 Integration Design (Detailed)

**Date**: 2025-01-27  
**API Version**: `beast-mailbox-core` v0.4.1  
**Status**: Design complete, ready for implementation

**Message Handler Integration**:

**Problem**: `RedisMailboxService.register_handler()` expects a handler that receives `MailboxMessage`, but `BaseAgent` handlers expect a plain dictionary.

**Solution**: Create a wrapper method `_mailbox_message_handler()` that:
1. Receives `MailboxMessage` from mailbox
2. Extracts `payload` (dict) containing `{"type": str, "content": dict}`
3. Routes to appropriate `BaseAgent` handler based on `payload["type"]`

```python
async def _mailbox_message_handler(self, mailbox_message: MailboxMessage) -> None:
    """Wrapper to route MailboxMessage to BaseAgent handlers."""
    try:
        # Extract payload (assumed to contain {"type": str, "content": dict})
        payload = mailbox_message.payload
        message_type = payload.get("type")
        
        # Route to registered handler
        if message_type in self._handlers:
            await self._handlers[message_type](payload.get("content", {}))
        else:
            self._logger.warning(f"No handler registered for message type: {message_type}")
    except Exception as e:
        self._error_count += 1
        self._logger.error(f"Error handling mailbox message: {e}", exc_info=True)
```

**Message Sending Integration**:

```python
async def send_message(
    self, 
    target: str, 
    message_type: str, 
    content: Dict[str, Any]
) -> str:
    """Send message via RedisMailboxService."""
    if not self._mailbox:
        raise RuntimeError("Mailbox not initialized. Call startup() first.")
    
    message_id = await self._mailbox.send_message(
        recipient=target,
        payload={"type": message_type, "content": content},
        message_type="direct_message"
    )
    
    self._logger.debug(f"Sent {message_type} to {target}: {message_id}")
    return message_id
```

**Configuration Integration**:

```python
from beast_mailbox_core import MailboxConfig

def _create_mailbox_config(self) -> MailboxConfig:
    """Create MailboxConfig from URL or env vars."""
    if isinstance(self._mailbox_url, MailboxConfig):
        return self._mailbox_url
    
    # Parse URL or use MailboxConfig.from_url()
    return MailboxConfig.from_url(self._mailbox_url)
```

**Discovery Integration (v0.2.0)**:

**Current Status**: `beast-mailbox-core` handles agent routing automatically via agent_id.  
**Future**: Capability-based discovery requires additional integration:
- Publish capabilities to Redis on startup
- Query capability registry for discovery
- Subscribe to agent join/leave events

**Design Decision**: Defer full discovery to v0.3.0, focus on message routing in v0.2.0.

**Error Handling Integration**:

**Connection Errors**:
- Catch exceptions during `start()` → transition to ERROR state
- Log connection failures with context

**Message Send Errors**:
- Catch `send_message()` exceptions → increment error_count
- Return error info or raise depending on context

**Message Receive Errors**:
- Catch handler exceptions in `_mailbox_message_handler()`
- Log error, increment error_count, continue processing

**Recovery Metrics** (Optional):
```python
async def _handle_recovery(self, metrics: RecoveryMetrics) -> None:
    """Handle pending message recovery metrics."""
    self._logger.info(
        f"Recovery metrics: {metrics.recovered_count} messages recovered, "
        f"{metrics.failed_count} failed"
    )
    # Update agent health status if needed
```

**v0.2.0 Implementation Checklist**:

- [x] Update `BaseAgent.startup()` to initialize `RedisMailboxService`
- [x] Implement `_mailbox_message_handler()` wrapper
- [x] Update `send_message()` to use `RedisMailboxService.send_message()`
- [x] Update `shutdown()` to call `RedisMailboxService.stop()`
- [x] Add mailbox connection error handling
- [x] Add recovery_callback support (optional)
- [x] Create integration tests with real Redis
- [ ] Update documentation with integration examples

### Optional: beast-observability

**Current Status**: Logging only (stdlib logging)

**Planned Integration**:
```python
from beast_observability import TelemetryCollector

class BaseAgent:
    def __init__(self, ...):
        if OBSERVABILITY_AVAILABLE:
            self._telemetry = TelemetryCollector(self.agent_id)
```

**Design Decision**: Optional dependency to keep Tier 1 minimal

---

## 🎨 Agent Patterns

### Pattern 1: Per-Repo Agent

**Use Case**: Monitor and automate a single repository

**Design**:
```python
class RepoAgent(BaseAgent):
    def __init__(self, repo_name: str):
        super().__init__(
            agent_id=f"repo-agent-{repo_name}",
            capabilities=["code_review", "pr_validation", "security_scan"]
        )
        self.repo_name = repo_name
```

**Deployment**: One agent instance per repository

---

### Pattern 2: Per-Branch Agent

**Use Case**: Branch-specific automation (deployment, testing)

**Design**:
```python
class BranchAgent(BaseAgent):
    def __init__(self, repo_name: str, branch_name: str):
        super().__init__(
            agent_id=f"branch-agent-{repo_name}-{branch_name}",
            capabilities=["deployment", "testing", "monitoring"]
        )
        self.repo = repo_name
        self.branch = branch_name
```

**Deployment**: Multiple agent instances per repository (one per branch)

---

### Pattern 3: Specialized Agent

**Use Case**: Domain-specific capabilities (NIM, ADK, etc.)

**Design**:
```python
class NIMAgent(BaseAgent):
    def __init__(self, nim_endpoint: str):
        super().__init__(
            agent_id=f"nim-agent-{uuid4()}",
            capabilities=["llm_reasoning", "embedding_retrieval"]
        )
        self.nim = NIMClient(nim_endpoint)
    
    @capability("llm_reasoning")
    async def reason(self, prompt: str) -> str:
        return await self.nim.generate(prompt)
```

**Deployment**: One or more specialized agents in the ecosystem

---

## 📚 Documentation Architecture

### README.md
- Quick start guide
- Installation instructions
- Agent pattern examples
- API overview

### docs/ (Future)
- `AGENT_DEVELOPMENT.md` - How to create custom agents
- `DEPLOYMENT.md` - Deployment patterns
- `API.md` - Complete API reference

### examples/
- `simple_agent.py` - Basic agent with single capability
- `advanced_agent.py` (Future) - Multi-capability agent with messaging

---

## 🔒 Security Considerations

### No Hardcoded Credentials
- All sensitive configuration via environment variables
- No default credentials in code

### Least Privilege
- Agents declare only required capabilities
- No god-mode agents

### Error Handling
- Exceptions logged but don't crash agent
- Error count tracked in health status

---

## 🚀 Performance Considerations

### Async by Default
- All I/O operations are async
- Non-blocking message handling

### Lazy Initialization
- Mailbox connection initialized in startup(), not __init__
- Reduces startup overhead

### Memory Efficiency
- No message queue in BaseAgent (delegated to mailbox)
- Minimal state tracking

---

## 🎯 Quality Gates

### Code Quality
- ✅ Black formatting (88 char line length)
- ✅ Type annotations (mypy)
- ✅ Docstrings (all public methods)

### Testing
- ✅ 90%+ test coverage target
- ✅ Pytest with async support
- ✅ Coverage reporting (XML for SonarCloud)

### CI/CD
- ✅ GitHub Actions workflow
- ✅ SonarCloud integration
- ✅ Automated quality gates

---

## 🔄 Future Enhancements

### Phase 1 (v0.2.0)
- [ ] Integrate with beast-mailbox-core (uncomment TODOs)
- [ ] Implement discovery system
- [ ] Add message queue management

### Phase 2 (v0.3.0)
- [ ] Integrate with beast-observability
- [ ] Add telemetry hooks
- [ ] Implement capability introspection

### Phase 3 (v0.4.0)
- [ ] Add agent-to-agent authentication
- [ ] Implement capability versioning
- [ ] Add performance benchmarks

---

## 📋 Design Decisions Log

| Decision | Rationale | Trade-offs |
|----------|-----------|------------|
| Abstract base class (ABC) | Enforces implementation of on_startup/on_shutdown | Slightly more boilerplate for users |
| Async by default | Better performance for I/O-bound operations | Requires async runtime (asyncio) |
| Lazy mailbox connection | Reduces __init__ overhead, clearer error handling | Requires explicit startup() call |
| Separate types module | Clean separation of concerns | One extra import for users |
| Metadata-based capabilities | Enables introspection and discovery | Requires decorator usage |
| Commented TODOs for mailbox | Allows independent testing of BaseAgent | Mailbox integration deferred to v0.2.0 |
| **Pydantic dependency** | Type-safe validation for messages/config; consistency across ecosystem; better DX with clear errors; automatic JSON serialization | Adds dependency (violates strict minimal deps) but justified for foundation package |

---

## ✅ Design Validation

### Requirements Traceability

| Requirement | Design Element | Validated |
|-------------|----------------|-----------|
| FR-1: BaseAgent class | `base_agent.py` - BaseAgent(ABC) | ✅ |
| FR-2: Lifecycle | startup(), shutdown(), health_check() | ✅ |
| FR-3: Message handling | register_handler(), send_message() | ✅ |
| FR-4: Discovery | agent_id, capabilities attributes | ✅ |
| FR-5: Capability declaration | @capability decorator | ✅ |
| FR-6: Logging hooks | _setup_logging(), self._logger | ✅ |
| FR-7: Error handling | try/except in handle_message() | ✅ |
| FR-8: Configuration | _load_config(), env vars | ✅ |
| NFR-1: Minimal dependencies | Only beast-mailbox-core | ✅ |
| NFR-2: Performance | Async, lazy init | ✅ |
| NFR-3: Testing | 90%+ coverage target | ✅ |
| NFR-4: Documentation | README, docstrings, examples | ✅ |
| NFR-5: Packaging | pyproject.toml, PyPI ready | ✅ |

---

**Design Status**: ✅ Complete and Implemented

**Next**: See `tasks.md` for implementation breakdown

