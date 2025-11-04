
# Frete MVP — Standalone Docker (10.10.10.10)

Pacote pronto para rodar **em Docker Standalone** no host 10.10.10.10 (Portainer/CLI).
A API conecta no SQL Server do Odin (10.10.10.100).

## Passos
1) Execute `sql/01_init.sql` no SQL Server (Odin) para criar o FreteDB.
2) Preencha `.env` com as strings de conexão.
3) **GitHub**: suba este projeto (comandos abaixo).
4) **Portainer** (endpoint Docker - NÃO Swarm): Stacks > Add stack (Git) apontando pro seu repo. Ou use CLI `docker compose up -d`.

## URLs
- Health: `http://10.10.10.10:8800/health`
- Swagger: `http://10.10.10.10:8800/docs`

