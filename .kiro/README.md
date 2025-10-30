# Kiro / cc-sdd Integration

This directory contains **spec-driven development (SDD)** configuration and templates for the beast-agent package.

## 🎯 What is cc-sdd?

**cc-sdd** (Cursor Commands for Spec-Driven Development) is a workflow system that enables:
- Systematic feature development through specs
- Requirements → Design → Tasks → Implementation flow
- Gap analysis and design validation
- Traceability from requirements to code

**Project**: https://github.com/gotalab/cc-sdd

---

## 📁 Directory Structure

```
.kiro/
├── config.yaml                  # cc-sdd project configuration
├── specs/                       # Specification documents
│   ├── requirements.md          # Functional and non-functional requirements
│   ├── design.md                # Architecture and design decisions
│   ├── tasks.md                 # Task breakdown and completion status
│   ├── QUALITY_STANDARDS_TEMPLATE.md
│   └── SONARCLOUD_INTEGRATION_GUIDE.md
└── settings/
    ├── templates/               # cc-sdd templates
    │   └── specs/
    │       ├── design.md
    │       ├── init.json
    │       ├── requirements-init.md
    │       ├── requirements.md
    │       └── tasks.md
    └── rules/                   # cc-sdd workflow rules
        ├── design-discovery-full.md
        ├── design-discovery-light.md
        ├── design-principles.md
        ├── design-review.md
        ├── ears-format.md
        ├── gap-analysis.md
        ├── steering-principles.md
        └── tasks-generation.md
```

---

## 🚀 Available cc-sdd Commands

### Feature Development Workflow

```bash
# 1. Initialize new feature spec
/kiro:spec-init <feature-name>

# 2. Create requirements document
/kiro:spec-requirements <feature-name>

# 3. Create design document
/kiro:spec-design <feature-name> -y

# 4. Create tasks breakdown
/kiro:spec-tasks <feature-name> -y

# 5. Implement specific tasks
/kiro:spec-impl <feature-name> 1.1,1.2,1.3
```

### Validation Commands

```bash
# Analyze gaps between existing code and requirements
/kiro:validate-gap <feature-name>

# Validate design integration
/kiro:validate-design <feature-name>

# Check feature status
/kiro:spec-status <feature-name>
```

---

## 📋 Example Workflow

### Example: Add Capability Introspection

```bash
# Step 1: Initialize spec
/kiro:spec-init capability-introspection

# Step 2: Define requirements
/kiro:spec-requirements capability-introspection
# This creates: .kiro/specs/capability-introspection/requirements.md

# Step 3: Design the feature
/kiro:spec-design capability-introspection -y
# This creates: .kiro/specs/capability-introspection/design.md

# Step 4: Break down tasks
/kiro:spec-tasks capability-introspection -y
# This creates: .kiro/specs/capability-introspection/tasks.md

# Step 5: Implement tasks
/kiro:spec-impl capability-introspection 1.1,1.2,1.3
# Implements tasks 1.1, 1.2, 1.3 from the task breakdown
```

---

## 📚 Spec Document Templates

### requirements.md Template

Based on **EARS format** (Easy Approach to Requirements Syntax):

```markdown
# Feature Name - Requirements

## Functional Requirements

### FR-1: Core Functionality
**When** <trigger>, **the system shall** <action>.

### FR-2: User Interaction
**If** <condition>, **then** <system behavior>.

## Non-Functional Requirements

### NFR-1: Performance
**Where** <feature>, **the system shall** <metric>.

### NFR-2: Security
**The system shall** <security requirement>.
```

### design.md Template

```markdown
# Feature Name - Design

## Architecture Overview
[Component diagrams, class hierarchies]

## Module Structure
[File organization and responsibilities]

## Integration Points
[Dependencies and interactions]

## Design Decisions
[Rationale for key architectural choices]
```

### tasks.md Template

```markdown
# Feature Name - Tasks

## Phase 1: Foundation
### Task 1.1: Setup
- [ ] Action item 1
- [ ] Action item 2

### Task 1.2: Core Implementation
- [ ] Action item 1
- [ ] Action item 2

## Phase 2: Testing
### Task 2.1: Unit Tests
- [ ] Action item 1
```

---

## 🎯 Quality Gates

All features developed via cc-sdd must meet:

- ✅ **90%+ test coverage** (from QUALITY_STANDARDS_TEMPLATE.md)
- ✅ **SonarCloud Quality Gate: Passed**
- ✅ **Zero linter errors** (Black, Flake8, MyPy)
- ✅ **Zero security issues** (Bandit)
- ✅ **Requirements traceability** (all FRs mapped to tests)

---

## 🔗 Integration with AGENT.md

When working on new features:

1. **Read AGENT.md first** - Understand repository constraints
2. **Use cc-sdd workflow** - Follow spec-driven development
3. **Meet quality standards** - 90%+ coverage, zero defects
4. **Update documentation** - README, docstrings, specs

---

## 📖 Additional Resources

### Internal Documentation
- `AGENT.md` - AI agent working guide
- `.kiro/specs/requirements.md` - Current package requirements
- `.kiro/specs/design.md` - Current package design
- `.kiro/specs/tasks.md` - Current package tasks

### External Resources
- [cc-sdd GitHub](https://github.com/gotalab/cc-sdd) - Official cc-sdd repository
- [Kiro IDE](https://kiro.dev) - Enhanced spec management
- [EARS Format](https://alistairmavin.com/ears/) - Requirements specification method

---

## ✅ Current Specs

The `.kiro/specs/` directory contains the current specifications for beast-agent v0.1.0:

- **requirements.md** - 8 Functional Requirements (FR-1 to FR-8), 5 Non-Functional (NFR-1 to NFR-5)
- **design.md** - Architecture, state machine, integration points
- **tasks.md** - 7 phases, 20 tasks (all completed for v0.1.0)
- **QUALITY_STANDARDS_TEMPLATE.md** - Quality metrics from beast-mailbox-core
- **SONARCLOUD_INTEGRATION_GUIDE.md** - SonarCloud setup

---

**Use cc-sdd for all new features to maintain high-quality, well-documented development!** 🚀

