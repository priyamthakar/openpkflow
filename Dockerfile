# Dockerfile for OpenPKFlow with Jupyter and all extras
# Build: docker build -t openpkflow .
# Run:   docker run -p 8888:8888 -v $(pwd):/workspace openpkflow

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
