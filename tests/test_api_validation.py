import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'datamgmtnode'))

from api.validation import (
    ValidationError,
    validate_eth_address,
    validate_amount,
    validate_data,
    validate_string,
    validate_hash,
    validate_transfer_request,
    validate_share_data_request,
    validate_filters,
    ValidatedTransferRequest,
    ValidatedShareDataRequest
)


class TestValidateEthAddress:
    """Tests for Ethereum address validation."""

    def test_valid_address(self):
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f1dE01"
        result = validate_eth_address(address)
        assert result == address

    def test_valid_address_lowercase(self):
        address = "0x742d35cc6634c0532925a3b844bc9e7595f1de01"
        result = validate_eth_address(address)
        assert result == address

    def test_valid_address_with_whitespace(self):
        address = "  0x742d35Cc6634C0532925a3b844Bc9e7595f1dE01  "
        result = validate_eth_address(address)
        assert result == address.strip()

    def test_invalid_address_no_prefix(self):
        with pytest.raises(ValidationError) as exc:
            validate_eth_address("742d35Cc6634C0532925a3b844Bc9e7595f1dE01")
        assert "valid Ethereum address" in exc.value.message

    def test_invalid_address_short(self):
        with pytest.raises(ValidationError):
            validate_eth_address("0x742d35Cc6634C0532925a3b844Bc")

    def test_invalid_address_long(self):
        with pytest.raises(ValidationError):
            validate_eth_address("0x742d35Cc6634C0532925a3b844Bc9e7595f1dE01EXTRA")

    def test_invalid_address_non_hex(self):
        with pytest.raises(ValidationError):
            validate_eth_address("0xGGGd35Cc6634C0532925a3b844Bc9e7595f1dE01")

    def test_missing_address(self):
        with pytest.raises(ValidationError) as exc:
            validate_eth_address(None)
        assert "is required" in exc.value.message

    def test_empty_address(self):
        with pytest.raises(ValidationError):
            validate_eth_address("")

    def test_non_string_address(self):
        with pytest.raises(ValidationError) as exc:
            validate_eth_address(12345)
        assert "must be a string" in exc.value.message

    def test_custom_field_name(self):
        with pytest.raises(ValidationError) as exc:
            validate_eth_address(None, "recipient")
        assert "recipient" in exc.value.message
        assert exc.value.field == "recipient"


class TestValidateAmount:
    """Tests for amount validation."""

    def test_valid_integer(self):
        assert validate_amount(100) == 100

    def test_valid_string_integer(self):
        assert validate_amount("100") == 100

    def test_valid_large_amount(self):
        assert validate_amount(10 ** 20) == 10 ** 20

    def test_invalid_zero(self):
        with pytest.raises(ValidationError) as exc:
            validate_amount(0)
        assert "greater than 0" in exc.value.message

    def test_invalid_negative(self):
        with pytest.raises(ValidationError):
            validate_amount(-100)

    def test_invalid_too_large(self):
        with pytest.raises(ValidationError) as exc:
            validate_amount(10 ** 31)
        assert "exceeds maximum" in exc.value.message

    def test_missing_amount(self):
        with pytest.raises(ValidationError) as exc:
            validate_amount(None)
        assert "is required" in exc.value.message

    def test_invalid_string(self):
        with pytest.raises(ValidationError):
            validate_amount("not_a_number")


class TestValidateData:
    """Tests for data payload validation."""

    def test_valid_data(self):
        data = "some test data"
        assert validate_data(data) == data

    def test_missing_data(self):
        with pytest.raises(ValidationError):
            validate_data(None)

    def test_empty_data(self):
        with pytest.raises(ValidationError) as exc:
            validate_data("")
        assert "cannot be empty" in exc.value.message

    def test_non_string_data(self):
        with pytest.raises(ValidationError):
            validate_data(12345)

    def test_data_too_large(self):
        large_data = "x" * (1024 * 1024 + 1)  # Over 1MB
        with pytest.raises(ValidationError) as exc:
            validate_data(large_data)
        assert "exceeds maximum size" in exc.value.message


