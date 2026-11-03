"""Previsões setoriais com o sinal dos juros, registradas todo mês (imutáveis).

Especificação "setorial_v1" (fixada em 03/11/2026, antes da primeira previsão; D18 e D22).
Qualquer mudança no que está em SPEC exige um SPEC_ID novo (um teste confere o hash):
- Séries-alvo públicas (registradas por padrão, automação): SETORES_PUBLICOS. Séries de uso
  pessoal (Macrodados) só com `prever-setor --pessoal`, fora da automação: SETORES_PESSOAIS.
- Variável prevista: variação em 12 meses (100·ln(x(t)/x(t−12))), como na análise.
- Origem t = último mês observado do alvo + defasagem de divulgação. Assim y(t−d) é o
  dado mais recente publicado e x(t) é a Selic do mês da origem.
- Modelos (MQO, janela expansiva com todo o histórico disponível na origem):
    base:   y(t+h) = a + b·y(t−d)
    juros:  y(t+h) = a + b·y(t−d) + c·ΔSelic12m(t)
  A medida de juros é a hipótese ORIGINAL da rodada 1, não a melhor da rodada 2.
- Faixa de 80%: empírica. Percentis 10 e 90 dos erros fora da amostra que já estavam
  realizados na origem (cada erro vem de uma previsão feita só com dados da época).
  Mínimo de 36 erros; abaixo disso, sem faixa.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import statsmodels.api as sm

from .. import __version__, storage
from ..analysis import leading

SETORES_PUBLICOS = ["eletrico_pim"]               # IBGE PIM-PF 3.27 (aberta)
SETORES_PESSOAIS = list(leading.SETORES_PESSOAIS_PREVISAO)  # CNI e ABIMAQ (privado/, fora do git)
SETORES_PREVISAO = SETORES_PUBLICOS + SETORES_PESSOAIS  # tudo o que pode aparecer na versão local
HORIZONTES = [3, 6]  # registro a partir de 03/11/2026 (Tarefa 4); a 1ª rodada também tinha h=0
MIN_ESTIMACAO = 48
MIN_ERROS_FAIXA = 36
INICIO_ERROS = "2010-01-01"  # primeiras origens usadas para formar a distribuição de erros

ESPEC = {
    "base": "y(t+h) = a + b·y(t−d), MQO em janela expansiva",
    "juros": "y(t+h) = a + b·y(t−d) + c·ΔSelic12m(t), MQO em janela expansiva",
}
SPEC_ID = "setorial_v1"
SPEC = {  # tudo o que define os números de uma previsão (os horizontes registrados ficam fora)
    "modelos": ESPEC,
    "alvo": "100·ln(x(t)/x(t−12)) da série do setor",
    "preditor": "selic_mensal, x(t) − x(t−12), sem defasagem adicional",
    "origem": "último mês observado do alvo + defasagem de divulgação do setor (leading.SETORES)",
    "min_estimacao": MIN_ESTIMACAO,
    "faixa": {"percentis": [10, 90], "erros_desde": INICIO_ERROS, "min_erros": MIN_ERROS_FAIXA,
              "janela": "expansiva (todos os erros realizados na origem)"},
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS previsoes_setoriais (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    registrado_em TEXT NOT NULL,
    setor TEXT NOT NULL,
    serie_id TEXT NOT NULL,
    transformacao TEXT NOT NULL,
    modelo TEXT NOT NULL,
    especificacao TEXT NOT NULL,
    versao_codigo TEXT NOT NULL,
    vintage_alvo INTEGER,
    vintage_x INTEGER,
    origem TEXT NOT NULL,
    alvo TEXT NOT NULL,
    horizonte INTEGER NOT NULL,
    valor REAL NOT NULL,
    lo80 REAL,
    hi80 REAL,
    n_erros INTEGER,
    UNIQUE (setor, modelo, origem, alvo)
);
CREATE TRIGGER IF NOT EXISTS prev_setoriais_sem_update BEFORE UPDATE ON previsoes_setoriais
BEGIN SELECT RAISE(ABORT, 'previsões registradas são imutáveis'); END;
CREATE TRIGGER IF NOT EXISTS prev_setoriais_sem_delete BEFORE DELETE ON previsoes_setoriais
BEGIN SELECT RAISE(ABORT, 'previsões registradas são imutáveis'); END;
"""


