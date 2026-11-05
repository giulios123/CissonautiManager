# Stage 1: build the frontend
FROM node:22-slim AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python app with the ODBC driver for SQL Server
# Pinned to Debian 12: the Microsoft ODBC driver below comes from the Debian 12 repository.
FROM python:3.12-slim-bookworm
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 ACCEPT_EULA=Y

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl gnupg ca-certificates unixodbc \
    && curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# Fail the build, not the first database connection, if the driver cannot load
# (a missing shared library shows up as "file not found" at runtime).
RUN ! ldd /opt/microsoft/msodbcsql18/lib64/libmsodbcsql-*.so* | grep "not found" \
    && odbcinst -q -d | grep -q "ODBC Driver 18 for SQL Server"

COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /usr/local/bin/uv

WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock backend/.python-version ./
RUN uv sync --frozen --no-dev --no-install-project
COPY backend/ ./
COPY --from=frontend /frontend/dist ./static

# Which commit is running and when it was built, shown in the in-app guide.
ARG APP_VERSION=dev
ARG BUILT_AT=
ENV APP_VERSION=$APP_VERSION BUILT_AT=$BUILT_AT

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
# Apply migrations, then start the server. Safe because the app runs one replica at most.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
