"""Armazenamento com rastreabilidade.

- Cada coleta bem-sucedida que traz dados diferentes da anterior vira uma *vintage*
  (versão), com data de coleta, origem, caminho do arquivo bruto e SHA-256.
- As observações são guardadas por vintage, o que permite ver revisões e,
  no futuro, fazer backtests apenas com dados disponíveis em cada data.
- O arquivo bruto vai para data/raw/<provedor>/<série>/<timestamp>.<ext> e nunca é alterado.
"""
import hashlib
import sqlite3
from datetime import datetime, timezone
from typing import Dict, List, Optional

import pandas as pd

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS vintages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    series_id TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    provider TEXT NOT NULL,
    source_url TEXT NOT NULL,
    raw_path TEXT NOT NULL,
    raw_sha256 TEXT NOT NULL,
    data_sha256 TEXT NOT NULL,
    n_obs INTEGER NOT NULL,
    first_date TEXT,
    last_date TEXT,
    n_new INTEGER NOT NULL,
    n_revised INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS observations (
    series_id TEXT NOT NULL,
    vintage_id INTEGER NOT NULL REFERENCES vintages(id),
    date TEXT NOT NULL,
    value REAL NOT NULL,
    PRIMARY KEY (series_id, vintage_id, date)
);
CREATE INDEX IF NOT EXISTS ix_vintages_series ON vintages(series_id, id);
"""


def connect(db_file=None) -> sqlite3.Connection:
    path = db_file or config.DB_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    if db_file is None and not path.exists() and config.DB_FILE_ANTIGO.exists():
        config.DB_FILE_ANTIGO.rename(path)  # banco criado antes da troca de nome (D35)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def _data_hash(df: pd.DataFrame) -> str:
    payload = "\n".join(f"{d:%Y-%m-%d};{v!r}" for d, v in zip(df["date"], df["value"]))
    return hashlib.sha256(payload.encode()).hexdigest()


def latest_vintage(conn, series_id: str) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM vintages WHERE series_id = ? ORDER BY id DESC LIMIT 1", (series_id,)
    ).fetchone()


def save_fetch(conn, meta, result, raw_dir=None) -> Dict:
    """Grava uma coleta. Retorna um resumo; não cria vintage se nada mudou."""
    df = result.data
    if df.empty:
        raise ValueError(f"{meta.id}: provedor não devolveu observações")
    data_sha = _data_hash(df)
    prev = latest_vintage(conn, meta.id)
    if prev is not None and prev["data_sha256"] == data_sha:
        return {"series_id": meta.id, "status": "sem_alteracao", "vintage_id": prev["id"], "n_obs": prev["n_obs"]}

    now = datetime.now(timezone.utc)
    raw_dir = raw_dir or config.RAW_DIR
    raw_path = raw_dir / meta.provedor / meta.id / f"{now:%Y%m%dT%H%M%S}.{result.raw_ext}"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_bytes(result.raw)

    n_new, n_revised = len(df), 0
    if prev is not None:
        old = load_observations(conn, meta.id, prev["id"])
        merged = df.set_index("date")["value"].to_frame("new").join(old.rename("old"), how="left")
        n_new = int(merged["old"].isna().sum())
        both = merged.dropna()
        n_revised = int(((both["new"] - both["old"]).abs() > 1e-12).sum())

    cur = conn.execute(
        """INSERT INTO vintages (series_id, fetched_at, provider, source_url, raw_path, raw_sha256,
               data_sha256, n_obs, first_date, last_date, n_new, n_revised)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            meta.id, now.isoformat(timespec="seconds"), meta.provedor, result.source_url,
            str(raw_path.relative_to(config.ROOT) if raw_path.is_relative_to(config.ROOT) else raw_path),
            hashlib.sha256(result.raw).hexdigest(), data_sha, len(df),
            f"{df['date'].min():%Y-%m-%d}", f"{df['date'].max():%Y-%m-%d}", n_new, n_revised,
        ),
    )
    vid = cur.lastrowid
    conn.executemany(
        "INSERT INTO observations (series_id, vintage_id, date, value) VALUES (?,?,?,?)",
        [(meta.id, vid, f"{d:%Y-%m-%d}", float(v)) for d, v in zip(df["date"], df["value"])],
    )
    conn.commit()
    return {"series_id": meta.id, "status": "nova_versao", "vintage_id": vid, "n_obs": len(df),
            "n_new": n_new, "n_revised": n_revised}


def load_observations(conn, series_id: str, vintage_id: Optional[int] = None) -> pd.Series:
    """Série (índice = data) da vintage pedida ou da mais recente."""
    if vintage_id is None:
        v = latest_vintage(conn, series_id)
        if v is None:
            return pd.Series(dtype=float, name=series_id)
        vintage_id = v["id"]
    rows = conn.execute(
        "SELECT date, value FROM observations WHERE series_id = ? AND vintage_id = ? ORDER BY date",
        (series_id, vintage_id),
    ).fetchall()
    s = pd.Series([r["value"] for r in rows], index=pd.to_datetime([r["date"] for r in rows]), name=series_id)
    s.index.name = "date"
    return s


def list_vintages(conn, series_id: str) -> List[Dict]:
    rows = conn.execute("SELECT * FROM vintages WHERE series_id = ? ORDER BY id DESC", (series_id,)).fetchall()
    return [dict(r) for r in rows]
