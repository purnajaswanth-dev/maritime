FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-lock.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements-lock.txt

COPY src/ ./src/
COPY configs/ ./configs/
COPY data/ ./data/
COPY models/ ./models/

ENV PORT=8000
ENV ALLOW_CONTAINER_BIND=1
EXPOSE 8000

CMD ["python", "-m", "src.simulation.daemon"]
