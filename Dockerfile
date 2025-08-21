FROM python:3.10-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git build-essential cmake \
    && rm -rf /var/lib/apt/lists/*

# Install requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install prism-core from private repo using token
ARG GITHUB_TOKEN=""
RUN if [ -n "$GITHUB_TOKEN" ]; then \
      pip install --no-cache-dir git+https://$GITHUB_TOKEN@github.com/PRISM-System/prism-core@v0.1.2 ; \
    else \
      echo "GITHUB_TOKEN not set; skipping prism-core install" && exit 1 ; \
    fi

# Copy app
COPY src ./src
COPY dev ./dev

# Expose
EXPOSE 8000

# Env passthrough (optional defaults)
ENV APP_HOST=0.0.0.0
ENV APP_PORT=8000

# Run
CMD ["python", "-m", "src.main"] 