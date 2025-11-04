
from fastapi import APIRouter, Query
from .. import db

router = APIRouter(prefix="/veiculos", tags=["Veiculos"])

@router.get("")
def listar_veiculos(ativo: int = Query(default=1)):
    sql = """
    SELECT
      ibetvec.codvec        AS COD_VEICULO,
      ibetvec.numplcvec     AS PLACA,
      IBETTPLPDRVEC.CODMTCEPG AS COD_MOTORISTA,
      IBETCPLEPG.nomepg     AS Motorista,
      IBETDOMMDLVEC.desmdlvec AS Tipo,
      CASE WHEN ibetvec.INDSTUVEC = '1' THEN 'Ativo' ELSE 'Inativo' END AS Ativo
    FROM flexx10071188.dbo.ibetvec ibetvec
    LEFT JOIN flexx10071188.dbo.IBETTPLPDRVEC ON ibetvec.codvec = IBETTPLPDRVEC.codvec
    LEFT JOIN flexx10071188.dbo.IBETCPLEPG    ON IBETTPLPDRVEC.codmtcepg = IBETCPLEPG.codmtcepg
    LEFT JOIN flexx10071188.dbo.IBETDOMMDLVEC ON ibetvec.tpomdlvec = IBETDOMMDLVEC.tpomdlvec
    WHERE IBETCPLEPG.tpoepg = 'm'
    """
    if ativo == 1:
        sql += " AND ibetvec.INDSTUVEC = '1'"
    with db.erp_conn() as conn:
        return db.query_all(conn, sql)
