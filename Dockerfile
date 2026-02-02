# GLTCH Docker Image
# Multi-stage build for Python agent + TypeScript gateway

# ============================================
# Stage 1: Build Gateway
# ============================================
FROM node:20-alpine AS gateway-builder

WORKDIR /app/gateway

# Copy gateway source
COPY gateway/package*.json ./
RUN npm ci

COPY gateway/ ./
RUN npm run build

# ============================================
# Stage 2: Build CLI
# ============================================
FROM node:20-alpine AS cli-builder

WORKDIR /app/cli

COPY cli/package*.json ./
RUN npm ci

COPY cli/ ./
RUN npm run build

# ============================================
# Stage 3: Final Image
# ============================================
FROM python:3.11-slim

# Install Node.js
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python agent
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY agent/ ./agent/
COPY gltch.py ./

# Copy built gateway
COPY --from=gateway-builder /app/gateway/dist ./gateway/dist
COPY --from=gateway-builder /app/gateway/package*.json ./gateway/
COPY --from=gateway-builder /app/gateway/node_modules ./gateway/node_modules

# Copy built CLI
COPY --from=cli-builder /app/cli/dist ./cli/dist
COPY --from=cli-builder /app/cli/package*.json ./cli/
COPY --from=cli-builder /app/cli/node_modules ./cli/node_modules

# Copy docs and configs
COPY docs/ ./docs/
COPY README.md ./
COPY AGENTS.md ./
COPY .env.example ./

# Create data directory
RUN mkdir -p /data/.gltch

# Environment
ENV GLTCH_DATA_DIR=/data/.gltch
ENV GLTCH_GATEWAY_HOST=0.0.0.0
ENV GLTCH_GATEWAY_PORT=18888
ENV GLTCH_GATEWAY_WS_PORT=18889

# Expose ports
EXPOSE 18888 18889 18890

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:18888/health || exit 1

# Default command: start both agent and gateway
CMD ["sh", "-c", "python gltch.py --rpc http --port 18890 & node gateway/dist/index.js start"]
