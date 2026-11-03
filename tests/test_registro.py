import subprocess
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest

from econatlas import registro, storage
from econatlas.catalog import SeriesMeta
from econatlas.forecast import focus, registry
from econatlas.providers import FetchResult


def _meta(sid, uso="publico"):
    return SeriesMeta(id=sid, nome=sid, modulo="radar_brasil", tema="t", instituicao="I", provedor="bcb_sgs",
                      codigo="1", unidade="% a.m.", periodicidade="mensal", geografia="Brasil", licenca="L", uso=uso)


@pytest.fixture
def banco(tmp_path, monkeypatch):
    monkeypatch.setattr(registry.empirico, "sarima_errors", lambda y, cache_file=None: pd.DataFrame(
        columns=["origem", "h", "alvo", "previsto", "realizado", "erro"]))
    conn = storage.connect(tmp_path / "t.sqlite")
    idx = pd.date_range("2004-01-01", periods=200, freq="MS")
    y = pd.Series(0.4 + np.random.default_rng(0).normal(0, 0.2, 200), index=idx)
    storage.save_fetch(conn, _meta("ipca_mensal"), FetchResult(b"x", "json", "u", pd.DataFrame({"date": idx, "value": y.values})),
                       raw_dir=tmp_path / "raw")
    focus.ensure_schema(conn)
    registry.register_ipca(conn, now=datetime(2020, 9, 15, tzinfo=timezone.utc))
    return conn, {"ipca_mensal": _meta("ipca_mensal")}


def _git(pasta, *args):
    subprocess.run(["git", *args], cwd=pasta, check=True, capture_output=True,
                   env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                        "GIT_COMMITTER_EMAIL": "t@t", "PATH": "/usr/bin:/bin:/opt/homebrew/bin"})


def test_export_only_appends(banco, tmp_path):
    conn, cat = banco
    pasta = tmp_path / "registro"
    assert registro.exportar(conn, pasta, cat)["previsoes_ipca.csv"] == 36
    antes = (pasta / "previsoes_ipca.csv").read_text()
    assert registro.exportar(conn, pasta, cat)["previsoes_ipca.csv"] == 0
    assert (pasta / "previsoes_ipca.csv").read_text() == antes


def test_personal_series_never_exported(banco, tmp_path):
    conn, cat = banco
    pasta = tmp_path / "registro"
    cat_pessoal = {"ipca_mensal": _meta("ipca_mensal", uso="pessoal")}
    assert registro.exportar(conn, pasta, cat_pessoal)["previsoes_ipca.csv"] == 0
    assert "ipca_mensal" not in (pasta / "coletas.csv").read_text()


def test_verify_catches_edited_old_line(banco, tmp_path):
    conn, cat = banco
    pasta = tmp_path / "registro"
    registro.exportar(conn, pasta, cat)
    _git(pasta, "init", "-q")
    _git(pasta, "add", ".")
    _git(pasta, "commit", "-qm", "registro")
    assert registro.verificar(conn, pasta, contra="HEAD") == []
    f = pasta / "previsoes_ipca.csv"
    linhas = f.read_text().splitlines()
    linhas[3] = linhas[3].replace(",1,", ",1,", 1)[:-1] + "9"  # muda um número de uma previsão antiga
    f.write_text("\n".join(linhas) + "\n")
    problemas = registro.verificar(None, pasta, contra="HEAD")
    assert problemas and "linha 4" in problemas[0]


def test_verify_catches_db_diverging_from_csv(banco, tmp_path):
    conn, cat = banco
    pasta = tmp_path / "registro"
    registro.exportar(conn, pasta, cat)
    novo = storage.connect(tmp_path / "outro.sqlite")
    registro.importar(novo, pasta)
    assert registro.verificar(novo, pasta, contra=None) == []
    f = pasta / "previsoes_ipca.csv"
    t = f.read_text().splitlines()
    cols = t[0].split(",")
    i = cols.index("valor")
    partes = t[1].split(",")
    partes[i] = "9.99"
    t[1] = ",".join(partes)
    f.write_text("\n".join(t) + "\n")
    assert any("banco diverge" in p for p in registro.verificar(novo, pasta, contra=None))


def test_import_then_register_appends_only_new(banco, tmp_path):
    conn, cat = banco
    pasta = tmp_path / "registro"
    registro.exportar(conn, pasta, cat)
    novo = storage.connect(tmp_path / "novo.sqlite")  # como no GitHub Actions: banco vazio
    assert registro.importar(novo, pasta)["previsoes_ipca.csv"] == 36
    assert registro.importar(novo, pasta)["previsoes_ipca.csv"] == 0
