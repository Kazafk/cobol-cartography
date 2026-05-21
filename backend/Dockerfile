# Stage 1: builder
FROM python:3.11-slim AS builder
WORKDIR /build
COPY pyproject.toml .
COPY src/ ./src/
RUN pip install --no-cache-dir .

# Stage 2: runtime
FROM python:3.11-slim AS runtime

RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid 1001 --no-create-home appuser

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn

WORKDIR /app

USER appuser
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
