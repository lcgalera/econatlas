import numpy as np
import pandas as pd
import pytest

from econatlas.analysis import leading


def test_holm_adjustment():
    assert leading.holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])


def _synthetic(n=260, seed=1):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2004-01-01", periods=n, freq="MS")
    x = pd.Series(rng.normal(size=n), index=idx).rolling(3, min_periods=1).mean()
    noise = pd.Series(rng.normal(scale=0.3, size=n), index=idx)
    y = 2 * x.shift(3) + noise  # x antecede y em 3 meses (= horizonte testado)
    return y.dropna(), x


def test_true_leading_indicator_is_detected():
    y, x = _synthetic()
    r = leading.oos_test(y, x, h=3, xlag=0)
    assert r["razao_rmse"] < 0.8 and r["p_valor"] < 0.01


def test_noise_indicator_is_not_detected():
    y, _ = _synthetic()
    noise = pd.Series(np.random.default_rng(7).normal(size=len(y)), index=y.index)
    r = leading.oos_test(y, noise, h=3, xlag=0)
    assert r["p_valor"] > 0.05


def test_forecast_does_not_use_unpublished_target():
    """Mudar o alvo depois do que estaria publicado na origem não pode mudar a previsão daquela origem."""
    y, x = _synthetic()
    origin = pd.Timestamp("2018-01-01")
    y2 = y.copy()
    y2[y2.index > origin - pd.DateOffset(months=leading.ALVO_DEFASAGEM)] += 50
    d1 = leading._design(y, x, 3, leading.ALVO_DEFASAGEM, 0)
    d2 = leading._design(y2, x, 3, leading.ALVO_DEFASAGEM, 0)
    cut = origin - pd.DateOffset(months=3 + leading.ALVO_DEFASAGEM)
    t1, t2 = d1[d1.index <= cut].dropna(), d2[d2.index <= cut].dropna()
    pd.testing.assert_frame_equal(t1, t2)                     # amostra de estimação idêntica
    assert d1.loc[origin, "ylag"] == d2.loc[origin, "ylag"]   # regressor da origem idêntico


def test_real_ex_ante_rate_is_fisher_identity(tmp_path):
    from econatlas import storage
    from econatlas.catalog import SeriesMeta
    from econatlas.providers import FetchResult
    conn = storage.connect(tmp_path / "t.sqlite")
    idx = pd.date_range("2024-01-01", periods=3, freq="MS")
    for sid, val in (("selic_mensal", 10.25), ("ipca_expect_12m", 5.0)):
        m = SeriesMeta(id=sid, nome=sid, modulo="radar_brasil", tema="t", instituicao="BCB", provedor="bcb_sgs",
                       codigo="0", unidade="%", periodicidade="mensal", geografia="Brasil", licenca="L", uso="publico")
        storage.save_fetch(conn, m, FetchResult(b"x", "json", "u", pd.DataFrame({"date": idx, "value": [val] * 3})),
                           raw_dir=tmp_path / "raw")
    r = leading.load_candidate(conn, "juro_real_exante")
    assert r.tolist() == pytest.approx([5.0] * 3)  # (1,1025 / 1,05 − 1) × 100


def test_sector_configs_are_complete():
    assert any(c[0] == "UCI_DO_SETOR" for c in leading.CANDIDATOS)
    for nome, cfg in leading.SETORES.items():  # públicos sempre; pessoais só se privado/ existir
        assert {"alvo", "rotulo", "fonte", "uci", "defasagem", "replicacao"} <= set(cfg), nome
    assert {"eletrico_pim", "maquinas_pim"} <= set(leading.SETORES)
