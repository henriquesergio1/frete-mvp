
import json
from . import db

def registrar_auditoria(frete_id: int, operacao: str, motivo: str, antes: dict | None, depois: dict | None, feito_por: str | None):
    with db.frete_conn() as conn:
        db.execute(conn, """
            INSERT INTO dbo.frete_lancamento_auditoria (frete_id, operacao, motivo, antes_json, depois_json, feito_por)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [frete_id, operacao, motivo, json.dumps(antes, ensure_ascii=False) if antes else None, json.dumps(depois, ensure_ascii=False) if depois else None, feito_por])
