"""Banco Central do Brasil – Sistema Gerenciador de Séries Temporais (SGS).

API pública: https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados?formato=json
O BCB limita consultas a janelas de até 10 anos, então a busca é feita em blocos.
"""
import json
import time
import urllib.request
from datetime import date
from typing import List

import pandas as pd

from .. import config
from . import FetchResult

BASE = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados?formato=json&dataInicial={ini}&dataFinal={fim}"
WINDOW_YEARS = 10


def _windows(start: date, end: date):
    cur = start
    while cur <= end:
        nxt = date(min(cur.year + WINDOW_YEARS, 9999), cur.month, 1)
        last = min(end, date.fromordinal(nxt.toordinal() - 1))
        yield cur, last
        cur = nxt


def _get(url: str, tries: int = 4) -> list:
    """GET com novas tentativas: a API do SGS às vezes demora ou responde vazio."""
    req = urllib.request.Request(url, headers={"User-Agent": config.USER_AGENT, "Accept": "application/json"})
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = resp.read()
            parsed = json.loads(body)
            break
        except (OSError, ValueError):
            if attempt == tries - 1:
                raise
            time.sleep(2 ** attempt)
    if isinstance(parsed, dict):  # o BCB responde com objeto de erro, p.ex. janela sem dados
        return []
    return parsed


def parse(records: List[dict]) -> pd.DataFrame:
    df = pd.DataFrame(records, columns=["data", "valor"])
    df["date"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
    df["value"] = pd.to_numeric(df["valor"], errors="coerce")
    df = df.dropna(subset=["value"]).drop_duplicates("date", keep="last")
    return df[["date", "value"]].sort_values("date").reset_index(drop=True)


def fetch(meta) -> FetchResult:
    start = date.fromisoformat(meta.inicio) if meta.inicio else date(1980, 1, 1)
    end = date.today()
    chunks = []
    records: List[dict] = []
    for ini, fim in _windows(start, end):
        url = BASE.format(codigo=meta.codigo, ini=ini.strftime("%d/%m/%Y"), fim=fim.strftime("%d/%m/%Y"))
        part = _get(url)
        chunks.append({"url": url, "body": part})
        records.extend(part)
    raw = json.dumps({"provedor": "bcb_sgs", "codigo": meta.codigo, "requisicoes": chunks}, ensure_ascii=False).encode()
    source = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{meta.codigo}/dados"
    return FetchResult(raw=raw, raw_ext="json", source_url=source, data=parse(records))
