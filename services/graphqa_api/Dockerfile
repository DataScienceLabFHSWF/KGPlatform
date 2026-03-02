FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git \
    && rm -rf /var/lib/apt/lists/*

# Install GraphQAAgent dependencies
COPY repos/GraphQAAgent/requirements.txt /tmp/repo-requirements.txt
RUN pip install --no-cache-dir -r /tmp/repo-requirements.txt

# Install FastAPI extras
RUN pip install --no-cache-dir \
    "fastapi>=0.115" \
    "uvicorn[standard]>=0.34" \
    "httpx>=0.25" \
    "sse-starlette>=2.0"

# Install GraphQAAgent package from the dev/fast-api-backend branch
COPY repos/GraphQAAgent/ /app
RUN pip install --no-cache-dir -e /app

EXPOSE 8002

# Run the actual GraphQAAgent FastAPI server (from kgrag.api.server:app)
CMD ["uvicorn", "kgrag.api.server:app", "--host", "0.0.0.0", "--port", "8002"]
