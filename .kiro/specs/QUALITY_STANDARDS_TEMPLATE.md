# Beast Mode Package Quality Standards

**Source**: beast-mailbox-core (production reference)  
**Standard**: Apply to ALL 8 packages in dual hackathon sprint  
**Non-Negotiable**: These are MINIMUM standards, not aspirations

---

## 📛 REQUIRED BADGES (Copy from beast-mailbox-core)

### PyPI Badges (5)
```markdown
[![PyPI version](https://img.shields.io/pypi/v/PACKAGE_NAME?label=PyPI&color=blue)](https://pypi.org/project/PACKAGE_NAME/)
[![Python Versions](https://img.shields.io/pypi/pyversions/PACKAGE_NAME.svg)](https://pypi.org/project/PACKAGE_NAME/)
[![Downloads](https://static.pepy.tech/badge/PACKAGE_NAME)](https://pepy.tech/project/PACKAGE_NAME)
[![PyPI status](https://img.shields.io/pypi/status/PACKAGE_NAME.svg)](https://pypi.org/project/PACKAGE_NAME/)
[![Wheel](https://img.shields.io/pypi/wheel/PACKAGE_NAME.svg)](https://pypi.org/project/PACKAGE_NAME/)
```

### Quality Badges (6)
```markdown
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=ORG_PACKAGE_NAME&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=ORG_PACKAGE_NAME)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=ORG_PACKAGE_NAME&metric=coverage)](https://sonarcloud.io/summary/new_code?id=ORG_PACKAGE_NAME)
[![Tests](https://img.shields.io/badge/tests-N%20passed-brightgreen)](https://github.com/ORG/PACKAGE_NAME/actions)
[![Maintainability Rating](https://img.shields.io/badge/maintainability-A-brightgreen)](https://sonarcloud.io/summary/new_code?id=ORG_PACKAGE_NAME)
```

### SonarCloud Badge
```markdown
[![SonarQube Cloud](https://sonarcloud.io/images/project_badges/sonarcloud-dark.svg)](https://sonarcloud.io/summary/new_code?id=ORG_PACKAGE_NAME)
```

**Total**: 12 badges showing production quality

---

## 🎯 QUALITY METRICS (beast-mailbox-core Standard)

### Test Coverage
- **Minimum**: 90% coverage
- **beast-mailbox-core**: 90% coverage ✅
- **Tool**: pytest-cov with XML reporting
- **Enforcement**: SonarCloud quality gate

### Test Count
- **Minimum**: Comprehensive test suite
- **beast-mailbox-core**: 59 tests, ZERO defects ✅
- **Coverage**: Unit tests, integration tests, edge cases

### Documentation Density
- **Minimum**: 50%+ documentation
- **beast-mailbox-core**: 52% ✅
- **Includes**: Docstrings, README, guides, examples

### Maintainability Rating
- **Minimum**: A rating
- **beast-mailbox-core**: A rating ✅
- **Tool**: SonarCloud maintainability

### Code Quality
- **Formatter**: Black (100% compliance)
- **Linter**: Flake8 + Ruff (zero errors)
- **Type Checking**: MyPy (strict mode)
- **Security**: Bandit (no HIGH/MEDIUM issues)

### Defects
- **Target**: ZERO defects
- **beast-mailbox-core**: ZERO defects ✅
- **Enforcement**: SonarCloud + GitHub Actions

---

## 📦 PACKAGING STANDARDS

### pyproject.toml Structure

```toml
[project]
name = "PACKAGE_NAME"
version = "0.1.0"  # Semantic versioning
description = "Brief description"
readme = "README.md"
requires-python = ">=3.9"
license = {text = "MIT"}
keywords = ["beast-mode", "relevant", "keywords"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Libraries :: Python Modules",
]
dependencies = [
  "minimal-deps-only>=version",
]

[project.optional-dependencies]
dev = [
  "pytest>=7.0.0",
  "pytest-asyncio>=0.21.0",
  "pytest-cov>=4.0.0",
  "black>=23.0.0",
  "flake8>=6.0.0",
  "mypy>=1.0.0",
  "bandit>=1.7.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = [
  "--cov=src/PACKAGE_NAME",
  "--cov-report=xml",
  "--cov-report=term-missing",
  "--cov-fail-under=90",  # Enforce 90% minimum
  "--verbose",
]

[project.urls]
Homepage = "https://github.com/ORG/PACKAGE_NAME"
Repository = "https://github.com/ORG/PACKAGE_NAME"

[project.scripts]
# CLI entry points if applicable
package-cli = "package_name.cli:main"

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"
```

---

## 🏗️ PROJECT STRUCTURE (Standard Layout)

