# ---------------------------
# Backend Dockerfile (Django)
# ---------------------------
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY erp_project/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend project
COPY erp_project /app/erp_project

# Expose port
EXPOSE 8000

# Run migrations & start server
CMD ["bash", "-c", "python3 erp_project/manage.py migrate && python3 erp_project/manage.py runserver 0.0.0.0:8000"]
