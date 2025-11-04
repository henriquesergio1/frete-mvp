
FROM python:3.11-bookworm

# ODBC para SQL Server (Debian 12)
RUN set -eux;     apt-get update;     apt-get install -y --no-install-recommends         curl gnupg2 ca-certificates         unixodbc unixodbc-dev libgssapi-krb5-2;     mkdir -p /usr/share/keyrings;     curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg;     echo "deb [signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/microsoft-prod.list;     apt-get update;     ACCEPT_EULA=Y apt-get install -y msodbcsql18;     rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
ENV PYTHONPATH=/app

ENV API_PORT=8080
EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
