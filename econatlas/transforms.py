"""Transformações declaradas.

Cada transformação tem um identificador, um rótulo, a fórmula em texto (exibida
ao usuário) e uma regra de aplicabilidade. Nada é calculado "escondido": a API
sempre devolve qual transformação foi aplicada.

As defasagens usam o calendário da série (asfreq), não a posição da linha,
para que meses faltantes não produzam variações erradas.
"""
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd

FREQ = {"mensal": ("MS", 12), "trimestral": ("QS", 4), "anual": ("YS", 1)}


@dataclass
class Transform:
    id: str
    rotulo: str
    formula: str
    unidade: Callable[[str], str]
    aplicavel: Callable[[object], bool]


def _regular(s: pd.Series, periodicidade: str) -> pd.Series:
    if periodicidade not in FREQ:
        raise ValueError(f"transformação não definida para periodicidade '{periodicidade}'")
    return s.asfreq(FREQ[periodicidade][0])


def _periods_per_year(periodicidade: str) -> int:
    return FREQ[periodicidade][1]


def _is_rate_per_period(meta) -> bool:
    return meta.unidade.startswith("% a.m.")


def _is_level(meta) -> bool:
    return not meta.unidade.startswith("%")


TRANSFORMS: Dict[str, Transform] = {
    t.id: t
    for t in [
        Transform("nivel", "Nível (dado original)", "x(t)", lambda u: u, lambda m: True),
        Transform(
            "var_periodo", "Variação % no período", "(x(t)/x(t-1) - 1) × 100",
            lambda u: "%", lambda m: m.periodicidade in FREQ and _is_level(m),
        ),
        Transform(
            "var_anual", "Variação % em 12 meses / mesmo período do ano anterior",
            "(x(t)/x(t-n) - 1) × 100, n = períodos por ano",
            lambda u: "%", lambda m: m.periodicidade in ("mensal", "trimestral") and _is_level(m),
        ),
        Transform(
            "acum_12m", "Acumulado em 12 meses", "(∏ (1 + x(t-i)/100), i=0..11 − 1) × 100",
            lambda u: "%", lambda m: m.periodicidade == "mensal" and _is_rate_per_period(m),
        ),
        Transform(
            "diff_anual", "Diferença em relação ao ano anterior", "x(t) − x(t−n)",
            lambda u: "p.p." if u.startswith("%") else u,
            lambda m: m.periodicidade in ("mensal", "trimestral"),
        ),
        Transform(
            "mm3", "Média móvel de 3 períodos", "(x(t) + x(t−1) + x(t−2)) / 3",
            lambda u: u, lambda m: m.periodicidade in ("mensal", "trimestral"),
        ),
        Transform(
            "media_mensal", "Média mensal", "média de x no mês",
            lambda u: u, lambda m: m.periodicidade == "diaria",
        ),
        Transform(
            "deflacionado_ipca", "Deflacionado pelo IPCA (R$ do último mês)",
            "x(t) × I(último) / I(t), I = número-índice do IPCA",
            lambda u: u.replace("(nominal)", "(reais, IPCA)"),
            lambda m: m.periodicidade == "mensal" and "nominal" in m.unidade,
        ),
    ]
}


def available(meta) -> List[Dict]:
    return [
        {"id": t.id, "rotulo": t.rotulo, "formula": t.formula}
        for t in TRANSFORMS.values()
        if t.aplicavel(meta)
    ]


def ipca_index(ipca_mensal: pd.Series) -> pd.Series:
    """Número-índice a partir das variações mensais (base arbitrária)."""
    return (1 + _regular(ipca_mensal, "mensal") / 100).cumprod()


def apply(s: pd.Series, meta, transform_id: str, deflator: Optional[pd.Series] = None) -> pd.Series:
    t = TRANSFORMS.get(transform_id)
    if t is None:
        raise ValueError(f"transformação desconhecida: {transform_id}")
    if not t.aplicavel(meta):
        raise ValueError(f"'{t.rotulo}' não se aplica à série {meta.id}")
    if transform_id == "nivel":
        return s
    if transform_id == "media_mensal":
        return s.resample("MS").mean()

    r = _regular(s, meta.periodicidade)
    if transform_id == "var_periodo":
        out = (r / r.shift(1) - 1) * 100
    elif transform_id == "var_anual":
        out = (r / r.shift(_periods_per_year(meta.periodicidade)) - 1) * 100
    elif transform_id == "acum_12m":
        out = (np.exp(np.log1p(r / 100).rolling(12, min_periods=12).sum()) - 1) * 100
    elif transform_id == "diff_anual":
        out = r - r.shift(_periods_per_year(meta.periodicidade))
    elif transform_id == "mm3":
        out = r.rolling(3, min_periods=3).mean()
    elif transform_id == "deflacionado_ipca":
        if deflator is None:
            raise ValueError("deflacionar exige a série ipca_mensal")
        idx = ipca_index(deflator).reindex(r.index)
        last = (idx.dropna().index.intersection(r.dropna().index)).max()
        out = r * idx.loc[last] / idx
        out.attrs["base"] = f"{last:%Y-%m}"
    else:  # pragma: no cover
        raise ValueError(transform_id)
    return out.dropna()