```
PACKAGE_NAME/
├── .github/
│   ├── workflows/
│   │   ├── sonarcloud.yml      # SonarCloud integration
│   │   ├── test.yml            # Test on multiple Python versions
│   │   └── publish.yml         # PyPI publishing
│   └── dependabot.yml          # Dependency updates
├── src/
│   └── package_name/
│       ├── __init__.py
│       ├── core.py             # Main logic
│       ├── cli.py              # CLI entry points (if applicable)
│       └── py.typed            # Type stub marker
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── test_core.py            # Core tests
│   ├── test_integration.py     # Integration tests
│   ├── test_edge_cases.py      # Edge case coverage
│   └── test_coverage_boost.py  # Coverage completeness
├── docs/
│   ├── USAGE_GUIDE.md          # How to use
│   ├── QUICK_REFERENCE.md      # API quick ref
│   └── LESSONS_LEARNED.md      # Development notes
├── CHANGELOG.md                # Semantic versioning changelog
├── LICENSE                     # MIT License
├── README.md                   # With 12 badges!
├── pyproject.toml              # Package metadata
├── sonar-project.properties    # SonarCloud config
├── coverage.xml                # Coverage report (gitignored)
└── uv.lock                     # UV lock file
```

---

## 🔬 CI/CD PIPELINE (GitHub Actions)

### Workflow 1: Test Matrix
```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11', '3.12']
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
      
      - name: Run Black
        run: black --check src/ tests/
      
      - name: Run Flake8
        run: flake8 src/ tests/
      
      - name: Run MyPy
        run: mypy src/
      
      - name: Run Bandit
        run: bandit -r src/
      
      - name: Run tests with coverage
        run: |
          pytest tests/ \
            --cov=src/PACKAGE_NAME \
            --cov-report=xml \
            --cov-report=term-missing \
            --cov-fail-under=90
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

### Workflow 2: SonarCloud Analysis
```yaml
name: SonarCloud Analysis

on:
  push:
    branches: [main]
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  sonarcloud:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
      
      - name: Run tests with coverage
        run: |
          pytest tests/ --cov=src/PACKAGE_NAME --cov-report=xml
      
      - name: SonarCloud Scan
        uses: SonarSource/sonarcloud-github-action@master
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
```

### Workflow 3: PyPI Publishing
```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.9'
      
      - name: Install build tools
        run: |
          python -m pip install --upgrade pip
          pip install build twine
      
      - name: Build package
        run: python -m build
      
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

---

## 📝 DOCUMENTATION STANDARDS

### README.md Structure
1. **Title + Badges** (12 badges showing quality)
2. **One-line description** (what it does)
3. **Features** (bullet list)
4. **Installation** (pip install)
5. **Quickstart** (minimal example)
6. **Usage Examples** (common patterns)
7. **Configuration** (environment variables, CLI args)
8. **Development** (contributing, testing)
9. **License** (MIT)

### Required Documentation Files
- `README.md` - Main documentation with badges
- `CHANGELOG.md` - Version history (semantic versioning)
- `LICENSE` - MIT License
- `docs/USAGE_GUIDE.md` - Comprehensive usage
- `docs/QUICK_REFERENCE.md` - API quick reference
- `docs/LESSONS_LEARNED.md` - Development notes (optional but valuable)

### Docstring Standards
- **Google style** docstrings
- **Type annotations** on all functions/methods
- **Parameter descriptions**
- **Return value descriptions**
- **Exception documentation**
- **Usage examples** in docstrings

---

## 🔒 SECURITY STANDARDS

### Bandit Security Scanning
- **Run on**: Every push/PR
- **Threshold**: ZERO HIGH/MEDIUM issues
- **Configuration**: Exclude tests, docs
- **Integration**: GitHub Actions

### Dependency Management
- **Dependabot**: Enabled (automatic dependency updates)
- **Security advisories**: GitHub security alerts enabled
- **Pin versions**: Use `>=` for flexibility, test on multiple versions

### Secrets Management
- **No hardcoded secrets**: Ever
- **Environment variables**: For all sensitive config
- **Example configs**: Use placeholders only
- **Documentation**: Security best practices

---

## 📊 SONARCLOUD INTEGRATION

### Required Configuration

**File**: `sonar-project.properties`
```properties
sonar.projectKey=ORG_PACKAGE_NAME
sonar.organization=ORG

# Exclusions
sonar.exclusions=**/node_modules/**,**/__pycache__/**,**/venv/**,**/.venv/**,**/dist/**,**/build/**,**/*.egg-info/**,**/docs/**

# Source directories
sonar.sources=src
sonar.tests=tests

# Python specific
sonar.python.version=3.9,3.10,3.11,3.12

# Coverage
sonar.python.coverage.reportPaths=coverage.xml
```

### Quality Gates
- **Coverage**: ≥90%
- **Duplications**: <3%
- **Maintainability**: A rating
- **Reliability**: A rating
- **Security**: A rating
- **Technical Debt**: ≤5% debt ratio

---

## ✅ PRE-RELEASE CHECKLIST

### Code Quality
- [ ] Black formatting (100% compliance)
- [ ] Flake8 linting (zero errors)
- [ ] MyPy type checking (strict mode, zero errors)
- [ ] Bandit security (no HIGH/MEDIUM issues)

