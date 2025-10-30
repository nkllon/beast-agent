# AI Agent Guide for beast-agent

**Repository**: `nkllon/beast-agent`  
**Purpose**: Base agent class for all Beast Mode agents  
**Tier**: 1 (Foundation - Minimal Dependencies)  
**Status**: Active Development (v0.1.0)

---

## 🎯 What This Repository Is

**beast-agent provides the foundational `BaseAgent` abstract base class that ALL Beast Mode agents inherit from.**

This is **Tier 1** in the Beast Mode dependency graph - every other agent package depends on this. Any changes here impact the entire ecosystem.

---

## 📋 Before You Start

### Required Reading (In Order)

1. **`.kiro/specs/requirements.md`** - What this package must do (FR-1 to FR-8, NFR-1 to NFR-5)
2. **`.kiro/specs/design.md`** - How it's architected (state machine, patterns, integration points)
3. **`.kiro/specs/tasks.md`** - What was built (7 phases, 20 tasks)
4. **`.kiro/specs/QUALITY_STANDARDS_TEMPLATE.md`** - Quality bar (90%+ coverage, SonarCloud, zero defects)
5. **`.kiro/specs/SONARCLOUD_INTEGRATION_GUIDE.md`** - CI/CD integration

### Key Constraints

- ✅ **Minimal dependencies**: ONLY `beast-mailbox-core` and stdlib
- ✅ **Python >= 3.9**: Support 3.9, 3.10, 3.11, 3.12
- ✅ **90%+ test coverage**: Non-negotiable quality bar
- ✅ **Zero defects**: No linter errors, no type errors, no security issues
- ✅ **Async by default**: All I/O operations are async
- ✅ **Abstract base class**: Force subclasses to implement on_startup/on_shutdown

---

## 🏗️ Architecture Overview

### Core Components

```
src/beast_agent/
├── __init__.py          # Package exports (BaseAgent, AgentState, HealthStatus, capability)
├── base_agent.py        # BaseAgent abstract class (lifecycle, messaging, health)
├── types.py             # AgentState enum, HealthStatus dataclass
└── decorators.py        # @capability decorator for method marking
```

### Lifecycle State Machine

```
INITIALIZING → READY → RUNNING → STOPPING → STOPPED
                  ↕
               (ERROR)
```

**Critical**: State transitions are managed by `BaseAgent`. Subclasses must NOT override state management.

### Design Patterns

1. **Template Method Pattern**: `startup()` calls `on_startup()` hook
2. **Strategy Pattern**: Message handlers registered per message type
3. **Decorator Pattern**: `@capability` marks agent methods

---

## 🧪 Testing Requirements

### Test Structure

```
tests/
├── test_base_agent.py   # Lifecycle, health checks, handler registration
└── test_decorators.py   # Capability decorator metadata
```

### Coverage Requirements

- **Unit tests**: >= 70% coverage
- **Integration tests**: >= 20% coverage (with beast-mailbox-core when integrated)
- **Total coverage**: >= 90%

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/beast_agent --cov-report=html

# Run specific test
pytest tests/test_base_agent.py::test_agent_startup
```

---

## 🚀 Development Workflow

### Making Changes

1. **Read the specs first** - Understand requirements and design
2. **Check existing tests** - See what's already validated
3. **Write tests first** - TDD approach for new features
4. **Implement changes** - Follow existing patterns
5. **Run quality checks** - Linting, type checking, tests
6. **Update docs** - README, docstrings, specs if needed

### Quality Checks

```bash
# Format code
black src/ tests/ examples/

# Lint code
flake8 src/ tests/ examples/

# Type check
mypy src/

# Run tests
pytest --cov=src/beast_agent --cov-report=term-missing

