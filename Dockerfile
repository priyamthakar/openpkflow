# Dockerfile for OpenPKFlow library + Jupyter Lab (all optional extras)
#
# Build:
#   docker build -t openpkflow .
#
# Run Jupyter:
#   docker run --rm -p 8888:8888 -v "%cd%":/workspace openpkflow
#   # Unix: docker run --rm -p 8888:8888 -v "$(pwd)":/workspace openpkflow
#
# Compose (Jupyter only by default):
#   docker compose up -d
#   Open http://localhost:8888
#
# Related images (not this file):
#   - API adapter:  docker build -t openpkflow-api -f api/Dockerfile .
#   - Web UI:       build/run separately via webapp/ (Node); see docker-compose.yml notes
#
# Optional multi-stage pattern (commented): use a builder stage if you need
# compilers only at install time and a slimmer runtime later.
#
#   # FROM python:3.12-slim AS builder
#   # WORKDIR /build
#   # RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ make \
#   #     && rm -rf /var/lib/apt/lists/*
#   # COPY pyproject.toml README.md ./
#   # COPY src/ src/
#   # RUN pip install --no-cache-dir --prefix=/install ".[reports,bayes,ml]"
#   # FROM python:3.12-slim
#   # COPY --from=builder /install /usr/local
#   # ...
#
# This single-stage image keeps local DX simple (Jupyter + full extras).

FROM python:3.12-slim

LABEL org.opencontainers.image.title="OpenPKFlow"
LABEL org.opencontainers.image.description="Python-first pharmacy toolkit for dissolution, NCA, PK/PD simulation, and pharmacometric reporting."
LABEL org.opencontainers.image.url="https://github.com/priyamthakar/openpkflow"
LABEL org.opencontainers.image.documentation="https://priyamthakar.github.io/openpkflow/"

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ make \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src/ src/

RUN pip install --no-cache-dir ".[reports,bayes,ml]" jupyter

EXPOSE 8888

ENTRYPOINT ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--allow-root", "--no-browser"]
