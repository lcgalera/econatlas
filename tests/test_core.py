from datetime import date

import pandas as pd
import pytest

from rotzx import storage, transforms
from rotzx.catalog import SeriesMeta
from rotzx.providers import FetchResult, arquivo, bcb_sgs, ibge_sidra


def meta(**kw):
    base = dict(id="x", nome="X", modulo="radar_brasil", tema="t", instituicao="I", provedor="bcb_sgs",
                codigo="1", unidade="índice", periodicidade="mensal", geografia="Brasil", licenca="L", uso="publico")
    base.update(kw)
    return SeriesMeta(**base)


def monthly(values, start="2020-01-01"):
    return pd.Series(values, index=pd.date_range(start, periods=len(values), freq="MS"), dtype=float)


# ---------- transformações ----------

def test_var_anual_uses_calendar_not_row_position():
    s = monthly(range(100, 125))
    s = s.drop(s.index[5])  # mês faltante: a variação de 12m de jun/21 não pode usar maio/20
    out = transforms.apply(s, meta(), "var_anual")
    assert pd.Timestamp("2021-06-01") not in out.index
    assert out[pd.Timestamp("2021-01-01")] == pytest.approx((112 / 100 - 1) * 100)


def test_acum_12m_compounds_monthly_rates():
    s = monthly([1.0] * 12)
    out = transforms.apply(s, meta(unidade="% a.m."), "acum_12m")
    assert len(out) == 1
    assert out.iloc[0] == pytest.approx((1.01 ** 12 - 1) * 100)


def test_transform_not_applicable_is_rejected():
    with pytest.raises(ValueError):
        transforms.apply(monthly([1, 2]), meta(unidade="%"), "var_periodo")  # variação % de taxa não faz sentido


def test_deflate_keeps_last_month_and_scales_past():
    nominal = monthly([100.0, 100.0, 100.0])
    ipca = monthly([0.0, 10.0, 0.0])  # preços sobem 10% em fev
    out = transforms.apply(nominal, meta(unidade="R$ (nominal)"), "deflacionado_ipca", deflator=ipca)
    assert out.iloc[-1] == pytest.approx(100.0)
    assert out.iloc[0] == pytest.approx(110.0)  # R$100 de jan valem R$110 a preços de mar
    assert out.attrs["base"] == "2020-03"


# ---------- provedores ----------

def test_bcb_windows_cover_range_without_gaps():
    wins = list(bcb_sgs._windows(date(1999, 3, 5), date(2026, 11, 2)))
    assert wins[0][0] == date(1999, 3, 5) and wins[-1][1] == date(2026, 11, 2)
    for (a0, a1), (b0, b1) in zip(wins, wins[1:]):
        assert b0 <= date.fromordinal(a1.toordinal() + 1)
        assert (a1.year - a0.year) <= 10


def test_bcb_parse():
    df = bcb_sgs.parse([{"data": "01/01/2024", "valor": "0.42"}, {"data": "01/02/2024", "valor": ""}])
    assert list(df["value"]) == [0.42]


def test_sidra_parse_quarters_and_missing():
    rows = [
        {"V": "Valor", "D2C": "Trimestre (Código)", "D2N": "Trimestre"},
        {"V": "2.0", "D2C": "202602", "D2N": "2º trimestre 2026"},
        {"V": "...", "D2C": "202603", "D2N": "3º trimestre 2026"},
    ]
    df = ibge_sidra.parse(rows)
    assert df["date"].tolist() == [pd.Timestamp("2026-04-01")]
    assert df["value"].tolist() == [2.0]


def test_file_import_brazilian_format():
    raw = "Data;Valor\n01/2024;1.234,50\n02/2024;1.300,00\n".encode()
    df = arquivo.read_table(raw, "export.csv")
    assert df["date"].tolist() == [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-02-01")]
    assert df["value"].tolist() == [1234.5, 1300.0]


def test_file_import_rejects_duplicate_dates():
    raw = b"data,valor\n2024-01-01,1\n2024-01-01,2\n"
    with pytest.raises(ValueError):
        arquivo.read_table(raw, "x.csv")


# ---------- armazenamento e versões ----------

def test_vintages_track_new_and_revised(tmp_path):
    conn = storage.connect(tmp_path / "t.sqlite")
    m = meta()
    df1 = pd.DataFrame({"date": pd.to_datetime(["2024-01-01", "2024-02-01"]), "value": [1.0, 2.0]})
    r1 = storage.save_fetch(conn, m, FetchResult(b"a", "json", "u", df1), raw_dir=tmp_path / "raw")
    assert r1["status"] == "nova_versao"

    r_same = storage.save_fetch(conn, m, FetchResult(b"a", "json", "u", df1), raw_dir=tmp_path / "raw")
    assert r_same["status"] == "sem_alteracao"

    df2 = pd.DataFrame({"date": pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"]), "value": [1.0, 2.5, 3.0]})
    r2 = storage.save_fetch(conn, m, FetchResult(b"b", "json", "u", df2), raw_dir=tmp_path / "raw")
    assert (r2["n_new"], r2["n_revised"]) == (1, 1)

    # a versão antiga continua consultável (base para backtests em tempo real)
    old = storage.load_observations(conn, "x", r1["vintage_id"])
    assert old.tolist() == [1.0, 2.0]
    assert storage.load_observations(conn, "x").tolist() == [1.0, 2.5, 3.0]


def test_confirmed_bcb_metadata_cites_its_source():
    """Série do BCB marcada como conferida precisa dizer de onde veio a confirmação (sem rótulo inventado)."""
    from rotzx.catalog import load_catalog
    for m in load_catalog().values():
        if m.provedor == "bcb_sgs" and m.metadados_conferidos:
            assert m.extra.get("nome_oficial") and m.extra.get("fonte_metadados"), m.id
