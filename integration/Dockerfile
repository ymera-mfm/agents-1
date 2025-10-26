FROM python:3.11-slim

WORKDIR /app

# Install specific versioned dependencies for reproducible builds
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    redis==5.0.1 \
    psycopg2-binary==2.9.9

# Copy application files (to be configured when ready)
# COPY . /app

# API Gateway entrypoint - configure with actual application when ready
# For now, this serves as a placeholder that can be easily replaced
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
