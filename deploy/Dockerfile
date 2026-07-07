FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY lethe ./lethe
RUN pip install --no-cache-dir ".[server]"

COPY server ./server

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
