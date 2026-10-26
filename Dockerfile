# Imagen de Rakim Bot. Se construye con `--pull` para traer siempre el último parche
# de la imagen base de Python.
FROM python:3.14-slim

# Versión mínima con los parches de seguridad de Python del 25 oct 2026 (3.14.10). Si la
# imagen base trae menos, la construcción falla en vez de desplegar un Python vulnerable.
# Al salir un parche nuevo, sube este número (ver docs/decisions.md).
RUN python -c "import sys; assert sys.version_info >= (3, 14, 10), sys.version"

# Sin bytecode en tiempo de ejecución (en producción el sistema de archivos es de solo
# lectura) y logs sin demora. uv usa siempre el Python de la imagen, nunca uno descargado.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON_PREFERENCE=only-system \
    PATH="/app/.venv/bin:$PATH"

COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /usr/local/bin/uv
WORKDIR /app

# Primero las dependencias: esta capa solo se reconstruye si cambia uv.lock.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY rakim ./rakim

# Sin privilegios de root. Aquí vive el estado (el aviso de bump pendiente); en producción es un volumen.
RUN useradd --system --uid 1000 rakim && mkdir -p /app/data && chown rakim /app/data
USER rakim
CMD ["python", "-m", "rakim"]
