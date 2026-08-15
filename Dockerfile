FROM python:3.12-slim

WORKDIR /app

# Node.js para o ACP CLI (se necessário)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia dependências primeiro (cache de camadas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instala o ACP CLI (opcional — comentar se não for usar)
# RUN npm install -g @virtuals-protocol/acp-cli

# Copia o código
COPY . .

# Cria diretório para dados persistentes
RUN mkdir -p /data
ENV SONEY_DB_PATH=/data/soney_data.db

# Porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Executa
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]