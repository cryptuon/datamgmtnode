import re
import logging
from typing import Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Ethereum address pattern
ETH_ADDRESS_PATTERN = re.compile(r'^0x[a-fA-F0-9]{40}$')

# Maximum sizes
MAX_DATA_SIZE = 1024 * 1024  # 1MB
MAX_STRING_LENGTH = 10000


class ValidationError(Exception):
    """Raised when request validation fails."""

    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(message)


@dataclass
class ValidatedTransferRequest:
    """Validated transfer request data."""
    from_address: str
    to_address: str
    amount: int
    token: str


@dataclass
class ValidatedShareDataRequest:
    """Validated share data request."""
    data: str
    recipient: str
    payment_token: Optional[str] = None
    payment_amount: Optional[int] = None


def validate_eth_address(address: Any, field_name: str = "address") -> str:
    """Validate an Ethereum address."""
    if not address:
        raise ValidationError(f"{field_name} is required", field_name)

    if not isinstance(address, str):
        raise ValidationError(f"{field_name} must be a string", field_name)

    address = address.strip()

    if not ETH_ADDRESS_PATTERN.match(address):
        raise ValidationError(f"{field_name} must be a valid Ethereum address (0x + 40 hex chars)", field_name)

    return address


def validate_amount(amount: Any, field_name: str = "amount") -> int:
    """Validate a token amount."""
    if amount is None:
        raise ValidationError(f"{field_name} is required", field_name)

    try:
        amount_int = int(amount)
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} must be a valid integer", field_name)

    if amount_int <= 0:
        raise ValidationError(f"{field_name} must be greater than 0", field_name)

    if amount_int > 10 ** 30:  # Reasonable upper bound
        raise ValidationError(f"{field_name} exceeds maximum allowed value", field_name)

    return amount_int


def validate_data(data: Any, field_name: str = "data") -> str:
    """Validate data payload."""
    if data is None:
        raise ValidationError(f"{field_name} is required", field_name)

    if not isinstance(data, str):
        raise ValidationError(f"{field_name} must be a string", field_name)

    if len(data) == 0:
        raise ValidationError(f"{field_name} cannot be empty", field_name)

    if len(data) > MAX_DATA_SIZE:
        raise ValidationError(f"{field_name} exceeds maximum size of {MAX_DATA_SIZE} bytes", field_name)

    return data


def validate_string(value: Any, field_name: str, required: bool = True, max_length: int = MAX_STRING_LENGTH) -> Optional[str]:
    """Validate a string field."""
    if value is None:
        if required:
            raise ValidationError(f"{field_name} is required", field_name)
        return None

    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string", field_name)

    value = value.strip()

    if required and len(value) == 0:
        raise ValidationError(f"{field_name} cannot be empty", field_name)

    if len(value) > max_length:
        raise ValidationError(f"{field_name} exceeds maximum length of {max_length}", field_name)

    return value


def validate_hash(hash_value: Any, field_name: str = "hash") -> str:
    """Validate a SHA256 hash."""
    if not hash_value:
        raise ValidationError(f"{field_name} is required", field_name)

    if not isinstance(hash_value, str):
        raise ValidationError(f"{field_name} must be a string", field_name)

    hash_value = hash_value.strip().lower()

    if len(hash_value) != 64:
        raise ValidationError(f"{field_name} must be a 64-character hex string", field_name)

    if not all(c in '0123456789abcdef' for c in hash_value):
        raise ValidationError(f"{field_name} must contain only hexadecimal characters", field_name)

    return hash_value


def validate_transfer_request(data: dict) -> ValidatedTransferRequest:
    """Validate a token transfer request."""
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object")

    return ValidatedTransferRequest(
        from_address=validate_eth_address(data.get('from'), 'from'),
        to_address=validate_eth_address(data.get('to'), 'to'),
        amount=validate_amount(data.get('amount')),
        token=validate_eth_address(data.get('token'), 'token')
    )


def validate_share_data_request(data: dict) -> ValidatedShareDataRequest:
    """Validate a data sharing request."""
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object")

    # Required fields
    validated_data = validate_data(data.get('data'))
    recipient = validate_eth_address(data.get('recipient'), 'recipient')

    # Optional payment fields
    payment_token = None
    payment_amount = None

    if data.get('payment_token') is not None:
        payment_token = validate_eth_address(data.get('payment_token'), 'payment_token')
        payment_amount = validate_amount(data.get('payment_amount'), 'payment_amount')
    elif data.get('payment_amount') is not None:
        raise ValidationError("payment_token is required when payment_amount is provided", 'payment_token')

    return ValidatedShareDataRequest(
        data=validated_data,
        recipient=recipient,
        payment_token=payment_token,
        payment_amount=payment_amount
    )


def validate_filters(filters_str: Optional[str]) -> Optional[list]:
    """Validate and parse filter string."""
    if not filters_str:
        return None

    filters = [f.strip() for f in filters_str.split(',') if f.strip()]

    # Validate each filter
    for f in filters:
        if len(f) > 100:
            raise ValidationError(f"Filter '{f[:20]}...' exceeds maximum length", 'filters')
        if not re.match(r'^[a-zA-Z0-9_-]+$', f):
            raise ValidationError(f"Filter '{f}' contains invalid characters", 'filters')

    return filters if filters else None