# Security scan
bandit -r src/
```

---

## 📦 Key Files and Their Purpose

### Configuration Files

- **`pyproject.toml`**: Package metadata, dependencies, tool configuration
- **`sonar-project.properties`**: SonarCloud quality tracking
- **`.github/workflows/sonarcloud.yml`**: CI/CD pipeline

### Source Files

- **`src/beast_agent/base_agent.py`**: Core implementation (180 LOC)
  - `BaseAgent(ABC)` class
  - Lifecycle methods: `startup()`, `shutdown()`, `health_check()`
  - Message routing: `register_handler()`, `handle_message()`
  - Abstract hooks: `on_startup()`, `on_shutdown()`

- **`src/beast_agent/types.py`**: Type definitions (30 LOC)
  - `AgentState` enum (6 states)
  - `HealthStatus` dataclass

- **`src/beast_agent/decorators.py`**: Decorators (30 LOC)
  - `@capability(name, version)` decorator

### Documentation Files

- **`README.md`**: User-facing documentation (quick start, patterns, examples)
- **`.kiro/specs/`**: Spec-driven development documentation
- **`examples/simple_agent.py`**: Runnable example

---

## 🔧 Common Tasks

### Task 1: Add New Agent Method

**Example**: Add a new utility method to `BaseAgent`

```python
# 1. Add to src/beast_agent/base_agent.py
def get_capabilities_metadata(self) -> List[Dict[str, str]]:
    """Get metadata for all registered capabilities."""
    return [
        {"name": cap, "version": "1.0.0"}
        for cap in self.capabilities
    ]

# 2. Add test to tests/test_base_agent.py
@pytest.mark.asyncio
async def test_get_capabilities_metadata():
    agent = TestAgent(agent_id="test", capabilities=["cap1", "cap2"])
    metadata = agent.get_capabilities_metadata()
    assert len(metadata) == 2
    assert metadata[0]["name"] == "cap1"

# 3. Update docstrings and type hints
# 4. Run quality checks
```

### Task 2: Integrate with beast-mailbox-core

**Current Status**: Commented out (TODOs in `base_agent.py`)

**To Integrate**:
1. Uncomment mailbox connection code in `startup()`
2. Uncomment mailbox disconnection in `shutdown()`
3. Add integration tests with real Redis
4. Update documentation

**Search for**: `# TODO: Integrate with beast-mailbox-core`

### Task 3: Add New Agent Pattern

**Example**: Add a new pattern to `examples/`

```python
# 1. Create examples/new_pattern_agent.py
# 2. Follow simple_agent.py structure
# 3. Add to README.md under "Agent Patterns"
# 4. Test the example runs successfully
```

---

## 🚨 Critical Rules

### DO NOT

- ❌ **Break backward compatibility** - This is Tier 1, other packages depend on it
- ❌ **Add dependencies** - Keep minimal (only beast-mailbox-core + stdlib)
- ❌ **Skip tests** - 90%+ coverage is non-negotiable
- ❌ **Bypass quality checks** - All checks must pass before commit
- ❌ **Hardcode configuration** - Use env vars or constructor args
- ❌ **Override state management** - State transitions are BaseAgent's responsibility

### ALWAYS

- ✅ **Read specs first** - Understand requirements and design
- ✅ **Write tests first** - TDD approach
- ✅ **Maintain async** - All I/O operations are async
- ✅ **Use type hints** - Full type annotation coverage
- ✅ **Document changes** - Update docstrings and README
- ✅ **Run quality checks** - Before every commit

---

## 🔗 Integration Points

### Upstream Dependencies (Required)

- **beast-mailbox-core** (>=0.3.0)
  - Provides: `MailboxClient` for agent messaging
  - Status: Integration deferred to v0.2.0 (TODOs in code)
  - Integration: Uncomment TODOs in `base_agent.py`

### Downstream Dependents (Packages That Use This)

- **beast-agentic-framework** (Tier 2.5)
- **beast-nim-integration** (Tier 3)
- **beast-adk-integration** (Tier 3)
- **beast-adapter-aws** (Tier 2)
- **beast-adapter-gcp** (Tier 2)
- **beast-mailbox-agent** (refactor to extend BaseAgent)

**Impact**: Changes here affect ALL downstream packages. Test thoroughly.

---

## 📊 Quality Standards (From beast-mailbox-core)

### Required Metrics

- ✅ **Test Coverage**: >= 90%
- ✅ **Maintainability Rating**: A
- ✅ **Security Rating**: A
- ✅ **Reliability Rating**: A
- ✅ **Code Smells**: Minimal
- ✅ **Duplications**: <= 3.0%
- ✅ **Bugs**: ZERO
- ✅ **Vulnerabilities**: ZERO

### CI/CD Pipeline

GitHub Actions runs on every push and PR:
1. Install dependencies
2. Run tests with coverage
3. SonarCloud quality scan
4. Report results

**Quality Gate must pass before merge.**

---

## 🎯 Current Implementation Status

### ✅ Completed (v0.1.0)

