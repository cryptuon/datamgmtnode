# Deployment

This guide covers deploying DataMgmt Node in production environments.

## Deployment Options

### Docker (Recommended)

Create a `Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libleveldb-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy project files
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --only main

COPY datamgmtnode/ ./datamgmtnode/

# Create data directory
RUN mkdir -p /data

ENV DATA_DIR=/data
ENV DB_PATH=/data/nodedb
ENV SQLITE_DB_PATH=/data/sqlite.db

EXPOSE 8080 8081 8000

CMD ["python", "datamgmtnode/main.py"]
```

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  datamgmt-node:
    build: .
    ports:
      - "8080:8080"  # Internal API
      - "8081:8081"  # External API
      - "8000:8000"  # P2P
    volumes:
      - node-data:/data
    environment:
      - KEY_MASTER_PASSWORD=${KEY_MASTER_PASSWORD}
      - BLOCKCHAIN_URL=${BLOCKCHAIN_URL}
      - PRIVATE_KEY=${PRIVATE_KEY}
      - NODE_ID=${NODE_ID}
      - INITIAL_PEERS=${INITIAL_PEERS}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

volumes:
  node-data:
```

Deploy:

```bash
# Set environment variables
export KEY_MASTER_PASSWORD="your-secure-password"
export BLOCKCHAIN_URL="https://mainnet.infura.io/v3/YOUR-PROJECT-ID"
export PRIVATE_KEY="0x..."
export NODE_ID="prod-node-1"
export INITIAL_PEERS="http://bootstrap1.example.com:8000"

# Deploy
docker-compose up -d
```

### Kubernetes

Create Kubernetes manifests:

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: datamgmt

---
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: datamgmt-secrets
  namespace: datamgmt
type: Opaque
stringData:
  KEY_MASTER_PASSWORD: "your-secure-password"
  PRIVATE_KEY: "0x..."

---
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: datamgmt-config
  namespace: datamgmt
data:
  BLOCKCHAIN_URL: "https://mainnet.infura.io/v3/YOUR-PROJECT-ID"
  NODE_ID: "k8s-node-1"
  P2P_PORT: "8000"
  INITIAL_PEERS: "http://bootstrap1.example.com:8000"

---
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: datamgmt-node
  namespace: datamgmt
spec:
  replicas: 1
  selector:
    matchLabels:
      app: datamgmt-node
  template:
    metadata:
      labels:
        app: datamgmt-node
    spec:
      containers:
      - name: datamgmt-node
        image: datamgmt-node:latest
        ports:
        - containerPort: 8080
          name: internal-api
        - containerPort: 8081
          name: external-api
        - containerPort: 8000
          name: p2p
        envFrom:
        - configMapRef:
            name: datamgmt-config
        - secretRef:
            name: datamgmt-secrets
        volumeMounts:
        - name: data
          mountPath: /data
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: datamgmt-pvc

---
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: datamgmt-node
  namespace: datamgmt
spec:
  selector:
    app: datamgmt-node
  ports:
  - name: internal-api
    port: 8080
    targetPort: 8080
  - name: external-api
    port: 8081
    targetPort: 8081
  - name: p2p
    port: 8000
    targetPort: 8000
```

Deploy:

```bash
kubectl apply -f namespace.yaml
kubectl apply -f secret.yaml
kubectl apply -f configmap.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

### Systemd (Linux)

Create a systemd service:

```ini
# /etc/systemd/system/datamgmt-node.service
[Unit]
Description=DataMgmt Node
After=network.target

[Service]
Type=simple
User=datamgmt
Group=datamgmt
WorkingDirectory=/opt/datamgmt
Environment="PATH=/opt/datamgmt/.venv/bin"
EnvironmentFile=/opt/datamgmt/.env
ExecStart=/opt/datamgmt/.venv/bin/python datamgmtnode/main.py
Restart=always
RestartSec=10

# Security hardening
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/opt/datamgmt/data
PrivateTmp=yes

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable datamgmt-node
sudo systemctl start datamgmt-node
```

## Production Checklist

### Security

- [ ] Strong `KEY_MASTER_PASSWORD` set
- [ ] Private key secured (not in version control)
- [ ] Firewall configured (only expose necessary ports)
- [ ] HTTPS reverse proxy configured
- [ ] API keys configured for external access
- [ ] Rate limiting enabled

### Networking

- [ ] P2P port accessible from internet (if public node)
- [ ] Internal API bound to localhost only
- [ ] External API behind reverse proxy
- [ ] SSL/TLS certificates configured

### Storage

- [ ] Persistent storage configured
- [ ] Backup strategy in place
- [ ] Disk space monitoring enabled

### Monitoring

- [ ] Health checks configured
- [ ] Logging to centralized system
- [ ] Metrics collection enabled
- [ ] Alerts configured

### High Availability

- [ ] Multiple nodes deployed
- [ ] Load balancer configured
- [ ] Database replication (if applicable)

## Reverse Proxy Configuration

### Nginx

```nginx
upstream datamgmt_external {
    server 127.0.0.1:8081;
}

server {
    listen 443 ssl http2;
    server_name api.datamgmt.example.com;

    ssl_certificate /etc/ssl/certs/datamgmt.crt;
    ssl_certificate_key /etc/ssl/private/datamgmt.key;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    location / {
        limit_req zone=api burst=20 nodelay;

        proxy_pass http://datamgmt_external;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        # No rate limiting for health checks
        proxy_pass http://datamgmt_external;
    }
}
```

### Traefik

```yaml
# traefik.yml
http:
  routers:
    datamgmt-api:
      rule: "Host(`api.datamgmt.example.com`)"
      service: datamgmt-api
      tls:
        certResolver: letsencrypt
      middlewares:
        - rate-limit

  services:
    datamgmt-api:
      loadBalancer:
        servers:
          - url: "http://127.0.0.1:8081"

  middlewares:
    rate-limit:
      rateLimit:
        average: 10
        burst: 20
```

## Scaling

### Horizontal Scaling

Deploy multiple nodes with shared bootstrap configuration:

```yaml
# docker-compose-cluster.yml
version: '3.8'

services:
  node1:
    build: .
    environment:
      - NODE_ID=node-1
      - P2P_PORT=8000
      - INITIAL_PEERS=http://node2:8000,http://node3:8000

  node2:
    build: .
    environment:
      - NODE_ID=node-2
      - P2P_PORT=8000
      - INITIAL_PEERS=http://node1:8000,http://node3:8000

  node3:
    build: .
    environment:
      - NODE_ID=node-3
      - P2P_PORT=8000
      - INITIAL_PEERS=http://node1:8000,http://node2:8000
```

### Load Balancing

Use a load balancer for API traffic:

```nginx
upstream datamgmt_cluster {
    least_conn;
    server node1:8081;
    server node2:8081;
    server node3:8081;
}
```

## Next Steps

- [Monitoring Guide](monitoring.md) - Monitor your deployment
- [Security Guide](security.md) - Secure your deployment
