FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY Backend/ .
COPY Frontend/ ./Frontend/
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

EXPOSE 8000

# All startup logic lives in ./entrypoint.sh (migrate + collectstatic
# for the primary instance, gunicorn or celery per role). Compose services
# just pass a short role like ["web", "--migrate"]. Gunicorn is the process
# manager, uvicorn workers serve the async ASGI app.
# DEBUG=False is set in docker-compose.yml for container runs.
ENTRYPOINT ["./entrypoint.sh"]
CMD ["web"]
