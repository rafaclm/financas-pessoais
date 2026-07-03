# Imagem base com Python
FROM python:3.12-slim

# Configuracoes de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Dependencias do sistema (para psycopg2 e outros)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Diretorio de trabalho
WORKDIR /app

# Copia arquivos de dependencia primeiro (cache do Docker)
COPY pyproject.toml ./

# Instala dependencias
RUN pip install --upgrade pip && \
    pip install -e .

# Copia o restante do codigo
COPY . .

# Cria pasta de dados se nao existir
RUN mkdir -p /app/data

# Expoe a porta (Railway define $PORT dinamicamente)
EXPOSE 8080

# Comando de inicializacao
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}