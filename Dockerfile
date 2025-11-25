FROM python:3.10-slim

# Install system dependencies required for mysqlclient
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY erp_project/requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY erp_project /app/erp_project

# Expose Django port
EXPOSE 8000

# Run Django migrations + start server
CMD ["bash", "-c", "python3 erp_project/manage.py migrate && python3 erp_project/manage.py runserver 0.0.0.0:8000"]
