
FROM python:3.11-slim

# Instala dependências para ODBC SQL Server
RUN apt-get update &&     apt-get install -y --no-install-recommends       curl gnupg apt-transport-https       unixodbc unixodbc-dev &&     curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - &&     curl https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list &&     apt-get update &&     ACCEPT_EULA=Y apt-get install -y msodbcsql18 &&     rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
ENV PYTHONPATH=/app

# Porta interna
ENV API_PORT=8080
EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
