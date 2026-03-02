FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install the repo's own dependencies
COPY repos/KnowledgeGraphBuilder/requirements.txt /tmp/repo-requirements.txt
RUN pip install --no-cache-dir -r /tmp/repo-requirements.txt

# Install FastAPI extras
RUN pip install --no-cache-dir \
    "fastapi>=0.115" \
    "uvicorn[standard]>=0.34" \
    "httpx>=0.25"

# Install kgbuilder package from the fast-api branch
COPY repos/KnowledgeGraphBuilder/ /app
RUN pip install --no-cache-dir -e /app

EXPOSE 8001

# Run the actual KGBuilder FastAPI server (from kgbuilder.api.server:app)
CMD ["uvicorn", "kgbuilder.api.server:app", "--host", "0.0.0.0", "--port", "8001"]
