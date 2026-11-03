"""BCB – Expectativas de mercado para a inflação dos próximos 12 meses (pesquisa Focus).

API Olinda: ExpectativasMercadoInflacao12Meses. O `codigo` no catálogo é o indicador
(ex.: "IPCA"). Usa a mediana suavizada (Suavizada = 'S') com baseCalculo = 0
e agrega as pesquisas diárias em média mensal.
"""
import json
import urllib.parse
import urllib.request

import pandas as pd

from .. import config
from . import FetchResult

URL = "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/ExpectativasMercadoInflacao12Meses"


def parse(records) -> pd.DataFrame:
    df = pd.DataFrame(records)
    df = df[(df["Suavizada"] == "S") & (df["baseCalculo"] == 0)]
    s = df.assign(date=pd.to_datetime(df["Data"])).set_index("date")["Mediana"].astype(float)
    monthly = s.resample("MS").mean().dropna()
    return pd.DataFrame({"date": monthly.index, "value": monthly.values})


def fetch(meta) -> FetchResult:
    params = {
        "$filter": f"Indicador eq '{meta.codigo}'",
        "$select": "Data,Suavizada,Mediana,baseCalculo",
        "$format": "json",
    }
    url = URL + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    req = urllib.request.Request(url, headers={"User-Agent": config.USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read()
    return FetchResult(raw=raw, raw_ext="json", source_url=url, data=parse(json.loads(raw)["value"]))
