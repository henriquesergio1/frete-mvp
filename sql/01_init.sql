
-- Script completo do schema (tabelas/índices/triggers/view) do FreteDB
-- Cole aqui o 01_init.sql enviado anteriormente. Mantido separado para execução no Odin (10.10.10.100).
/* ========================================================================
   ETAPA 1 — BANCO DE DADOS DO FRETE (SQL SERVER)
   Recriação completa do schema para MVP de Frete
   Compatível com: SQL Server 2017+
   ======================================================================== */

IF DB_ID('FreteDB') IS NULL
BEGIN
    PRINT '>> Criando banco FreteDB...';
    CREATE DATABASE FreteDB;
END
GO

USE FreteDB;
GO

IF OBJECT_ID('dbo.vw_pendencias_cargas', 'V') IS NOT NULL DROP VIEW dbo.vw_pendencias_cargas;
GO

IF OBJECT_ID('dbo.frete_lancamento_auditoria', 'U') IS NOT NULL DROP TABLE dbo.frete_lancamento_auditoria;
IF OBJECT_ID('dbo.frete_lancamento_carga',      'U') IS NOT NULL DROP TABLE dbo.frete_lancamento_carga;
IF OBJECT_ID('dbo.frete_lancamento',            'U') IS NOT NULL DROP TABLE dbo.frete_lancamento;
IF OBJECT_ID('dbo.parametros_taxas',            'U') IS NOT NULL DROP TABLE dbo.parametros_taxas;
IF OBJECT_ID('dbo.parametros_base',             'U') IS NOT NULL DROP TABLE dbo.parametros_base;
IF OBJECT_ID('dbo.versao_schema',               'U') IS NOT NULL DROP TABLE dbo.versao_schema;
GO

CREATE TABLE dbo.versao_schema (
    id           INT IDENTITY PRIMARY KEY,
    versao       VARCHAR(20)  NOT NULL,
    descricao    NVARCHAR(200) NULL,
    aplicado_em  DATETIME2     NOT NULL DEFAULT SYSDATETIME()
);

INSERT INTO dbo.versao_schema (versao, descricao)
VALUES ('1.0.0', N'Criação inicial do schema FreteDB');
GO

CREATE TABLE dbo.parametros_base (
    id              INT IDENTITY PRIMARY KEY,
    cidade          NVARCHAR(120) NOT NULL,
    tipo_veiculo    NVARCHAR(80)  NOT NULL,
    km              INT           NOT NULL,
    valor_base      DECIMAL(18,2) NOT NULL,
    ativo           BIT           NOT NULL DEFAULT 1,
    CONSTRAINT CK_parametros_base_km       CHECK (km >= 0),
    CONSTRAINT CK_parametros_base_valor    CHECK (valor_base >= 0),
    CONSTRAINT UQ_parametros_base UNIQUE (cidade, tipo_veiculo)
);

CREATE TABLE dbo.parametros_taxas (
    id              INT IDENTITY PRIMARY KEY,
    cidade          NVARCHAR(120) NOT NULL,
    tipo_veiculo    NVARCHAR(80)  NOT NULL,
    taxa_tipo       NVARCHAR(60)  NOT NULL,
    modalidade      VARCHAR(20)   NOT NULL,
    valor           DECIMAL(18,2) NOT NULL,
    ativo           BIT           NOT NULL DEFAULT 1,
    CONSTRAINT CK_parametros_taxas_modalidade CHECK (modalidade IN ('fixa','por_km','por_carga')),
    CONSTRAINT CK_parametros_taxas_valor      CHECK (valor >= 0),
    CONSTRAINT UQ_parametros_taxas UNIQUE (cidade, tipo_veiculo, taxa_tipo)
);

CREATE INDEX IX_parametros_base_tipo   ON dbo.parametros_base (tipo_veiculo, cidade);
CREATE INDEX IX_parametros_taxas_tipo  ON dbo.parametros_taxas (tipo_veiculo, cidade);
GO

CREATE TABLE dbo.frete_lancamento (
    id               INT IDENTITY PRIMARY KEY,
    data_frete       DATE          NOT NULL,
    cod_veiculo      INT           NOT NULL,
    placa            NVARCHAR(20)  NOT NULL,
    cod_motorista    INT           NULL,
    motorista        NVARCHAR(120) NULL,
    tipo_veiculo     NVARCHAR(80)  NOT NULL,

    cidade_base      NVARCHAR(120) NOT NULL,
    km_base          INT           NOT NULL,
    valor_base       DECIMAL(18,2) NOT NULL,

    valor_taxas      DECIMAL(18,2) NOT NULL,
    valor_total      AS (valor_base + valor_taxas) PERSISTED,

    status           VARCHAR(20)   NOT NULL DEFAULT 'ativo',
    observacoes      NVARCHAR(500) NULL,

    cancelado_em     DATETIME2     NULL,
    cancelado_por    NVARCHAR(120) NULL,
    cancelado_motivo NVARCHAR(500) NULL,

    criado_em        DATETIME2     NOT NULL DEFAULT SYSDATETIME(),
    criado_por       NVARCHAR(120) NULL,
    atualizado_em    DATETIME2     NULL,
    atualizado_por   NVARCHAR(120) NULL,

    CONSTRAINT CK_frete_status CHECK (status IN ('ativo','cancelado')),
    CONSTRAINT CK_frete_valores CHECK (valor_base >= 0 AND valor_taxas >= 0 AND km_base >= 0)
);

