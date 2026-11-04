import sqlite3
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest

from rotzx import storage
from rotzx.catalog import SeriesMeta
from rotzx.forecast import empirico, focus, registry
from rotzx.providers import FetchResult


def ipca_like(n=240, start="2004-01-01", seed=0):
    idx = pd.date_range(start, periods=n, freq="MS")
    rng = np.random.default_rng(seed)
    return pd.Series(0.4 + 0.15 * np.sin(2 * np.pi * idx.month / 12) + rng.normal(0, 0.15, n), index=idx)


def _errors(y):
    """Erros sintéticos conhecidos, sem rodar o SARIMA: erro = h/100 + ruído pequeno."""
    rows = []
    for o in y.index[y.index >= "2008-01-01"]:
        for h in range(1, 13):
            alvo = o + pd.DateOffset(months=h)
            real = y.get(alvo)
            rows.append({"origem": o, "h": h, "alvo": alvo, "previsto": 0.0, "realizado": real})
    df = pd.DataFrame(rows)
    df["erro"] = df["realizado"] - df["previsto"]
    return df


def test_band_only_uses_errors_realized_at_origin():
    y = ipca_like()
    e = _errors(y)
    origem = pd.Timestamp("2016-06-01")
    b1 = empirico.band(e, 3, origem)
    e2 = e.copy()
    e2.loc[e2["alvo"] > origem, "erro"] += 50  # erros ainda não conhecidos na origem
    assert empirico.band(e2, 3, origem) == pytest.approx(b1)


def test_band_uses_only_last_60_months():
    y = ipca_like()
    e = _errors(y)
    origem = pd.Timestamp("2018-01-01")
    e2 = e.copy()
    e2.loc[e2["alvo"] <= origem - pd.DateOffset(months=empirico.JANELA_MESES), "erro"] += 50  # fora da janela
    assert empirico.band(e2, 3, origem) == pytest.approx(empirico.band(e, 3, origem))


def test_band_needs_minimum_errors():
    y = ipca_like()
    assert empirico.band(_errors(y), 1, pd.Timestamp("2009-06-01")) is None


def test_cache_is_discarded_when_series_changes(tmp_path, monkeypatch):
    monkeypatch.setattr(empirico, "INICIO_ERROS", "2016-06-01")  # poucas origens: teste rápido
    y = ipca_like(n=160)
    f = tmp_path / "c.json"
    a = empirico.sarima_errors(y, cache_file=f)
    y2 = y.copy()
    y2.iloc[150] += 1.0  # "revisão" de um mês
    b = empirico.sarima_errors(y2, cache_file=f)
    o = y.index[152]
    pa = a[(a.origem == o) & (a.h == 1)]["previsto"].iloc[0]
    pb = b[(b.origem == o) & (b.h == 1)]["previsto"].iloc[0]
    assert pa != pytest.approx(pb)  # recalculado com a série nova, não lido do cache velho


def test_new_registrations_get_empirical_band_and_old_rows_stay(tmp_path, monkeypatch):
    monkeypatch.setattr(empirico, "sarima_errors", lambda y, cache_file=None: _errors(y.asfreq("MS")))
    conn = storage.connect(tmp_path / "t.sqlite")
    meta = SeriesMeta(id="ipca_mensal", nome="IPCA", modulo="radar_brasil", tema="inflacao", instituicao="IBGE",
                      provedor="bcb_sgs", codigo="433", unidade="% a.m.", periodicidade="mensal", geografia="Brasil",
                      licenca="L", uso="publico")
    y = ipca_like(n=260)
    storage.save_fetch(conn, meta, FetchResult(b"x", "json", "u", pd.DataFrame({"date": y.index, "value": y.values})),
                       raw_dir=tmp_path / "raw")
    focus.ensure_schema(conn)
    # simula uma linha antiga (antes da coluna metodo_faixa existir)
    conn.executescript(registry.SCHEMA)
    conn.execute("""INSERT INTO previsoes (registrado_em, serie_id, modelo, especificacao, versao_codigo, vintage_id,
                    origem, alvo, horizonte, valor, lo80, hi80) VALUES ('2020-01-01','ipca_mensal','sarima','s','0',1,
                    '2019-12-01','2020-01-01',1,0.5,0.4,0.6)""")
    conn.commit()
    registry.register_ipca(conn, now=datetime(2026, 1, 15, tzinfo=timezone.utc))
    antiga = conn.execute("SELECT valor, lo80, hi80, metodo_faixa FROM previsoes WHERE origem='2019-12-01'").fetchone()
    assert tuple(antiga) == (0.5, 0.4, 0.6, "parametrica")
    novas = conn.execute("SELECT DISTINCT metodo_faixa FROM previsoes WHERE modelo='sarima' AND origem != '2019-12-01'").fetchall()
    assert [r[0] for r in novas] == [empirico.METODO]
    with pytest.raises(sqlite3.DatabaseError):
        conn.execute("UPDATE previsoes SET metodo_faixa = 'x'")