def ensure_schema(conn):
    conn.executescript(SCHEMA)


def _fit_predict(train: pd.DataFrame, row: pd.Series, modelo: str) -> float:
    cols = ["ylag"] if modelo == "base" else ["ylag", "x"]
    params = sm.OLS(train["alvo"], sm.add_constant(train[cols])).fit().params
    return float(params["const"] + sum(params[c] * row[c] for c in cols))


def forecast(y: pd.Series, x: pd.Series, h: int, ylag: int, origem: pd.Timestamp, modelo: str) -> Dict:
    """Previsão de y(origem+h) com a faixa empírica de 80%. Usa só dados disponíveis na origem."""
    # calendário até a origem, para a linha da origem existir mesmo sem o alvo publicado (é o caso normal)
    cal = pd.date_range(min(y.index.min(), x.index.min()), max(origem, y.index.max(), x.index.max()), freq="MS")
    d = leading._design(y.reindex(cal), x.reindex(cal), h, ylag, 0)

    def available(t):  # pares cujo alvo y(s+h) já estava publicado em t
        return d[d.index <= t - pd.DateOffset(months=h + ylag)].dropna()

    train = available(origem)
    row = d.loc[origem] if origem in d.index else None
    if row is None or pd.isna(row["ylag"]) or (modelo == "juros" and pd.isna(row["x"])) or len(train) < MIN_ESTIMACAO:
        return {"valor": None}
    valor = _fit_predict(train, row, modelo)

    # erros fora da amostra de origens passadas cujo resultado já era conhecido na origem atual
    erros = []
    for s in d.index[(d.index >= INICIO_ERROS) & (d.index <= origem - pd.DateOffset(months=h + ylag))]:
        r = d.loc[s]
        if r[["alvo", "ylag", "x"]].isna().any():
            continue
        tr = available(s)
        if len(tr) < MIN_ESTIMACAO:
            continue
        erros.append(r["alvo"] - _fit_predict(tr, r, modelo))
    lo = hi = None
    if len(erros) >= MIN_ERROS_FAIXA:
        q10, q90 = np.percentile(erros, [10, 90])
        lo, hi = valor + q10, valor + q90
    return {"valor": valor, "lo80": lo, "hi80": hi, "n_erros": len(erros)}


def _series(conn, setor: str):
    cfg = leading.SETORES[setor]
    y = leading.transform(storage.load_observations(conn, cfg["alvo"]), "log12").dropna()
    x = leading.transform(storage.load_observations(conn, "selic_mensal"), "dif12").dropna()
    return cfg, y, x


