FROM python:3.13-slim

# Set work directory
WORKDIR /app

# Install system dependencies for graphviz, opencv, cairo, and arrow
RUN apt-get update && apt-get install -y \
    graphviz \
    libgl1 \
    gcc \
    build-essential \
    libcairo2-dev \
    pkg-config \
    python3-dev \
    libarrow-dev \
    libarrow-glib-dev \
    libparquet-dev \
    npm \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --upgrade pip && pip install uv

# Copy project files
COPY . .

# Sync and install dependencies using uv
RUN uv sync

# Pre-create the .venv by running a dummy command
RUN uv run -- python -c "import sys; print('venv ready:', sys.prefix)"

# Set default command (adjust as needed)
CMD ["python"]