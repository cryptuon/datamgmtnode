# =============================================================================
# DataMgmt Node - Unified Deployment
# Combines: Static Website (nginx) + Python Node (API + WebSocket)
# =============================================================================

# Stage 1: Build the Astro website
FROM node:22-alpine AS website-builder

WORKDIR /website
COPY website/package*.json ./
RUN npm ci

COPY website/ ./
RUN npm run build


# Stage 2: Python runtime with website
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    libleveldb-dev \
    build-essential \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies via pip (simpler than poetry in Docker)
WORKDIR /app

# Install Python packages
RUN pip install --no-cache-dir \
    asyncio==3.4.3 \
    cryptography==43.0.0 \
    web3==6.20.1 \
    aiohttp==3.9.0 \
    plyvel==1.5.1 \
    python-dotenv==1.0.0 \
    kademlia==2.2.3

# Copy DataMgmt Node source
COPY datamgmtnode ./datamgmtnode
COPY contracts ./contracts
COPY plugins ./plugins

# Create data directories
RUN mkdir -p /app/data /var/log/supervisor /var/log/nginx

# Copy website static files
COPY --from=website-builder /website/dist /usr/share/nginx/html

# Copy deployment configuration
COPY deploy/nginx.conf /etc/nginx/nginx.conf
COPY deploy/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY deploy/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port 80 (nginx handles all routing)
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
