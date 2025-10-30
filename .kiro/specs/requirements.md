# beast-agent - Requirements

**Package Type**: PyPI-ready Python library  
**Tier**: 1 (Foundation - Minimal Dependencies)  
**Purpose**: Base agent class for ALL Beast Mode agents  
**Target**: Production-ready, 90%+ coverage, universal agent foundation

**Insight Source**: External agent recommendation - "significantly tighten multi-agent operations"

---

## 🎯 Package Vision

**The foundational base class that EVERY Beast Mode agent inherits from, providing standardized lifecycle, messaging, discovery, and capability management.**

**Key Principle**: "At least one agent per repo, potentially more per branch" - agents are the operational units of Beast Mode.

**Architectural Clarity**: 
- `beast-agent` = LOW-level base class (every agent IS-A beast-agent)
- `beast-agentic-framework` = HIGH-level orchestration (multi-agent coordination)

---

## 📋 Functional Requirements

### FR-1: BaseAgent Class
- **Must** provide `BaseAgent` abstract base class
- **Must** define standard agent lifecycle methods
- **Must** enforce capability declaration
- **Must** provide message handling interface
- **Must** support agent registration and discovery
- **Must** be extensible for specific agent types

### FR-2: Agent Lifecycle
- **Must** implement `startup()` - Agent initialization
- **Must** implement `shutdown()` - Graceful cleanup
- **Must** implement `health_check()` - Health status reporting
- **Must** implement `ready()` - Readiness probe
- **Must** handle lifecycle transitions (starting → ready → running → stopping → stopped)
- **Must** support async lifecycle methods

### FR-3: Message Handling (via beast-mailbox-core)
- **Must** integrate with beast-mailbox-core for messaging
- **Must** provide `send_message(target, content)` method
- **Must** provide `register_handler(message_type, callback)` method
- **Must** route incoming messages to registered handlers
- **Must** support request/response patterns
- **Must** support pub/sub patterns
- **Must** handle message serialization/deserialization

### FR-4: Agent Registration & Discovery
- **Must** register agent on startup (with central registry or service mesh)
- **Must** declare agent capabilities
- **Must** declare agent ID (unique per agent instance)
- **Must** support agent discovery (find other agents by capability)
- **Must** support agent health monitoring
- **Must** handle agent join/leave events

### FR-5: Capability Declaration
- **Must** provide `@capability` decorator for methods
- **Must** expose capabilities via metadata
- **Must** support capability querying
- **Must** validate capability usage
- **Must** support capability versioning

### FR-6: Logging & Telemetry Hooks
- **Must** provide standard logging interface
- **Must** integrate with Python stdlib logging
- **Must** provide telemetry hooks (for beast-observability)
- **Must** log agent lifecycle events
- **Must** log message handling events
- **Must** NOT require beast-observability (optional integration)

### FR-7: Error Handling
- **Must** handle message delivery failures
- **Must** handle handler exceptions gracefully
- **Must** provide error callbacks
- **Must** support retry logic
- **Must** emit error metrics

### FR-8: Configuration
- **Must** load configuration from environment variables
- **Must** support configuration via constructor args
- **Must** validate configuration on startup
- **Must** provide sensible defaults
- **Must** support per-repo, per-branch agent patterns

---

## 🔒 Non-Functional Requirements

### NFR-1: Minimal Dependencies
- **Must** depend ONLY on beast-mailbox-core
- **Must** use stdlib for everything else
- **Should** make beast-observability optional
- **Must** not depend on any cloud provider SDKs
- **Must** be platform-agnostic

### NFR-2: Performance
- **Must** handle message dispatch <10ms overhead
- **Must** support 1000+ messages/sec per agent
- **Must** not block on I/O in message handlers
- **Must** support async/await throughout
- **Must** be memory-efficient (no leaks)

### NFR-3: Testing
- **Must** achieve 90%+ test coverage
- **Must** include unit tests for lifecycle
- **Must** include integration tests with beast-mailbox-core
- **Must** include tests for capability system
- **Must** include performance tests

