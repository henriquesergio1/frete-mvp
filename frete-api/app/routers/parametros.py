
from fastapi import APIRouter, HTTPException
from .. import db

router = APIRouter(prefix="/parametros", tags=["Parametros"])

@router.get("/base")
def listar_base():
    with db.frete_conn() as conn:
        return db.query_all(conn, "SELECT * FROM dbo.parametros_base WHERE ativo=1 ORDER BY cidade, tipo_veiculo")

@router.post("/base")
def criar_base(item: dict):
    with db.frete_conn() as conn:
        db.execute(conn, """
            INSERT INTO dbo.parametros_base (cidade, tipo_veiculo, km, valor_base, ativo) VALUES (?,?,?,?,?)
        """, [item['cidade'], item['tipo_veiculo'], item['km'], item['valor_base'], item.get('ativo',1)])
    return {"ok": True}

@router.put("/base/{id}")
def atualizar_base(id: int, item: dict):
    with db.frete_conn() as conn:
        db.execute(conn, """
            UPDATE dbo.parametros_base SET cidade=?, tipo_veiculo=?, km=?, valor_base=?, ativo=? WHERE id=?
        """, [item['cidade'], item['tipo_veiculo'], item['km'], item['valor_base'], item.get('ativo',1), id])
    return {"ok": True}

@router.get("/taxas")
def listar_taxas():
    with db.frete_conn() as conn:
        return db.query_all(conn, "SELECT * FROM dbo.parametros_taxas WHERE ativo=1 ORDER BY cidade, tipo_veiculo, taxa_tipo")

@router.post("/taxas")
def criar_taxa(item: dict):
    with db.frete_conn() as conn:
        db.execute(conn, """
            INSERT INTO dbo.parametros_taxas (cidade, tipo_veiculo, taxa_tipo, modalidade, valor, ativo) VALUES (?,?,?,?,?,?)
        """, [item['cidade'], item['tipo_veiculo'], item['taxa_tipo'], item['modalidade'], item['valor'], item.get('ativo',1)])
    return {"ok": True}

@router.put("/taxas/{id}")
def atualizar_taxa(id: int, item: dict):
    with db.frete_conn() as conn:
        db.execute(conn, """
            UPDATE dbo.parametros_taxas SET cidade=?, tipo_veiculo=?, taxa_tipo=?, modalidade=?, valor=?, ativo=? WHERE id=?
        """, [item['cidade'], item['tipo_veiculo'], item['taxa_tipo'], item['modalidade'], item['valor'], item.get('ativo',1), id])
    return {"ok": True}
