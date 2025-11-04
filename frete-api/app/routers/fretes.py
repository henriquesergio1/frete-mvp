
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from .. import db
from ..schemas import FreteCreate, FreteUpdate, FreteCancel
from ..services.calc import escolher_cidade_base, calcular_taxas_por_rota
from ..services import audit as aud

router = APIRouter(prefix="/fretes", tags=["Fretes"])

@router.get("")
def listar_fretes(status: Optional[str] = Query(default=None), data_ini: Optional[str] = None, data_fim: Optional[str] = None, cod_veiculo: Optional[int] = None):
    where = ["1=1"]
    params = []
    if status:
        where.append("status = ?")
        params.append(status)
    if data_ini:
        where.append("data_frete >= ?")
        params.append(data_ini)
    if data_fim:
        where.append("data_frete <= ?")
        params.append(data_fim)
    if cod_veiculo:
        where.append("cod_veiculo = ?")
        params.append(cod_veiculo)
    sql = f"SELECT * FROM dbo.frete_lancamento WHERE {' AND '.join(where)} ORDER BY data_frete DESC, id DESC"
    with db.frete_conn() as conn:
        return db.query_all(conn, sql, params)

@router.get("/{id}")
def obter_frete(id: int):
    with db.frete_conn() as conn:
        cab = db.query_one(conn, "SELECT * FROM dbo.frete_lancamento WHERE id=?", [id])
        if not cab:
            raise HTTPException(404, "Frete não encontrado")
        cargas = db.query_all(conn, "SELECT * FROM dbo.frete_lancamento_carga WHERE frete_id=?", [id])
        audit = db.query_all(conn, "SELECT * FROM dbo.frete_lancamento_auditoria WHERE frete_id=? ORDER BY feito_em DESC", [id])
    return {"cabecalho": cab, "cargas": cargas, "auditoria": audit}

@router.post("")
def criar_frete(payload: FreteCreate):
    cidades = list({c.cidade for c in payload.cargas})
    if not cidades:
        raise HTTPException(400, "Selecione ao menos uma carga")
    with db.frete_conn() as conn:
        base_rows = db.query_all(conn, f"SELECT cidade, tipo_veiculo, km, valor_base FROM dbo.parametros_base WHERE tipo_veiculo=? AND cidade IN ({','.join(['?']*len(cidades))}) AND ativo=1", [payload.tipo_veiculo, *cidades])
        taxas_rows = db.query_all(conn, f"SELECT cidade, tipo_veiculo, taxa_tipo, modalidade, valor FROM dbo.parametros_taxas WHERE tipo_veiculo=? AND cidade IN ({','.join(['?']*len(cidades))}) AND ativo=1", [payload.tipo_veiculo, *cidades])
    base_params = {(r['cidade'], r['tipo_veiculo']): {'km': r['km'], 'valor_base': float(r['valor_base'])} for r in base_rows}
    taxas_dict = {}
    for r in taxas_rows:
        key = (r['cidade'], r['tipo_veiculo'])
        taxas_dict.setdefault(key, []).append({'taxa_tipo': r['taxa_tipo'], 'modalidade': r['modalidade'], 'valor': float(r['valor'])})

    cargas_list = [c.model_dump() for c in payload.cargas]
    cidade_base_info = escolher_cidade_base(cargas_list, base_params, payload.tipo_veiculo)
    valor_taxas = calcular_taxas_por_rota(cargas_list, payload.tipo_veiculo, base_params, taxas_dict)
    if payload.override_taxas:
        valor_taxas += sum([float(x.valor) for x in payload.override_taxas])
    valor_base = float(cidade_base_info['valor_base'])

    with db.frete_conn() as conn:
        db.execute(conn, """
            INSERT INTO dbo.frete_lancamento
            (data_frete, cod_veiculo, placa, cod_motorista, motorista, tipo_veiculo,
             cidade_base, km_base, valor_base, valor_taxas, observacoes, criado_por)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, [payload.data_frete, payload.cod_veiculo, payload.placa, payload.cod_motorista, payload.motorista, payload.tipo_veiculo,
               cidade_base_info['cidade'], cidade_base_info['km'], valor_base, valor_taxas, payload.observacoes, payload.criado_por])
        row = db.query_one(conn, "SELECT TOP 1 id FROM dbo.frete_lancamento WHERE cod_veiculo=? ORDER BY id DESC", [payload.cod_veiculo])
        frete_id = row['id']

        to_insert = []
        for c in cargas_list:
            origem = c.get('origem') or 'erp'
            pendencia = 0
            cod_veic_erp = None
            pend_motivo = None
            if origem == 'manual':
                with db.erp_conn() as erp:
                    found = db.query_one(erp, "SELECT TOP 1 PDD.CODVEC AS COD_VEICULO FROM Flexx10071188.dbo.IBETPDDSVCNF_ PDD WHERE PDD.NUMSEQETGPDD = ?", [c['carga_num']])
                if found:
                    cod_veic_erp = int(found['COD_VEICULO'])
                    if cod_veic_erp != payload.cod_veiculo:
                        pendencia = 1
                        pend_motivo = f"Carga pertence ao veículo {cod_veic_erp}, lançada no veículo {payload.cod_veiculo}."
            b = base_params[(c['cidade'], payload.tipo_veiculo)]
            qtd = sum(1 for x in cargas_list if x['cidade'] == c['cidade'])
            total_taxa_cidade = 0.0
            for t in (taxas_dict.get((c['cidade'], payload.tipo_veiculo), [])):
                if t['modalidade'] == 'fixa':
                    total_taxa_cidade += t['valor']
                elif t['modalidade'] == 'por_km':
                    total_taxa_cidade += t['valor'] * b['km']
                elif t['modalidade'] == 'por_carga':
                    total_taxa_cidade += t['valor'] * qtd
            to_insert.append([
                frete_id,
                c['carga_num'],
                c.get('data_cte'),
                c['cidade'],
                b['km'],
                float(b['valor_base']),
                float(round(total_taxa_cidade,2)),
                origem,
                pendencia,
                cod_veic_erp,
                payload.cod_veiculo,
                pend_motivo
            ])
        db.executemany(conn, """
            INSERT INTO dbo.frete_lancamento_carga
            (frete_id, carga_num, data_cte, cidade, km_cidade, valor_base_cidade, valor_taxas_cidade,
             origem, pendencia, cod_veiculo_erp, cod_veiculo_lancado, pendencia_motivo)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, to_insert)

    aud.registrar_auditoria(frete_id, 'create', motivo='Criacao de frete', antes=None, depois={"payload": payload.model_dump()}, feito_por=payload.criado_por)
    return {"id": frete_id, "valor_base": valor_base, "valor_taxas": valor_taxas, "valor_total": round(valor_base+valor_taxas,2)}

