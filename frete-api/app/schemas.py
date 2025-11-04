
from typing import List, Optional
from pydantic import BaseModel, Field

class CargaIn(BaseModel):
    carga_num: int
    cidade: str
    data_cte: Optional[str] = None
    origem: Optional[str] = Field(default="erp", pattern="^(erp|manual)$")

class OverrideTaxa(BaseModel):
    cidade: str
    taxa_tipo: str
    valor: float

class FreteCreate(BaseModel):
    data_frete: str
    cod_veiculo: int
    placa: str
    cod_motorista: Optional[int] = None
    motorista: Optional[str] = None
    tipo_veiculo: str
    cargas: List[CargaIn]
    override_taxas: Optional[List[OverrideTaxa]] = None
    observacoes: Optional[str] = None
    criado_por: Optional[str] = None

class FreteUpdate(BaseModel):
    motivo: str
    data_frete: Optional[str] = None
    cod_veiculo: Optional[int] = None
    placa: Optional[str] = None
    cod_motorista: Optional[int] = None
    motorista: Optional[str] = None
    tipo_veiculo: Optional[str] = None
    cargas: Optional[List[CargaIn]] = None
    override_taxas: Optional[List[OverrideTaxa]] = None
    observacoes: Optional[str] = None
    atualizado_por: Optional[str] = None

class FreteCancel(BaseModel):
    motivo: str
    cancelado_por: Optional[str] = None
