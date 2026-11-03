"""Backtest com origem móvel (pseudo-fora-da-amostra).

Para cada origem o (último mês observado), cada modelo é estimado só com dados
até o e prevê o+1 … o+12. O erro é comparado com o valor realizado.

Comparação com o Focus: para a origem o, usa-se a última pesquisa Focus
publicada até o dia 15 do mês o+1, data em que o IPCA de o já foi divulgado
(por volta do dia 10). Assim os dois conjuntos de informação incluem y(o).
O Focus ainda tem vantagem informacional (IPCA-15, preços de alta frequência),
o que o torna um benchmark exigente, e não injusto contra ele.

Limitação: usa a versão mais recente da série, não as versões da época.
Para o IPCA isso quase não importa, porque a série não é revisada.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from . import focus, models

HORIZONTES = 12


def run(y: pd.Series, focus_surveys: pd.DataFrame, inicio: str = "2016-01-01",
        errors: Optional[pd.DataFrame] = None) -> Dict:
    """`errors`: histórico de erros do SARIMA (empirico.sarima_errors). Se dado, cada previsão do
    SARIMA ganha também a faixa empírica, montada só com erros já realizados na sua origem."""
    y = y.asfreq("MS").dropna()
    origins = [o for o in y.index if o >= pd.Timestamp(inicio) and o < y.index[-1]]
    rows: List[Dict] = []
    for o in origins:
        hist = y[y.index <= o]
        for nome in models.MODELOS:
            fc = models.run(nome, hist, HORIZONTES)
            for h, (alvo, r) in enumerate(fc.iterrows(), start=1):
                if alvo in y.index:
                    rows.append({"modelo": nome, "origem": o, "h": h, "alvo": alvo, "previsto": r["valor"],
                                 "lo80": r["lo80"], "hi80": r["hi80"], "realizado": y[alvo]})
        if focus_surveys is not None and len(focus_surveys):
            cutoff = o + pd.offsets.MonthBegin(1) + pd.Timedelta(days=14)
            avail = focus_surveys[focus_surveys["data_pesquisa"] <= cutoff]
            if len(avail):
                last = avail["data_pesquisa"].max()
                snap = avail[avail["data_pesquisa"] == last].set_index("referencia")["mediana"]
                for h in range(1, HORIZONTES + 1):
                    alvo = o + pd.DateOffset(months=h)
                    if alvo in y.index and alvo in snap.index:
                        rows.append({"modelo": "focus_mediana", "origem": o, "h": h, "alvo": alvo,
                                     "previsto": snap[alvo], "lo80": np.nan, "hi80": np.nan, "realizado": y[alvo]})
    df = pd.DataFrame(rows)
    df["lo80_emp"] = np.nan
    df["hi80_emp"] = np.nan
    if errors is not None:
        from . import empirico
        for i in df.index[df["modelo"] == "sarima"]:
            b = empirico.band(errors, int(df.at[i, "h"]), df.at[i, "origem"])
            if b:
                df.at[i, "lo80_emp"] = df.at[i, "previsto"] + b[0]
                df.at[i, "hi80_emp"] = df.at[i, "previsto"] + b[1]
    return {"detalhe": df, "resumo": summarize(df)}


def summarize(df: pd.DataFrame) -> List[Dict]:
    out = []
    df = df.assign(erro=df["realizado"] - df["previsto"])
    # comparação justa: só pares (origem, h) em que todos os modelos têm previsão
    common = df.groupby(["origem", "h"])["modelo"].nunique()
    full = common[common == df["modelo"].nunique()].index
    dfc = df.set_index(["origem", "h"]).loc[full].reset_index()
    for (nome, h), g in dfc.groupby(["modelo", "h"]):
        def coverage(lo, hi):
            ok = g[lo].notna()
            if not ok.any():
                return None, 0
            gg = g[ok]
            return float(((gg["realizado"] >= gg[lo]) & (gg["realizado"] <= gg[hi])).mean()), int(ok.sum())
        cov, _ = coverage("lo80", "hi80")
        cov_emp, n_emp = coverage("lo80_emp", "hi80_emp") if "lo80_emp" in g else (None, 0)
        out.append({"modelo": nome, "h": int(h), "n": int(len(g)),
                    "mae": float(g["erro"].abs().mean()), "rmse": float(np.sqrt((g["erro"] ** 2).mean())),
                    "vies": float(g["erro"].mean()), "cobertura80": cov,
                    "cobertura80_emp": cov_emp, "n_cobertura_emp": n_emp})
    return out


def _selecao():
    """Comparação das variantes de janela (antes da escolha) e o holdout 2021–2026, se já calculada."""
    import json
    from .. import config
    f = config.DATA_DIR / "backtests" / "ipca_faixa_selecao.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def run_ipca(conn) -> Dict:
    from .. import storage
    y = storage.load_observations(conn, "ipca_mensal")
    v = storage.latest_vintage(conn, "ipca_mensal")
    from . import empirico
    res = run(y, focus.all_surveys(conn), errors=empirico.sarima_errors(y))
    det = res["detalhe"]
    return {
        "serie_id": "ipca_mensal",
        "vintage_id": v["id"],
        "executado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "origens": [f"{det['origem'].min():%Y-%m}", f"{det['origem'].max():%Y-%m}"],
        "metodo": __doc__.strip(),
        "metodo_faixa_empirica": empirico.__doc__.strip(),
        "faixa_metodo": empirico.METODO,
        "faixa_selecao": _selecao(),
        "modelos": {k: {"rotulo": m["rotulo"], "spec": m["spec"]} for k, m in models.MODELOS.items()}
                   | {"focus_mediana": {"rotulo": "Focus (mediana)", "spec": "última pesquisa até o dia 15 do mês seguinte à origem"}},
        "resumo": res["resumo"],
    }
