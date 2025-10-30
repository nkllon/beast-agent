# Requirements Writing Guidance for AI Agents

**Purpose**: Learn from the NFR-1 refinement to write better, more flexible requirements

---

## 🚨 Common Pitfall: Overly Rigid Constraints

### The Problem We Encountered

**Original NFR-1**:
```
### NFR-1: Minimal Dependencies
- **Must** depend ONLY on beast-mailbox-core
- **Must** use stdlib for everything else
```

### Why This Was Problematic

1. **Too Absolute**: "ONLY" creates an inflexible constraint that doesn't account for legitimate architectural decisions
2. **No Framework**: Doesn't provide criteria for evaluating when exceptions might be justified
3. **Assumes Single Solution**: Implies there's only one valid way to achieve the goal (minimal dependencies)
4. **Blocks Architectural Decisions**: Forces implementation details rather than guiding them

### What Happened

During implementation review, we discovered that `pydantic` was a justified dependency for:
- Type-safe validation (FR-3: message serialization)
- Configuration validation (FR-8: configuration validation)
- Consistency across ecosystem
- Better developer experience

But the original requirement blocked this architectural decision.

---

## ✅ Better Approach: Principle-Based Requirements

### The Refined NFR-1

```
### NFR-1: Minimal Dependencies
**Principle**: Minimize dependencies to reduce footprint, avoid conflicts, and maintain flexibility for downstream packages.

**Required Dependencies**:
- **Must** depend on beast-mailbox-core (messaging and discovery)
- **Must** depend on pydantic (type-safe validation and serialization)

**Additional Dependencies Policy**:
- **Must** use stdlib for everything else unless justified
- **Must** document rationale for any additional dependency
- **Must** ensure each dependency provides clear value that can't be achieved with stdlib
- **Should** make beast-observability optional (not required)
- **Must** not depend on any cloud provider SDKs
- **Must** be platform-agnostic

**Rationale for Pydantic**:
- Provides type-safe validation for messages (FR-3) and configuration (FR-8)
- Ensures consistency across Beast Mode ecosystem (foundation package)
- Better developer experience with clear error messages
- Automatic JSON serialization/deserialization for message handling
- Type coercion and validation reduces runtime errors

**Dependency Criteria**: Additional dependencies beyond beast-mailbox-core and pydantic must:
1. Address a specific functional requirement (FR-1 through FR-8)
2. Provide capabilities not achievable with stdlib alone
3. Have documented rationale in design decisions log
4. Maintain platform-agnostic and minimal footprint principles
```

### Why This Works Better

1. **States the Principle**: Explains *why* minimal dependencies matter
2. **Explicit Requirements**: Lists what's required (beast-mailbox-core, pydantic)
3. **Provides Framework**: Criteria for evaluating additional dependencies
4. **Documents Rationale**: Each dependency has documented justification
5. **Guides Decisions**: Helps make architectural decisions rather than blocking them

---

## 📋 Guidelines for Writing Better Requirements

### 1. State Principles, Not Just Constraints

❌ **Bad**: "Must depend ONLY on X"
✅ **Good**: "Minimize dependencies. Required: X. Additional dependencies must meet criteria..."

**Why**: Principles provide flexibility while maintaining intent.

### 2. Provide Evaluation Criteria

❌ **Bad**: "No additional dependencies allowed"
✅ **Good**: "Additional dependencies must: (1) Address FR-X, (2) Not achievable with stdlib, (3) Documented rationale, (4) Maintain principles"

**Why**: Criteria enable justified exceptions while maintaining standards.

### 3. Document Rationale for Explicit Choices

❌ **Bad**: "Must depend on pydantic"
✅ **Good**: "Must depend on pydantic. Rationale: Type-safe validation for FR-3 and FR-8..."

**Why**: Rationale helps future maintainers understand decisions and evaluate changes.

### 4. Separate "Required" from "Policy"

❌ **Bad**: "Must depend ONLY on X and stdlib"
✅ **Good**: "Required: X. Policy: Use stdlib unless criteria met. Criteria: ..."

**Why**: Clear separation between hard requirements and flexible policies.

### 5. Avoid Absolute Terms Like "ONLY"

❌ **Bad**: "ONLY beast-mailbox-core"
✅ **Good**: "Required: beast-mailbox-core. Additional dependencies must meet criteria..."

**Why**: "ONLY" creates rigid constraints that block legitimate architectural decisions.

---

## 🎯 Template for Dependency Requirements

When writing dependency requirements, use this structure:

```
### NFR-X: [Dependency Category]

**Principle**: [Why this matters - reduce footprint, avoid conflicts, etc.]

**Required Dependencies**:
- **Must** depend on [X] ([rationale])
- **Must** depend on [Y] ([rationale])

**Additional Dependencies Policy**:
- **Must** use [stdlib/standard approach] unless justified
- **Must** document rationale for any additional dependency
- **Must** ensure each dependency provides clear value
- **Must** not [specific exclusions - e.g., cloud SDKs]
- **Must** [platform/architectural constraints]

**Rationale for [Specific Dependency]**:
- [Clear justification 1]
- [Clear justification 2]
- [Clear justification 3]

**Dependency Criteria**: Additional dependencies must:
1. Address a specific functional requirement
2. Provide capabilities not achievable with [standard approach]
3. Have documented rationale in design decisions log
4. Maintain [key principles]
```

---

## 🔍 Red Flags: When to Refine a Requirement

If a requirement contains:
- ❌ **Absolute terms**: "ONLY", "NEVER", "ALWAYS" (without exceptions framework)
- ❌ **No rationale**: Lists dependencies without explaining why
- ❌ **No criteria**: Blocks additions without framework for evaluation
- ❌ **Assumes implementation**: Prescribes *how* rather than *what*
- ❌ **Single solution**: Doesn't allow for architectural decisions

**Then**: Refine it to include principles, criteria, and rationale.

---

## 💡 Key Takeaway

**Requirements should guide architectural decisions, not block them.**

A good requirement:
- States the principle/goal
- Provides criteria for evaluation
- Documents rationale for specific choices
- Allows for justified exceptions

A bad requirement:
- Creates rigid, absolute constraints
- Blocks legitimate architectural decisions
- Assumes there's only one valid solution
- Lacks framework for evaluation

---

## 📚 Example: Applying This to Other Requirements

### Configuration Requirement

❌ **Bad**: "Must use environment variables ONLY"
✅ **Good**: "Must load configuration from environment variables. Policy: Constructor args override env vars. Defaults provided. Validation required on startup."

### Error Handling Requirement

❌ **Bad**: "Must never crash on errors"
✅ **Good**: "Must handle errors gracefully. Policy: Log errors, track error count, support retry logic, provide error callbacks. Exceptions must not crash agent lifecycle."

---

**Remember**: Requirements document *what* and *why*. Design documents *how*. Don't mix them.

**For Requirements Writers**: When you find yourself writing "ONLY" or "NEVER", ask: "Is this really absolute, or should I provide criteria for evaluation?"

