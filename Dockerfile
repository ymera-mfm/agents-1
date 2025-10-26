FROM python:3.11-slim

WORKDIR /app

# Install basic dependencies
RUN pip install fastapi uvicorn redis psycopg2-binary

# Placeholder entrypoint
CMD ["python", "-c", "print('API Gateway placeholder - Configure your application here')"]
