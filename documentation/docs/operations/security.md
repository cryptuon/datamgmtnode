# Security

Security best practices for operating DataMgmt Node.

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Layers                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Network Security                        │   │
│  │  • TLS/SSL encryption                               │   │
│  │  • Firewall rules                                   │   │
│  │  • Rate limiting                                    │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Authentication                          │   │
│  │  • API key validation                               │   │
│  │  • Node signature verification                      │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Data Security                           │   │
│  │  • Fernet encryption (AES-128-CBC)                  │   │
│  │  • PBKDF2 key derivation                            │   │
│  │  • Key rotation support                             │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Input Validation                        │   │
│  │  • Schema validation                                │   │
│  │  • Size limits                                      │   │
│  │  • Format verification                              │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Encryption

### Key Management

DataMgmt Node uses a hierarchical key management system:

1. **Master Password** - Protects all encryption keys at rest
2. **Data Keys** - Fernet keys for encrypting shared data
3. **Key Versions** - Support for key rotation

### Master Password

!!! danger "Critical Security"
    The `KEY_MASTER_PASSWORD` is the most critical security setting. If compromised, all encrypted data is at risk.

Best practices:

- Use a strong, unique password (32+ characters)
- Store securely (password manager, secrets vault)
- Never commit to version control
- Rotate periodically

```bash
# Generate a strong password
openssl rand -base64 32
```

### Key Rotation

Rotate encryption keys periodically:

```python
from services.key_manager import KeyManager

# Initialize key manager
key_manager = KeyManager("/data", master_password="your-password")
key_manager.initialize()

# Rotate to new key
new_version = key_manager.rotate_key()
print(f"Rotated to key version {new_version}")
```

!!! info "Backward Compatibility"
    Old data can still be decrypted after rotation using the previous key version.

### Encryption at Rest

Keys are encrypted at rest using PBKDF2:

```json
{
  "salt": "base64-encoded-salt",
  "current_version": 2,
  "keys": {
    "1": "encrypted-key-v1",
    "2": "encrypted-key-v2"
  }
}
```

## Authentication

### API Keys

Protected endpoints require API key authentication:

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8081/share_data
```

Best practices:

- Generate unique keys per client
- Set expiration dates
- Monitor usage patterns
- Revoke compromised keys immediately

### Node Authentication

Nodes authenticate using RSA signatures:

```python
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

# Sign data
signature = private_key.sign(
    data_hash.encode(),
    padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.MAX_LENGTH
    ),
    hashes.SHA256()
)
```

## Network Security

### Firewall Configuration

Recommended firewall rules:

```bash
# Allow internal API only from localhost
ufw allow from 127.0.0.1 to any port 8080

# Allow external API from anywhere (behind reverse proxy)
ufw allow from any to any port 8081

# Allow P2P from anywhere
ufw allow from any to any port 8000

# Enable firewall
ufw enable
```

### TLS/SSL

Always use TLS in production:

```nginx
server {
    listen 443 ssl http2;
    server_name api.datamgmt.example.com;

    ssl_certificate /etc/ssl/certs/datamgmt.crt;
    ssl_certificate_key /etc/ssl/private/datamgmt.key;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;
}
```

### Rate Limiting

Built-in rate limiting protects against abuse:

| API | Rate | Burst |
|-----|------|-------|
| Internal | 50 req/s | 100 |
| External | 10 req/s | 20 |

Additional Nginx rate limiting:

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location / {
    limit_req zone=api burst=20 nodelay;
    proxy_pass http://backend;
}
```

## Input Validation

### Validated Fields

All inputs are validated before processing:

| Field | Validation |
|-------|------------|
| Ethereum Address | Regex: `^0x[a-fA-F0-9]{40}$` |
| Amount | Integer > 0, < 10^30 |
| Data | String, max 1MB |
| Hash | 64 hex characters |

### Protection Against

- **SQL Injection** - Parameterized queries
- **XSS** - JSON responses only
- **Command Injection** - No shell commands
- **Path Traversal** - Validated file paths

## Secrets Management

### Environment Variables

Store secrets in environment variables:

```bash
# .env (never commit!)
KEY_MASTER_PASSWORD=your-secure-password
PRIVATE_KEY=0x1234...
```

### Secrets Vault

For production, use a secrets manager:

=== "AWS Secrets Manager"

    ```python
    import boto3

    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId='datamgmt/prod')
    secrets = json.loads(response['SecretString'])
    ```

=== "HashiCorp Vault"

    ```python
    import hvac

    client = hvac.Client(url='https://vault.example.com')
    secret = client.secrets.kv.read_secret_version(path='datamgmt/prod')
    ```

=== "Kubernetes Secrets"

    ```yaml
    apiVersion: v1
    kind: Secret
    metadata:
      name: datamgmt-secrets
    type: Opaque
    data:
      KEY_MASTER_PASSWORD: base64-encoded-value
      PRIVATE_KEY: base64-encoded-value
    ```

## Audit Logging

### What to Log

- Authentication attempts (success/failure)
- Data share operations
- Configuration changes
- Error events
- Rate limit violations

### Log Format

```
2024-01-15 10:30:00 - security - WARNING - Rate limit exceeded for 192.168.1.100
2024-01-15 10:30:01 - security - INFO - Successful authentication: api_key=abc***
2024-01-15 10:30:02 - security - ERROR - Invalid signature for user_id=node1
```

### Log Retention

- Keep security logs for at least 90 days
- Store in tamper-proof storage
- Enable log integrity verification

## Compliance

### Blockchain Audit Trail

All operations are recorded on-chain:

```json
{
  "event_type": "data_share",
  "data_hash": "abc123...",
  "recipient": "0x742d...",
  "timestamp": 1705312200,
  "tx_hash": "0x1234..."
}
```

### Compliance Verification

```bash
curl http://localhost:8081/verify_data/abc123...
```

## Security Checklist

### Initial Setup

- [ ] Strong master password configured
- [ ] Private key secured
- [ ] Firewall enabled
- [ ] TLS certificates installed
- [ ] API keys generated

### Ongoing

- [ ] Regular key rotation
- [ ] Security updates applied
- [ ] Logs monitored
- [ ] Access reviewed
- [ ] Backups verified

### Incident Response

- [ ] Incident response plan documented
- [ ] Contact list maintained
- [ ] Recovery procedures tested

## Security Updates

Stay informed about security updates:

1. Watch the GitHub repository
2. Subscribe to security announcements
3. Apply patches promptly
4. Test updates in staging first

## Reporting Vulnerabilities

Report security issues responsibly:

1. Do not disclose publicly
2. Email security@example.com
3. Include detailed reproduction steps
4. Allow time for fix before disclosure

## Next Steps

- [Deployment Guide](deployment.md) - Secure deployment
- [Monitoring Guide](monitoring.md) - Security monitoring
