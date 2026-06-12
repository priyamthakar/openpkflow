# Build context: repo root (not api/).
# docker build -t openpkflow-api -f api/Dockerfile .
#
# Render does NOT use this Dockerfile when runtime: python is set in render.yaml.
# This file is kept for local Docker testing and as an alternative deploy path.

FROM python:3.12-slim
WORKDIR /app

# Install the openpkflow engine from source (includes [reports] extras).
# Must copy src/ and pyproject.toml before pip install.
COPY pyproject.toml README.md ./
COPY src/ src/
RUN pip install --no-cache-dir ".[reports]"

# Install the API adapter dependencies.
COPY api/requirements.txt api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

# Copy the API source.
COPY api/ api/

WORKDIR /app/api
EXPOSE 8000
# $PORT is injected by Render; fall back to 8000 for local Docker runs.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
