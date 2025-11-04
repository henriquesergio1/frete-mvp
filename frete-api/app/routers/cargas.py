
from fastapi import APIRouter, Query
from .. import db

router = APIRouter(prefix="/cargas", tags=["Cargas"])

@router.get("")
def listar_cargas(data: str = Query(..., description="YYYY-MM-DD"), cod_veiculo: int = Query(...)):
    cargas_sql = f"""
    SELECT
      PDD.NUMSEQETGPDD AS CARGA,
      PDD.CODVEC AS COD_VEICULO,
      ibetvec.numplcvec AS PLACA,
      CDD.DESCDD AS CIDADE,
      LVR.DATEMSNF_LVRSVC AS DATA_CTE
    FROM Flexx10071188.dbo.IRFTLVRSVC LVR (NOLOCK)
    LEFT JOIN Flexx10071188.dbo.IBETPDDSVCNF_ PDD (NOLOCK)
      ON PDD.CODEMP = LVR.CODEMP AND PDD.NUMDOCTPTPDD = LVR.NUMNF_LVRSVC AND PDD.INDSERDOCTPTPDD = LVR.CODSERNF_LVRSVC AND PDD.NUMSEQNF_SVC = LVR.NUMSEQNF_SVC
    LEFT JOIN Flexx10071188.dbo.IBETEDRCET EDR (NOLOCK)
      ON LVR.CODEMP = EDR.CODEMP AND LVR.CODCET = EDR.CODCET AND EDR.CODTPOEDR = 1
    LEFT JOIN Flexx10071188.dbo.IBETCDD CDD (NOLOCK)
      ON EDR.CODEMP = CDD.CODEMP AND EDR.CODPAS = CDD.CODPAS AND EDR.CODUF_ = CDD.CODUF_ AND EDR.CODCDD = CDD.CODCDD
    LEFT JOIN ibetvec ibetvec ON PDD.CODVEC = ibetvec.codvec
    WHERE LVR.DATEMSNF_LVRSVC = '{data}' AND PDD.CODVEC = {cod_veiculo}
    """
    with db.erp_conn() as erp:
        cargas = db.query_all(erp, cargas_sql)
    if not cargas:
        return []
    nums = [c['CARGA'] for c in cargas]
    placeholders = ','.join(['?']*len(nums))
    with db.frete_conn() as frete:
        existentes = db.query_all(frete, f"SELECT carga_num FROM dbo.frete_lancamento_carga WHERE ativo = 1 AND carga_num IN ({placeholders})", nums)
    bloqueadas = {e['carga_num'] for e in existentes}
    return [c for c in cargas if c['CARGA'] not in bloqueadas]
