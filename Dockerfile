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

# Install CPU-only PyTorch explicitly first.
# Using --index-url (primary) guarantees the CPU wheel is chosen before
# any downstream dep (silero-vad, whisper-timestamped) can pull in CUDA torch.
RUN pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    torch==2.6.0+cpu \
    torchaudio==2.6.0+cpu

# Install remaining dependencies (torch already present, so CPU version is kept)
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y gcc g++ && apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/* /root/.cache /tmp/*

# Copy backend source
COPY backend/ ./

# Copy built frontend from stage 1
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Persistent data lives here — mount a volume to survive restarts
RUN mkdir -p uploads data

EXPOSE 7860

CMD uvicorn main:app --host 0.0.0.0 --port 7860
