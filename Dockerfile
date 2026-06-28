# ==============================================================================
# LUNARATLAS MULTI-STAGE DOCKERFILE
# Containerizes both the FastAPI python backend and the Vite static frontend.
# ==============================================================================

# --- Stage 1: Build the Client (Vite Frontend) ---
FROM node:18-alpine AS client-builder
WORKDIR /app/client

# Copy package descriptors and lockfiles
COPY core/client/package*.json ./
RUN npm ci --silent

# Copy client source code and build static assets
COPY core/client/ ./
RUN npm run build

# --- Stage 2: Build the Server (Python FastAPI Backend) ---
FROM python:3.11-slim AS server-runtime
WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY core/server/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy server source code
COPY core/server/ ./

# --- Stage 3: Assemble Production Container ---
# For simplified standalone deployment, we run the FastAPI server 
# and copy built static client assets to be served directly by FastAPI.
COPY --from=client-builder /app/client/dist ./static

# Configure environment defaults
ENV PORT=8000
ENV HOST=0.0.0.0
ENV DB_HOST=localhost

EXPOSE 8000

# Start FastAPI server via uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
