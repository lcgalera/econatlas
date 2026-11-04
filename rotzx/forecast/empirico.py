"""Faixa empírica de 80% para o SARIMA do IPCA, por horizonte.

Método (D21):
- a previsão pontual é a do SARIMA de sempre (models.sarima, especificação fixa);
- para o horizonte h, a faixa é previsto + [P10, P90] dos erros fora da amostra do próprio
  SARIMA no MESMO horizonte h;
- só entram erros já realizados na data da previsão: origem o' com o' + h <= origem atual
  (o IPCA do mês-alvo já estava publicado);
- e só os dos últimos 60 meses (mês-alvo dentro da janela), porque o erro do SARIMA mudou de
  patamar: desvio de ~0,2 p.p. em 2008–14 contra 0,4–0,7 em 2018–22;
- mínimo de 36 erros; abaixo disso, sem faixa.

Como a janela foi escolhida (registrado em data/backtests/ipca_faixa_selecao.json): três variantes
declaradas antes de comparar (todos os erros; últimos 60 meses; últimos 36 meses), escolha pela
cobertura mais próxima de 80% nas origens de 2016–2020, resultado reportado em 2021–2026, que não
participou da escolha. A versão anterior (empirica_v1, todos os erros) cobriu 63–71% e foi descartada.

Os erros são guardados em cache (data/backtests/ipca_sarima_erros.json) e só as origens novas são
calculadas. O IPCA não é revisado, então o erro de uma origem passada não muda; se a especificação
do SARIMA mudar, o cache é descartado.
"""
import json
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd

from .. import config
from . import models

METODO = "empirica_v2_60m"
JANELA_MESES = 60
INICIO_ERROS = "2008-01-01"
MIN_ERROS = 36
HORIZONTES = 12
NIVEL = (10, 90)
CACHE_FILE = config.DATA_DIR / "backtests" / "ipca_sarima_erros.json"


def _spec() -> str:
    return models.MODELOS["sarima"]["spec"]


def sarima_errors(y: pd.Series, cache_file=None) -> pd.DataFrame:
    """Previsões do SARIMA feitas em cada origem desde INICIO_ERROS, com o realizado quando já existe.

    Colunas: origem, h, alvo, previsto, realizado, erro.
    `cache_file`: None = CACHE_FILE do módulo (lido na chamada); False = sem cache.
    O cache guarda a série usada; se qualquer mês dela diferir da série atual (revisão, outra série),
    ele é descartado e tudo é recalculado."""
    y = y.asfreq("MS").dropna()
    if cache_file is None:
        cache_file = CACHE_FILE
    serie_atual = {f"{d:%Y-%m}": round(float(v), 6) for d, v in y.items()}
    cache = {}
    if cache_file and Path(cache_file).exists():
        c = json.loads(Path(cache_file).read_text(encoding="utf-8"))
        antiga = c.get("serie", {})
        mesma_serie = all(serie_atual.get(k) == v for k, v in antiga.items()) and antiga
        if c.get("spec") == _spec() and mesma_serie:
            cache = c["origens"]
    origins = [o for o in y.index if o >= pd.Timestamp(INICIO_ERROS)]
    changed = False
    for o in origins:
        key = f"{o:%Y-%m}"
        if key in cache:
            continue
        fc = models.run("sarima", y[y.index <= o], HORIZONTES)
        cache[key] = [round(float(v), 6) for v in fc["valor"]]
        changed = True
    if cache_file and changed:
        Path(cache_file).parent.mkdir(parents=True, exist_ok=True)
        Path(cache_file).write_text(json.dumps({"spec": _spec(), "serie": serie_atual, "origens": cache}), encoding="utf-8")
    rows = []
    for key, prev in cache.items():
        o = pd.Timestamp(key + "-01")
        if o not in y.index:  # origem fora da série atual (ex.: série de teste diferente)
            continue
        for h, p in enumerate(prev, start=1):
            alvo = o + pd.DateOffset(months=h)
            real = y.get(alvo)
            rows.append({"origem": o, "h": h, "alvo": alvo, "previsto": p,
                         "realizado": None if real is None else float(real)})
    df = pd.DataFrame(rows)
    df["erro"] = df["realizado"] - df["previsto"]
    return df


def band(errors: pd.DataFrame, h: int, origem: pd.Timestamp) -> Optional[Tuple[float, float, int]]:
    """(P10, P90, n) dos erros no horizonte h já realizados na origem; None se houver menos de MIN_ERROS."""
    e = errors[(errors["h"] == h) & (errors["alvo"] <= origem) & (errors["origem"] < origem)
               & (errors["alvo"] > origem - pd.DateOffset(months=JANELA_MESES))]["erro"].dropna()
    if len(e) < MIN_ERROS:
        return None
    lo, hi = np.percentile(e, NIVEL)
    return float(lo), float(hi), int(len(e))
