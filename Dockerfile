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

# prism-core is already installed via requirements.txt

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