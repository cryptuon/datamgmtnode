# =============================================================================
# DataMgmt Node Unified Deployment
# Combines: Static Website (nginx) + Python Node (API + WebSocket)
# =============================================================================

# Stage 1: Build the Astro website
FROM node:22-alpine AS website-builder

WORKDIR /website

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Stage 2: Build Python dependencies
FROM python:3.12-slim AS python-builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libleveldb-dev \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install --no-cache-dir poetry==1.7.1

# Copy Python project files from parent directory
COPY ../pyproject.toml ../poetry.lock ./

# Export requirements and install
RUN poetry export -f requirements.txt --without-hashes -o requirements.txt \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 3: Final runtime image
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    libleveldb1d \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages
COPY --from=python-builder /install /usr/local

# Copy DataMgmt Node source
WORKDIR /app
COPY ../datamgmtnode ./datamgmtnode
COPY ../contracts ./contracts
COPY ../plugins ./plugins

# Create data directories
RUN mkdir -p /app/data /var/log/supervisor

# Copy website static files
COPY --from=website-builder /website/dist /usr/share/nginx/html

# Copy configuration files
COPY deploy/nginx.conf /etc/nginx/nginx.conf
COPY deploy/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create startup script
COPY deploy/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose ports
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
