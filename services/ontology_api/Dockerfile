FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git \
    && rm -rf /var/lib/apt/lists/*

# Install OntologyExtender dependencies
COPY repos/OntologyExtender/requirements.txt /tmp/repo-requirements.txt
RUN pip install --no-cache-dir -r /tmp/repo-requirements.txt || true

# Install FastAPI extras
RUN pip install --no-cache-dir \
    "fastapi>=0.115" \
    "uvicorn[standard]>=0.34" \
    "httpx>=0.25" \
    "rdflib>=7.0" \
    "pyshacl>=0.25.0"

# Install OntologyExtender package
COPY repos/OntologyExtender/ /app
RUN pip install --no-cache-dir -e /app || true

# Copy the FastAPI wrapper
COPY services/ontology_api/ /app/service/
COPY services/shared/ /app/service/shared/

WORKDIR /app/service

EXPOSE 8003

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
