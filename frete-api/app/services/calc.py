
from collections import defaultdict
from typing import Dict, List

# Funções de cálculo do frete e taxas

def escolher_cidade_base(cargas: List[dict], base_params: Dict[tuple, dict], tipo_veiculo: str) -> dict:
    """
    Retorna dict {cidade, km, valor_base} da cidade com MAIOR KM entre as cargas.
    base_params indexado por (cidade, tipo_veiculo) -> {km, valor_base}
    """
    maior = {"cidade": None, "km": -1, "valor_base": 0.0}
    for c in cargas:
        chave = (c['cidade'], tipo_veiculo)
        if chave not in base_params:
            raise ValueError(f"Parâmetro base não encontrado para cidade={c['cidade']} tipo={tipo_veiculo}")
        km = base_params[chave]['km']
        if km > maior['km']:
            maior = {"cidade": c['cidade'], "km": km, "valor_base": base_params[chave]['valor_base']}
    return maior

def calcular_taxas_por_rota(cargas: List[dict], tipo_veiculo: str, base_params: Dict[tuple, dict], taxas_params: Dict[tuple, list]) -> float:
    """ Soma taxas de TODAS as cidades das cargas. """
    valor = 0.0
    cidades = {c['cidade'] for c in cargas}
    # quantidade de cargas por cidade
    qtd_por_cidade = defaultdict(int)
    for c in cargas:
        qtd_por_cidade[c['cidade']] += 1

    for cidade in cidades:
        chave = (cidade, tipo_veiculo)
        if chave not in taxas_params:
            continue
        for taxa in taxas_params[chave]:
            mod = taxa['modalidade']
            v = float(taxa['valor'])
            if mod == 'fixa':
                valor += v
            elif mod == 'por_km':
                km = base_params[chave]['km']
                valor += v * km
            elif mod == 'por_carga':
                valor += v * qtd_por_cidade[cidade]
    return round(valor, 2)
