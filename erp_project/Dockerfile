
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Kolkata
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies + wkhtmltopdf
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    wkhtmltopdf \
    xfonts-75dpi \
    xfonts-base \
    fontconfig \
    libxrender1 \
    libxext6 \
    libssl-dev \
    libffi-dev \
    default-libmysqlclient-dev \
    pkg-config \
    gcc \
    build-essential \
    tzdata \
    curl && \
    wkhtmltopdf --version && \
    rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .
COPY erp_project/require.txt /app/erp_project/require.txt
# Install Python dependencies (IMPORTANT: require.txt)
RUN python3 -m pip install --upgrade pip setuptools wheel && \
    python3 -m pip install --no-cache-dir -r erp_project/require.txt

EXPOSE 8000

# Run migrations and start Django
CMD ["bash", "-c", "python3 erp_project/manage.py makemigrations && python3 erp_project/manage.py migrate && python3 erp_project/manage.py runserver 0.0.0.0:8000"]