CREATE INDEX IX_frete_lancamento_data     ON dbo.frete_lancamento (data_frete);
CREATE INDEX IX_frete_lancamento_status   ON dbo.frete_lancamento (status);
CREATE INDEX IX_frete_lancamento_veiculo  ON dbo.frete_lancamento (cod_veiculo, data_frete);
GO

CREATE TABLE dbo.frete_lancamento_carga (
    id                   INT IDENTITY PRIMARY KEY,
    frete_id             INT            NOT NULL
        CONSTRAINT FK_frete_lancamento_carga_frete
        REFERENCES dbo.frete_lancamento(id) ON DELETE CASCADE,

    carga_num            BIGINT         NOT NULL,
    data_cte             DATE           NULL,
    cidade               NVARCHAR(120)  NOT NULL,

    km_cidade            INT            NOT NULL,
    valor_base_cidade    DECIMAL(18,2)  NOT NULL,
    valor_taxas_cidade   DECIMAL(18,2)  NOT NULL,

    origem               VARCHAR(20)    NOT NULL DEFAULT 'erp',
    pendencia            BIT            NOT NULL DEFAULT 0,
    cod_veiculo_erp      INT            NULL,
    cod_veiculo_lancado  INT            NULL,
    pendencia_motivo     NVARCHAR(500)  NULL,

    ativo                BIT            NOT NULL DEFAULT 1,

    CONSTRAINT CK_frete_carga_valores CHECK (km_cidade >= 0 AND valor_base_cidade >= 0 AND valor_taxas_cidade >= 0),
    CONSTRAINT CK_frete_carga_origem  CHECK (origem IN ('erp','manual'))
);

CREATE INDEX IX_frete_carga_frete    ON dbo.frete_lancamento_carga (frete_id);
CREATE INDEX IX_frete_carga_cidade   ON dbo.frete_lancamento_carga (cidade);
CREATE INDEX IX_frete_carga_pend     ON dbo.frete_lancamento_carga (pendencia) INCLUDE (carga_num, cod_veiculo_erp, cod_veiculo_lancado);

CREATE UNIQUE INDEX UX_frete_carga_unica_ativa
ON dbo.frete_lancamento_carga (carga_num)
WHERE (ativo = 1);
GO

CREATE TABLE dbo.frete_lancamento_auditoria (
    id           INT IDENTITY PRIMARY KEY,
    frete_id     INT            NOT NULL,
    operacao     VARCHAR(20)    NOT NULL,
    motivo       NVARCHAR(500)  NULL,
    antes_json   NVARCHAR(MAX)  NULL,
    depois_json  NVARCHAR(MAX)  NULL,
    feito_por    NVARCHAR(120)  NULL,
    feito_em     DATETIME2      NOT NULL DEFAULT SYSDATETIME()
);

CREATE INDEX IX_frete_auditoria_frete ON dbo.frete_lancamento_auditoria (frete_id, operacao, feito_em DESC);
GO

CREATE OR ALTER TRIGGER dbo.trg_frete_status_sync_cargas
ON dbo.frete_lancamento
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT UPDATE(status) RETURN;
    UPDATE c
    SET c.ativo = CASE WHEN f.status = 'ativo' THEN 1 ELSE 0 END
    FROM dbo.frete_lancamento_carga c
    INNER JOIN inserted i ON i.id = c.frete_id
    INNER JOIN dbo.frete_lancamento f ON f.id = i.id;
END;
GO

CREATE OR ALTER TRIGGER dbo.trg_carga_set_ativo_from_frete
ON dbo.frete_lancamento_carga
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE c
    SET c.ativo = CASE WHEN f.status = 'ativo' THEN 1 ELSE 0 END
    FROM dbo.frete_lancamento_carga c
    INNER JOIN inserted i ON i.id = c.id
    INNER JOIN dbo.frete_lancamento f ON f.id = i.frete_id;
END;
GO

CREATE VIEW dbo.vw_pendencias_cargas
AS
SELECT
    f.id              AS frete_id,
    f.data_frete,
    f.placa,
    f.motorista,
    f.tipo_veiculo,
    f.status,
    c.carga_num,
    c.cidade,
    c.origem,
    c.pendencia,
    c.cod_veiculo_erp,
    c.cod_veiculo_lancado,
    c.pendencia_motivo
FROM dbo.frete_lancamento f
JOIN dbo.frete_lancamento_carga c ON c.frete_id = f.id
WHERE c.pendencia = 1
  AND f.status = 'ativo';
GO

INSERT INTO dbo.parametros_base (cidade, tipo_veiculo, km, valor_base) VALUES
(N'Caçapava', N'Van',       18, 500.00),
(N'Caçapava', N'Caminhão',  18, 800.00),
(N'Taubaté',  N'Van',       45, 700.00),
(N'Taubaté',  N'Caminhão',  45, 950.00);

INSERT INTO dbo.parametros_taxas (cidade, tipo_veiculo, taxa_tipo, modalidade, valor, ativo) VALUES
(N'Caçapava', N'Van',       N'pedagio',    'fixa',     25.00, 1),
(N'Caçapava', N'Caminhão',  N'pedagio',    'fixa',     25.00, 1),
(N'Caçapava', N'Van',       N'ambiental',  'por_carga',10.00, 1),
(N'Taubaté',  N'Caminhão',  N'pedagio',    'fixa',     40.00, 1),
(N'Taubaté',  N'Caminhão',  N'balsa',      'fixa',      0.00, 1);
GO
