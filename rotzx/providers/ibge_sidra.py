"""IBGE – SIDRA (API de valores).

O `codigo` no catálogo é o caminho da consulta sem o período, por exemplo
"t/5436/n1/all/v/5932/c2/6794". O período "/p/all" é acrescentado aqui.
A consulta deve devolver exatamente um valor por período; se vier mais de um,
o catálogo está mal especificado e a importação é recusada.
"""
import json
import urllib.request

import pandas as pd

from .. import config
from . import FetchResult

BASE = "https://apisidra.ibge.gov.br/values/{codigo}/p/all"


def _period_to_date(code: str, kind: str) -> pd.Timestamp:
    year = int(code[:4])
    n = int(code[4:])
    if kind == "trimestre":
        return pd.Timestamp(year=year, month=3 * (n - 1) + 1, day=1)
    if kind == "mes":
        return pd.Timestamp(year=year, month=n, day=1)
    if kind == "ano":
        return pd.Timestamp(year=year, month=1, day=1)
    raise ValueError(f"tipo de período não suportado: {kind}")


def parse(rows: list) -> pd.DataFrame:
    header, body = rows[0], rows[1:]
    period_key, kind = None, None
    for key, label in header.items():
        low = label.lower()
        if key.endswith("C") and "(código)" in low:
            if low.startswith("trimestre"):
                period_key, kind = key, "trimestre"
            elif low.startswith("mês"):
                period_key, kind = key, "mes"
            elif low.startswith("ano"):
                period_key, kind = key, "ano"
    if period_key is None:
        raise ValueError("não encontrei a dimensão de período na resposta do SIDRA")
    out = []
    for r in body:
        try:
            value = float(r["V"])
        except (TypeError, ValueError):
            continue  # "..", "-", "X" = sem dado / sigilo
        out.append((_period_to_date(r[period_key], kind), value))
    df = pd.DataFrame(out, columns=["date", "value"])
    if df["date"].duplicated().any():
        raise ValueError("consulta SIDRA devolveu mais de um valor por período; especifique variáveis/classificações")
    return df.sort_values("date").reset_index(drop=True)


def fetch(meta) -> FetchResult:
    url = BASE.format(codigo=meta.codigo.strip("/"))
    req = urllib.request.Request(url, headers={"User-Agent": config.USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read()
    return FetchResult(raw=raw, raw_ext="json", source_url=url, data=parse(json.loads(raw)))
