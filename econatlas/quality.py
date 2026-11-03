"""Verificações de qualidade dos dados.

Cada verificação devolve um dicionário com nome, resultado (ok/alerta/erro/sem_dados),
descrição do método e números que sustentam o resultado.
"""
from typing import Dict, List

import pandas as pd

from . import storage, transforms


def check_ipca_consistency(conn, catalog, tolerance_pp: float = 0.05) -> Dict:
    """IPCA 12m publicado (SGS 13522) × IPCA 12m calculado a partir das variações mensais (SGS 433)."""
    name = "IPCA 12m: publicado × calculado das variações mensais"
    mensal = storage.load_observations(conn, "ipca_mensal")
    publicado = storage.load_observations(conn, "ipca_12m")
    if mensal.empty or publicado.empty:
        return {"verificacao": name, "resultado": "sem_dados"}
    calculado = transforms.apply(mensal, catalog["ipca_mensal"], "acum_12m")
    both = pd.concat([calculado.rename("calc"), publicado.rename("pub")], axis=1).dropna()
    both = both[both.index >= "2000-01-01"]  # antes disso, hiperinflação e mudanças de moeda distorcem a comparação
    diff = (both["calc"] - both["pub"]).abs()
    worst = diff.idxmax()
    return {
        "verificacao": name,
        "resultado": "ok" if diff.max() <= tolerance_pp else "alerta",
        "metodo": "acumula 12 variações mensais e compara com a série publicada, de 2000 em diante; "
                  f"tolerância de {tolerance_pp} p.p. (arredondamento das variações a 2 casas)",
        "n_meses": int(len(both)),
        "maior_diferenca_pp": round(float(diff.max()), 4),
        "mes_maior_diferenca": f"{worst:%Y-%m}",
        "diferenca_media_pp": round(float(diff.mean()), 4),
    }


def check_staleness(conn, catalog) -> List[Dict]:
    """Séries cuja última observação está mais atrasada do que o normal para a periodicidade."""
    limits = {"diaria": 10, "mensal": 120, "trimestral": 200, "anual": 550}
    today = pd.Timestamp.today().normalize()
    out = []
    for meta in catalog.values():
        v = storage.latest_vintage(conn, meta.id)
        if v is None:
            out.append({"verificacao": f"Atualidade: {meta.id}", "resultado": "sem_dados"})
            continue
        lag = (today - pd.Timestamp(v["last_date"])).days
        out.append({
            "verificacao": f"Atualidade: {meta.id}",
            "resultado": "ok" if lag <= limits[meta.periodicidade] else "alerta",
            "metodo": f"dias desde a última observação ≤ {limits[meta.periodicidade]} ({meta.periodicidade})",
            "ultima_observacao": v["last_date"],
            "dias": int(lag),
        })
    return out


def run_all(conn, catalog) -> List[Dict]:
    return [check_ipca_consistency(conn, catalog)] + check_staleness(conn, catalog)
