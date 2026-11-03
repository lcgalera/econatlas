import sqlite3
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest

from econatlas import storage
from econatlas.catalog import SeriesMeta
from econatlas.forecast import setorial
from econatlas.providers import FetchResult


def _synthetic(n=260, seed=3):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2004-01-01", periods=n, freq="MS")
    x = pd.Series(rng.normal(size=n), index=idx).rolling(6, min_periods=1).mean()
    y = (-2 * x.shift(3) + pd.Series(rng.normal(scale=0.5, size=n), index=idx)).dropna()
    return y, x


def test_forecast_ignores_data_published_after_origin():
    y, x = _synthetic()
    origem = pd.Timestamp("2018-06-01")
    f1 = setorial.forecast(y, x, 3, 2, origem, "juros")
    y2 = y.copy()
    y2[y2.index > origem - pd.DateOffset(months=2)] += 100  # dados que ainda não estavam publicados
    f2 = setorial.forecast(y2, x, 3, 2, origem, "juros")
    assert f1["valor"] == pytest.approx(f2["valor"])
    assert (f1["lo80"], f1["hi80"]) == pytest.approx((f2["lo80"], f2["hi80"]))


def test_band_contains_point_and_needs_enough_errors():
    y, x = _synthetic()
    f = setorial.forecast(y, x, 3, 2, pd.Timestamp("2020-01-01"), "juros")
    assert f["lo80"] < f["valor"] < f["hi80"] and f["n_erros"] >= setorial.MIN_ERROS_FAIXA
    early = setorial.forecast(y, x, 3, 2, pd.Timestamp("2010-06-01"), "juros")
    assert early["valor"] is None or early["lo80"] is None


def _meta(sid):
    return SeriesMeta(id=sid, nome=sid, modulo="radar_setorial", tema="t", instituicao="I", provedor="arquivo",
                      codigo="x", unidade="índice", periodicidade="mensal", geografia="Brasil", licenca="L", uso="pessoal")


def test_register_is_immutable_and_idempotent(tmp_path, monkeypatch):
    conn = storage.connect(tmp_path / "t.sqlite")
    n = 280
    idx = pd.date_range("2003-01-01", periods=n, freq="MS")
    rng = np.random.default_rng(0)
    level = pd.Series(100 * np.exp(np.cumsum(rng.normal(0.003, 0.03, n))), index=idx)
    sidx = pd.date_range("2003-01-01", periods=n + 2, freq="MS")  # Selic sai antes do alvo, como na realidade
    selic = pd.Series(10 + np.cumsum(rng.normal(0, 0.3, n + 2)), index=sidx)
    for sid, s in (("alvo_teste", level), ("selic_mensal", selic)):
        storage.save_fetch(conn, _meta(sid), FetchResult(b"x", "csv", "u", pd.DataFrame({"date": s.index, "value": s.values})),
                           raw_dir=tmp_path / "raw")
    monkeypatch.setitem(setorial.leading.SETORES, "teste", {"alvo": "alvo_teste", "rotulo": "t", "fonte": "f",
                                                          "uci": "", "defasagem": 2, "replicacao": True})
    now = datetime(2026, 11, 3, tzinfo=timezone.utc)
    r1 = setorial.register(conn, ["teste"], now=now)
    assert r1[0]["registradas"] == len(setorial.HORIZONTES) * 2  # horizontes × 2 modelos
    assert setorial.register(conn, ["teste"], now=now)[0]["registradas"] == 0
    with pytest.raises(sqlite3.DatabaseError):
        conn.execute("UPDATE previsoes_setoriais SET valor = 0")
    with pytest.raises(sqlite3.DatabaseError):
        conn.execute("DELETE FROM previsoes_setoriais")
    rows = setorial.evaluated(conn)
    assert all(r["realizado"] is None for r in rows if r["horizonte"] > 0)


def test_base_model_does_not_need_selic_at_origin():
    y, x = _synthetic()
    origem = y.index[-1] + pd.DateOffset(months=2)
    xs = x[x.index <= y.index[-1]]  # Selic ainda não publicada na origem
    assert setorial.forecast(y, xs, 3, 2, origem, "base")["valor"] is not None
    assert setorial.forecast(y, xs, 3, 2, origem, "juros")["valor"] is None


def test_spec_cannot_change_without_new_id():
    """A especificação setorial_v1 foi fixada antes da primeira previsão. Mudou algo em SPEC?
    Crie um SPEC_ID novo (ex.: setorial_v2) e atualize este hash. Não edite o v1 em silêncio."""
    import hashlib, json
    h = hashlib.sha256(json.dumps(setorial.SPEC, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    esperado = {"setorial_v1": "5d7c0f8cf2aa2a15006c58d3b88c7cb93e9ae1e46f44a057c7831740fe0ef97b"}
    assert setorial.SPEC_ID in esperado and h == esperado[setorial.SPEC_ID]


def test_default_registration_is_public_only():
    from econatlas.catalog import load_catalog
    from econatlas.analysis import leading
    cat = load_catalog()
    assert not set(setorial.SETORES_PUBLICOS) & set(setorial.SETORES_PESSOAIS)
    for s in setorial.SETORES_PUBLICOS:
        assert cat[leading.SETORES[s]["alvo"]].uso == "publico", s
    import inspect
    assert "SETORES_PUBLICOS" in inspect.getsource(setorial.register)


def test_scoreboard_compares_with_base_on_same_pairs():
    rows = []
    for i, (eb, ej) in enumerate([(2.0, 1.0), (-2.0, -1.0), (1.0, 1.0)]):
        o = f"2027-0{i + 1}-01"
        for modelo, e, lo, hi in (("base", eb, None, None), ("juros", ej, -1.5, 1.5)):
            rows.append({"setor": "s", "modelo": modelo, "origem": o, "alvo": o, "erro": e,
                         "lo80": lo, "hi80": hi, "dentro_faixa": None if lo is None else bool(lo <= e <= hi)})
    rows.append({"setor": "s", "modelo": "juros", "origem": "2027-09-01", "alvo": "2027-12-01", "erro": None,
                 "lo80": -1, "hi80": 1, "dentro_faixa": None})  # ainda sem dado: fica fora
    sb = {r["modelo"]: r for r in setorial.scoreboard(rows)}
    assert sb["juros"]["n"] == 3 and sb["base"]["n"] == 3
    assert sb["juros"]["vs_base"] == pytest.approx(np.sqrt(1.0) / np.sqrt(3.0))
    assert sb["juros"]["cobertura80"] == pytest.approx(1.0)
