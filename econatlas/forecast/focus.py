"""Expectativas de mercado (relatório Focus/BCB) para o IPCA mensal.

API pública Olinda: ExpectativaMercadoMensais. Usa baseCalculo = 0 (respostas
dos últimos 30 dias, a estatística divulgada no relatório Focus).
Cada coleta arquiva a resposta bruta; a tabela guarda a união das pesquisas
(valores passados do Focus não são revisados).
"""
import hashlib
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Optional

import pandas as pd

from .. import config

URL = "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/ExpectativaMercadoMensais"
SCHEMA = """
CREATE TABLE IF NOT EXISTS focus_ipca_mensal (
    data_pesquisa TEXT NOT NULL,
    referencia TEXT NOT NULL,      -- 1º dia do mês-alvo (YYYY-MM-01)
    mediana REAL NOT NULL,
    media REAL,
    respondentes INTEGER,
    raw_sha256 TEXT NOT NULL,
    PRIMARY KEY (data_pesquisa, referencia)
);
"""


def ensure_schema(conn):
    conn.executescript(SCHEMA)


def update(conn, since: Optional[str] = None) -> dict:
    ensure_schema(conn)
    last = conn.execute("SELECT MAX(data_pesquisa) FROM focus_ipca_mensal").fetchone()[0]
    since = since or last or "2015-01-01"
    params = {
        "$filter": f"Indicador eq 'IPCA' and baseCalculo eq 0 and Data ge '{since}'",
        "$select": "Data,DataReferencia,Mediana,Media,numeroRespondentes",
        "$format": "json",
    }
    url = URL + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    req = urllib.request.Request(url, headers={"User-Agent": config.USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read()
    sha = hashlib.sha256(raw).hexdigest()
    now = datetime.now(timezone.utc)
    path = config.RAW_DIR / "bcb_focus" / "ipca_mensal" / f"{now:%Y%m%dT%H%M%S}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    rows = []
    for r in json.loads(raw)["value"]:
        m, y = r["DataReferencia"].split("/")
        rows.append((r["Data"], f"{y}-{m}-01", r["Mediana"], r["Media"], r["numeroRespondentes"], sha))
    before = conn.total_changes
    conn.executemany("INSERT OR IGNORE INTO focus_ipca_mensal VALUES (?,?,?,?,?,?)", rows)
    conn.commit()
    return {"recebidos": len(rows), "novos": conn.total_changes - before, "arquivo": str(path.relative_to(config.ROOT))}


def snapshot(conn, as_of: str) -> pd.DataFrame:
    """Medianas da última pesquisa disponível em `as_of` (inclusive), por mês-alvo."""
    ensure_schema(conn)
    d = conn.execute("SELECT MAX(data_pesquisa) FROM focus_ipca_mensal WHERE data_pesquisa <= ?", (as_of,)).fetchone()[0]
    if d is None:
        return pd.DataFrame(columns=["data_pesquisa", "mediana"])
    rows = conn.execute(
        "SELECT referencia, mediana, data_pesquisa FROM focus_ipca_mensal WHERE data_pesquisa = ?", (d,)
    ).fetchall()
    df = pd.DataFrame([dict(r) for r in rows])
    df.index = pd.to_datetime(df.pop("referencia"))
    return df.sort_index()


def all_surveys(conn) -> pd.DataFrame:
    ensure_schema(conn)
    df = pd.read_sql("SELECT data_pesquisa, referencia, mediana FROM focus_ipca_mensal", conn)
    df["data_pesquisa"] = pd.to_datetime(df["data_pesquisa"])
    df["referencia"] = pd.to_datetime(df["referencia"])
    return df
