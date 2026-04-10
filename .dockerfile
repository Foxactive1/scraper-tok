# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema (opcional, mas útil para psycopg2 se for usar PostgreSQL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia o arquivo de dependências primeiro (melhora cache)
COPY requirements.txt .

# Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código da aplicação
COPY . .

# Expõe a porta do Flask
EXPOSE 5000

# Comando padrão para o serviço web (pode ser sobrescrito no docker-compose)
CMD ["python", "run.py"]