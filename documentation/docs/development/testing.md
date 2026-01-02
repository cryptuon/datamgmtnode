# Testing

Comprehensive guide to testing DataMgmt Node.

## Test Overview

DataMgmt Node uses pytest for testing with 173+ tests covering:

- Unit tests for all services
- API validation tests
- Rate limiter tests
- Configuration tests
- Key management tests

## Running Tests

### Run All Tests

```bash
# Basic run
poetry run pytest tests/ -v

# With coverage
poetry run pytest tests/ --cov=datamgmtnode --cov-report=html

# Parallel execution
poetry run pytest tests/ -n auto
```

### Run Specific Tests

```bash
# Single file
poetry run pytest tests/test_api_validation.py -v

# Single class
poetry run pytest tests/test_api_validation.py::TestValidateEthAddress -v

# Single test
poetry run pytest tests/test_api_validation.py::TestValidateEthAddress::test_valid_address -v

# By keyword
poetry run pytest tests/ -k "validation" -v
```

### Test Output Options

```bash
# Verbose output
poetry run pytest tests/ -v

# Very verbose (show test values)
poetry run pytest tests/ -vv

# Short traceback
poetry run pytest tests/ --tb=short

# No traceback
poetry run pytest tests/ --tb=no

# Show local variables
poetry run pytest tests/ --tb=long
```

## Test Structure

### Directory Layout

```
tests/
├── conftest.py              # Shared fixtures
├── test_authorisation.py    # Authorization tests
├── test_compliance_manager.py
├── test_data_manager.py
├── test_p2p_network.py
├── test_payment_processor.py
├── test_token_manager.py
├── test_api_validation.py   # API validation tests
├── test_rate_limiter.py     # Rate limiting tests
├── test_config.py           # Configuration tests
└── test_key_manager.py      # Key management tests
```

### Test File Structure

```python
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'datamgmtnode'))

from module_to_test import ClassToTest


class TestClassName:
    """Tests for ClassName."""

    @pytest.fixture
    def instance(self):
        """Create test instance."""
        return ClassToTest()

    def test_method_normal_case(self, instance):
        """Test normal operation."""
        result = instance.method()
        assert result == expected

    def test_method_edge_case(self, instance):
        """Test edge case."""
        with pytest.raises(ExpectedException):
            instance.method(invalid_input)
```

## Fixtures

### Common Fixtures

```python
# conftest.py
import pytest
import tempfile

@pytest.fixture
def temp_db_path(tmp_path):
    """Provide temporary database path."""
    return str(tmp_path / "testdb")

@pytest.fixture
def mock_blockchain():
    """Provide mock blockchain interface."""
    mock = MagicMock()
    mock.is_connected.return_value = True
    return mock

@pytest.fixture
def valid_eth_address():
    """Provide valid Ethereum address."""
    return "0x742d35Cc6634C0532925a3b844Bc9e7595f1dE01"
```

### Async Fixtures

```python
import pytest
import asyncio

@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def async_client():
    """Create async HTTP client."""
    async with aiohttp.ClientSession() as session:
        yield session
```

## Testing Patterns

### Testing Validation

```python
class TestValidateEthAddress:
    def test_valid_address(self):
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f1dE01"
        result = validate_eth_address(address)
        assert result == address

    def test_invalid_address_raises_error(self):
        with pytest.raises(ValidationError) as exc:
            validate_eth_address("invalid")
        assert "valid Ethereum address" in exc.value.message
        assert exc.value.field == "address"

    @pytest.mark.parametrize("address", [
        "0x742d35Cc6634C0532925a3b844Bc9e7595f1dE01",
        "0x742d35cc6634c0532925a3b844bc9e7595f1de01",
        "  0x742d35Cc6634C0532925a3b844Bc9e7595f1dE01  ",
    ])
    def test_various_valid_addresses(self, address):
        result = validate_eth_address(address)
        assert result.startswith("0x")
```

### Testing Async Code

```python
import pytest

class TestP2PNetwork:
    @pytest.mark.asyncio
    async def test_start(self, network):
        await network.start()
        assert network.is_running == True

    @pytest.mark.asyncio
    async def test_send_data(self, network):
        await network.start()
        await network.send_data("hash123", "data")
        # Verify data was sent
```

