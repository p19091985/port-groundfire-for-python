FROM python:3.12-slim

WORKDIR /app

# Copy groundfire_net code
COPY groundfire_net/ /app/groundfire_net/
COPY src/ /app/src/

# Install dependencies if any (none required for the basic gateway/directory beyond stdlib, but we set PYTHONPATH)
ENV PYTHONPATH=/app

# Default command: show help or run gateway. User will override in docker-compose.
CMD ["python", "-m", "groundfire_net.websocket_gateway", "--help"]
