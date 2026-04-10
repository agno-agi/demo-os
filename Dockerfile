# ===========================================================================
# AgentOS Demo
# ===========================================================================
# Multi-agent system built with Agno.
# Runs as a non-root user (app) with:
#   /app    - read-only application code
#   /repos  - persistent volume for Coda's cloned repositories
# ===========================================================================

FROM agnohq/python:3.12

# ---------------------------------------------------------------------------
# System dependencies (required by Coda agent)
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    git-lfs \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Git configuration (safe defaults for Coda agent)
# ---------------------------------------------------------------------------
RUN git config --system init.defaultBranch main \
    && git config --system user.name "Coda" \
    && git config --system user.email "coda@agno.com" \
    && git config --system advice.detachedHead false

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# ---------------------------------------------------------------------------
# Create non-root user
# ---------------------------------------------------------------------------
RUN groupadd -r app && useradd -r -g app -m -s /bin/bash app

# ---------------------------------------------------------------------------
# Application code
# ---------------------------------------------------------------------------
WORKDIR /app
COPY requirements.txt .
RUN uv pip sync requirements.txt --system
COPY . .

# ---------------------------------------------------------------------------
# Directory setup & permissions
# ---------------------------------------------------------------------------
# /repos - Coda's persistent repository storage (Docker volume)
# /app   - readable but not writable by the app user
RUN mkdir -p /repos \
    && chown -R app:app /repos \
    && chmod 755 /app

# ---------------------------------------------------------------------------
# GitHub token configuration (for Coda agent)
# ---------------------------------------------------------------------------
# The GITHUB_TOKEN env var is used for cloning private repos.
# Git credential helper reads it from the environment (never written to disk).
# Set via: docker compose env or .env file
# ---------------------------------------------------------------------------
RUN printf '%s\n' \
        '#!/bin/bash' \
        'if [ -n "$GITHUB_TOKEN" ]; then' \
        '    echo "protocol=https"' \
        '    echo "host=github.com"' \
        '    echo "username=x-access-token"' \
        '    echo "password=$GITHUB_TOKEN"' \
        'fi' \
        > /usr/local/bin/git-credential-env \
    && chmod +x /usr/local/bin/git-credential-env \
    && git config --system credential.helper '/usr/local/bin/git-credential-env'

# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
RUN chmod +x /app/scripts/entrypoint.sh
ENTRYPOINT ["/app/scripts/entrypoint.sh"]

# ---------------------------------------------------------------------------
# Switch to non-root user
# ---------------------------------------------------------------------------
USER app
WORKDIR /app

EXPOSE 8000

# ---------------------------------------------------------------------------
# Default command (overridden by compose)
# ---------------------------------------------------------------------------
CMD ["chill"]