- [x] BaseAgent abstract class
- [x] AgentState enum (6 states)
- [x] HealthStatus dataclass
- [x] @capability decorator
- [x] Lifecycle management (startup, shutdown)
- [x] Health checks (health_check, ready)
- [x] Message routing (register_handler, handle_message)
- [x] Configuration management (env vars, constructor args)
- [x] Logging (per-agent logger)
- [x] Unit tests (lifecycle, decorators)
- [x] SonarCloud integration
- [x] GitHub Actions workflow
- [x] Documentation (README, specs, examples)

### ⏳ Planned (v0.2.0)

- [ ] Integrate with beast-mailbox-core (uncomment TODOs)
- [ ] Implement discovery system
- [ ] Add message queue management
- [ ] Integration tests with real Redis
- [ ] Performance benchmarks

### 🔮 Future (v0.3.0+)

- [ ] Integrate with beast-observability
- [ ] Add telemetry hooks
- [ ] Implement capability introspection
- [ ] Agent-to-agent authentication
- [ ] Capability versioning

---

## 🆘 Troubleshooting

### Tests Failing

**Problem**: Tests fail after making changes

**Solution**:
1. Run tests individually to isolate failure
2. Check if you broke BaseAgent contract
3. Verify async/await usage
4. Check state transitions match state machine

### Linting Errors

**Problem**: Black/Flake8/MyPy errors

**Solution**:
```bash
# Auto-fix formatting
black src/ tests/ examples/

# Check remaining issues
flake8 src/ tests/
mypy src/
```

### Import Errors

**Problem**: Cannot import beast_agent

**Solution**:
```bash
# Install in development mode
pip install -e .

# Or use directly
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

---

## 📚 Additional Resources

### Internal Documentation

- `.kiro/specs/requirements.md` - Functional and non-functional requirements
- `.kiro/specs/design.md` - Architecture and design decisions
- `.kiro/specs/tasks.md` - Implementation task breakdown
- `README.md` - User-facing documentation

### External References

- [beast-mailbox-core](https://github.com/nkllon/beast-mailbox-core) - Reference implementation for quality standards
- [Python AsyncIO](https://docs.python.org/3/library/asyncio.html) - Async programming patterns
- [ABCs in Python](https://docs.python.org/3/library/abc.html) - Abstract base classes

### Beast Mode Ecosystem

- **OpenFlow-Playground**: https://github.com/louspringer/OpenFlow-Playground
- **Beast Mode Packages**: https://github.com/nkllon
- **Dependency Map**: See `.kiro/specs/DEPENDENCY_MAP_AND_PACKAGES.md` (in OpenFlow-Playground)

---

## 🤝 Contributing

### For AI Agents

1. **Read all specs** before making changes
2. **Follow existing patterns** - consistency is key
3. **Test thoroughly** - 90%+ coverage required
4. **Document changes** - update README and specs
5. **Run quality checks** - all must pass
6. **Commit with descriptive messages** - use conventional commits

### Commit Message Format

```
<type>: <description>

<body>

<footer>
```

**Types**: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`

**Example**:
```
feat: Add capability introspection to BaseAgent

Implement get_capabilities_metadata() method to query
registered capabilities with their versions.

- Added BaseAgent.get_capabilities_metadata()
- Added unit tests for capability introspection
- Updated README with new method

Closes #42
```

---

## ✅ Pre-Commit Checklist

Before committing changes:

- [ ] Read relevant specs
- [ ] Tests written (TDD)
- [ ] Tests passing (pytest)
- [ ] Coverage >= 90% (pytest --cov)
- [ ] Formatted (black)
- [ ] Linted (flake8)
- [ ] Type checked (mypy)
- [ ] Security scanned (bandit)
- [ ] Documentation updated
- [ ] Examples still run
- [ ] Commit message follows format

---

## 🎯 Success Metrics

### Package Health

- ✅ All tests passing
- ✅ 90%+ test coverage
- ✅ SonarCloud Quality Gate: Passed
- ✅ Zero linter errors
- ✅ Zero type errors
- ✅ Zero security issues

### Ecosystem Impact

- ✅ Used by all downstream packages (Tier 2+)
- ✅ No breaking changes without major version bump
- ✅ Clear upgrade path for consumers

---

**Remember**: You are working on the **foundation** of the Beast Mode ecosystem. Quality and stability are paramount. Every change impacts multiple downstream packages.

**When in doubt, read the specs first.** 📚

---

**Last Updated**: 2025-10-30  
**Version**: 0.1.0  
**Status**: Active Development

