
# Frete MVP — API + Docker (Corrigido)

Este pacote contém a API FastAPI com cálculo de frete, auditoria, validação de cargas, e Docker pronto para deploy via **Portainer**. 

**Correções incluídas**
- `Dockerfile` ajustado para Debian 12 (bookworm), usando **keyring** da Microsoft (sem `apt-key`).
- `docker-compose.yml` lendo variáveis via `env_file: .env` para evitar warnings no Portainer.
- `.env` de exemplo na **raiz** do repositório.

**Endpoints principais**
- `GET /veiculos`, `GET /cargas`
- `POST /fretes`, `GET /fretes`, `GET /fretes/{id}`, `PUT /fretes/{id}`, `DELETE /fretes/{id}`
- `GET/POST/PUT /parametros/base` e `GET/POST/PUT /parametros/taxas`

**URLs após deploy**
- Swagger: `http://10.10.10.100:8800/docs`
- OpenAPI: `http://10.10.10.100:8800/openapi.json`

**Banco**
- Execute `sql/01_init.sql` no SQL Server para criar o schema `FreteDB` com tabelas, índices, triggers e view de pendências.
