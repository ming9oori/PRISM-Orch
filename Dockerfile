FROM python:3.10-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git build-essential cmake \
    && rm -rf /var/lib/apt/lists/*

# Conditional prism-core installation
ARG USE_LOCAL_PRISM_CORE=false
ARG PRISM_CORE_VERSION=main
COPY requirements.txt ./

# Install requirements conditionally
RUN pip install --no-cache-dir --upgrade pip
RUN if [ "$USE_LOCAL_PRISM_CORE" = "true" ]; then \
        # Skip prism-core from requirements.txt and install others
        grep -v "prism_core" requirements.txt > requirements_no_prism.txt && \
        pip install --no-cache-dir -r requirements_no_prism.txt; \
    else \
        # Install specific version of prism-core from GitHub
        echo "Installing prism-core from GitHub: $PRISM_CORE_VERSION" && \
        grep -v "prism_core" requirements.txt > requirements_no_prism.txt && \
        pip install --no-cache-dir -r requirements_no_prism.txt && \
        pip install --no-cache-dir "prism_core @ git+https://github.com/PRISM-System/prism-core.git@$PRISM_CORE_VERSION"; \
    fi

# Copy app
COPY src ./src
COPY dev ./dev

# Expose
EXPOSE 8100

# Env passthrough (optional defaults)
ENV APP_HOST=0.0.0.0
ENV APP_PORT=8100

# Run
CMD ["python", "-m", "src.main"] 