### NFR-4: Documentation
- **Must** include comprehensive README
- **Must** include agent development tutorial
- **Must** include deployment patterns (repo agent, branch agent)
- **Must** include examples (simple agent, multi-capability agent)
- **Must** include API reference

### NFR-5: Packaging
- **Must** be installable via `pip install beast-agent`
- **Must** follow semantic versioning (start 0.1.0)
- **Must** include `pyproject.toml` with metadata
- **Must** include LICENSE (MIT)
- **Must** publish to PyPI

---

## 🧩 Component Architecture

### Core Classes

#### `BaseAgent` (Abstract)
```python
from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional
from beast_mailbox_core import MailboxClient

class BaseAgent(ABC):
    """Base class for all Beast Mode agents"""
    
    def __init__(
        self,
        agent_id: str,
        capabilities: List[str],
        mailbox_url: Optional[str] = None,
        config: Optional[Dict] = None
    ):
        """Initialize agent with ID, capabilities, and configuration"""
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.mailbox = MailboxClient(mailbox_url or self._get_mailbox_url())
        self.config = config or self._load_config()
        self._handlers: Dict[str, Callable] = {}
        self._state = AgentState.INITIALIZING
        
    async def startup(self) -> None:
        """Initialize agent and register with mailbox"""
        await self.mailbox.connect()
        await self.mailbox.register_agent(self.agent_id, self.capabilities)
        await self.on_startup()
        self._state = AgentState.READY
        
    @abstractmethod
    async def on_startup(self) -> None:
        """Subclass hook for custom startup logic"""
        
    async def shutdown(self) -> None:
        """Graceful shutdown"""
        self._state = AgentState.STOPPING
        await self.on_shutdown()
        await self.mailbox.disconnect()
        self._state = AgentState.STOPPED
        
    @abstractmethod
    async def on_shutdown(self) -> None:
        """Subclass hook for custom shutdown logic"""
        
    def health_check(self) -> HealthStatus:
        """Return agent health status"""
        
    def ready(self) -> bool:
        """Return True if agent is ready to handle messages"""
        
    def register_handler(
        self, 
        message_type: str, 
        handler: Callable
    ) -> None:
        """Register handler for message type"""
        
    async def send_message(
        self, 
        target: str, 
        message_type: str, 
        content: dict
    ) -> None:
        """Send message to target agent"""
        
    async def handle_message(self, message: Message) -> None:
        """Route message to registered handler"""
```

#### `AgentState` (Enum)
```python
from enum import Enum

class AgentState(Enum):
    """Agent lifecycle states"""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
```

#### `@capability` Decorator
```python
def capability(name: str, version: str = "1.0.0"):
    """Decorator to mark methods as agent capabilities"""
    def decorator(func):
        func._capability_name = name
        func._capability_version = version
        return func
    return decorator

# Usage:
class MyAgent(BaseAgent):
    @capability("process_document", version="1.0.0")
    async def process_document(self, document: str) -> dict:
        """Process document and return results"""
```

#### `HealthStatus` (Dataclass)
```python
@dataclass
class HealthStatus:
    """Agent health status"""
    healthy: bool
    state: AgentState
    last_heartbeat: datetime
    message_queue_size: int
    error_count: int
    metadata: dict
```

---

## 🧪 Testing Requirements

### Unit Tests (70% coverage minimum)
- BaseAgent initialization
- Lifecycle transitions
- Message routing
- Capability registration
- Health checks
- Configuration loading
- Error handling

### Integration Tests (20% coverage minimum)
- Integration with beast-mailbox-core
- Agent registration and discovery
- Message send/receive
- Multi-agent communication
- Lifecycle with real mailbox

### Performance Tests (Required)
- Message dispatch latency (<10ms)
- Throughput (1000+ msg/sec)
- Memory usage (no leaks)
- Startup/shutdown time

---

## 📚 Documentation Requirements

### README.md
- Quick start (create simple agent)
- Agent patterns (repo agent, branch agent)
- Lifecycle explanation
- Capability system
- Examples
- Deployment guide