### Testing
- [ ] 90%+ test coverage
- [ ] All tests passing
- [ ] Tests on Python 3.9, 3.10, 3.11, 3.12
- [ ] Integration tests with dependencies
- [ ] Edge case tests
- [ ] Performance tests (if applicable)

### Documentation
- [ ] README with 12 badges
- [ ] CHANGELOG updated (semantic versioning)
- [ ] API documentation (docstrings)
- [ ] Usage guide
- [ ] Quick reference
- [ ] Examples

### SonarCloud
- [ ] Quality gate passing
- [ ] Coverage ≥90%
- [ ] Maintainability A
- [ ] Zero code smells (or documented exceptions)
- [ ] Zero bugs
- [ ] Zero vulnerabilities

### Packaging
- [ ] pyproject.toml complete
- [ ] Semantic version bumped
- [ ] LICENSE file (MIT)
- [ ] src/ layout with py.typed
- [ ] Built wheel and sdist
- [ ] Uploaded to test.pypi.org
- [ ] Tested install from test.pypi.org

### GitHub
- [ ] GitHub Actions workflows (test, sonarcloud, publish)
- [ ] Dependabot enabled
- [ ] Security advisories enabled
- [ ] Branch protection (main requires PR + tests passing)

---

## 🎯 APPLY TO ALL 8 PACKAGES

### Package List (All Must Meet Standards)
1. **beast-agent** (Tier 1)
2. **beast-redaction-client** (Tier 1)
3. **beast-observability** (Tier 1 - UPDATE to standard)
4. **beast-adapter-aws** (Tier 2)
5. **beast-adapter-gcp** (Tier 2)
6. **beast-agentic-framework** (Tier 2.5)
7. **beast-nim-integration** (Tier 3)
8. **beast-adk-integration** (Tier 3)

### Quality Enforcement
- **No exceptions**: Every package meets every standard
- **No shortcuts**: Even under tight timeline
- **No "we'll fix it later"**: Fix it now or don't ship

### Timeline Impact
- **Add 20% time**: For quality gates and documentation
- **Worth it**: Production-ready packages > quick hacks
- **Philosophy**: "Win whether we win or lose"

---

## 🚀 IMPLEMENTATION STRATEGY

### Template Repository
Create `beast-package-template` with:
- All GitHub Actions workflows
- sonar-project.properties template
- pyproject.toml template
- Standard directory structure
- README.md template with badges
- CHANGELOG.md template
- LICENSE (MIT)

### Package Creation Process
1. **Copy template** → new package directory
2. **Customize** pyproject.toml, sonar config
3. **Implement** core functionality
4. **Test** to 90%+ coverage
5. **Document** README, usage guide, API docs
6. **Quality check** Black, Flake8, MyPy, Bandit
7. **SonarCloud** setup and scan
8. **Badges** update in README
9. **Publish** to test.pypi.org
10. **Validate** install and usage
11. **Publish** to pypi.org

### Quality Automation
- **Pre-commit hooks**: Black, Flake8, MyPy
- **GitHub Actions**: Run on every push/PR
- **SonarCloud**: Automatic scan on PR
- **Coverage reports**: Uploaded to SonarCloud
- **Badge updates**: Automatic from SonarCloud/PyPI

---

## 📋 DELIVERABLE STANDARDS

### Each Package Includes
- ✅ 12 badges in README
- ✅ 90%+ test coverage
- ✅ Zero defects (SonarCloud)
- ✅ A maintainability rating
- ✅ 50%+ documentation density
- ✅ Published to PyPI
- ✅ GitHub Actions CI/CD
- ✅ SonarCloud integration
- ✅ Multiple Python versions tested
- ✅ Semantic versioning
- ✅ Comprehensive CHANGELOG
- ✅ MIT License

### Verification
**Every package MUST show**:
- "Enterprise-grade with 90% coverage, 52%+ documentation density, and ZERO defects!"
- Similar badge collection to beast-mailbox-core
- Production-ready quality metrics

---

## 🎯 WHY THIS MATTERS

### For Hackathon Judges
- **Technological Implementation (40%)**: Code quality, documentation → MAX SCORE
- **Demonstrates professionalism**: Not just "it works" but "enterprise-ready"
- **Differentiation**: While others hack, we ship production

### For Real Stakeholder (Us)
- **Portfolio quality**: Each package demonstrates expertise
- **Reusability**: Production packages we can actually use
- **Credibility**: "90% coverage, ZERO defects" speaks volumes
- **Open source value**: Community can trust and adopt

### For Multi-LLM Collaboration Proof
- **Proves the framework**: Built using the coordination patterns
- **Shows repeatability**: Not one package, but EIGHT to same standard
- **Validates approach**: Multi-LLM can deliver enterprise quality

---

## 🚨 NON-NEGOTIABLE

**Every package ships with ALL quality standards met, or it doesn't ship.**

**No "good enough for hackathon" - only "production-ready".**

**The badges don't lie - earn them or don't claim them.**

---

**NEXT**: Apply this template to every spec we create, starting with beast-agent.

