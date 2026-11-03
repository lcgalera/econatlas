"""Modelos de previsão para séries mensais (inicialmente: IPCA, variação mensal).

Todos recebem o histórico observado até a origem (série mensal regular) e o
horizonte, e devolvem um DataFrame indexado pelos meses-alvo com as colunas
`valor`, `lo80` e `hi80`. O intervalo fica vazio (NaN) quando o modelo não
tem um intervalo defensável.

Especificações fixas, escolhidas antes do backtest, para evitar seleção de
modelo com olhar no resultado:
- ingenuo:          y(t+k) = y(t)
- sazonal_ingenuo:  y(t+k) = y(t+k−12)
- sarima:           SARIMA(1,0,0)(1,0,0)[12] com constante, estimado de jan/2004 até a origem
"""
import warnings
from typing import Callable, Dict

import numpy as np
import pandas as pd

ESTIMATION_START = "2004-01-01"  # pós-choque de 2002–03; regime de metas já consolidado


def _target_index(y: pd.Series, h: int) -> pd.DatetimeIndex:
    return pd.date_range(y.index[-1] + pd.offsets.MonthBegin(1), periods=h, freq="MS")


def ingenuo(y: pd.Series, h: int) -> pd.DataFrame:
    idx = _target_index(y, h)
    return pd.DataFrame({"valor": y.iloc[-1], "lo80": np.nan, "hi80": np.nan}, index=idx)


def sazonal_ingenuo(y: pd.Series, h: int) -> pd.DataFrame:
    if h > 12:
        raise ValueError("sazonal ingênuo definido até 12 meses")
    idx = _target_index(y, h)
    vals = [y.get(d - pd.DateOffset(years=1), np.nan) for d in idx]
    return pd.DataFrame({"valor": vals, "lo80": np.nan, "hi80": np.nan}, index=idx)


def sarima(y: pd.Series, h: int) -> pd.DataFrame:
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    sample = y[y.index >= ESTIMATION_START].asfreq("MS")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = SARIMAX(sample, order=(1, 0, 0), seasonal_order=(1, 0, 0, 12), trend="c").fit(disp=False)
        fc = fit.get_forecast(h)
    ci = fc.conf_int(alpha=0.20)
    return pd.DataFrame(
        {"valor": fc.predicted_mean.values, "lo80": ci.iloc[:, 0].values, "hi80": ci.iloc[:, 1].values},
        index=_target_index(y, h),
    )


MODELOS: Dict[str, Dict] = {
    "ingenuo": {"fn": ingenuo, "rotulo": "Ingênuo (último valor)", "spec": "y(t+k) = y(t)"},
    "sazonal_ingenuo": {"fn": sazonal_ingenuo, "rotulo": "Sazonal ingênuo", "spec": "y(t+k) = y(t+k−12)"},
    "sarima": {"fn": sarima, "rotulo": "SARIMA(1,0,0)(1,0,0)[12]",
               "spec": f"SARIMAX order=(1,0,0) seasonal=(1,0,0,12) trend=c, amostra desde {ESTIMATION_START[:7]}"},
}


def run(nome: str, y: pd.Series, h: int) -> pd.DataFrame:
    fn: Callable = MODELOS[nome]["fn"]
    return fn(y.asfreq("MS"), h)
