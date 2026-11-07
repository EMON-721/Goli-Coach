FROM node:24-bookworm-slim AS web
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN apt-get update && apt-get install -y --no-install-recommends python3 && rm -rf /var/lib/apt/lists/*
RUN python3 scripts/download_model.py && npm run build

FROM python:3.12-slim-bookworm
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 libportaudio2 && rm -rf /var/lib/apt/lists/*
COPY server/requirements.lock server/requirements.lock
RUN pip install --no-cache-dir -r server/requirements.lock
COPY server server
COPY models models
COPY --from=web /app/out out
COPY --from=web /app/public/models public/models
RUN useradd --uid 10001 --create-home coach && mkdir /data && chown coach:coach /data
USER coach
ENV DATABASE_PATH=/data/golicoach.sqlite SECURE_COOKIES=1 REQUIRE_EMAIL_VERIFICATION=1
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health',timeout=3)"
CMD ["python", "-m", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log"]