### Testing with Mocks

```python
from unittest.mock import MagicMock, patch, AsyncMock

class TestPaymentProcessor:
    def test_process_payment_success(self):
        mock_blockchain = MagicMock()
        mock_blockchain.send_transaction.return_value = "0xabc123"

        processor = PaymentProcessor(mock_blockchain, mock_token_manager)
        success, tx_hash = processor.process_payment(
            from_addr, to_addr, 1000, token
        )

        assert success == True
        assert tx_hash == "0xabc123"
        mock_blockchain.send_transaction.assert_called_once()

    @patch('aiohttp.ClientSession')
    async def test_with_mocked_http(self, mock_session):
        mock_response = AsyncMock()
        mock_response.json.return_value = {"status": "ok"}
        mock_session.return_value.__aenter__.return_value.get.return_value = mock_response

        # Test code that makes HTTP requests
```

### Testing Time-Sensitive Code

```python
import time

class TestRateLimiter:
    def test_replenishes_over_time(self):
        limiter = RateLimiter(burst_size=2, requests_per_second=20.0)
        request = MockRequest(ip='10.0.0.1')

        # Exhaust tokens
        limiter.is_allowed(request)
        limiter.is_allowed(request)

        # Should be denied
        allowed, _ = limiter.is_allowed(request)
        assert allowed == False

        # Wait for replenishment
        time.sleep(0.12)  # 2+ tokens at 20/sec

        # Should be allowed
        allowed, _ = limiter.is_allowed(request)
        assert allowed == True
```

## Test Coverage

### Generate Coverage Report

```bash
# Terminal report
poetry run pytest tests/ --cov=datamgmtnode --cov-report=term-missing

# HTML report
poetry run pytest tests/ --cov=datamgmtnode --cov-report=html
open htmlcov/index.html

# XML report (for CI)
poetry run pytest tests/ --cov=datamgmtnode --cov-report=xml
```

### Coverage Configuration

```toml
# pyproject.toml
[tool.coverage.run]
source = ["datamgmtnode"]
omit = ["*/tests/*", "*/__init__.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
]
```

### Target Coverage

| Component | Target |
|-----------|--------|
| Services | 90%+ |
| API | 85%+ |
| Validation | 95%+ |
| Overall | 85%+ |

## Continuous Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install Poetry
        run: pip install poetry

      - name: Install dependencies
        run: poetry install

      - name: Run tests
        run: poetry run pytest tests/ -v --cov=datamgmtnode

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: poetry run pytest tests/ -x
        language: system
        pass_filenames: false
        always_run: true
```

## Debugging Tests

### Print Debugging

```python
def test_something(self, capsys):
    print("Debug info")
    result = function()
    print(f"Result: {result}")

    captured = capsys.readouterr()
    print(captured.out)  # See printed output
```

### Using pdb

```python
def test_with_debugger(self):
    import pdb; pdb.set_trace()
    result = function()
    assert result == expected
```

Run with:
```bash
poetry run pytest tests/test_file.py -s --pdb
```

### Logging in Tests

```python
import logging

def test_with_logging(caplog):
    with caplog.at_level(logging.DEBUG):
        function_that_logs()

    assert "expected message" in caplog.text
```

## Best Practices

### Test Isolation

- Each test should be independent
- Use fixtures for setup/teardown
- Clean up resources after tests

### Test Naming

```python
# Good - descriptive
def test_validate_eth_address_with_invalid_prefix_raises_validation_error(): ...

# Bad - unclear
def test_1(): ...
def test_address(): ...
```

### Test Organization

- Group related tests in classes
- Use markers for categorization
- Keep test files focused

```python
@pytest.mark.slow
def test_long_running_operation(): ...

@pytest.mark.integration
def test_full_workflow(): ...
```

Run specific markers:
```bash
poetry run pytest tests/ -m "not slow"
poetry run pytest tests/ -m integration
```

## Next Steps

- [Architecture](architecture.md) - Understand what to test
- [Contributing](contributing.md) - Submit your tests
