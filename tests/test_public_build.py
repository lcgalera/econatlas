"""O build público não pode carregar nada de série de uso pessoal (Macrodados)."""
import json

import numpy as np
import pandas as pd
import pytest

from econatlas import payloads, public_build, storage
from econatlas.catalog import SeriesMeta
from econatlas.providers import FetchResult


def _meta(sid, uso, **extra):
    return SeriesMeta(id=sid, nome=f"Série {sid} para teste", modulo="radar_setorial", tema="industria",
                      instituicao="X", provedor="arquivo" if uso != "publico" else "bcb_sgs", codigo="1",
                      unidade="índice", periodicidade="mensal", geografia="Brasil", licenca="L", uso=uso, extra=extra)


@pytest.fixture
def ambiente(tmp_path):
    conn = storage.connect(tmp_path / "t.sqlite")
    idx = pd.date_range("2010-01-01", periods=120, freq="MS")
    rng = np.random.default_rng(1)
    catalog = {
        "serie_publica": _meta("serie_publica", "publico"),
        "md_xpto_pessoal": _meta("md_xpto_pessoal", "pessoal", codigo_md="zz9999", coluna_valor="XPTO - Faturamento (R$ M)"),
    }
    for sid in catalog:
        vals = 100 + np.cumsum(rng.normal(0, 1, len(idx))).round(4)
        storage.save_fetch(conn, catalog[sid], FetchResult(b"x", "csv", "u", pd.DataFrame({"date": idx, "value": vals})),
                           raw_dir=tmp_path / "raw")
    return conn, catalog, tmp_path


def test_public_build_has_no_trace_of_personal_series(ambiente):
    conn, catalog, tmp = ambiente
    out = tmp / "site"
    meta = public_build.build(out, conn=conn, catalog=catalog)  # a própria build roda verificar()
    assert meta["series"] == 1
    tudo = "".join(p.read_text(errors="ignore") for p in out.rglob("*") if p.suffix in (".json", ".html"))
    for proibido in ("md_xpto_pessoal", "zz9999", "XPTO - Faturamento", "Série md_xpto_pessoal"):
        assert proibido not in tudo
    assert "serie_publica" in tudo
    cat_pub = json.loads((out / "data" / "catalogo.json").read_text())
    assert [s["id"] for s in cat_pub] == ["serie_publica"]
    import sqlite3
    db = sqlite3.connect(out / "data" / "econatlas_publico.sqlite")
    assert db.execute("SELECT COUNT(*) FROM observations WHERE series_id = 'md_xpto_pessoal'").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM observations WHERE series_id = 'serie_publica'").fetchone()[0] == 120


def test_verifier_catches_disguised_personal_values(ambiente):
    conn, catalog, tmp = ambiente
    out = tmp / "site"
    public_build.build(out, conn=conn, catalog=catalog)
    # valores da série pessoal copiados sob outro nome: tem de ser pego pela comparação de sequências
    vazado = payloads.series(conn, catalog, "md_xpto_pessoal", "nivel")["dados"]
    (out / "data" / "series" / "disfarce.json").write_text(json.dumps({"dados": vazado}))
    with pytest.raises(public_build.VazamentoPublico):
        public_build.verificar(out, catalog, conn)


def test_verifier_catches_personal_code_in_text(ambiente):
    conn, catalog, tmp = ambiente
    out = tmp / "site"
    public_build.build(out, conn=conn, catalog=catalog)
    (out / "data" / "nota.json").write_text(json.dumps({"obs": "fonte zz9999"}))
    with pytest.raises(public_build.VazamentoPublico):
        public_build.verificar(out, catalog, conn)


def test_build_refuses_to_wipe_unrelated_folder(tmp_path, ambiente):
    conn, catalog, _ = ambiente
    alheia = tmp_path / "minha_pasta"
    alheia.mkdir()
    (alheia / "importante.txt").write_text("não apagar")
    with pytest.raises(RuntimeError):
        public_build.build(alheia, conn=conn, catalog=catalog)
    assert (alheia / "importante.txt").exists()
