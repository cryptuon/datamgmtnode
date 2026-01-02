# Contributing

Guide for contributing to DataMgmt Node.

## Getting Started

### Prerequisites

- Python 3.10+
- Poetry
- Git
- LevelDB (for running tests)

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/example/datamgmtnode.git
cd datamgmtnode

# Install dependencies
poetry install

# Install pre-commit hooks (optional)
poetry run pre-commit install
```

### Verify Setup

```bash
# Run tests
poetry run pytest tests/ -v

# Check code style
poetry run flake8 datamgmtnode/

# Type checking (if configured)
poetry run mypy datamgmtnode/
```

## Development Workflow

### 1. Create a Branch

```bash
# Update main branch
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name
```

Branch naming conventions:

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions/changes

### 2. Make Changes

Follow these guidelines:

- Write clear, concise code
- Add tests for new functionality
- Update documentation as needed
- Keep commits atomic and well-described

### 3. Test Your Changes

```bash
# Run all tests
poetry run pytest tests/ -v

# Run specific test file
poetry run pytest tests/test_api_validation.py -v

# Run with coverage
poetry run pytest tests/ --cov=datamgmtnode --cov-report=html
```

### 4. Commit Changes

Write clear commit messages:

```bash
# Good commit message
git commit -m "Add rate limiting middleware to APIs

- Implement token bucket algorithm
- Add per-IP rate limiting
- Exempt health endpoints from limits
- Add unit tests for rate limiter"

# Bad commit message
git commit -m "fix stuff"
```

### 5. Push and Create PR

```bash
# Push branch
git push origin feature/your-feature-name

# Create pull request via GitHub
```

## Code Style

### Python Style Guide

Follow PEP 8 with these additions:

- Maximum line length: 100 characters
- Use double quotes for strings
- Use type hints where practical

```python
# Good
def validate_eth_address(address: str, field_name: str = "address") -> str:
    """Validate an Ethereum address.

    Args:
        address: The address to validate
        field_name: Name of the field for error messages

    Returns:
        The validated address

    Raises:
        ValidationError: If address is invalid
    """
    if not address:
        raise ValidationError(f"{field_name} is required", field_name)
    return address.strip()
```

### Import Order

```python
# Standard library
import os
import json
from typing import Dict, Optional

# Third-party
import aiohttp
from cryptography.fernet import Fernet

# Local
from api.validation import ValidationError
from services.data_manager import DataManager
```

### Logging

Use the logging module, not print:

```python
import logging

logger = logging.getLogger(__name__)

# Good
logger.info("Node started successfully")
logger.error(f"Failed to connect: {e}")

# Bad
print("Node started successfully")
```

## Testing Guidelines

### Test Structure

```python
import pytest

class TestFeatureName:
    """Tests for FeatureName."""

    @pytest.fixture
    def setup_data(self):
        """Fixture for test data."""
        return {"key": "value"}

    def test_specific_behavior(self, setup_data):
        """Test that specific behavior works."""
        result = function_under_test(setup_data)
        assert result == expected_value

    def test_error_handling(self):
        """Test error cases."""
        with pytest.raises(ValidationError):
            function_under_test(invalid_input)
```

### Test Naming

- Use descriptive names
- Follow pattern: `test_<what>_<condition>_<expected>`

```python
def test_validate_eth_address_with_valid_address_returns_address(): ...
def test_validate_eth_address_with_empty_string_raises_error(): ...
```

### Mocking

```python
from unittest.mock import MagicMock, patch

def test_blockchain_connection():
    mock_w3 = MagicMock()
    mock_w3.is_connected.return_value = True

    with patch('web3.Web3', return_value=mock_w3):
        interface = EVMBlockchainInterface("http://localhost:8545", "0x...")
        assert interface.connect() == True
```

## Documentation

### Docstrings

Use Google-style docstrings:

```python
def share_data(self, data: str, recipient: str,
               payment_token: str = None) -> str:
    """Share encrypted data with a recipient.

    Args:
        data: The data to share (max 1MB)
        recipient: Recipient's Ethereum address
        payment_token: Optional payment token address

    Returns:
        Transaction hash of the compliance record

    Raises:
        ValidationError: If inputs are invalid
        ValueError: If authorization fails

    Example:
        >>> tx_hash = node.share_data("secret", "0x742d...")
        >>> print(f"Shared with tx: {tx_hash}")
    """
```

### README Updates

Update README.md for:

- New features
- Changed requirements
- Modified configuration

### MkDocs Documentation

Documentation lives in `documentation/docs/`:

```bash
# Serve documentation locally
cd documentation
mkdocs serve

# Build documentation
mkdocs build
```

## Pull Request Guidelines

### PR Checklist

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] PR description explains changes

### PR Description Template

```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How were these changes tested?

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

### Review Process

1. Create PR with description
2. Automated tests run
3. Code review by maintainer
4. Address feedback
5. Merge when approved

## Architecture Decisions

### When to Document

Create an Architecture Decision Record (ADR) for:

- New major components
- Technology choices
- Breaking changes
- Security decisions

### ADR Template

```markdown
# ADR-001: Use Kademlia for P2P

## Status
Accepted

## Context
Need a P2P protocol for data distribution

## Decision
Use Kademlia DHT via the `kademlia` Python library

## Consequences
- Pro: Well-tested, scalable
- Pro: Good Python support
- Con: Learning curve for team
```

## Release Process

### Version Numbering

Follow Semantic Versioning:

- `MAJOR.MINOR.PATCH`
- `1.0.0` → `1.0.1` (bug fix)
- `1.0.0` → `1.1.0` (new feature)
- `1.0.0` → `2.0.0` (breaking change)

### Release Checklist

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release PR
4. Merge to main
5. Tag release
6. Publish to PyPI (if applicable)

## Getting Help

- **GitHub Issues** - Bug reports, feature requests
- **Discussions** - Questions, ideas
- **Security Issues** - Email security@example.com

## Next Steps

- [Architecture](architecture.md) - Understand the codebase
- [Testing Guide](testing.md) - Testing in detail
