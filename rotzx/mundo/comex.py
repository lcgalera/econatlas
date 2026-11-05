"""Comex Stat (MDIC): exportações e importações brasileiras por país e por produto (SH4), em US$ FOB.

A API devolve 429 com frequência a partir de IPs compartilhados; as chamadas são espaçadas (INTERVALO) e repetidas com espera
crescente. O formato de consulta que funciona é o "filter" em GET (conferido em 04/11/2026): o POST /general respondeu 429 em
todas as tentativas. Cada resposta bruta é guardada em data/fontes/mundo/comex/ com SHA-256 no nome.
"""
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

from .. import config

BASE = "https://api-comexstat.mdic.gov.br/general?filter="
INTERVALO = 12.0  # segundos entre chamadas
FLUXO = {"exportacao": 1, "importacao": 2}
_ultima = [0.0]


def _filtro(ano: str, fluxo: str, detalhe: str, pais: Optional[str] = None) -> dict:
    f = {"yearStart": ano, "yearEnd": ano, "typeForm": FLUXO[fluxo], "typeOrder": 2, "filterList": [], "filterArray": [],
         "rangeFilter": [], "detailDatabase": [{"id": detalhe, "text": ""}], "monthDetail": False, "metricFOB": True,
         "metricKG": False, "metricStatistic": False, "monthStart": "01", "monthEnd": "12", "formQueue": "general", "langDefault": "pt"}
    if pais:
        f["filterList"] = [{"id": "noPaispt"}]
        f["filterArray"] = [{"item": [pais], "idInput": "noPaispt"}]
    return f


def _get(filtro: dict, pasta: Optional[Path] = None, tentativas: int = 5) -> List[dict]:
    url = BASE + urllib.parse.quote(json.dumps(filtro, ensure_ascii=False))
    req = urllib.request.Request(url, headers={"User-Agent": config.USER_AGENT})
    espera = INTERVALO
    for t in range(tentativas):
        falta = INTERVALO - (time.time() - _ultima[0])
        if falta > 0:
            time.sleep(falta)
        _ultima[0] = time.time()
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                corpo = r.read()
            break
        except urllib.error.HTTPError as e:
            if e.code != 429 or t == tentativas - 1:
                raise
            time.sleep(espera)
            espera *= 2
    if pasta:
        pasta.mkdir(parents=True, exist_ok=True)
        (pasta / f"{hashlib.sha256(corpo).hexdigest()[:12]}.json").write_bytes(corpo)
    return json.loads(corpo)["data"]["list"]


def por_pais(ano: str, fluxo: str, pasta: Optional[Path] = None) -> Dict[str, float]:
    """US$ FOB por país (nome do Comex Stat), num ano e fluxo."""
    return {x["noPaispt"]: float(x["vlFob"]) for x in _get(_filtro(ano, fluxo, "noPaispt"), pasta)}


def produtos(ano: str, fluxo: str, pais_comex: str, top: int = 5, pasta: Optional[Path] = None) -> List[dict]:
    """Principais produtos (SH4) num ano e fluxo para um país, com a participação no total do país."""
    lista = _get(_filtro(ano, fluxo, "noSh4pt", pais_comex), pasta)
    total = sum(float(x["vlFob"]) for x in lista) or 1.0
    lista = sorted(lista, key=lambda x: -float(x["vlFob"]))[:top]
    return [{"sh4": x["coSh4"], "produto": x["noSh4pt"], "fob": float(x["vlFob"]), "participacao": float(x["vlFob"]) / total} for x in lista]


def serie(ano_ini: str, ano_fim: str, fluxo: str, pasta: Optional[Path] = None) -> Dict[tuple, float]:
    """US$ FOB por (país, ano) de ano_ini a ano_fim numa consulta só: a API devolve uma linha por ano (coAno) (D46)."""
    f = _filtro(ano_ini, fluxo, "noPaispt")
    f["yearEnd"] = ano_fim
    return {(x["noPaispt"], int(x["coAno"])): float(x["vlFob"]) for x in _get(f, pasta)}


def produtos_todos(ano: str, fluxo: str, pasta: Optional[Path] = None) -> Dict[str, List[tuple]]:
    """Todos os pares país × produto (SH4) de um ano numa consulta só: {país: [(sh4, nome do produto, US$ FOB)]} (D46)."""
    f = _filtro(ano, fluxo, "noPaispt")
    f["detailDatabase"] = [{"id": "noPaispt", "text": ""}, {"id": "noSh4pt", "text": ""}]
    out: Dict[str, List[tuple]] = {}
    for x in _get(f, pasta):
        out.setdefault(x["noPaispt"], []).append((x["coSh4"], x["noSh4pt"].replace("\xa0", " "), float(x["vlFob"])))
    return out
