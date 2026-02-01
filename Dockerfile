FROM python:3.12-slim

WORKDIR /app

# Install system dependencies if any (usually just simple python deps needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

# Copy local package
COPY stock_gita_engine_charts /app/stock_gita_engine_charts

# Copy requirements (assuming it's inside the charts folder, or we create one)
COPY stock_gita_engine_charts/requirements.txt /app/requirements.txt

# Install python deps
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install uvicorn fastapi langchain-aws langchain-core pandas numpy requests boto3 

# Set python path to include app root so imports work
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Run the API bridge
CMD ["python", "stock_gita_engine_charts/api_bridge.py"]
