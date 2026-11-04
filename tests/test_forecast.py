import sqlite3
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest

from rotzx import storage
from rotzx.catalog import SeriesMeta
from rotzx.forecast import backtest, focus, models, registry
from rotzx.providers import FetchResult


def ipca_like(n=200, start="2004-01-01"):
    idx = pd.date_range(start, periods=n, freq="MS")
    rng = np.random.default_rng(0)
    seasonal = 0.15 * np.sin(2 * np.pi * idx.month / 12)
    return pd.Series(0.4 + seasonal + rng.normal(0, 0.15, n), index=idx)


def test_seasonal_naive_repeats_last_year():
    y = ipca_like(36)
    fc = models.run("sazonal_ingenuo", y, 12)
    assert fc.index[0] == y.index[-1] + pd.offsets.MonthBegin(1)
    assert fc["valor"].tolist() == pytest.approx(y.iloc[-12:].tolist())


def test_sarima_interval_contains_point():
    fc = models.run("sarima", ipca_like(), 6)
    assert len(fc) == 6
    assert ((fc["lo80"] < fc["valor"]) & (fc["valor"] < fc["hi80"])).all()


def test_backtest_does_not_use_future_data():
    """Se os dados depois da origem mudarem, a previsão feita na origem não pode mudar."""
    y = ipca_like(150)
    origin = y.index[120]
    y_alt = y.copy()
    y_alt[y_alt.index > origin] += 5.0
    for nome in models.MODELOS:
        a = models.run(nome, y[y.index <= origin], 3)
        b = models.run(nome, y_alt[y_alt.index <= origin], 3)
        assert a["valor"].tolist() == pytest.approx(b["valor"].tolist())


def test_backtest_focus_uses_survey_available_at_origin():
    y = ipca_like(150)
    o = pd.Timestamp("2015-06-01")
    target = o + pd.DateOffset(months=1)
    surveys = pd.DataFrame({
        "data_pesquisa": pd.to_datetime(["2015-07-10", "2015-07-20"]),  # a segunda é depois do corte (dia 15)
        "referencia": [target, target],
        "mediana": [0.30, 9.99],
    })
    det = backtest.run(y[y.index <= pd.Timestamp("2015-12-01")], surveys, inicio="2015-06-01")["detalhe"]
    f = det[(det.modelo == "focus_mediana") & (det.origem == o) & (det.h == 1)]
    assert f["previsto"].tolist() == [0.30]


def _conn_with_ipca(tmp_path):
    conn = storage.connect(tmp_path / "t.sqlite")
    meta = SeriesMeta(id="ipca_mensal", nome="IPCA", modulo="radar_brasil", tema="inflacao", instituicao="IBGE",
                      provedor="bcb_sgs", codigo="433", unidade="% a.m.", periodicidade="mensal", geografia="Brasil",
                      licenca="L", uso="publico")
    y = ipca_like()
    storage.save_fetch(conn, meta, FetchResult(b"x", "json", "u", pd.DataFrame({"date": y.index, "value": y.values})),
                       raw_dir=tmp_path / "raw")
    return conn


def test_registry_is_immutable_and_first_forecast_wins(tmp_path, monkeypatch):
    # a faixa empírica do SARIMA é testada em test_empirico; aqui só importa o registro
    monkeypatch.setattr(registry.empirico, "sarima_errors", lambda y, cache_file=None: pd.DataFrame(
        columns=["origem", "h", "alvo", "previsto", "realizado", "erro"]))
    conn = _conn_with_ipca(tmp_path)
    focus.ensure_schema(conn)
    now = datetime(2020, 9, 15, tzinfo=timezone.utc)
    r1 = registry.register_ipca(conn, now=now)
    assert r1["registradas"] == 3 * 12
    r2 = registry.register_ipca(conn, now=now)
    assert r2["registradas"] == 0
    with pytest.raises(sqlite3.DatabaseError):
        conn.execute("UPDATE previsoes SET valor = 0")
    with pytest.raises(sqlite3.DatabaseError):
        conn.execute("DELETE FROM previsoes")
    rows = registry.evaluated(conn)
    assert all(r["realizado"] is None for r in rows)  # alvos ainda não observados
    assert registry.scoreboard(rows) == []