### Agent Development Guide (`docs/AGENT_DEVELOPMENT.md`)
- How to create custom agents
- Best practices
- Capability design
- Message handling patterns
- Error handling strategies

### Deployment Patterns (`docs/DEPLOYMENT.md`)
- **One agent per repo** - Monitor repo events
- **Multiple agents per branch** - Branch-specific automation
- **Agent orchestration** - Coordinating multiple agents
- **Agent scaling** - Horizontal scaling patterns

### API Documentation
- Full docstrings
- Type annotations
- Parameter descriptions
- Return values
- Exceptions

---

## 🔄 Integration Points

### Required: beast-mailbox-core
- Agent registration
- Message pub/sub
- Agent discovery
- Health monitoring

### Optional: beast-observability
- Telemetry emission
- Structured logging
- Trace correlation
- Metrics collection

### Optional: Any Cloud Platform
- Works on AWS, GCP, Azure, on-prem
- No cloud-specific code
- Platform-agnostic by design

---

## 🎯 Use Cases

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
```

### Specialized Agent Pattern
```python
class NIMAgent(BaseAgent):
    """Agent powered by NVIDIA NIM"""
    
    def __init__(self, nim_endpoint: str):
        super().__init__(
            agent_id=f"nim-agent-{uuid4()}",
            capabilities=["llm_reasoning", "embedding_retrieval"]
        )
        self.nim = NIMClient(nim_endpoint)
        
    @capability("llm_reasoning")
    async def reason(self, prompt: str) -> str:
        """LLM reasoning via NIM"""
```

---

## 🚀 Success Criteria

### Package Quality
- [ ] Published to PyPI
- [ ] 90%+ test coverage
- [ ] Zero Bandit HIGH/MEDIUM issues
- [ ] Black/Flake8/MyPy compliant
- [ ] Comprehensive documentation

### Adoption
- [ ] Used by beast-nim-integration
- [ ] Used by beast-adk-integration
- [ ] Used by aws-nvidia-hackathon-app
- [ ] Used by cloud-run-hackathon-app
- [ ] Used by beast-agentic-framework

### Architectural Impact
- [ ] Standardizes ALL agent development
- [ ] Enables per-repo agent pattern
- [ ] Enables per-branch agent pattern
- [ ] Simplifies multi-agent coordination
- [ ] Reduces code duplication across agents

---

## 📝 Traceability

**Maps to**:
- Hackathon Requirements: Foundation for FR-050, FR-051
- Multi-agent operations: Tightens coordination
- Beast Mode framework: Standardizes agent implementation
- Both AWS×NVIDIA and Cloud Run: Universal base class

**Depended On By**:
- beast-agentic-framework (orchestration)
- beast-nim-integration (NIM-powered agents)
- beast-adk-integration (ADK-powered agents)
- aws-nvidia-hackathon-app
- cloud-run-hackathon-app

**Impact**: This ONE package makes ALL other agents consistent, testable, and production-ready.

---

## 🎯 Why This Is HIGHEST PRIORITY

### Architectural Benefits
1. **Consistency**: All agents follow same patterns
2. **Testability**: Standard testing approach for all agents
3. **Discoverability**: Agents can find each other
4. **Observability**: Standard telemetry hooks
5. **Scalability**: Horizontal scaling built-in

### Development Benefits
1. **Faster agent creation**: Inherit, implement capabilities, done
2. **Reduced duplication**: Common code in one place
3. **Easier debugging**: Standard lifecycle and logging
4. **Better documentation**: One place to document agent patterns
5. **Production-ready**: Enterprise patterns from day 1

### Operational Benefits
1. **Per-repo agents**: Monitor and automate repos
2. **Per-branch agents**: Branch-specific automation
3. **Agent scaling**: Deploy more agents as needed
4. **Agent health**: Standard health checks and monitoring
5. **Agent coordination**: Built-in discovery and messaging

---

**This package is the cornerstone. Build it right, everything else follows naturally.**

**Next**: Create `design.md` with detailed architecture, API contracts, and implementation plan.

