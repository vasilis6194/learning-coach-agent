# -----------------------------
# Stage 1: Base Python environment
# -----------------------------
FROM python:3.12-slim AS base

# Install OS dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install pnpm (needed only if you ever want to build inside container)
RUN npm install -g pnpm

# -----------------------------
# Stage 2: Install Python deps
# -----------------------------
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -----------------------------
# Stage 3: Copy project code
# -----------------------------
COPY . .

# -----------------------------
# Stage 4: Runtime
# -----------------------------
WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PATH="/root/.local/bin:$PATH"

# Expose port for ADK web UI
EXPOSE 8000

CMD ["adk", "web"]
