FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy
WORKDIR /app
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium
RUN playwright install-deps chromium
RUN mkdir -p /app/data && chmod 777 /app/data
COPY app/ ./app/
COPY fallback_data/ ./fallback_data/
EXPOSE 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--reload", "--timeout-keep-alive", "120"]