def register(conn, setores: Optional[List[str]] = None, now: datetime = None) -> List[Dict]:
    ensure_schema(conn)
    now = now or datetime.now(timezone.utc)
    out = []
    for setor in setores or SETORES_PUBLICOS:
        cfg, y, x = _series(conn, setor)
        if y.empty:
            out.append({"setor": setor, "erro": "série-alvo sem dados"})
            continue
        ylag = cfg["defasagem"]
        origem = y.index[-1] + pd.DateOffset(months=ylag)
        va = storage.latest_vintage(conn, cfg["alvo"])["id"]
        vx = storage.latest_vintage(conn, "selic_mensal")["id"]
        rows = []
        for h in HORIZONTES:
            alvo = origem + pd.DateOffset(months=h)
            for modelo in ("base", "juros"):
                f = forecast(y, x, h, ylag, origem, modelo)
                if f["valor"] is None:
                    continue
                rows.append((now.isoformat(timespec="seconds"), setor, cfg["alvo"], "100·ln(x(t)/x(t−12))", modelo,
                             f"{SPEC_ID} · {ESPEC[modelo]}", __version__, va, vx, f"{origem:%Y-%m-%d}", f"{alvo:%Y-%m-%d}", h,
                             f["valor"], f["lo80"], f["hi80"], f["n_erros"]))
        before = conn.total_changes
        conn.executemany(
            """INSERT OR IGNORE INTO previsoes_setoriais (registrado_em, setor, serie_id, transformacao, modelo,
                   especificacao, versao_codigo, vintage_alvo, vintage_x, origem, alvo, horizonte, valor, lo80, hi80, n_erros)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", rows)
        conn.commit()
        out.append({"setor": setor, "origem": f"{origem:%Y-%m}", "candidatas": len(rows),
                    "registradas": conn.total_changes - before})
    return out


def evaluated(conn) -> List[Dict]:
    """Todas as previsões setoriais registradas, com o realizado (var. 12m) quando já disponível."""
    ensure_schema(conn)
    rows = [dict(r) for r in conn.execute("SELECT * FROM previsoes_setoriais ORDER BY setor, origem DESC, horizonte, modelo")]
    cache = {}
    for r in rows:
        if r["serie_id"] not in cache:
            cache[r["serie_id"]] = leading.transform(storage.load_observations(conn, r["serie_id"]), "log12")
        real = cache[r["serie_id"]].get(pd.Timestamp(r["alvo"]))
        r["realizado"] = None if real is None or pd.isna(real) else float(real)
        r["erro"] = None if r["realizado"] is None else r["realizado"] - r["valor"]
        r["dentro_faixa"] = (None if r["realizado"] is None or r["lo80"] is None
                             else bool(r["lo80"] <= r["realizado"] <= r["hi80"]))
    return rows


def scoreboard(rows: List[Dict]) -> List[Dict]:
    """Placar ao vivo por setor e modelo, só com previsões cujo mês-alvo já foi publicado.

    `vs_base`: RMSE do modelo com juros ÷ RMSE do base, nos mesmos pares (origem, alvo)."""
    df = pd.DataFrame([r for r in rows if r.get("erro") is not None])
    if df.empty:
        return []
    out = []
    for (setor, modelo), g in df.groupby(["setor", "modelo"]):
        fx = g[g["lo80"].notna()]
        item = {"setor": setor, "modelo": modelo, "n": int(len(g)),
                "mae": float(g["erro"].abs().mean()), "rmse": float(np.sqrt((g["erro"] ** 2).mean())),
                "cobertura80": float(fx["dentro_faixa"].mean()) if len(fx) else None, "n_faixa": int(len(fx))}
        if modelo == "juros":
            base = df[(df["setor"] == setor) & (df["modelo"] == "base")].set_index(["origem", "alvo"])["erro"]
            par = g.set_index(["origem", "alvo"])["erro"].to_frame("juros").join(base.rename("base"), how="inner")
            if len(par):
                item["vs_base"] = float(np.sqrt((par["juros"] ** 2).mean()) / np.sqrt((par["base"] ** 2).mean()))
        out.append(item)
    return out


def calibration(conn, setor: str, inicio: str = "2016-01-01") -> Dict:
    """Backtest das faixas empíricas: em que fração das origens passadas o realizado caiu dentro da faixa?"""
    cfg, y, x = _series(conn, setor)
    ylag = cfg["defasagem"]
    res = {}
    for modelo in ("base", "juros"):
        for h in HORIZONTES:
            d = leading._design(y, x, h, ylag, 0)
            hits = []
            for t in d.index[(d.index >= inicio) & d.notna().all(axis=1)]:
                f = forecast(y, x, h, ylag, t, modelo)
                if f["valor"] is not None and f["lo80"] is not None:
                    hits.append(f["lo80"] <= d.loc[t, "alvo"] <= f["hi80"])
            res[f"{modelo}_h{h}"] = {"n": len(hits), "cobertura80": float(np.mean(hits)) if hits else None}
    return res