@router.put("/{id}")
def atualizar_frete(id: int, payload: FreteUpdate):
    if not payload.motivo:
        raise HTTPException(400, "Motivo é obrigatório")
    with db.frete_conn() as conn:
        antes = {
            "cab": db.query_one(conn, "SELECT * FROM dbo.frete_lancamento WHERE id=?", [id]),
            "cargas": db.query_all(conn, "SELECT * FROM dbo.frete_lancamento_carga WHERE frete_id=?", [id])
        }
        if not antes["cab"]:
            raise HTTPException(404, "Frete não encontrado")
    cab = antes["cab"]
    tipo_veic = payload.tipo_veiculo or cab['tipo_veiculo']

    if payload.cargas is not None:
        cidades = list({c.cidade for c in payload.cargas})
        with db.frete_conn() as conn:
            base_rows = db.query_all(conn, f"SELECT cidade, tipo_veiculo, km, valor_base FROM dbo.parametros_base WHERE tipo_veiculo=? AND cidade IN ({','.join(['?']*len(cidades))}) AND ativo=1", [tipo_veic, *cidades])
            taxas_rows = db.query_all(conn, f"SELECT cidade, tipo_veiculo, taxa_tipo, modalidade, valor FROM dbo.parametros_taxas WHERE tipo_veiculo=? AND cidade IN ({','.join(['?']*len(cidades))}) AND ativo=1", [tipo_veic, *cidades])
        base_params = {(r['cidade'], r['tipo_veiculo']): {'km': r['km'], 'valor_base': float(r['valor_base'])} for r in base_rows}
        taxas_dict = {}
        for r in taxas_rows:
            key = (r['cidade'], r['tipo_veiculo'])
            taxas_dict.setdefault(key, []).append({'taxa_tipo': r['taxa_tipo'], 'modalidade': r['modalidade'], 'valor': float(r['valor'])})
        cargas_list = [c.model_dump() for c in payload.cargas]
        cidade_base_info = escolher_cidade_base(cargas_list, base_params, tipo_veic)
        valor_taxas = calcular_taxas_por_rota(cargas_list, tipo_veic, base_params, taxas_dict)
        if payload.override_taxas:
            valor_taxas += sum([float(x.valor) for x in payload.override_taxas])
        valor_base = float(cidade_base_info['valor_base'])

    with db.frete_conn() as conn:
        campos = []
        params = []
        for col, v in [
            ("data_frete", payload.data_frete),
            ("cod_veiculo", payload.cod_veiculo),
            ("placa", payload.placa),
            ("cod_motorista", payload.cod_motorista),
            ("motorista", payload.motorista),
            ("tipo_veiculo", payload.tipo_veiculo),
            ("observacoes", payload.observacoes)
        ]:
            if v is not None:
                campos.append(f"{col}=?")
                params.append(v)
        if payload.cargas is not None:
            campos.extend(["cidade_base=?", "km_base=?", "valor_base=?", "valor_taxas=?"])
            params.extend([cidade_base_info['cidade'], cidade_base_info['km'], valor_base, valor_taxas])
        if campos:
            db.execute(conn, f"UPDATE dbo.frete_lancamento SET {', '.join(campos)}, atualizado_em=SYSDATETIME(), atualizado_por=? WHERE id=?", params + [payload.atualizado_por, id])
        if payload.cargas is not None:
            db.execute(conn, "DELETE FROM dbo.frete_lancamento_carga WHERE frete_id=?", [id])
            to_insert = []
            for c in [x.model_dump() for x in payload.cargas]:
                origem = c.get('origem') or 'erp'
                pendencia = 0
                cod_veic_erp = None
                pend_motivo = None
                if origem == 'manual':
                    with db.erp_conn() as erp:
                        found = db.query_one(erp, "SELECT TOP 1 PDD.CODVEC AS COD_VEICULO FROM Flexx10071188.dbo.IBETPDDSVCNF_ PDD WHERE PDD.NUMSEQETGPDD = ?", [c['carga_num']])
                    if found:
                        cod_veic_erp = int(found['COD_VEICULO'])
                        alvo = payload.cod_veiculo or cab['cod_veiculo']
                        if cod_veic_erp != alvo:
                            pendencia = 1
                            pend_motivo = f"Carga pertence ao veículo {cod_veic_erp}, lançada no veículo {alvo}."
                b = base_params[(c['cidade'], tipo_veic)]
                qtd = sum(1 for x in [x.model_dump() for x in payload.cargas] if x['cidade'] == c['cidade'])
                total_taxa_cidade = 0.0
                for t in (taxas_dict.get((c['cidade'], tipo_veic), [])):
                    if t['modalidade'] == 'fixa':
                        total_taxa_cidade += t['valor']
                    elif t['modalidade'] == 'por_km':
                        total_taxa_cidade += t['valor'] * b['km']
                    elif t['modalidade'] == 'por_carga':
                        total_taxa_cidade += t['valor'] * qtd
                to_insert.append([
                    id,
                    c['carga_num'],
                    c.get('data_cte'),
                    c['cidade'],
                    b['km'],
                    float(b['valor_base']),
                    float(round(total_taxa_cidade,2)),
                    origem,
                    pendencia,
                    cod_veic_erp,
                    (payload.cod_veiculo or cab['cod_veiculo']),
                    pend_motivo
                ])
            db.executemany(conn, """
                INSERT INTO dbo.frete_lancamento_carga
                (frete_id, carga_num, data_cte, cidade, km_cidade, valor_base_cidade, valor_taxas_cidade,
                 origem, pendencia, cod_veiculo_erp, cod_veiculo_lancado, pendencia_motivo)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, to_insert)

    depois = obter_frete(id)
    aud.registrar_auditoria(id, 'update', payload.motivo, antes, depois, payload.atualizado_por)
    return {"ok": True}

@router.delete("/{id}")
def cancelar_frete(id: int, payload: FreteCancel):
    if not payload.motivo:
        raise HTTPException(400, "Motivo é obrigatório")
    with db.frete_conn() as conn:
        found = db.query_one(conn, "SELECT * FROM dbo.frete_lancamento WHERE id=?", [id])
        if not found:
            raise HTTPException(404, "Frete não encontrado")
        db.execute(conn, """
            UPDATE dbo.frete_lancamento
            SET status='cancelado', cancelado_em=SYSDATETIME(), cancelado_por=?, cancelado_motivo=?
            WHERE id=?
        """, [payload.cancelado_por, payload.motivo, id])
    aud.registrar_auditoria(id, 'cancel', payload.motivo, antes=found, depois=None, feito_por=payload.cancelado_por)
    return {"ok": True}
