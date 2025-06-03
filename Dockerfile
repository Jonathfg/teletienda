# Usa imagen oficial de Python 3.10
FROM python:3.10-slim

# Variables de entorno para evitar buffering de Python y crear logs
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Crear carpeta para la aplicación
WORKDIR /app

# Copiar requirements (en este ejemplo, instalamos directamente paquetes básicos)
COPY ./requirements.txt /app/requirements.txt

# Instalar dependencias del sistema (si se requiere libpq-dev, build-essential, etc.) y pip
RUN apt-get update && \
    apt-get install -y build-essential libpq-dev && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt && \
    apt-get remove -y build-essential libpq-dev && apt-get autoremove -y

# Copiar el código de la aplicación
COPY ./app /app/app

# Exponer el puerto en el que correrá la API
EXPOSE 8000

# Comando por defecto
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]