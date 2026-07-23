# =========================================================================
# Stage 1: Build & Cache Dependencies
# =========================================================================
FROM python:3.11-slim-bookworm AS builder

WORKDIR /app

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dependencies into a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download and cache the sentence-transformers model during build time
# Set custom cache folder so it is easily portable and persistent
ENV SENTENCE_TRANSFORMERS_HOME=/app/models_cache
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# =========================================================================
# Stage 2: Runtime Environment
# =========================================================================
FROM python:3.11-slim-bookworm AS runner

WORKDIR /app

# Install runtime system libraries (required for PyMuPDF / fitz under Linux)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment and cached models from builder
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app/models_cache /app/models_cache

# Set Environment Paths
ENV PATH="/opt/venv/bin:$PATH"
ENV SENTENCE_TRANSFORMERS_HOME=/app/models_cache
ENV PYTHONUNBUFFERED=1

# Copy backend application source
COPY src/ ./src/

# Create uploads and reports directories and set permissions
RUN mkdir -p uploads reports && \
    useradd -u 8888 appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Health check to ensure API is responsive
HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