class TestValidateHash:
    """Tests for SHA256 hash validation."""

    def test_valid_hash(self):
        hash_val = "a" * 64
        result = validate_hash(hash_val)
        assert result == hash_val

    def test_valid_hash_uppercase(self):
        hash_val = "A" * 64
        result = validate_hash(hash_val)
        assert result == hash_val.lower()

    def test_valid_hash_mixed_case(self):
        hash_val = "aAbBcCdDeEfF" + "0123456789" * 5 + "ab"
        result = validate_hash(hash_val)
        assert result == hash_val.lower()

    def test_invalid_hash_short(self):
        with pytest.raises(ValidationError) as exc:
            validate_hash("abc123")
        assert "64-character" in exc.value.message

    def test_invalid_hash_long(self):
        with pytest.raises(ValidationError):
            validate_hash("a" * 65)

    def test_invalid_hash_non_hex(self):
        with pytest.raises(ValidationError) as exc:
            validate_hash("g" * 64)
        assert "hexadecimal" in exc.value.message

    def test_missing_hash(self):
        with pytest.raises(ValidationError):
            validate_hash(None)


class TestValidateTransferRequest:
    """Tests for transfer request validation."""

    def test_valid_request(self):
        data = {
            'from': '0x742d35Cc6634C0532925a3b844Bc9e7595f1dE01',
            'to': '0x742d35Cc6634C0532925a3b844Bc9e7595f1dE02',
            'amount': 1000,
            'token': '0x742d35Cc6634C0532925a3b844Bc9e7595f1dE03'
        }
        result = validate_transfer_request(data)
        assert isinstance(result, ValidatedTransferRequest)
        assert result.amount == 1000

    def test_missing_from(self):
        data = {
            'to': '0x742d35Cc6634C0532925a3b844Bc9e7595f1dE02',
            'amount': 1000,
            'token': '0x742d35Cc6634C0532925a3b844Bc9e7595f1dE03'
        }
        with pytest.raises(ValidationError) as exc:
            validate_transfer_request(data)
        assert exc.value.field == 'from'

    def test_missing_to(self):
        data = {
            'from': '0x742d35Cc6634C0532925a3b844Bc9e7595f1dE01',
            'amount': 1000,
            'token': '0x742d35Cc6634C0532925a3b844Bc9e7595f1dE03'
        }
        with pytest.raises(ValidationError) as exc:
            validate_transfer_request(data)
        assert exc.value.field == 'to'

    def test_not_a_dict(self):
        with pytest.raises(ValidationError) as exc:
            validate_transfer_request("not a dict")
        assert "JSON object" in exc.value.message


class TestValidateShareDataRequest:
    """Tests for share data request validation."""

    def test_valid_request_without_payment(self):
        data = {
            'data': 'test data payload',
            'recipient': '0x742d35Cc6634C0532925a3b844Bc9e7595f1dE01'
        }
        result = validate_share_data_request(data)
        assert isinstance(result, ValidatedShareDataRequest)
        assert result.data == 'test data payload'
        assert result.payment_token is None
        assert result.payment_amount is None

    def test_valid_request_with_payment(self):
        data = {
            'data': 'test data payload',
            'recipient': '0x742d35Cc6634C0532925a3b844Bc9e7595f1dE01',
            'payment_token': '0x742d35Cc6634C0532925a3b844Bc9e7595f1dE02',
            'payment_amount': 1000
        }
        result = validate_share_data_request(data)
        assert result.payment_token is not None
        assert result.payment_amount == 1000

    def test_payment_amount_without_token(self):
        data = {
            'data': 'test data payload',
            'recipient': '0x742d35Cc6634C0532925a3b844Bc9e7595f1dE01',
            'payment_amount': 1000
        }
        with pytest.raises(ValidationError) as exc:
            validate_share_data_request(data)
        assert "payment_token is required" in exc.value.message

    def test_missing_data(self):
        data = {
            'recipient': '0x742d35Cc6634C0532925a3b844Bc9e7595f1dE01'
        }
        with pytest.raises(ValidationError) as exc:
            validate_share_data_request(data)
        assert exc.value.field == 'data'


class TestValidateFilters:
    """Tests for filter validation."""

    def test_empty_filter(self):
        assert validate_filters(None) is None
        assert validate_filters("") is None

    def test_single_filter(self):
        result = validate_filters("data_share")
        assert result == ["data_share"]

    def test_multiple_filters(self):
        result = validate_filters("data_share,transfer,compliance")
        assert result == ["data_share", "transfer", "compliance"]

    def test_filters_with_whitespace(self):
        result = validate_filters("data_share , transfer , compliance")
        assert result == ["data_share", "transfer", "compliance"]

    def test_filter_too_long(self):
        with pytest.raises(ValidationError) as exc:
            validate_filters("a" * 101)
        assert "exceeds maximum length" in exc.value.message

    def test_filter_invalid_characters(self):
        with pytest.raises(ValidationError) as exc:
            validate_filters("data share!")  # space and ! are invalid
        assert "invalid characters" in exc.value.message

    def test_filter_valid_characters(self):
        result = validate_filters("data_share-v2")
        assert result == ["data_share-v2"]
