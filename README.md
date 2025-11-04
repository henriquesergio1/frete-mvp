
# Frete MVP — API + Docker

MVP de sistema de pagamento de frete para lançamento, edição, cancelamento com auditoria, e cálculo de valores baseado em **cidade + tipo de veículo** e **taxas por rota**.

## Arquitetura
- API: **FastAPI**
- Banco: **SQL Server** (FreteDB) — escrita
- ERP: **SQL Server** (somente leitura)
- Deploy: **Docker** (recomendado via Portainer no Odin `10.10.10.100`), expondo porta **8800**

## Pastas
```
frete-mvp/
├─ frete-api/
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ db.py
│  │  ├─ models.py
│  │  ├─ schemas.py
│  │  ├─ services/
│  │  │  ├─ calc.py
│  │  │  └─ audit.py
│  │  └─ routers/
│  │     ├─ veiculos.py
│  │     ├─ cargas.py
│  │     ├─ fretes.py
│  │     └─ parametros.py
│  ├─ Dockerfile
│  ├─ requirements.txt
│  └─ .env.example
├─ docker-compose.yml
├─ sql/
│  └─ 01_init.sql
└─ README.md
```

## Como subir (Portainer)
1. Suba este repositório no GitHub.
2. No Portainer (`10.10.10.10`), **Stacks > Add stack > Git repository**:
   - Repository URL: `https://github.com/<sua-org>/<seu-repo>.git`
   - Compose path: `docker-compose.yml`
   - Branch: `main` (ou conforme seu repo)
3. Defina as variáveis via **Env** ou use arquivo `.env` (veja `.env.example`).
4. Deploy stack.

Depois de subir:
- API: `http://10.10.10.100:8800/docs` (Swagger)
- OpenAPI para Custom Connector: `http://10.10.10.100:8800/openapi.json`

## Banco de Dados
Execute o script `sql/01_init.sql` no seu SQL Server para criar/zerar o schema `FreteDB` com tabelas, índices, triggers e view de pendências.

## Notas
- A instalação do **msodbcsql18** é feita no Dockerfile.
- Conexões são lidas de `ERP_SQL_CONN` e `FRETE_SQL_CONN` (ODBC) via environment.
- Esta API implementa o essencial para o MVP: lançamentos, edição, cancelamento com motivo e auditoria, validação de carga manual vs veículo do ERP, e cálculo de taxas por rota.
