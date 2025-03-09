FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    ffmpeg \
    libssl-dev \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1001 appuser
USER appuser
WORKDIR /home/appuser/app

# Use virtual environment
RUN python -m venv venv
ENV PATH="/home/appuser/app/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--timeout", "600", "app:app"]