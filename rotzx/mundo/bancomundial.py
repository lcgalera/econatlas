"""Banco Mundial (API v2, licença CC BY 4.0): indicadores anuais por país, o último valor disponível de cada um."""
import json
import time
import urllib.request
from typing import Dict, List

from .. import config

URL = "https://api.worldbank.org/v2/country/{paises}/indicator/{ind}?format=json&mrv=6&per_page=2000"
INDICADORES = {
    "NY.GDP.MKTP.KD.ZG": {"rotulo": "Crescimento do PIB", "unidade": "% no ano"},
    "FP.CPI.TOTL.ZG": {"rotulo": "Inflação (preços ao consumidor)", "unidade": "% no ano"},
    "NY.GDP.MKTP.CD": {"rotulo": "PIB", "unidade": "US$ correntes"},
    "SP.POP.TOTL": {"rotulo": "População", "unidade": "pessoas"},
}


def _get(url: str, tentativas: int = 4):
    req = urllib.request.Request(url, headers={"User-Agent": config.USER_AGENT})
    for t in range(tentativas):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except OSError:
            if t == tentativas - 1:
                raise
            time.sleep(2 ** t)


def indicadores(iso3: List[str]) -> Dict[str, Dict[str, dict]]:
    """{iso3: {indicador: {valor, ano, atualizado}}} com o valor mais recente não nulo de cada indicador."""
    out: Dict[str, Dict[str, dict]] = {i: {} for i in iso3}
    for ind in INDICADORES:
        meta, dados = _get(URL.format(paises=";".join(iso3), ind=ind))
        for d in sorted(dados or [], key=lambda x: x["date"], reverse=True):
            iso = d["countryiso3code"]
            if d["value"] is not None and iso in out and ind not in out[iso]:
                out[iso][ind] = {"valor": float(d["value"]), "ano": d["date"], "atualizado": meta.get("lastupdated")}
    return out
