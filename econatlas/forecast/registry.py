"""Registro imutável de previsões.

Cada previsão fica gravada com o modelo, a especificação, a versão dos dados usada,
a origem e o horário. Gatilhos no SQLite impedem UPDATE e DELETE: uma previsão
errada continua registrada. Previsões repetidas para a mesma (modelo, série,
origem, alvo) são ignoradas, ou seja, vale a primeira.

A avaliação é feita na leitura, comparando com a versão mais recente da série.
"""
from datetime import datetime, timezone
from typing import Dict, List

import numpy as np
import pandas as pd

from .. import __version__, storage
from . import empirico, focus, models

SCHEMA = """
CREATE TABLE IF NOT EXISTS previsoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    registrado_em TEXT NOT NULL,
    serie_id TEXT NOT NULL,
    modelo TEXT NOT NULL,
    especificacao TEXT NOT NULL,
    versao_codigo TEXT NOT NULL,
    vintage_id INTEGER,
    origem TEXT NOT NULL,
    alvo TEXT NOT NULL,
    horizonte INTEGER NOT NULL,
    valor REAL NOT NULL,
    lo80 REAL,
    hi80 REAL,
    UNIQUE (modelo, serie_id, origem, alvo)
);
CREATE TRIGGER IF NOT EXISTS previsoes_sem_update BEFORE UPDATE ON previsoes
BEGIN SELECT RAISE(ABORT, 'previsões registradas são imutáveis'); END;
CREATE TRIGGER IF NOT EXISTS previsoes_sem_delete BEFORE DELETE ON previsoes
BEGIN SELECT RAISE(ABORT, 'previsões registradas são imutáveis'); END;
"""


def ensure_schema(conn):
    conn.executescript(SCHEMA)
    # coluna acrescentada em 03/11/2026 (D21). ADD COLUMN não reescreve linhas nem dispara o gatilho de
    # UPDATE: as previsões antigas ficam como estavam e leem o padrão 'parametrica', que é o método delas.
    cols = {r[1] for r in conn.execute("PRAGMA table_info(previsoes)")}
    if "metodo_faixa" not in cols:
        conn.execute("ALTER TABLE previsoes ADD COLUMN metodo_faixa TEXT DEFAULT 'parametrica'")
        conn.commit()


def _nan_to_none(v):
    return None if v is None or (isinstance(v, float) and np.isnan(v)) else float(v)


def register_ipca(conn, horizonte: int = 12, now: datetime = None) -> Dict:
    ensure_schema(conn)
    now = now or datetime.now(timezone.utc)
    y = storage.load_observations(conn, "ipca_mensal")
    v = storage.latest_vintage(conn, "ipca_mensal")
    origem = y.index[-1]
    rows = []
    erros = empirico.sarima_errors(y)  # faixa do SARIMA: empírica por horizonte (D21)
    for nome, m in models.MODELOS.items():
        fc = models.run(nome, y, horizonte)
        for h, (alvo, r) in enumerate(fc.iterrows(), start=1):
            lo, hi, metodo = _nan_to_none(r["lo80"]), _nan_to_none(r["hi80"]), None
            if lo is not None:
                metodo = "parametrica"
            if nome == "sarima":
                b = empirico.band(erros, h, origem)
                if b:
                    lo, hi, metodo = float(r["valor"]) + b[0], float(r["valor"]) + b[1], empirico.METODO
            rows.append((now.isoformat(timespec="seconds"), "ipca_mensal", nome, m["spec"], __version__, v["id"],
                         f"{origem:%Y-%m-%d}", f"{alvo:%Y-%m-%d}", h, float(r["valor"]), lo, hi, metodo))
    # Focus: guarda a mediana disponível agora, para formar o placar comparativo daqui para a frente
    snap = focus.snapshot(conn, f"{now:%Y-%m-%d}")
    for h in range(1, horizonte + 1):
        alvo = origem + pd.DateOffset(months=h)
        if alvo in snap.index:
            rows.append((now.isoformat(timespec="seconds"), "ipca_mensal", "focus_mediana",
                         f"Focus mediana, pesquisa de {snap.loc[alvo, 'data_pesquisa']}", __version__, None,
                         f"{origem:%Y-%m-%d}", f"{alvo:%Y-%m-%d}", h, float(snap.loc[alvo, "mediana"]), None, None, None))
    before = conn.total_changes
    conn.executemany(
        """INSERT OR IGNORE INTO previsoes (registrado_em, serie_id, modelo, especificacao, versao_codigo,
               vintage_id, origem, alvo, horizonte, valor, lo80, hi80, metodo_faixa) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""", rows)
    conn.commit()
    return {"origem": f"{origem:%Y-%m}", "candidatas": len(rows), "registradas": conn.total_changes - before}


def evaluated(conn, serie_id: str = "ipca_mensal") -> List[Dict]:
    """Todas as previsões registradas, com valor realizado e erro quando já disponível."""
    ensure_schema(conn)
    y = storage.load_observations(conn, serie_id)
    rows = [dict(r) for r in conn.execute(
        "SELECT * FROM previsoes WHERE serie_id = ? ORDER BY origem DESC, modelo, horizonte", (serie_id,))]
    for r in rows:
        real = y.get(pd.Timestamp(r["alvo"]))
        r["realizado"] = None if real is None else float(real)
        r["erro"] = None if real is None else float(real) - r["valor"]
    return rows


def scoreboard(rows: List[Dict]) -> List[Dict]:
    df = pd.DataFrame([r for r in rows if r["erro"] is not None])
    if df.empty:
        return []
    out = []
    for nome, g in df.groupby("modelo"):
        item = {"modelo": nome, "n": int(len(g)), "mae": float(g["erro"].abs().mean()),
                "rmse": float(np.sqrt((g["erro"] ** 2).mean())), "cobertura80": []}
        # cobertura da faixa ao vivo, separada por método (as faixas antigas continuam avaliadas pelo que eram)
        fx = g[g["lo80"].notna()]
        for metodo, gm in fx.groupby(fx["metodo_faixa"].fillna("parametrica")):
            dentro = ((gm["realizado"] >= gm["lo80"]) & (gm["realizado"] <= gm["hi80"]))
            item["cobertura80"].append({"metodo": metodo, "n": int(len(gm)), "cobertura": float(dentro.mean())})
        out.append(item)
    return out
