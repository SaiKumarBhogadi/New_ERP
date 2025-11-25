FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Kolkata

WORKDIR /app

# Install dependencies and wkhtmltopdf
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
    tzdata && \
    wkhtmltopdf --version && \
    rm -rf /var/lib/apt/lists/*

# Copy all files into container
COPY . .

# Install Python dependencies
# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r erp_project/requirements.txt
# Run Django server
CMD ["bash", "-c", "python3 erp_project/manage.py migrate && python3 erp_project/manage.py runserver 0.0.0.0:8000"]
