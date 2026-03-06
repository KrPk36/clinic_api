# =============================================================================
# Stage 1 – dependencies
# =============================================================================
FROM python:3.13-slim AS deps

WORKDIR /app

# compilation dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# venv to isolate libraries and facilitate copying
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


# =============================================================================
# Stage 2 – runtime
# =============================================================================
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# ONLY the Postgres shared library required for execution
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for security reasons
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# copy venv from 'deps'
COPY --from=deps --chown=appuser /opt/venv /opt/venv

# copy source code
COPY --chown=appuser . .

# entrypoint script
COPY --chown=appuser ./scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]