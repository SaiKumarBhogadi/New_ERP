# -----------------------
# Backend Dockerfile
# -----------------------
FROM python:3.10-slim

# Install dependencies including wkhtmltopdf
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    gcc \
    wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY erp_project/requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY erp_project /app/erp_project

EXPOSE 8000

CMD ["bash", "-c", "python3 erp_project/manage.py migrate && python3 erp_project/manage.py runserver 0.0.0.0:8000"]
