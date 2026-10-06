FROM python:3.12-slim

WORKDIR /app

# Copy the canonical groundfire_net code from the unified online service.
COPY groundfire-online-service/src/groundfire_net/ /app/groundfire_net/
COPY versao-python/groundfire/ /app/groundfire/
COPY versao-python/src/ /app/src/

# Install dependencies if any (none required for the basic gateway/directory beyond stdlib, but we set PYTHONPATH)
ENV PYTHONPATH=/app

# Default command: show help or run gateway. User will override in docker-compose.
CMD ["python", "-m", "groundfire_net.websocket_gateway", "--help"]
