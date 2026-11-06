"""O build público não pode carregar nada de série de uso pessoal (Macrodados)."""
import json

import numpy as np
import pandas as pd
import pytest

from rotzx import payloads, public_build, storage
from rotzx.catalog import SeriesMeta
from rotzx.providers import FetchResult


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
    meta = public_build.build(out, conn=conn, catalog=catalog, completo=True)  # a própria build roda verificar()
    assert meta["series"] == 1
    tudo = "".join(p.read_text(errors="ignore") for p in out.rglob("*") if p.suffix in (".json", ".html"))
    for proibido in ("md_xpto_pessoal", "zz9999", "XPTO - Faturamento", "Série md_xpto_pessoal"):
        assert proibido not in tudo
    assert "serie_publica" in tudo
    cat_pub = json.loads((out / "data" / "catalogo.json").read_text())
    assert [s["id"] for s in cat_pub] == ["serie_publica"]
    import sqlite3
    db = sqlite3.connect(out / "data" / "rotzx_publico.sqlite")
    assert db.execute("SELECT COUNT(*) FROM observations WHERE series_id = 'md_xpto_pessoal'").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM observations WHERE series_id = 'serie_publica'").fetchone()[0] == 120


def test_verifier_catches_disguised_personal_values(ambiente):
    conn, catalog, tmp = ambiente
    out = tmp / "site"
    public_build.build(out, conn=conn, catalog=catalog, completo=True)
    # valores da série pessoal copiados sob outro nome: tem de ser pego pela comparação de sequências
    vazado = payloads.series(conn, catalog, "md_xpto_pessoal", "nivel")["dados"]
    (out / "data" / "series" / "disfarce.json").write_text(json.dumps({"dados": vazado}))
    with pytest.raises(public_build.VazamentoPublico):
        public_build.verificar(out, catalog, conn)


def test_verifier_catches_personal_code_in_text(ambiente):
    conn, catalog, tmp = ambiente
    out = tmp / "site"
    public_build.build(out, conn=conn, catalog=catalog, completo=True)
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


def test_public_build_ships_every_script_the_page_loads(ambiente):
    import re
    conn, catalog, tmp = ambiente
    out = tmp / "site"
    public_build.build(out, conn=conn, catalog=catalog, completo=True)
    html = (out / "index.html").read_text()
    locais = [s.split("?")[0] for s in re.findall(r'<script src="([^"]+)"', html) if not s.startswith("http")]
    assert "texto.js" in locais and "app.js" in locais
    assert locais.index("texto.js") < locais.index("app.js")  # app.js usa window.Texto
    for nome in locais:
        assert (out / nome).exists(), nome


def test_site_completo_leva_o_globo_com_os_dados(ambiente):
    conn, catalog, tmp = ambiente
    out = tmp / "site"
    public_build.build(out, conn=conn, catalog=catalog, completo=True)
    assert (out / "globo" / "index.html").exists() and (out / "globo" / "dados" / "mundo.js").exists()
    assert not (out / "globo" / "LEIAME.md").exists()
    assert 'href="globo/"' in (out / "index.html").read_text(encoding="utf-8")  # link no menu do site


def test_site_publico_e_so_o_atlas_na_raiz(ambiente):
    """D53: o site público é o atlas na raiz; /globo/ redireciona levando o hash; nada dos radares é publicado."""
    import re
    conn, catalog, tmp = ambiente
    out = tmp / "site"
    public_build.build(out, conn=conn, catalog=catalog)
    html = (out / "index.html").read_text(encoding="utf-8")
    assert "Como o Brasil se conecta ao mundo" in html
    for local in re.findall(r'<script src="([^"]+)"', html):
        if not local.startswith("http"):
            assert (out / local.split("?")[0]).exists(), local
    for arq in ("dados/historia.js", "dados/produtos.js", "icone.svg", "icone-180.png", ".nojekyll"):
        assert (out / arq).exists(), arq
    assert not (out / "LEIAME.md").exists()
    assert not (out / "app.js").exists() and not (out / "data").exists()
    redir = (out / "globo" / "index.html").read_text(encoding="utf-8")
    assert 'location.replace("../" + location.hash)' in redir and 'href="../"' in redir
