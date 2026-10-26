# Imagen de Rakim Bot. Se construye con `--pull` para traer siempre el último parche
# de la imagen base de Python.
FROM python:3.13-slim

# Python no escribe bytecode en tiempo de ejecución (el sistema de archivos es de solo lectura
# en producción) y deja salir los logs sin demora.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

COPY --from=ghcr.io/astral-sh/uv:0.11.6 /uv /usr/local/bin/uv
WORKDIR /app

# Primero las dependencias: esta capa solo se reconstruye si cambia uv.lock.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY rakim ./rakim

# Sin privilegios de root. Aquí vive el estado (el aviso de bump pendiente); en producción es un volumen.
RUN useradd --system --uid 1000 rakim && mkdir -p /app/data && chown rakim /app/data
USER rakim
CMD ["python", "-m", "rakim"]
