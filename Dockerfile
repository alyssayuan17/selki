# ── Stage 1: build the React frontend ────────────────────────────────────────
FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build


# ── Stage 2: production image ─────────────────────────────────────────────────
FROM python:3.11-slim

# System deps needed by audio libraries (librosa, torch, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip/setuptools first
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install openai-whisper separately (latest version has proper build system)
RUN pip install --no-cache-dir openai-whisper==20250625

# Install remaining dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y gcc g++ && apt-get autoremove -y && rm -rf /var/lib/apt/lists/* /root/.cache

# Copy backend source
COPY backend/ ./

# Copy built frontend from stage 1
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Persistent data lives here — mount a volume to survive restarts
RUN mkdir -p uploads data

EXPOSE 8000

# Use $PORT if set (Railway), otherwise default to 8000
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
